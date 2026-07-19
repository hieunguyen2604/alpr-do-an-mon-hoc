"""A local, keyboard-driven tool for hand-labelling plate crops.

Why a tool at all
-----------------
Labelling several hundred plates by hand is a chore measured in the seconds it
takes per image. Anything that adds a second -- hunting for the next file,
remembering whether a plate was already done, re-typing a hyphen -- multiplies
by five hundred. This tool exists to drive that per-image cost down to a couple
of keystrokes: look, type, press Enter.

Design constraints
------------------
**Standard library only.** The server is :mod:`http.server`. No web framework is
involved, which keeps the labelling step free of the API layer's dependencies
and keeps this script honest about NFR-M1: nothing under ``ai/`` gains a
framework import because of it. It also means the tool runs from any virtual
environment that has the project on its path.

**Local only.** The socket binds to the loopback address. There is no
authentication because there is no network exposure; do not change the bind
address without adding one.

**Autosave, always.** Every answer is flushed to CSV before the browser is told
the save succeeded. A closed laptop lid must never cost more than the plate
currently on screen. Restarting resumes at the first unanswered crop.

**Validation is the real thing.** The green tick comes from
:class:`~ai.inference.normalizer.VietnamesePlateNormalizer`, the same code the
pipeline uses. A hand-written copy of the rules would drift from it, and the
labels would then encode a format the system does not actually accept. When the
normalizer cannot be imported the tool still works and simply says so, because
being unable to check the format is a much smaller problem than being unable to
label at all.

Usage::

    python scripts/labeling/label_tool.py
    python scripts/labeling/label_tool.py --port 9000 --no-browser
"""

from __future__ import annotations

import argparse
import csv
import http.server
import json
import logging
import os
import socketserver
import sys
import threading
import webbrowser
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Sequence
from urllib.parse import parse_qs, urlparse

__all__ = [
    "PROJECT_ROOT",
    "LABEL_FIELDNAMES",
    "BadRequestError",
    "CropItem",
    "LabelRecord",
    "LabelStore",
    "build_handler",
    "load_manifest",
    "main",
    "serve",
]

