"""Generic CRUD repository base class with flush-only transactions and safe pagination."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final, Generic, TypeVar

from sqlalchemy import Select, delete, func, inspect, select
from sqlalchemy.orm import InstrumentedAttribute, Session

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.detection import Base

__all__ = ["BaseRepository", "DEFAULT_PAGE_SIZE", "MAX_PAGE_SIZE"]

ModelT = TypeVar("ModelT", bound=Base)
"""The ORM class a repository manages."""

IdT = TypeVar("IdT")
"""Type of that class's primary key: ``int`` for history, ``str`` for jobs."""

DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 200
"""Hard ceiling on ``page_size``."""

_BULK_DELETE_CHUNK: Final[int] = 500
"""Identifiers per ``DELETE ... WHERE id IN (...)`` statement."""


class BaseRepository(Generic[ModelT, IdT]):
    """CRUD operations common to every ORM model."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        """Bind the repository to a session."""
        if not hasattr(self.__class__, "model"):
            raise TypeError(f"{self.__class__.__name__} must declare a 'model' class attribute")
        self.session = session

    # -- Introspection ----------------------------------------------------

    @property
    def _pk(self) -> InstrumentedAttribute[Any]:
        """Return the mapped attribute for this model's primary key."""
        mapper = inspect(self.model)
        columns = mapper.primary_key
        if len(columns) != 1:
            raise TypeError(
                f"{self.model.__name__} has a composite primary key; "
                "the generic repository methods require a single-column key"
            )
        return getattr(self.model, columns[0].name)

    # -- Create -----------------------------------------------------------

    def create(self, **fields: Any) -> ModelT:
        """Insert a new row built from keyword arguments."""
        entity = self.model(**fields)
        return self.add(entity)

    def add(self, entity: ModelT) -> ModelT:
        """Insert an instance that the caller has already constructed."""
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_all(self, entities: Sequence[ModelT]) -> list[ModelT]:
        """Insert several instances in one flush."""
        items = list(entities)
        if not items:
            return []
        self.session.add_all(items)
        self.session.flush()
        return items

    # -- Read -------------------------------------------------------------

    def get_by_id(self, entity_id: IdT) -> ModelT | None:
        """Fetch one row by primary key."""
        return self.session.get(self.model, entity_id)

    def get_or_raise(self, entity_id: IdT) -> ModelT:
        """Fetch one row by primary key, or raise a 404."""
        entity = self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError.for_resource(self.model.__tablename__, entity_id)
        return entity

    def exists(self, entity_id: IdT) -> bool:
        """Return whether a row with the given primary key exists."""
        stmt = select(1).select_from(self.model).where(self._pk == entity_id).limit(1)
        return self.session.execute(stmt).scalar() is not None

    def count(self) -> int:
        """Return the total number of rows in the table."""
        stmt = select(func.count()).select_from(self.model)
        return int(self.session.execute(stmt).scalar_one())

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        """Return rows in primary-key order."""
        stmt: Select[tuple[ModelT]] = select(self.model).order_by(self._pk)
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    # -- Update -----------------------------------------------------------

    def update(self, entity: ModelT, **fields: Any) -> ModelT:
        """Apply field updates to a loaded instance."""
        mapper = inspect(self.model)
        for name, value in fields.items():
            if name not in mapper.attrs:
                raise ValidationError(
                    f"{self.model.__name__} has no attribute {name!r}",
                    context={"model": self.model.__name__, "field": name},
                )
            setattr(entity, name, value)
        self.session.flush()
        return entity

    # -- Delete -----------------------------------------------------------

    def delete(self, entity_id: IdT) -> bool:
        """Delete one row by primary key."""
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        self.session.delete(entity)
        self.session.flush()
        return True

    def delete_instance(self, entity: ModelT) -> None:
        """Delete an already loaded instance."""
        self.session.delete(entity)
        self.session.flush()

    def bulk_delete(self, entity_ids: Sequence[IdT]) -> int:
        """Delete many rows by primary key in as few statements as possible."""
        unique_ids = list(dict.fromkeys(entity_ids))
        if not unique_ids:
            return 0

        deleted = 0
        for start in range(0, len(unique_ids), _BULK_DELETE_CHUNK):
            chunk = unique_ids[start : start + _BULK_DELETE_CHUNK]
            stmt = delete(self.model).where(self._pk.in_(chunk))
            result = self.session.execute(stmt, execution_options={"synchronize_session": False})
            deleted += result.rowcount or 0

        # Expire stale identity map entries after bulk delete
        self.session.expire_all()
        self.session.flush()
        return deleted

    # -- Pagination helpers -----------------------------------------------

    def paginate(
        self,
        stmt: Select[tuple[ModelT]],
        *,
        page: int,
        page_size: int,
        sort_by: str | None = None,
        sort_columns: Mapping[str, InstrumentedAttribute[Any]] | None = None,
        default_sort: InstrumentedAttribute[Any] | None = None,
        descending: bool = True,
    ) -> tuple[list[ModelT], int]:
        """Apply ordering and a page window to a filtered query."""
        page = max(1, page)
        page_size = max(1, min(page_size, MAX_PAGE_SIZE))

        total = self.count_for(stmt)

        column = self._resolve_sort_column(sort_by, sort_columns, default_sort)
        ordering = column.desc() if descending else column.asc()
        tiebreak = self._pk.desc() if descending else self._pk.asc()

        windowed = (
            stmt.order_by(None)
            .order_by(ordering, tiebreak)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(self.session.execute(windowed).scalars().all())
        return rows, total

    def count_for(self, stmt: Select[Any]) -> int:
        """Count the rows a filtered statement would return."""
        bare = stmt.order_by(None).limit(None).offset(None)
        counted = select(func.count()).select_from(bare.subquery())
        return int(self.session.execute(counted).scalar_one())

    def _resolve_sort_column(
        self,
        sort_by: str | None,
        sort_columns: Mapping[str, InstrumentedAttribute[Any]] | None,
        default_sort: InstrumentedAttribute[Any] | None,
    ) -> InstrumentedAttribute[Any]:
        """Translate a public sort name into a model attribute."""
        if sort_by is None:
            return default_sort if default_sort is not None else self._pk
        allowed = sort_columns or {}
        column = allowed.get(sort_by)
        if column is None:
            raise ValidationError(
                f"Unsupported sort key {sort_by!r} for {self.model.__name__}",
                user_message=(
                    "Tiêu chí sắp xếp không hợp lệ. "
                    "Vui lòng chọn một tiêu chí có trong danh sách."
                ),
                context={"sort_by": sort_by, "allowed": sorted(allowed)},
            )
        return column

    def __repr__(self) -> str:
        """Return a developer-facing representation naming the managed model."""
        return f"{self.__class__.__name__}(model={self.model.__name__})"
