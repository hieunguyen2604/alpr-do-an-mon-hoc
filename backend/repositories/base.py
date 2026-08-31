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
"""Hard ceiling on ``page_size``.

Without it, ``?page_size=1000000`` loads the entire history table into memory
and serialises it, which is a denial of service that costs the caller one
request to trigger. The ceiling is applied by clamping rather than by raising,
so a client asking for too much gets the maximum instead of an error.
"""

_BULK_DELETE_CHUNK: Final[int] = 500
"""Identifiers per ``DELETE ... WHERE id IN (...)`` statement.

SQLite's compiled-statement limit (``SQLITE_MAX_VARIABLE_NUMBER``) is 999 on
older builds. A user selecting every row on a large page and deleting them
would exceed it and get an opaque "too many SQL variables" error, so the
statement is split.
"""


class BaseRepository(Generic[ModelT, IdT]):
    """CRUD operations common to every ORM model.

    Subclasses set the :attr:`model` class attribute and add the queries that
    are specific to their table::

        class JobRepository(BaseRepository[DetectionJob, str]):
            model = DetectionJob

    Attributes:
        model: The ORM class this repository reads and writes. Must be set by
            every concrete subclass.
        session: The session all queries run on. Supplied by the caller rather
            than created here, so that several repositories used in one request
            share a transaction -- writing a job and its detections through two
            independently created sessions could not be rolled back as a unit.
    """

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        """Bind the repository to a session.

        Args:
            session: An open SQLAlchemy session. Its lifetime and its commit
                are the caller's responsibility.

        Raises:
            TypeError: If the subclass did not declare :attr:`model`. Caught
                here at construction rather than at the first query, where the
                failure would name a line that looks unrelated.
        """
        if not hasattr(self.__class__, "model"):
            raise TypeError(f"{self.__class__.__name__} must declare a 'model' class attribute")
        self.session = session

    # -- Introspection ----------------------------------------------------

    @property
    def _pk(self) -> InstrumentedAttribute[Any]:
        """Return the mapped attribute for this model's primary key.

        Resolved through SQLAlchemy's mapper instead of being hard-coded as
        ``self.model.id`` so that the generic methods keep working if a model
        ever names its key differently.

        Returns:
            The primary key attribute.

        Raises:
            TypeError: If the model uses a composite primary key, which the
                generic single-value lookups here cannot express.
        """
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
        """Insert a new row built from keyword arguments.

        Args:
            **fields: Column values for the new instance.

        Returns:
            The persisted instance, flushed so that its generated primary key
            and any server-side defaults are populated.
        """
        entity = self.model(**fields)
        return self.add(entity)

    def add(self, entity: ModelT) -> ModelT:
        """Insert an instance that the caller has already constructed.

        Used where the object is assembled elsewhere -- for example a
        :class:`~backend.models.detection.DetectionHistory` built field by
        field from an ``ai.inference`` result.

        Args:
            entity: The instance to persist.

        Returns:
            The same instance, flushed.
        """
        self.session.add(entity)
        self.session.flush()
        return entity

    def add_all(self, entities: Sequence[ModelT]) -> list[ModelT]:
        """Insert several instances in one flush.

        One flush rather than one per row is what keeps saving the plates of a
        single upload to a single round trip.

        Args:
            entities: Instances to persist. An empty sequence is a no-op.

        Returns:
            The persisted instances, in the order given.
        """
        items = list(entities)
        if not items:
            return []
        self.session.add_all(items)
        self.session.flush()
        return items

    # -- Read -------------------------------------------------------------

    def get_by_id(self, entity_id: IdT) -> ModelT | None:
        """Fetch one row by primary key.

        Args:
            entity_id: The primary key to look up.

        Returns:
            The instance, or ``None`` when no row has that key. Returning
            ``None`` rather than raising keeps "does this exist?" expressible
            without exception handling; use :meth:`get_or_raise` when absence
            is an error.
        """
        return self.session.get(self.model, entity_id)

    def get_or_raise(self, entity_id: IdT) -> ModelT:
        """Fetch one row by primary key, or raise a 404.

        Args:
            entity_id: The primary key to look up.

        Returns:
            The instance.

        Raises:
            NotFoundError: If no row has that key. The identifier is recorded
                in the error's log context; the user sees only the generic
                Vietnamese message (NFR-S4).
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError.for_resource(self.model.__tablename__, entity_id)
        return entity

    def exists(self, entity_id: IdT) -> bool:
        """Return whether a row with the given primary key exists.

        Issues a ``SELECT 1 ... LIMIT 1`` instead of loading the row, so an
        existence check on a wide table does not read every column.

        Args:
            entity_id: The primary key to test.

        Returns:
            ``True`` if the row exists.
        """
        stmt = select(1).select_from(self.model).where(self._pk == entity_id).limit(1)
        return self.session.execute(stmt).scalar() is not None

    def count(self) -> int:
        """Return the total number of rows in the table.

        Returns:
            The row count.
        """
        stmt = select(func.count()).select_from(self.model)
        return int(self.session.execute(stmt).scalar_one())

    def list_all(self, *, limit: int | None = None, offset: int = 0) -> list[ModelT]:
        """Return rows in primary-key order.

        Intended for small tables, fixtures and administrative scripts. The
        history table is paginated through :meth:`paginate` instead -- it may
        hold 100 000 rows (NFR-SC2), and loading those at once would exhaust
        memory long before the response was built.

        Args:
            limit: Maximum rows to return, or ``None`` for all of them.
            offset: Rows to skip.

        Returns:
            The matching instances.
        """
        stmt: Select[tuple[ModelT]] = select(self.model).order_by(self._pk)
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    # -- Update -----------------------------------------------------------

    def update(self, entity: ModelT, **fields: Any) -> ModelT:
        """Apply field updates to a loaded instance.

        Only attributes that already exist on the model are assigned. A typo in
        a caller's keyword would otherwise attach a stray Python attribute that
        is never written to the database and never reported -- the update would
        appear to succeed and change nothing.

        Args:
            entity: The instance to modify.
            **fields: New values, keyed by column name.

        Returns:
            The updated instance, flushed.

        Raises:
            ValidationError: If a keyword does not name a column of the model.
        """
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
        """Delete one row by primary key.

        Loads the instance before deleting it so that ORM-level cascades and
        relationship bookkeeping run. This matters for
        :class:`~backend.models.detection.DetectionJob`, whose detections are
        removed with it.

        Args:
            entity_id: The primary key to delete.

        Returns:
            ``True`` if a row was deleted, ``False`` if none matched. A missing
            row is not an error: deleting something already gone leaves the
            caller in exactly the state it asked for.
        """
        entity = self.get_by_id(entity_id)
        if entity is None:
            return False
        self.session.delete(entity)
        self.session.flush()
        return True

    def delete_instance(self, entity: ModelT) -> None:
        """Delete an already loaded instance.

        Args:
            entity: The instance to remove.
        """
        self.session.delete(entity)
        self.session.flush()

    def bulk_delete(self, entity_ids: Sequence[IdT]) -> int:
        """Delete many rows by primary key in as few statements as possible.

        Uses a bulk ``DELETE`` rather than loading each row, so removing a page
        of history costs one statement instead of one per row.

        The identifiers are chunked (see :data:`_BULK_DELETE_CHUNK`) because
        SQLite caps the number of bound parameters per statement, and duplicates
        are removed first so that a client sending the same id twice does not
        make the reported count exceed the number of rows actually affected.

        .. note::
           This bypasses ORM-level cascades. It is safe for
           :class:`~backend.models.detection.DetectionHistory`, which owns no
           children, and safe for :class:`DetectionJob` **only** because the
           foreign key declares ``ON DELETE CASCADE`` and
           :mod:`backend.models.database` switches SQLite's foreign key
           enforcement on for every connection. Without that pragma this method
           would silently orphan every detection of a deleted job.

        Args:
            entity_ids: Primary keys to delete. May contain duplicates.

        Returns:
            The number of rows actually deleted, which is at most the number of
            distinct identifiers supplied.
        """
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
        """Apply ordering and a page window to a filtered query.

        Both halves of a paginated response are produced here: the rows for the
        requested page, and the total number of rows matching the filters. The
        total is counted from the same statement with its ordering removed, so
        the count can never drift out of step with the filters -- the classic
        way for a paginated list to report a total that does not match what
        paging through it actually yields.

        A tie-breaker on the primary key is always appended to the ordering.
        Without it, rows sharing a ``detected_time`` -- which every plate from
        a single image does, since they are written in the same instant -- have
        no defined order between pages, so a row can appear on both page 1 and
        page 2 while another appears on neither.

        Args:
            stmt: A ``SELECT`` of :attr:`model` with all filters applied.
            page: 1-based page number. Values below 1 are clamped to 1.
            page_size: Rows per page, clamped to ``[1, MAX_PAGE_SIZE]``.
            sort_by: Name of the column to sort by, looked up in
                ``sort_columns``. ``None`` uses ``default_sort``.
            sort_columns: Allow-list mapping public sort names to model
                attributes.
            default_sort: Column used when ``sort_by`` is ``None``. Defaults to
                the primary key.
            descending: Sort direction; ``True`` puts newest first.

        Returns:
            A tuple of ``(rows for this page, total matching rows)``.

        Raises:
            ValidationError: If ``sort_by`` is not in ``sort_columns``.
        """
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
        """Count the rows a filtered statement would return.

        Args:
            stmt: A ``SELECT`` with filters applied. Its ordering, offset and
                limit are stripped -- an ``ORDER BY`` inside a counted subquery
                is pointless work, and a leftover ``LIMIT`` would cap the total
                at the page size, making every list claim it has exactly one
                page.

        Returns:
            The number of matching rows.
        """
        bare = stmt.order_by(None).limit(None).offset(None)
        counted = select(func.count()).select_from(bare.subquery())
        return int(self.session.execute(counted).scalar_one())

    def _resolve_sort_column(
        self,
        sort_by: str | None,
        sort_columns: Mapping[str, InstrumentedAttribute[Any]] | None,
        default_sort: InstrumentedAttribute[Any] | None,
    ) -> InstrumentedAttribute[Any]:
        """Translate a public sort name into a model attribute.

        Args:
            sort_by: Requested sort key, or ``None``.
            sort_columns: Allow-list of acceptable keys.
            default_sort: Fallback column.

        Returns:
            The attribute to order by.

        Raises:
            ValidationError: If the key is not in the allow-list. The message
                lists the accepted keys, which is genuinely useful to an API
                consumer and reveals nothing about the schema that the response
                model does not already document.
        """
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
