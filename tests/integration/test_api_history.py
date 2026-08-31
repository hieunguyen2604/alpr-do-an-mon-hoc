"""Integration tests for the history endpoints."""

from __future__ import annotations

import csv
import datetime as dt
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.config import Settings
from backend.models.detection import DetectionHistory, DetectionJob, InputType

pytestmark = pytest.mark.integration

HISTORY_URL = "/api/history"
EXPORT_URL = "/api/history/export"

UTF8_BOM = b"\xef\xbb\xbf"

_BASE_TIME = dt.datetime(2026, 7, 10, 8, 0, 0, tzinfo=dt.timezone.utc)


@pytest.fixture()
def seeded(db: Session) -> list[DetectionHistory]:
    """Insert a small, deliberately varied history."""
    jobs = {
        "image": DetectionJob(
            input_type=InputType.IMAGE.value,
            status="completed",
            progress=1.0,
            created_at=_BASE_TIME,
        ),
        "video": DetectionJob(
            input_type=InputType.VIDEO.value,
            status="completed",
            progress=1.0,
            created_at=_BASE_TIME + dt.timedelta(days=1),
        ),
        "webcam": DetectionJob(
            input_type=InputType.WEBCAM.value,
            status="completed",
            progress=1.0,
            created_at=_BASE_TIME + dt.timedelta(days=2),
        ),
    }
    for job in jobs.values():
        db.add(job)
    db.flush()

    specification = [
        # (job, plate, raw, confidence, ocr, valid, day offset)
        ("image", "51F-12345", "51FI2345", 0.95, 0.90, True, 0),
        ("image", "51F-54321", "51F54321", 0.85, 0.80, True, 0),
        ("image", "29A1-11111", "29AI11111", 0.75, 0.70, True, 0),
        ("video", "XX-00000", "XXOOOOO", 0.65, 0.40, False, 1),
        ("video", "30G-99999", "30G99999", 0.55, 0.60, True, 1),
        ("webcam", None, None, 0.45, None, False, 2),
    ]

    rows: list[DetectionHistory] = []
    for index, (key, plate, raw, confidence, ocr, valid, offset) in enumerate(specification):
        row = DetectionHistory(
            plate_number=plate,
            raw_ocr_text=raw,
            confidence=confidence,
            ocr_confidence=ocr,
            input_type=jobs[key].input_type,
            image_path=f"uploads/source-{key}.jpg",
            plate_image_path=f"plates/{key}-plate-{index}.jpg",
            bbox_x=10 + index,
            bbox_y=20 + index,
            bbox_w=100,
            bbox_h=40,
            is_valid_format=valid,
            plate_line_count=1,
            processing_time=0.1 * (index + 1),
            detected_time=_BASE_TIME + dt.timedelta(days=offset, minutes=index),
            source_job_id=jobs[key].id,
        )
        db.add(row)
        rows.append(row)

    db.commit()
    return rows