LOGGER = logging.getLogger("labeling.label_tool")

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repository root, derived from ``<root>/scripts/labeling/label_tool.py``."""

LABEL_FIELDNAMES: Final[tuple[str, ...]] = (
    "crop_file",
    "source_image",
    "plate_text",
    "line_count",
    "is_skipped",
    "labeled_at",
)
"""Column order of ``plate_labels.csv``. Fixed -- downstream evaluation reads it."""

DEFAULT_PORT: Final[int] = 8765
"""Default loopback port. Chosen high enough to need no privileges."""

class BadRequestError(Exception):
    """A request the browser got wrong, carrying a message meant for the user.

    Distinct from :class:`KeyError` and friends on purpose: ``str()`` of a
    ``KeyError`` re-quotes its argument, so the Vietnamese message would reach
    the browser wrapped in stray quote marks. This exception renders cleanly and
    also makes the boundary explicit -- what it carries is user-facing text, not
    a diagnostic.
    """


_KIND_LABELS_VI: Final[dict[str, str]] = {
    "car": "Ô tô",
    "motorcycle_new": "Xe máy (kiểu mới)",
    "motorcycle_old": "Xe máy (kiểu cũ)",
    "blue_car": "Ô tô nền xanh",
    "blue_motorcycle": "Xe máy nền xanh",
    "special": "Biển đặc biệt",
    "diplomatic": "Biển ngoại giao",
    "military": "Biển quân đội",
    "unknown": "Không nhận dạng được",
}
"""Vietnamese display names for plate families, used in the browser only."""


@dataclass(frozen=True, slots=True)
class CropItem:
    """One crop waiting to be labelled, as read from the extraction manifest.

    Attributes:
        crop_file: File name of the crop, and the join key to the label CSV.
        source_image: File name of the image the crop came from.
        aspect_ratio: Width/height of the original ground-truth box.
        estimated_lines: Line count guessed from the aspect ratio, used to
            pre-select the radio button. The human overrides it when wrong.
    """

    crop_file: str
    source_image: str
    aspect_ratio: float
    estimated_lines: int


@dataclass(frozen=True, slots=True)
class LabelRecord:
    """One answer given by the person labelling.

    A skipped crop is recorded, not omitted. "This image is unreadable" is a
    finding about the dataset, and dropping it would quietly shrink the
    denominator of every accuracy figure computed later.

    Attributes:
        crop_file: Which crop this answers.
        source_image: Carried through from the manifest so the CSV is readable
            without a join.
        plate_text: The plate string in canonical form -- upper case, no
            separators. Empty when the crop was skipped.
        line_count: ``1`` or ``2``.
        is_skipped: ``True`` when the plate could not be read.
        labeled_at: ISO-8601 UTC timestamp of the answer.
    """

    crop_file: str
    source_image: str
    plate_text: str
    line_count: int
    is_skipped: bool
    labeled_at: str

    def as_row(self) -> dict[str, Any]:
        """Return the record as a CSV row.

        Returns:
            A mapping keyed by :data:`LABEL_FIELDNAMES`, with the boolean
            rendered as ``true``/``false`` so the file stays readable in Excel
            and unambiguous to parse back.
        """
        return {
            "crop_file": self.crop_file,
            "source_image": self.source_image,
            "plate_text": self.plate_text,
            "line_count": self.line_count,
            "is_skipped": "true" if self.is_skipped else "false",
            "labeled_at": self.labeled_at,
        }


@dataclass(slots=True)
class LabelStore:
    """The label file, kept in memory and rewritten on every change.

    Rewriting the whole file rather than appending is a deliberate trade. The
    file holds a few hundred rows, so a rewrite costs under a millisecond, and
    in exchange re-answering a crop replaces its row instead of adding a second
    one. An append-only file would need a de-duplication pass before it could be
    used, and that pass would be one more place to get the answer wrong.

    Writes go to a temporary file and are then moved into place, so an
    interruption mid-write leaves the previous good file intact rather than a
    truncated one.

    Attributes:
        csv_path: Where labels are persisted.
        records: Answers keyed by crop file name, in insertion order.
    """

    csv_path: Path
    records: dict[str, LabelRecord] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def load(self) -> int:
        """Read any existing answers back in, so a rerun resumes where it stopped.

        Rows that are malformed or name a column set this tool does not
        recognise are skipped with a warning rather than aborting the run: the
        cost of losing one hand-made label is far lower than the cost of the
        tool refusing to start.

        Returns:
            The number of answers loaded.

        Raises:
            OSError: If the file exists but cannot be read.
        """
        if not self.csv_path.is_file():
            LOGGER.info("No existing label file; starting fresh at %s", self.csv_path)
            return 0

        loaded = 0
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line_number, row in enumerate(csv.DictReader(handle), start=2):
                crop_file = (row.get("crop_file") or "").strip()
                if not crop_file:
                    LOGGER.warning("Row %d has no crop_file; skipping", line_number)
                    continue
                try:
                    line_count = int(row.get("line_count") or 1)
                except ValueError:
                    LOGGER.warning(
                        "Row %d has a non-numeric line_count; defaulting to 1",
                        line_number,
                    )
                    line_count = 1

                self.records[crop_file] = LabelRecord(
                    crop_file=crop_file,
                    source_image=(row.get("source_image") or "").strip(),
                    plate_text=(row.get("plate_text") or "").strip().upper(),
                    line_count=line_count if line_count in (1, 2) else 1,
                    is_skipped=str(row.get("is_skipped", "")).strip().lower()
                    in {"true", "1", "yes"},
                    labeled_at=(row.get("labeled_at") or "").strip(),
                )
                loaded += 1

        LOGGER.info("Resumed %d existing labels from %s", loaded, self.csv_path)
        return loaded

    def upsert(self, record: LabelRecord) -> int:
        """Record one answer and flush the whole file to disk.

        Args:
            record: The answer. Replaces any previous answer for the same crop.

        Returns:
            The total number of answers held after the update.

        Raises:
            OSError: If the file cannot be written. The in-memory state is
                rolled back so it never claims a durability the disk does not
                have.
        """
        with self._lock:
            previous = self.records.get(record.crop_file)
            self.records[record.crop_file] = record
            try:
                self._flush_locked()
            except OSError:
                if previous is None:
                    self.records.pop(record.crop_file, None)
                else:
                    self.records[record.crop_file] = previous
                raise
            return len(self.records)

    def _flush_locked(self) -> None:
        """Write every held answer to disk. The caller must hold the lock.

        Raises:
            OSError: If the file cannot be written or moved into place.
        """
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.csv_path.with_suffix(self.csv_path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(LABEL_FIELDNAMES))
            writer.writeheader()
            for record in self.records.values():
                writer.writerow(record.as_row())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.csv_path)


def load_manifest(manifest_path: Path) -> list[CropItem]:
    """Read the crop manifest produced by ``extract_plates.py``.

    Args:
        manifest_path: The manifest CSV.

    Returns:
        One :class:`CropItem` per row, in file order.

    Raises:
        FileNotFoundError: If the manifest does not exist -- which almost always
            means ``extract_plates.py`` has not been run yet.
        ValueError: If the file has no usable rows.
    """
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Manifest not found: {manifest_path}. "
            "Run scripts/labeling/extract_plates.py first."
        )

    items: list[CropItem] = []
    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, row in enumerate(csv.DictReader(handle), start=2):
            crop_file = (row.get("crop_file") or "").strip()
            if not crop_file:
                LOGGER.warning("Manifest row %d has no crop_file", line_number)
                continue
            try:
                aspect_ratio = float(row.get("aspect_ratio") or 0.0)
                estimated_lines = int(row.get("estimated_lines") or 1)
            except ValueError:
                LOGGER.warning(
                    "Manifest row %d has unusable numbers; defaulting", line_number
                )
                aspect_ratio, estimated_lines = 0.0, 1
            items.append(
                CropItem(
                    crop_file=crop_file,
                    source_image=(row.get("source_image") or "").strip(),
                    aspect_ratio=aspect_ratio,
                    estimated_lines=estimated_lines if estimated_lines in (1, 2) else 1,
                )
            )

    if not items:
        raise ValueError(f"Manifest contains no usable rows: {manifest_path}")
    return items


class _Validator:
    """Thin wrapper that keeps the tool usable when the normalizer is absent.

    The normalizer lives under ``ai/`` and pulls NumPy in through the shared
    type definitions. If the interpreter running this tool cannot import it, the
    right behaviour is to carry on labelling without the live format check --
    not to refuse to start. The failure is reported once, at start-up, and then
    surfaced in the browser so the person labelling knows the tick is missing
    rather than wondering why nothing ever validates.
    """

    def __init__(self) -> None:
        """Try to import the pipeline normalizer, recording why if it fails."""
        self._normalizer: Any = None
        self.error: str | None = None

        root = str(PROJECT_ROOT)
        if root not in sys.path:
            sys.path.insert(0, root)
        try:
            from ai.inference.normalizer import VietnamesePlateNormalizer

            self._normalizer = VietnamesePlateNormalizer()
            LOGGER.info("Live format checking enabled (pipeline normalizer loaded)")
        except Exception as exc:  # noqa: BLE001 - any import failure degrades the same way
            self.error = f"{type(exc).__name__}: {exc}"
            LOGGER.warning(
                "Normalizer unavailable, labelling will run without the live "
                "format check: %s",
                self.error,
            )

    @property
    def available(self) -> bool:
        """Return ``True`` when the live format check is working."""
        return self._normalizer is not None

    def check(self, text: str, line_count: int | None) -> dict[str, Any]:
        """Validate a typed plate string.

        Args:
            text: What the person has typed so far, already upper-cased and
                stripped of separators by the browser.
            line_count: ``1`` or ``2`` when the radio button is set, else
                ``None``. Forwarded to the normalizer, which uses it to settle
                the car / old-motorcycle ambiguity.

        Returns:
            A JSON-ready mapping with keys ``available``, ``valid``,
            ``normalized``, ``display``, ``kind``, ``kind_label``,
            ``is_ambiguous`` and ``corrected``. When the normalizer is missing,
            ``available`` is ``False`` and the rest carry neutral values -- the
            browser then shows a muted notice instead of a misleading cross.
        """
        if self._normalizer is None:
            return {
                "available": False,
                "valid": False,
                "normalized": text,
                "display": text,
                "kind": "unknown",
                "kind_label": _KIND_LABELS_VI["unknown"],
                "is_ambiguous": False,
                "corrected": False,
                "error": self.error,
            }

        outcome = self._normalizer.normalize_detailed(text, line_count=line_count)
        kind = str(outcome.decision.kind)
        return {
            "available": True,
            "valid": bool(outcome.is_valid_format),
            "normalized": outcome.text,
            "display": self._normalizer.format_for_display(
                outcome.text, line_count=line_count
            ),
            "kind": kind,
            "kind_label": _KIND_LABELS_VI.get(kind, kind),
            "is_ambiguous": bool(outcome.decision.is_ambiguous),
            "corrected": bool(outcome.corrections),
        }


def _now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string with second precision.

    Returns:
        A timestamp such as ``"2026-07-19T15:04:59+00:00"``.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_handler(
    *,
    items: Sequence[CropItem],
    store: LabelStore,
    crops_dir: Path,
    validator: _Validator,
) -> type[http.server.BaseHTTPRequestHandler]:
    """Create the request handler class, closed over the tool's state.

    A factory rather than a module-level class: :mod:`http.server` instantiates
    the handler afresh for every request and offers no way to pass arguments in,
    so the state has to arrive through a closure. Building it here also keeps
    the paths and the store out of module-level globals, which makes the tool
    testable.

    Args:
        items: Every crop to label, in display order.
        store: Where answers are persisted.
        crops_dir: Directory the crop images are served from.
        validator: The live format checker.

    Returns:
        A handler class ready to be passed to a :mod:`socketserver` server.
    """
    items_by_name = {item.crop_file: item for item in items}

    class LabelRequestHandler(http.server.BaseHTTPRequestHandler):
        """Serves the labelling page, the crop images and the tiny JSON API."""

        server_version = "PlateLabelTool/1.0"
        protocol_version = "HTTP/1.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            """Route the server's own access log into the project logger.

            Args:
                format: A printf-style template, named by the base class.
                *args: Its arguments.
            """
            LOGGER.debug("%s - %s", self.address_string(), format % args)

        def do_GET(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
            """Dispatch a GET request."""
            parsed = urlparse(self.path)
            route = parsed.path

            try:
                if route in ("/", "/index.html"):
                    self._send_bytes(
                        _render_page().encode("utf-8"), "text/html; charset=utf-8"
                    )
                elif route == "/api/items":
                    self._send_json(self._items_payload())
                elif route == "/api/validate":
                    query = parse_qs(parsed.query)
                    text = (query.get("text", [""])[0] or "").upper()
                    raw_lines = query.get("line_count", [""])[0]
                    line_count = int(raw_lines) if raw_lines in ("1", "2") else None
                    self._send_json(validator.check(text, line_count))
                elif route.startswith("/crops/"):
                    self._send_crop(route[len("/crops/") :])
                else:
                    self._send_json({"error": "Không tìm thấy đường dẫn"}, status=404)
            except BrokenPipeError:
                LOGGER.debug("Client disconnected mid-response")
            except Exception as exc:  # noqa: BLE001 - never let one request kill the tool
                LOGGER.exception("Unhandled error serving %s", route)
                self._send_json({"error": str(exc)}, status=500)

        def do_POST(self) -> None:  # noqa: N802 - name fixed by BaseHTTPRequestHandler
            """Dispatch a POST request."""
            if urlparse(self.path).path != "/api/label":
                self._send_json({"error": "Không tìm thấy đường dẫn"}, status=404)
                return

            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                self._send_json({"error": "Content-Length không hợp lệ"}, status=400)
                return
            if length <= 0 or length > 1_000_000:
                self._send_json({"error": "Nội dung rỗng hoặc quá lớn"}, status=400)
                return

            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                self._send_json({"error": f"JSON không hợp lệ: {exc}"}, status=400)
                return

            try:
                self._send_json(self._save_label(payload))
            except BadRequestError as exc:
                self._send_json({"error": str(exc)}, status=400)
            except OSError as exc:
                LOGGER.error("Cannot persist label: %s", exc)
                self._send_json(
                    {"error": f"Không ghi được tệp nhãn: {exc}"}, status=500
                )

        def _save_label(self, payload: dict[str, Any]) -> dict[str, Any]:
            """Validate an incoming answer, store it, and report the new totals.

            Args:
                payload: The decoded JSON body. Must carry ``crop_file``; may
                    carry ``plate_text``, ``line_count`` and ``is_skipped``.

            Returns:
                A mapping with ``ok``, ``labeled`` and ``total``.

            Raises:
                BadRequestError: If the crop is unknown or a non-skipped answer
                    carries no text. Rejecting an empty answer is the point: an
                    empty string and "unreadable" mean different things, and only
                    the explicit skip is allowed to record the latter.
                OSError: If the label file cannot be written.
            """
            crop_file = str(payload.get("crop_file") or "")
            item = items_by_name.get(crop_file)
            if item is None:
                raise BadRequestError(f"Không biết ảnh cắt: {crop_file}")

            is_skipped = bool(payload.get("is_skipped"))
            plate_text = str(payload.get("plate_text") or "").strip().upper()
            if not is_skipped and not plate_text:
                raise BadRequestError(
                    "Chuỗi biển số rỗng: hãy nhập nội dung hoặc bấm Bỏ qua"
                )

            line_count = payload.get("line_count", item.estimated_lines)
            try:
                line_count = int(line_count)
            except (TypeError, ValueError):
                line_count = item.estimated_lines
            if line_count not in (1, 2):
                line_count = item.estimated_lines

            total = store.upsert(
                LabelRecord(
                    crop_file=crop_file,
                    source_image=item.source_image,
                    plate_text="" if is_skipped else plate_text,
                    line_count=line_count,
                    is_skipped=is_skipped,
                    labeled_at=_now_iso(),
                )
            )
            LOGGER.info(
                "Saved label %s (%d/%d done)",
                "SKIP" if is_skipped else plate_text,
                total,
                len(items),
            )
            return {"ok": True, "labeled": total, "total": len(items)}

        def _items_payload(self) -> dict[str, Any]:
            """Build the whole work list for the browser.

            The list is sent once at start-up rather than one item per request.
            A few hundred rows is a trivial payload, and having it client-side
            means moving between plates costs no round trip -- which is the
            difference between a tool that feels instant and one that does not.

            Returns:
                A mapping with the item list, the existing answers, the index to
                resume from, and whether live validation is available.
            """
            payload_items = []
            for item in items:
                record = store.records.get(item.crop_file)
                entry: dict[str, Any] = asdict(item)
                entry["label"] = record.as_row() if record is not None else None
                payload_items.append(entry)

            first_unlabeled = next(
                (
                    index
                    for index, item in enumerate(items)
                    if item.crop_file not in store.records
                ),
                0,
            )
            return {
                "items": payload_items,
                "labeled": len(store.records),
                "total": len(items),
                "start_index": first_unlabeled,
                "validation_available": validator.available,
                "validation_error": validator.error,
                "csv_path": str(store.csv_path),
            }

        def _send_crop(self, name: str) -> None:
            """Serve one crop image.

            The name is checked against the manifest rather than sanitised.
            Whitelisting is what makes path traversal impossible here: a name
            that is not a known crop is simply not served, so ``..`` and
            absolute paths never reach the filesystem at all.

            Args:
                name: The requested crop file name.
            """
            if name not in items_by_name:
                self._send_json({"error": "Không có ảnh này"}, status=404)
                return

            path = crops_dir / name
            if not path.is_file():
                LOGGER.warning("Crop listed in the manifest is missing: %s", path)
                self._send_json({"error": "Tệp ảnh không tồn tại"}, status=404)
                return

            suffix = path.suffix.lower()
            content_type = "image/png" if suffix == ".png" else "image/jpeg"
            self._send_bytes(path.read_bytes(), content_type, cache=True)

        def _send_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
            """Serialise a mapping and send it as a JSON response.

            Args:
                payload: The body.
                status: HTTP status code.
            """
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(body, "application/json; charset=utf-8", status=status)

        def _send_bytes(
            self,
            body: bytes,
            content_type: str,
            *,
            status: int = 200,
            cache: bool = False,
        ) -> None:
            """Send a complete response.

            Args:
                body: The response body.
                content_type: Its media type.
                status: HTTP status code.
                cache: Allow the browser to cache it. Set for crop images, which
                    never change, and left off for the API, whose answers do.
            """
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header(
                "Cache-Control", "max-age=3600" if cache else "no-store"
            )
            self.end_headers()
            self.wfile.write(body)

    return LabelRequestHandler


class _ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """A threaded server whose worker threads die with the process.

    Threading matters even for a single user: the browser opens several
    connections at once for the page and its images, and a single-threaded
    server would serialise them behind whichever request arrived first. HTTP
    keep-alive makes that visible as a stalled page rather than a slow one.
    """

    daemon_threads = True
    allow_reuse_address = True


def serve(
    *,
    items: Sequence[CropItem],
    store: LabelStore,
    crops_dir: Path,
    validator: _Validator,
    host: str = "127.0.0.1",
    port: int = DEFAULT_PORT,
    open_browser: bool = True,
) -> None:
    """Run the labelling server until interrupted.

    Args:
        items: Crops to label.
        store: Where answers are persisted.
        crops_dir: Directory holding the crop images.
        validator: The live format checker.
        host: Bind address. Keep it on loopback -- see the module docstring.
        port: TCP port.
        open_browser: Open the default browser at the tool's URL on start-up.

    Raises:
        OSError: If the port cannot be bound, typically because another copy of
            the tool is already running.
    """
    handler = build_handler(
        items=items, store=store, crops_dir=crops_dir, validator=validator
    )
    url = f"http://{host}:{port}/"

    with _ThreadingHTTPServer((host, port), handler) as server:
        LOGGER.info("Labelling tool ready at %s", url)
        LOGGER.info("Labels are written to %s", store.csv_path)
        LOGGER.info("Press Ctrl+C to stop")
        if open_browser:
            threading.Timer(0.5, webbrowser.open, args=(url,)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            LOGGER.info("Stopping; %d labels saved", len(store.records))


def _render_page() -> str:
    """Return the labelling page.

    The page is one self-contained document with no external asset, so the tool
    needs no static-file plumbing and works with no network at all.

    Returns:
        The complete HTML document.
    """
    return _PAGE_HTML


_PAGE_HTML: Final[str] = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gán nhãn biển số</title>
<style>
  :root {
    --bg: #12141a; --panel: #1c1f27; --line: #2c313d;
    --text: #e8eaf0; --muted: #9aa2b4;
    --ok: #34d399; --warn: #fbbf24; --bad: #f87171; --accent: #60a5fa;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: "Segoe UI", system-ui, sans-serif; font-size: 15px;
  }
  .wrap { max-width: 1000px; margin: 0 auto; padding: 18px 20px 40px; }
  header { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; }
  h1 { font-size: 19px; margin: 0; font-weight: 600; }
  .counter { color: var(--muted); font-variant-numeric: tabular-nums; }
  .bar { height: 8px; background: var(--panel); border-radius: 4px; margin: 12px 0 18px; overflow: hidden; }
  .bar > div { height: 100%; width: 0; background: var(--accent); transition: width .18s ease; }
  .stage {
    background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
    padding: 16px; display: flex; align-items: center; justify-content: center;
    min-height: 230px; overflow-x: auto;
  }
  .stage img { max-width: 100%; image-rendering: -webkit-optimize-contrast; border-radius: 4px; }
  .meta { color: var(--muted); font-size: 13px; margin: 8px 2px 16px; word-break: break-all; }
  .row { display: flex; gap: 14px; align-items: stretch; flex-wrap: wrap; }
  input[type=text] {
    flex: 1 1 320px; min-width: 260px; padding: 14px 16px;
    font-size: 30px; font-weight: 600; letter-spacing: 3px;
    font-family: "Cascadia Mono", Consolas, monospace;
    background: #0d0f14; color: var(--text);
    border: 2px solid var(--line); border-radius: 8px; outline: none;
  }
  input[type=text]:focus { border-color: var(--accent); }
  .verdict {
    flex: 1 1 300px; min-width: 260px; padding: 12px 16px;
    border: 1px solid var(--line); border-radius: 8px; background: #0d0f14;
    display: flex; flex-direction: column; justify-content: center; gap: 4px;
  }
  .verdict .headline { font-size: 17px; font-weight: 600; }
  .verdict .detail { color: var(--muted); font-size: 13px; }
  .ok  .headline { color: var(--ok); }
  .warn .headline { color: var(--warn); }
  .off .headline { color: var(--muted); }
  fieldset { border: 1px solid var(--line); border-radius: 8px; margin: 16px 0; padding: 10px 14px; }
  legend { color: var(--muted); font-size: 13px; padding: 0 6px; }
  label.opt { margin-right: 20px; cursor: pointer; }
  .guessed { color: var(--muted); font-size: 12px; }
  .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }
  button {
    font: inherit; padding: 11px 18px; border-radius: 8px; cursor: pointer;
    border: 1px solid var(--line); background: var(--panel); color: var(--text);
  }
  button:hover { border-color: var(--accent); }
  button.primary { background: var(--accent); border-color: var(--accent); color: #0b1020; font-weight: 600; }
  .hint { color: var(--muted); font-size: 13px; margin-top: 18px; line-height: 1.7; }
  kbd {
    background: var(--panel); border: 1px solid var(--line); border-bottom-width: 2px;
    border-radius: 4px; padding: 1px 6px; font-family: inherit; font-size: 12px;
  }
  .toast {
    position: fixed; left: 50%; bottom: 26px; transform: translateX(-50%);
    background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
    padding: 10px 18px; opacity: 0; transition: opacity .2s ease; pointer-events: none;
  }
  .toast.show { opacity: 1; }
  .toast.error { border-color: var(--bad); color: var(--bad); }
  .done { text-align: center; padding: 40px 0; }
  .done h2 { color: var(--ok); }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Gán nhãn biển số</h1>
    <span class="counter" id="counter">đang tải…</span>
  </header>
  <div class="bar"><div id="progress"></div></div>

  <div id="app" hidden>
    <div class="stage"><img id="crop" alt="Ảnh biển số đã cắt"></div>
    <div class="meta" id="meta"></div>

    <div class="row">
      <input type="text" id="plate" autocomplete="off" autocapitalize="characters"
             spellcheck="false" placeholder="Ví dụ 51G49539">
      <div class="verdict off" id="verdict">
        <div class="headline" id="verdictHead">Chưa nhập</div>
        <div class="detail" id="verdictDetail">Gõ liền, không dấu cách, không gạch ngang.</div>
      </div>
    </div>

    <fieldset>
      <legend>Số dòng trên biển</legend>
      <label class="opt"><input type="radio" name="lines" value="1"> 1 dòng</label>
      <label class="opt"><input type="radio" name="lines" value="2"> 2 dòng</label>
      <span class="guessed" id="guessed"></span>
    </fieldset>

    <div class="actions">
      <button class="primary" id="save">Lưu và tiếp (Enter)</button>
      <button id="skip">Bỏ qua – không đọc được (Ctrl+Enter)</button>
      <button id="back">← Quay lại (Alt+←)</button>
      <button id="forward">Bỏ trống, sang ảnh sau (Alt+→) →</button>
    </div>

    <p class="hint">
      <kbd>Enter</kbd> lưu và sang ảnh kế &nbsp;·&nbsp;
      <kbd>Ctrl</kbd>+<kbd>Enter</kbd> bỏ qua ảnh không đọc được &nbsp;·&nbsp;
      <kbd>Alt</kbd>+<kbd>←</kbd> / <kbd>Alt</kbd>+<kbd>→</kbd> chuyển ảnh &nbsp;·&nbsp;
      <kbd>Alt</kbd>+<kbd>1</kbd> / <kbd>Alt</kbd>+<kbd>2</kbd> chọn số dòng<br>
      Chữ tự động viết hoa; dấu cách, gạch ngang và dấu chấm bị bỏ tự động.
      Mỗi ảnh được lưu ngay vào tệp CSV, đóng trình duyệt không mất dữ liệu.
    </p>
  </div>

  <div class="done" id="done" hidden>
    <h2>Đã gán nhãn xong toàn bộ ảnh.</h2>
    <p class="hint">Có thể dùng <kbd>Alt</kbd>+<kbd>←</kbd> để quay lại sửa, hoặc tắt cửa sổ dòng lệnh.</p>
    <div class="actions" style="justify-content:center">
      <button id="reviewBack">← Quay lại ảnh cuối</button>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
"use strict";
const state = { items: [], index: 0, total: 0, labeled: 0, validation: true };

const el = (id) => document.getElementById(id);
const plateInput = el("plate");

/** Show a short-lived message at the bottom of the screen. */
let toastTimer = null;
function toast(message, isError) {
  const node = el("toast");
  node.textContent = message;
  node.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { node.className = "toast"; }, isError ? 4000 : 1200);
}

/** Strip everything that is not a plate character and upper-case the rest. */
function clean(value) {
  return value.toUpperCase().replace(/[^A-Z0-9]/g, "");
}

/** Count how many crops already carry an answer. */
function countLabeled() {
  return state.items.reduce((n, item) => n + (item.label ? 1 : 0), 0);
}

/** Repaint the counter and the progress bar. */
function renderProgress() {
  state.labeled = countLabeled();
  el("counter").textContent =
    "đã gán " + state.labeled + " / " + state.total +
    "  ·  đang xem ảnh thứ " + (state.index + 1);
  el("progress").style.width = (state.total ? (100 * state.labeled / state.total) : 0) + "%";
}

/** Load the crop at the current index into the form. */
function renderItem() {
  const item = state.items[state.index];
  if (!item) { return; }
  el("crop").src = "/crops/" + encodeURIComponent(item.crop_file);
  el("meta").textContent =
    item.crop_file + "  ·  ảnh gốc: " + item.source_image +
    "  ·  tỉ lệ ngang/dọc: " + item.aspect_ratio.toFixed(2);
  el("guessed").textContent =
    "(máy đoán " + item.estimated_lines + " dòng theo tỉ lệ khung — sửa nếu sai)";

  const previous = item.label;
  plateInput.value = previous ? previous.plate_text : "";
  const lines = previous ? String(previous.line_count) : String(item.estimated_lines);
  const radio = document.querySelector('input[name=lines][value="' + lines + '"]');
  if (radio) { radio.checked = true; }

  plateInput.focus();
  plateInput.select();
  renderProgress();
  validate();
}

/** Ask the server whether the typed string is a valid Vietnamese plate. */
let validateTimer = null;
function validate() {
  clearTimeout(validateTimer);
  validateTimer = setTimeout(runValidate, 90);
}

async function runValidate() {
  const box = el("verdict");
  const head = el("verdictHead");
  const detail = el("verdictDetail");
  const text = plateInput.value;

  if (!state.validation) {
    box.className = "verdict off";
    head.textContent = "Không kiểm tra được định dạng";
    detail.textContent = "Không nạp được bộ chuẩn hoá; vẫn gán nhãn bình thường.";
    return;
  }
  if (!text) {
    box.className = "verdict off";
    head.textContent = "Chưa nhập";
    detail.textContent = "Gõ liền, không dấu cách, không gạch ngang.";
    return;
  }

  const params = new URLSearchParams({ text: text, line_count: currentLines() });
  try {
    const response = await fetch("/api/validate?" + params.toString());
    const data = await response.json();
    if (data.valid) {
      box.className = "verdict ok";
      head.textContent = "✔ Hợp lệ — " + data.display;
      detail.textContent = data.kind_label + (data.is_ambiguous ? " (có thể lẫn loại khác)" : "");
    } else {
      box.className = "verdict warn";
      head.textContent = "⚠ Chưa khớp định dạng nào";
      detail.textContent = "Vẫn lưu được — hãy kiểm tra lại xem có gõ nhầm không.";
    }
  } catch (error) {
    box.className = "verdict off";
    head.textContent = "Không gọi được máy chủ";
    detail.textContent = String(error);
  }
}

/** Return the line count currently selected in the radio group. */
function currentLines() {
  const checked = document.querySelector("input[name=lines]:checked");
  return checked ? checked.value : "";
}

/** Move to another crop, clamping at both ends. */
function goTo(index) {
  if (index < 0) { toast("Đang ở ảnh đầu tiên"); return; }
  if (index >= state.total) { showDone(); return; }
  el("app").hidden = false;
  el("done").hidden = true;
  state.index = index;
  renderItem();
}

function showDone() {
  el("app").hidden = true;
  el("done").hidden = false;
  state.index = state.total;
  renderProgress();
}

/** Persist the current answer, then advance. */
async function submit(isSkipped) {
  const item = state.items[state.index];
  if (!item) { return; }
  const text = clean(plateInput.value);
  if (!isSkipped && !text) {
    toast("Chưa nhập biển số. Dùng Ctrl+Enter nếu ảnh không đọc được.", true);
    return;
  }

  const body = {
    crop_file: item.crop_file,
    plate_text: text,
    line_count: Number(currentLines()) || item.estimated_lines,
    is_skipped: Boolean(isSkipped)
  };

  try {
    const response = await fetch("/api/label", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const data = await response.json();
    if (!response.ok) {
      toast(data.error || "Lưu thất bại", true);
      return;
    }
    item.label = {
      crop_file: item.crop_file,
      source_image: item.source_image,
      plate_text: isSkipped ? "" : text,
      line_count: body.line_count,
      is_skipped: isSkipped ? "true" : "false",
      labeled_at: ""
    };
    toast(isSkipped ? "Đã đánh dấu bỏ qua" : "Đã lưu " + text);
    goTo(state.index + 1);
  } catch (error) {
    toast("Không gửi được tới máy chủ: " + error, true);
  }
}

plateInput.addEventListener("input", () => {
  const cleaned = clean(plateInput.value);
  if (cleaned !== plateInput.value) { plateInput.value = cleaned; }
  validate();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    submit(event.ctrlKey || event.metaKey);
  } else if (event.altKey && event.key === "ArrowLeft") {
    event.preventDefault();
    goTo(state.index - 1);
  } else if (event.altKey && event.key === "ArrowRight") {
    event.preventDefault();
    goTo(state.index + 1);
  } else if (event.altKey && (event.key === "1" || event.key === "2")) {
    event.preventDefault();
    const radio = document.querySelector('input[name=lines][value="' + event.key + '"]');
    if (radio) { radio.checked = true; validate(); }
    plateInput.focus();
  }
});

el("save").addEventListener("click", () => submit(false));
el("skip").addEventListener("click", () => submit(true));
el("back").addEventListener("click", () => goTo(state.index - 1));
el("forward").addEventListener("click", () => goTo(state.index + 1));
el("reviewBack").addEventListener("click", () => goTo(state.total - 1));
document.querySelectorAll("input[name=lines]").forEach((radio) => {
  radio.addEventListener("change", () => { validate(); plateInput.focus(); });
});

(async function start() {
  try {
    const response = await fetch("/api/items");
    const data = await response.json();
    state.items = data.items;
    state.total = data.total;
    state.validation = data.validation_available;
    if (!state.validation && data.validation_error) {
      toast("Không nạp được bộ kiểm tra định dạng: " + data.validation_error, true);
    }
    if (state.total === 0) {
      el("counter").textContent = "không có ảnh nào để gán nhãn";
      return;
    }
    goTo(Math.min(data.start_index, state.total - 1));
    if (data.labeled > 0) {
      toast("Tiếp tục từ ảnh thứ " + (data.start_index + 1) +
            " (" + data.labeled + " ảnh đã gán trước đó)");
    }
  } catch (error) {
    el("counter").textContent = "lỗi tải danh sách: " + error;
  }
})();
</script>
</body>
</html>
"""


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        A parser covering the paths and the server settings.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Serve a small local web page for hand-labelling the plate crops "
            "produced by extract_plates.py."
        )
    )
    parser.add_argument(
        "--datasets-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Root of the datasets tree (default: <project root>/datasets).",
    )
    parser.add_argument(
        "--crops-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory of crops (default: <datasets>/annotations/plates_to_label).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        metavar="FILE",
        help="Crop manifest CSV (default: <crops dir>/manifest.csv).",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=None,
        metavar="FILE",
        help=(
            "Label CSV to append to and resume from "
            "(default: <datasets>/annotations/plate_labels.csv)."
        ),
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address; keep it on loopback (default: %(default)s).",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="TCP port (default: %(default)s)."
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not open a browser window on start-up.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Console verbosity (default: %(default)s).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Start the labelling server from the command line.

    Args:
        argv: Argument vector, defaulting to :data:`sys.argv`.

    Returns:
        ``0`` on a clean shutdown, ``1`` if the inputs are missing or the port
        cannot be bound.
    """
    args = _build_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    datasets_dir = (args.datasets_dir or PROJECT_ROOT / "datasets").expanduser().resolve()
    crops_dir = (
        args.crops_dir or datasets_dir / "annotations" / "plates_to_label"
    ).expanduser().resolve()
    manifest_path = (args.manifest or crops_dir / "manifest.csv").expanduser().resolve()
    labels_path = (
        args.labels or datasets_dir / "annotations" / "plate_labels.csv"
    ).expanduser().resolve()

    try:
        items = load_manifest(manifest_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        LOGGER.error("Cannot start: %s", exc)
        return 1

    store = LabelStore(csv_path=labels_path)
    try:
        store.load()
    except OSError as exc:
        LOGGER.error("Cannot read the existing label file: %s", exc)
        return 1

    LOGGER.info(
        "%d crops to label, %d already answered", len(items), len(store.records)
    )

    try:
        serve(
            items=items,
            store=store,
            crops_dir=crops_dir,
            validator=_Validator(),
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
        )
    except OSError as exc:
        LOGGER.error(
            "Cannot bind %s:%d (%s). Another copy may already be running; "
            "try --port with a different number.",
            args.host,
            args.port,
            exc,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
