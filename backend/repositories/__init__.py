"""The persistence layer: every SQL query in the backend lives below here.

Services depend on this package instead of on SQLAlchemy directly, which is
what keeps a schema change from rippling through the routers. The rule the
package exists to enforce is narrow but strict: **no module outside
``backend.repositories`` builds a query.** A router that reaches for
``session.execute(select(...))`` has quietly created a second place where the
history filter logic lives, and the two drift.

Repositories flush but never commit; the service layer owns the transaction
boundary. :mod:`backend.repositories.base` explains why in full.

The statistics contract
-----------------------
:class:`~backend.repositories.detection_repository.DetectionStatistics`
separates two counters that are easy to confuse and expensive to confuse:
``total_jobs`` counts **uploads** and ``total_detections`` counts **plates**.
One image containing three plates is one job and three detections. A dashboard
tile labelled "images processed" must read ``total_jobs``; reading
``total_detections`` there overstates usage by the average number of plates per
image, and the resulting figure is wrong in a way that looks entirely
believable.
"""

from __future__ import annotations

from backend.repositories.base import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    BaseRepository,
)
from backend.repositories.detection_repository import (
    DEFAULT_TREND_DAYS,
    HISTORY_SORT_COLUMNS,
    DailyCount,
    DetectionRepository,
    DetectionStatistics,
    HistoryFilter,
    InputTypeCount,
)
from backend.repositories.job_repository import JOB_SORT_COLUMNS, JobRepository

__all__ = [
    "BaseRepository",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "DetectionRepository",
    "HistoryFilter",
    "DetectionStatistics",
    "InputTypeCount",
    "DailyCount",
    "HISTORY_SORT_COLUMNS",
    "DEFAULT_TREND_DAYS",
    "JobRepository",
    "JOB_SORT_COLUMNS",
]