class TestListing:
    """The default page."""

    def test_returns_every_record_by_default(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL).json()
        assert body["total"] == 6
        assert len(body["items"]) == 6

    def test_an_empty_history_is_a_valid_empty_page(self, client: TestClient) -> None:
        body = client.get(HISTORY_URL).json()
        assert body["total"] == 0
        assert body["items"] == []
        assert body["total_pages"] == 0
        assert body["has_next"] is False

    def test_newest_first_by_default(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        items = client.get(HISTORY_URL).json()["items"]
        times = [item["detected_time"] for item in items]
        assert times == sorted(times, reverse=True)

    def test_a_record_carries_both_box_forms(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        item = client.get(HISTORY_URL).json()["items"][0]
        assert item["bbox"]["x"] == item["bbox_x"]
        assert item["bbox"]["width"] == item["bbox_w"]

    def test_paths_are_published_as_urls_not_filesystem_paths(
        self, client: TestClient, seeded: list[DetectionHistory], settings: Settings
    ) -> None:
        """NFR-S2: the server's directory layout is not revealed."""
        raw = client.get(HISTORY_URL).text
        assert "/files/uploads/" in raw
        assert str(settings.storage_root) not in raw

    def test_a_single_record_can_be_fetched(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        response = client.get(f"{HISTORY_URL}/{seeded[0].id}")
        assert response.status_code == 200
        assert response.json()["id"] == seeded[0].id

    def test_an_unknown_record_is_a_404(self, client: TestClient) -> None:
        response = client.get(f"{HISTORY_URL}/999999")
        assert response.status_code == 404
        assert response.json()["error"] == "NOT_FOUND"


class TestPagination:
    """Paging is mandatory; there is no unpaginated variant."""

    def test_respects_the_page_size(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"page_size": 2}).json()
        assert len(body["items"]) == 2
        assert body["total"] == 6
        assert body["total_pages"] == 3

    def test_walks_through_every_page_without_repeating_a_row(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        seen: list[int] = []
        for page in (1, 2, 3):
            body = client.get(HISTORY_URL, params={"page": page, "page_size": 2}).json()
            seen.extend(item["id"] for item in body["items"])
        assert len(seen) == 6
        assert len(set(seen)) == 6

    def test_the_navigation_flags_are_correct(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        first = client.get(HISTORY_URL, params={"page": 1, "page_size": 2}).json()
        middle = client.get(HISTORY_URL, params={"page": 2, "page_size": 2}).json()
        last = client.get(HISTORY_URL, params={"page": 3, "page_size": 2}).json()

        assert (first["has_previous"], first["has_next"]) == (False, True)
        assert (middle["has_previous"], middle["has_next"]) == (True, True)
        assert (last["has_previous"], last["has_next"]) == (True, False)

    def test_a_page_past_the_end_is_empty_but_reports_the_total(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"page": 99, "page_size": 2}).json()
        assert body["items"] == []
        assert body["total"] == 6

    @pytest.mark.parametrize("page_size", [0, 101, 100_000])
    def test_an_out_of_range_page_size_is_refused(self, client: TestClient, page_size: int) -> None:
        """``?page_size=100000`` would undo the pagination entirely."""
        assert client.get(HISTORY_URL, params={"page_size": page_size}).status_code == 422

    def test_a_page_below_one_is_refused(self, client: TestClient) -> None:
        assert client.get(HISTORY_URL, params={"page": 0}).status_code == 422


class TestPartialSearch:
    """Free-text search over both the corrected and the raw string."""

    def test_finds_records_by_a_plate_prefix(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"search": "51F"}).json()
        assert body["total"] == 2
        assert all("51F" in item["plate_number"] for item in body["items"])

    def test_finds_a_record_by_a_middle_fragment(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"search": "1234"}).json()
        assert body["total"] == 1
        assert body["items"][0]["plate_number"] == "51F-12345"

    def test_search_is_case_insensitive(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        upper = client.get(HISTORY_URL, params={"search": "51F"}).json()["total"]
        lower = client.get(HISTORY_URL, params={"search": "51f"}).json()["total"]
        assert upper == lower == 2

    def test_searches_the_raw_ocr_string_too(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """A user searching for what they saw on the vehicle should still find"""
        body = client.get(HISTORY_URL, params={"search": "29AI"}).json()
        assert body["total"] == 1
        assert body["items"][0]["plate_number"] == "29A1-11111"

    def test_a_search_matching_nothing_returns_an_empty_page(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"search": "ZZZZZZ"}).json()
        assert body["total"] == 0
        assert body["items"] == []

    def test_a_percent_sign_is_escaped_not_used_as_a_wildcard(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Left unescaped it would match every row, reading as an ignored filter."""
        body = client.get(HISTORY_URL, params={"search": "%"}).json()
        assert body["total"] == 0

    def test_an_underscore_is_escaped_too(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"search": "51F_12345"}).json()
        assert body["total"] == 0

    def test_an_overlong_search_term_is_refused(self, client: TestClient) -> None:
        assert client.get(HISTORY_URL, params={"search": "x" * 200}).status_code == 422


class TestFiltering:
    """Each filter alone, then several together."""

    @pytest.mark.parametrize(
        ("input_type", "expected"),
        [("image", 3), ("video", 2), ("webcam", 1)],
    )
    def test_filters_by_input_type(
        self,
        client: TestClient,
        seeded: list[DetectionHistory],
        input_type: str,
        expected: int,
    ) -> None:
        body = client.get(HISTORY_URL, params={"input_type": input_type}).json()
        assert body["total"] == expected

    def test_rejects_an_unknown_input_type(self, client: TestClient) -> None:
        assert client.get(HISTORY_URL, params={"input_type": "satellite"}).status_code == 422

    def test_filters_by_format_validity(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        valid = client.get(HISTORY_URL, params={"is_valid_format": True}).json()
        invalid = client.get(HISTORY_URL, params={"is_valid_format": False}).json()
        assert valid["total"] == 4
        assert invalid["total"] == 2

    def test_filters_by_minimum_confidence(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"min_confidence": 0.8}).json()
        assert body["total"] == 2
        assert all(item["confidence"] >= 0.8 for item in body["items"])

    @pytest.mark.parametrize("value", [-0.5, 1.5])
    def test_rejects_an_out_of_range_confidence(self, client: TestClient, value: float) -> None:
        assert client.get(HISTORY_URL, params={"min_confidence": value}).status_code == 422

    def test_filters_by_date_range(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(
            HISTORY_URL,
            params={
                "date_from": _BASE_TIME.isoformat(),
                "date_to": (_BASE_TIME + dt.timedelta(hours=12)).isoformat(),
            },
        ).json()
        assert body["total"] == 3

    def test_rejects_a_reversed_date_range(self, client: TestClient) -> None:
        """An empty page looks identical to "no data yet"."""
        response = client.get(
            HISTORY_URL,
            params={
                "date_from": (_BASE_TIME + dt.timedelta(days=5)).isoformat(),
                "date_to": _BASE_TIME.isoformat(),
            },
        )
        assert response.status_code == 400
        assert response.json()["error"] == "VALIDATION_ERROR"

    def test_filters_by_job(self, client: TestClient, seeded: list[DetectionHistory]) -> None:
        """The plates of one upload, which is what ``source_job_id`` groups."""
        job_id = seeded[0].source_job_id
        body = client.get(HISTORY_URL, params={"job_id": job_id}).json()
        assert body["total"] == 3
        assert {item["source_job_id"] for item in body["items"]} == {job_id}

    def test_combines_search_and_input_type(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(HISTORY_URL, params={"search": "51F", "input_type": "image"}).json()
        assert body["total"] == 2

    def test_combines_three_filters(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(
            HISTORY_URL,
            params={
                "input_type": "image",
                "is_valid_format": True,
                "min_confidence": 0.9,
            },
        ).json()
        assert body["total"] == 1
        assert body["items"][0]["plate_number"] == "51F-12345"

    def test_combined_filters_can_select_nothing(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        body = client.get(
            HISTORY_URL, params={"input_type": "webcam", "min_confidence": 0.99}
        ).json()
        assert body["total"] == 0

    def test_a_filter_narrows_the_total_not_just_the_page(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """A total that ignores the filters makes the page counter wrong."""
        body = client.get(HISTORY_URL, params={"input_type": "image", "page_size": 1}).json()
        assert len(body["items"]) == 1
        assert body["total"] == 3
        assert body["total_pages"] == 3


class TestSorting:
    """Ordering, in both directions, over several columns."""

    @pytest.mark.parametrize("field", ["detected_time", "confidence", "processing_time", "id"])
    def test_sorts_descending(
        self, client: TestClient, seeded: list[DetectionHistory], field: str
    ) -> None:
        items = client.get(HISTORY_URL, params={"sort_by": field, "order": "desc"}).json()["items"]
        values = [item[field] for item in items]
        assert values == sorted(values, reverse=True)

    @pytest.mark.parametrize("field", ["detected_time", "confidence", "id"])
    def test_sorts_ascending(
        self, client: TestClient, seeded: list[DetectionHistory], field: str
    ) -> None:
        items = client.get(HISTORY_URL, params={"sort_by": field, "order": "asc"}).json()["items"]
        values = [item[field] for item in items]
        assert values == sorted(values)

    def test_ascending_and_descending_are_exact_reverses(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Guaranteed only because the ordering carries a unique tiebreaker."""
        ascending = client.get(
            HISTORY_URL, params={"sort_by": "confidence", "order": "asc"}
        ).json()["items"]
        descending = client.get(
            HISTORY_URL, params={"sort_by": "confidence", "order": "desc"}
        ).json()["items"]
        assert [item["id"] for item in ascending] == [item["id"] for item in reversed(descending)]

    def test_sorts_by_plate_number(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        items = client.get(
            HISTORY_URL,
            params={"sort_by": "plate_number", "order": "asc", "is_valid_format": True},
        ).json()["items"]
        plates = [item["plate_number"] for item in items]
        assert plates == sorted(plates)

    def test_an_unknown_sort_key_is_refused(self, client: TestClient) -> None:
        """The value ends up in an ``ORDER BY``; an enum rejects it up front."""
        assert (
            client.get(
                HISTORY_URL, params={"sort_by": "; DROP TABLE detection_history"}
            ).status_code
            == 422
        )

    def test_an_unknown_sort_direction_is_refused(self, client: TestClient) -> None:
        assert client.get(HISTORY_URL, params={"order": "sideways"}).status_code == 422


class TestCsvExport:
    """The export a user opens in Excel."""

    def test_returns_a_csv_attachment(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        response = client.get(EXPORT_URL)
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "attachment" in response.headers["content-disposition"]
        assert ".csv" in response.headers["content-disposition"]

    def test_the_file_begins_with_a_utf8_byte_order_mark(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Without it Excel falls back to the system code page and every"""
        content = client.get(EXPORT_URL).content
        assert content.startswith(UTF8_BOM)

    def test_the_bom_appears_exactly_once(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """A BOM per streamed chunk would corrupt the middle of the file."""
        content = client.get(EXPORT_URL).content
        assert content.count(UTF8_BOM) == 1

    def test_the_headers_are_vietnamese_and_decode_correctly(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        text = client.get(EXPORT_URL).content.decode("utf-8-sig")
        header = text.splitlines()[0]
        assert "Biển số" in header
        assert "Độ tin cậy phát hiện" in header
        assert "Mã lượt tải lên" in header

    def test_uses_the_line_terminator_excel_expects(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """A bare ``\\n`` renders the whole file as one row in some locales."""
        content = client.get(EXPORT_URL).content
        assert b"\r\n" in content

    def test_exports_one_row_per_record_plus_the_header(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        text = client.get(EXPORT_URL).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        assert len(rows) == 1 + 6

    def test_confidences_are_written_at_fixed_precision(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Raw floats would print as ``0.9400000000000001``."""
        text = client.get(EXPORT_URL).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        for row in rows[1:]:
            assert len(row[3].split(".")[1]) == 4

    def test_an_unread_plate_exports_as_empty_cells_not_the_word_none(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        text = client.get(EXPORT_URL).content.decode("utf-8-sig")
        assert "None" not in text

    def test_the_validity_flag_is_written_in_vietnamese(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        text = client.get(EXPORT_URL).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(text)))
        flags = {row[6] for row in rows[1:]}
        assert flags <= {"Có", "Không"}

    def test_the_export_honours_the_same_filters_as_the_list(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Otherwise a user exports something other than what they were looking"""
        params = {"input_type": "image", "is_valid_format": True}

        listed = client.get(HISTORY_URL, params=params).json()
        exported = client.get(EXPORT_URL, params=params).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(exported)))

        assert len(rows) - 1 == listed["total"] == 3

    def test_the_export_honours_the_search_term(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        exported = client.get(EXPORT_URL, params={"search": "51F"}).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(exported)))
        assert len(rows) - 1 == 2

    def test_the_export_honours_the_sort_order(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        exported = client.get(
            EXPORT_URL, params={"sort_by": "confidence", "order": "asc"}
        ).content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(exported)))
        confidences = [float(row[3]) for row in rows[1:]]
        assert confidences == sorted(confidences)

    def test_an_export_matching_nothing_is_a_header_only_file(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Still a valid CSV, and still carrying the BOM."""
        content = client.get(EXPORT_URL, params={"search": "ZZZZZZ"}).content
        assert content.startswith(UTF8_BOM)
        rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig"))))
        assert len(rows) == 1

    def test_an_export_of_an_empty_history_still_works(self, client: TestClient) -> None:
        content = client.get(EXPORT_URL).content
        assert content.startswith(UTF8_BOM)

    def test_a_contradictory_filter_fails_before_streaming_starts(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """Once the first byte of a 200 has gone out, an error can no longer be"""
        response = client.get(
            EXPORT_URL,
            params={
                "date_from": (_BASE_TIME + dt.timedelta(days=5)).isoformat(),
                "date_to": _BASE_TIME.isoformat(),
            },
        )
        assert response.status_code == 400
        assert not response.content.startswith(UTF8_BOM)

    def test_the_export_route_is_not_shadowed_by_the_detail_route(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """``/history/export`` must be declared before ``/history/{id:int}``."""
        assert client.get(EXPORT_URL).status_code == 200


class TestDeletion:
    """Removing a record, and the files that belong only to it."""

    def test_deleting_a_record_returns_204(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        response = client.delete(f"{HISTORY_URL}/{seeded[0].id}")
        assert response.status_code == 204
        assert response.content == b""

    def test_the_row_is_actually_gone(
        self, client: TestClient, seeded: list[DetectionHistory], db: Session
    ) -> None:
        target = seeded[0].id
        client.delete(f"{HISTORY_URL}/{target}")

        db.expire_all()
        assert db.get(DetectionHistory, target) is None
        assert db.execute(select(func.count()).select_from(DetectionHistory)).scalar_one() == 5

    def test_the_deleted_record_disappears_from_the_listing(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        target = seeded[0].id
        client.delete(f"{HISTORY_URL}/{target}")

        body = client.get(HISTORY_URL).json()
        assert body["total"] == 5
        assert target not in {item["id"] for item in body["items"]}

    def test_deleting_an_unknown_record_is_a_404(self, client: TestClient) -> None:
        """Not a silent success: a client must be able to tell a completed"""
        response = client.delete(f"{HISTORY_URL}/999999")
        assert response.status_code == 404

    def test_deleting_twice_reports_404_the_second_time(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        target = seeded[0].id
        assert client.delete(f"{HISTORY_URL}/{target}").status_code == 204
        assert client.delete(f"{HISTORY_URL}/{target}").status_code == 404

    def test_the_source_image_is_kept_while_a_sibling_still_references_it(
        self, client: TestClient, seeded: list[DetectionHistory], settings: Settings
    ) -> None:
        """Several plates found in one photograph share that file; deleting it"""
        shared = settings.upload_dir / "source-image.jpg"
        shared.parent.mkdir(parents=True, exist_ok=True)
        shared.write_bytes(b"\xff\xd8\xff" + b"\x00" * 32)

        # Three seeded rows share ``uploads/source-image.jpg``.
        client.delete(f"{HISTORY_URL}/{seeded[0].id}")
        assert shared.exists()

    def test_the_source_image_is_removed_with_the_last_record(
        self, client: TestClient, seeded: list[DetectionHistory], settings: Settings
    ) -> None:
        shared = settings.upload_dir / "source-image.jpg"
        shared.parent.mkdir(parents=True, exist_ok=True)
        shared.write_bytes(b"\xff\xd8\xff" + b"\x00" * 32)

        for row in seeded[:3]:
            client.delete(f"{HISTORY_URL}/{row.id}")

        assert not shared.exists()

    def test_the_plate_crop_is_removed_with_its_record(
        self, client: TestClient, seeded: list[DetectionHistory], settings: Settings
    ) -> None:
        crop = settings.plate_dir / "image-plate-0.jpg"
        crop.parent.mkdir(parents=True, exist_ok=True)
        crop.write_bytes(b"\xff\xd8\xff" + b"\x00" * 32)

        client.delete(f"{HISTORY_URL}/{seeded[0].id}")
        assert not crop.exists()

    def test_a_missing_file_does_not_break_the_delete(
        self, client: TestClient, seeded: list[DetectionHistory]
    ) -> None:
        """The row references files that were never written in this test."""
        assert client.delete(f"{HISTORY_URL}/{seeded[0].id}").status_code == 204

    def test_an_invalid_identifier_is_refused(self, client: TestClient) -> None:
        assert client.delete(f"{HISTORY_URL}/0").status_code == 422
        assert client.delete(f"{HISTORY_URL}/abc").status_code == 422
