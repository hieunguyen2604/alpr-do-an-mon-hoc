#!/usr/bin/env python3
"""Fetch Vietnamese licence-plate images from Wikimedia Commons.

Why this source
---------------
An audit of the project's 2,801 labelled plates found the corpus is 97.7% white
plates, with 20 yellow, 4 blue and **zero** army or diplomatic plates
(``docs/reports/17-plate-type-audit.json``). Every accuracy figure published so
far is therefore, to within a rounding error, an accuracy on white plates.

The public ALPR datasets share that bias -- they are scraped from traffic
cameras and parking barriers, where private vehicles dominate. Commons is
different in exactly the way that matters here: it is curated by topic rather
than by camera, so the rare classes are represented in proportion to how
*interesting* they are, not how common. Searching it for "Vietnam diplomatic
license plate" returns diplomatic plates.

What this script does and does not claim
----------------------------------------
It downloads images and records, for each one, the licence and author that
Commons reports. It does **not** claim the result is a benchmark:

* **Mixed provenance.** Commons holds photographs *and* vector templates. A
  template drawn in Inkscape is useful for checking that a plate family is
  handled at all, and useless for measuring real-world OCR, which is dominated
  by blur, glare and angle. The manifest records the file type so the two can
  never be silently averaged together.
* **No ground-truth text.** Nothing here is labelled with the plate string. The
  images support a *coverage* claim -- "the system handles an army plate" -- and
  a per-type error review, not an accuracy figure. Producing one means reading
  the plates by eye and writing them into the manifest.
* **Small.** Tens of images, not thousands.

Licence handling
----------------
Only files whose Commons licence is public domain or a CC licence permitting
reuse are downloaded; anything else is skipped and reported. The manifest keeps
the licence, the author and the file page URL for every image, because a thesis
that reproduces a photograph has to attribute it, and reconstructing that later
from a folder of JPEGs is impossible.

Usage
-----
::

    python scripts/dataset/fetch_commons_plates.py --limit 40
    python scripts/dataset/fetch_commons_plates.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

LOGGER = logging.getLogger("fetch_commons_plates")

API = "https://commons.wikimedia.org/w/api.php"

USER_AGENT = (
    "VN-ALPR-Thesis/1.0 "
    "(https://github.com/hieunguyen2604/vn-license-plate-recognition) "
    "python-urllib/3.13"
)
"""Identifies the client the way Wikimedia's User-Agent policy requires.

Not a formality. An agent without a contact URL is refused outright with
``429 Your request does not comply with our robot policy`` -- and that refusal
looks exactly like ordinary rate limiting in the log, which sent the first
version of this script into a pointless back-off loop. The policy is at
https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
and asks for tool name, version and a way to get in touch."""

#: Search terms, chosen to reach the classes the corpus lacks rather than to
#: maximise the total count. The plain "license plate" query is included last
#: because it returns mostly white plates -- which the project already has
#: thousands of, and which would otherwise crowd out the rare classes.
QUERIES: tuple[tuple[str, str], ...] = (
    ('intitle:"license plate" Vietnam diplomatic', "ngoai_giao"),
    ('intitle:"license plate" Vietnam', "hon_hop"),
    ('intitle:"registration plate" Vietnam', "hon_hop"),
    ('intitle:"bien so" xe', "hon_hop"),
    ("Vietnam diplomatic license plate NG", "ngoai_giao"),
    ("Vietnam military vehicle registration plate", "quan_doi"),
)
"""Deliberately anchored on ``intitle:`` for the broad terms.

The unanchored form matched any Commons file whose *description* mentioned a
vehicle in Vietnam, which returned 1942 rickshaw permits, a T-90 tank and street
scenes with no readable plate at all -- noise that costs download bandwidth from
a donated service and then has to be filtered out by hand. Anchoring on the title
trades a little recall for a large gain in precision. The two unanchored queries
that remain target the classes the corpus has none of, where recall matters more
than precision."""

#: Licence names Commons reports that permit reuse with attribution. Matched
#: case-insensitively as a prefix, because Commons appends version numbers
#: ("CC BY-SA 4.0", "CC BY 2.0") that are irrelevant to the permission itself.
CATEGORIES: tuple[tuple[str, str], ...] = (
    ("Category:License plates of Vietnam", "hon_hop"),
    ("Category:Diplomatic license plates in Vietnam", "ngoai_giao"),
)
"""Commons categories walked before the text queries run.

Curated membership, so precision is far higher than free-text search: every file
here is a Vietnamese plate because a human filed it as one."""

FREE_LICENCE_PREFIXES: tuple[str, ...] = (
    "cc0",
    "cc by",
    "cc-by",
    "public domain",
    "pd-",
    "gfdl",
)

_THUMB_WIDTH = 1600
"""Long-edge width requested from Commons, in pixels."""

_MAX_RETRIES = 4
"""Attempts per API call before giving up on it."""

_BACKOFF_SECONDS = 3.0
"""Base wait after a 429, multiplied by the attempt number."""

PHOTO_SUFFIXES = frozenset({".jpg", ".jpeg"})
"""Raster photographs. A ``.png``/``.svg``/``.gif`` from Commons is nearly
always a drawn template, which is a different kind of evidence."""


@dataclass(slots=True)
class CommonsImage:
    """One downloaded file and the attribution it carries.

    Attributes:
        filename: Local filename under the images directory.
        commons_title: The ``File:`` page title on Commons.
        page_url: Human-readable file page, for attribution.
        image_url: Direct URL the bytes came from.
        license_name: Licence as Commons reports it.
        artist: Author string, HTML stripped.
        query: Which search term surfaced this file.
        expected_type: Plate type that query was aiming at -- an *intent*, not a
            verified label. The audit re-derives the actual colour from pixels.
        is_photo: Whether the file is a photograph rather than a drawn template.
        width: Pixel width reported by Commons.
        height: Pixel height reported by Commons.
    """

    filename: str
    commons_title: str
    page_url: str
    image_url: str
    license_name: str
    artist: str
    query: str
    expected_type: str
    is_photo: bool
    width: int
    height: int


def _request(params: dict[str, str]) -> dict:
    """Call the Commons API with the required headers.

    Args:
        params: Query parameters; ``format=json`` is added.

    Returns:
        The decoded JSON response.

    Raises:
        urllib.error.URLError: If the request fails at the transport level.
    """
    params = {**params, "format": "json"}
    url = f"{API}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    # Commons answers 429 when queries arrive back to back. Backing off and
    # retrying matters more than it looks: without it a rate-limited query is
    # silently dropped, and the classes this script exists to collect are
    # exactly the ones found by a single query each -- losing one loses the
    # whole class, with nothing in the output to say so.
    for attempt in range(_MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == _MAX_RETRIES - 1:
                raise
            wait = _BACKOFF_SECONDS * (attempt + 1)
            LOGGER.info("  bi gioi han tan suat, cho %.1fs roi thu lai", wait)
            time.sleep(wait)
    raise RuntimeError("unreachable")


def _strip_html(value: str) -> str:
    """Reduce an HTML attribution snippet to plain text.

    Commons returns the author as HTML -- often an anchor tag. A CSV column is
    not the place for markup, and the link target adds nothing an attribution
    needs beyond the name.

    Args:
        value: Raw HTML from ``extmetadata``.

    Returns:
        Text with tags removed and whitespace collapsed.
    """
    out: list[str] = []
    depth = 0
    for char in value:
        if char == "<":
            depth += 1
        elif char == ">":
            depth = max(depth - 1, 0)
        elif depth == 0:
            out.append(char)
    return " ".join("".join(out).split())


def _ascii_filename(title: str) -> str:
    """Reduce a Commons title to a pure-ASCII filename.

    Not cosmetic. OpenCV's ``imread`` goes through the C locale on Windows and
    silently returns ``None`` for any path containing a character outside it --
    no exception, just a missing image. Saving a file as
    ``Biển_số_xe_Đà_Nẵng.jpg`` therefore produced a download that every
    downstream tool reported as corrupt: 14 of 34 images vanished that way, and
    the audit counted them as unreadable rather than as a bug.

    Diacritics are stripped rather than dropped, so ``Biển số`` becomes
    ``Bien_so`` and the file stays recognisable to a human reading the folder.

    Args:
        title: Commons page title, without the ``File:`` prefix.

    Returns:
        An ASCII filename, at most 120 characters.
    """
    decomposed = unicodedata.normalize("NFD", title.replace(" ", "_"))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    # Vietnamese "d with stroke" carries no combining mark, so NFD leaves it.
    stripped = stripped.replace("Đ", "D").replace("đ", "d")
    kept = "".join(ch for ch in stripped if ch.isascii() and (ch.isalnum() or ch in "._-"))
    return (kept or "commons_file")[:120]


def _is_free(license_name: str) -> bool:
    """Return whether a licence permits reuse with attribution.

    Args:
        license_name: Licence string as Commons reports it.

    Returns:
        ``True`` for public domain and reuse-permitting CC licences. Unknown or
        empty licences return ``False`` -- an unlabelled licence is not a free
        one, and guessing here would put an unattributable image in a thesis.
    """
    lowered = license_name.strip().lower()
    return any(lowered.startswith(prefix) for prefix in FREE_LICENCE_PREFIXES)


def search(query: str, limit: int) -> list[str]:
    """Return Commons file titles matching a query.

    Args:
        query: Search expression.
        limit: Maximum titles to return.

    Returns:
        ``File:`` titles, most relevant first. An API error yields an empty
        list and a warning: one failing query must not abort the whole fetch.
    """
    try:
        data = _request(
            {
                "action": "query",
                "list": "search",
                "srsearch": f"{query} filetype:bitmap",
                "srnamespace": "6",
                "srlimit": str(limit),
            }
        )
    except Exception as error:  # noqa: BLE001 - one query failing is not fatal
        LOGGER.warning("search %r failed: %s", query, error)
        return []
    return [hit["title"] for hit in data.get("query", {}).get("search", [])]


def category_members(category: str, limit: int = 200) -> list[str]:
    """List the files a Commons category contains, following one level of subcategory.

    Categories beat free-text search for this job. Commons curators file an image
    under "License plates of Vietnam" because that is what it *is*, whereas the
    search index matches any file whose description merely mentions a vehicle in
    Vietnam -- which is how a 1942 rickshaw permit and a T-90 tank ended up in the
    first version of these results.

    Only one level of subcategory is followed. Commons category graphs are deep
    and cyclic; recursing without a bound is how a scraper accidentally walks half
    the site.

    Args:
        category: Full category title, including the ``Category:`` prefix.
        limit: Maximum members requested per category.

    Returns:
        ``File:`` titles from the category and its immediate subcategories.
    """
    try:
        data = _request(
            {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": category,
                "cmtype": "file|subcat",
                "cmlimit": str(limit),
            }
        )
    except Exception as error:  # noqa: BLE001 - a missing category is not fatal
        LOGGER.warning("category %r failed: %s", category, error)
        return []

    members = data.get("query", {}).get("categorymembers", [])
    files = [m["title"] for m in members if m["title"].startswith("File:")]
    for member in members:
        if not member["title"].startswith("Category:"):
            continue
        time.sleep(1.0)
        try:
            sub = _request(
                {
                    "action": "query",
                    "list": "categorymembers",
                    "cmtitle": member["title"],
                    "cmtype": "file",
                    "cmlimit": str(limit),
                }
            )
        except Exception:  # noqa: BLE001
            continue
        files.extend(
            m["title"]
            for m in sub.get("query", {}).get("categorymembers", [])
            if m["title"].startswith("File:")
        )
    return files


def image_info(titles: list[str]) -> dict[str, dict]:
    """Fetch URL, size and licence metadata for a batch of files.

    Args:
        titles: ``File:`` titles, at most 50 -- the API's per-request cap.

    Returns:
        A mapping of title to its ``imageinfo`` payload. Titles the API did not
        return are simply absent.
    """
    if not titles:
        return {}
    try:
        data = _request(
            {
                "action": "query",
                "titles": "|".join(titles[:50]),
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                # Wikimedia answers 429 on bulk fetches of full-size originals and
                # its own error text asks callers to take thumbnails instead. A plate
                # occupies a small part of the frame, so 1600px on the long edge is
                # still far more resolution than the detector needs, and it turns a
                # multi-megabyte original into a couple of hundred kilobytes.
                "iiurlwidth": str(_THUMB_WIDTH),
            }
        )
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("imageinfo failed: %s", error)
        return {}

    out: dict[str, dict] = {}
    for page in data.get("query", {}).get("pages", {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        if info:
            out[page.get("title", "")] = info
    return out


def download(url: str, destination: Path) -> bool:
    """Save one image, skipping it if it is already present.

    Args:
        url: Direct file URL from Commons.
        destination: Where to write it.

    Returns:
        ``True`` if the file exists locally afterwards.
    """
    if destination.exists() and destination.stat().st_size > 0:
        return True

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(_MAX_RETRIES):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                destination.write_bytes(response.read())
            return True
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == _MAX_RETRIES - 1:
                LOGGER.warning("download failed for %s: %s", destination.name, error)
                return False
            time.sleep(_BACKOFF_SECONDS * (attempt + 1))
        except Exception as error:  # noqa: BLE001 - one bad file must not stop the run
            LOGGER.warning("download failed for %s: %s", destination.name, error)
            return False
    return False


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out",
        default="datasets/raw/commons_vn_plates",
        help="Destination directory; images land in <out>/images.",
    )
    parser.add_argument("--limit", type=int, default=25, help="Results per search query.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be fetched, with licences, and download nothing.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.4,
        help="Seconds between downloads. Commons is a donated service; do not hammer it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Fetch the images and write the manifest.

    Args:
        argv: Command-line arguments; ``sys.argv[1:]`` when omitted.

    Returns:
        ``0`` on success, ``1`` when nothing usable was found.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = build_parser().parse_args(argv)

    out_dir = Path(args.out)
    images_dir = out_dir / "images"
    seen: set[str] = set()
    records: list[CommonsImage] = []
    skipped_licence: list[tuple[str, str]] = []

    sources: list[tuple[str, str, list[str]]] = []
    for category, expected_type in CATEGORIES:
        sources.append((category, expected_type, category_members(category)))
        time.sleep(args.delay)
    for query, expected_type in QUERIES:
        sources.append((query, expected_type, search(query, args.limit)))
        time.sleep(args.delay)

    for query, expected_type, found in sources:
        titles = [t for t in found if t not in seen]
        LOGGER.info("%-46s %d ket qua moi", query[:46], len(titles))
        if not titles:
            continue
        infos: dict[str, dict] = {}
        # The API caps a titles= query at 50; categories return more than that.
        for start in range(0, len(titles), 50):
            infos.update(image_info(titles[start : start + 50]))
            time.sleep(args.delay)

        for title in titles:
            info = infos.get(title)
            if not info:
                continue
            seen.add(title)

            meta = info.get("extmetadata", {})
            license_name = _strip_html(str(meta.get("LicenseShortName", {}).get("value", "")))
            if not _is_free(license_name):
                skipped_licence.append((title, license_name or "khong ro"))
                continue

            # Prefer the thumbnail; fall back to the original only when Commons
            # could not render one (some file types have no thumbnailer).
            url = info.get("thumburl") or info.get("url", "")
            suffix = Path(urllib.parse.urlparse(info.get("url", "")).path).suffix.lower()
            safe = _ascii_filename(title.removeprefix("File:"))

            record = CommonsImage(
                filename=safe,
                commons_title=title,
                page_url=info.get("descriptionurl", ""),
                image_url=url,
                license_name=license_name,
                artist=_strip_html(str(meta.get("Artist", {}).get("value", ""))),
                query=query,
                expected_type=expected_type,
                is_photo=suffix in PHOTO_SUFFIXES,
                width=int(info.get("width") or 0),
                height=int(info.get("height") or 0),
            )

            if args.dry_run:
                records.append(record)
                continue

            images_dir.mkdir(parents=True, exist_ok=True)
            if download(url, images_dir / safe):
                records.append(record)
                time.sleep(args.delay)

    if not records:
        LOGGER.error("khong lay duoc anh nao")
        return 1

    photos = sum(1 for r in records if r.is_photo)
    LOGGER.info("")
    LOGGER.info(
        "Lay duoc %d anh (%d anh chup, %d ban ve mau)", len(records), photos, len(records) - photos
    )
    LOGGER.info("Bo qua vi giay phep: %d", len(skipped_licence))
    for title, licence in skipped_licence[:8]:
        LOGGER.info("   - %-58s %s", title[:58], licence)

    if args.dry_run:
        LOGGER.info("(dry-run: khong tai file nao)")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0]).keys()))
        writer.writeheader()
        for record in records:
            writer.writerow(asdict(record))

    (out_dir / "SOURCE.md").write_text(
        "# Anh bien so Viet Nam tu Wikimedia Commons\n\n"
        f"Tai ngay 2026-07-20 bang `scripts/dataset/fetch_commons_plates.py`.\n\n"
        f"- Tong: **{len(records)} anh** ({photos} anh chup, {len(records) - photos} ban ve mau)\n"
        f"- Bo qua vi giay phep khong cho phep dung lai: {len(skipped_licence)} tep\n\n"
        "## Dung bo nay de lam gi\n\n"
        "Bo sung **cac loai bien vang / xanh / do / ngoai giao** — nhung loai ma bo du lieu\n"
        "chinh gan nhu khong co (xem `docs/reports/17-plate-type-audit.json`: 97,7% bien trang,\n"
        "0 bien do, 0 bien ngoai giao).\n\n"
        "## KHONG duoc dung bo nay de lam gi\n\n"
        "**Khong** dung de cong bo do chinh xac. Ly do:\n\n"
        "1. Khong co nhan chuoi bien so — muon do phai doc bang mat va dien vao manifest.\n"
        "2. Tron ca **anh chup** lan **ban ve mau** (template). Ban ve khong co\n"
        "   nhoe, loa hay nghieng — do OCR tren ban ve roi cong bo se cho con so\n"
        "   cao gia tao. Cot `is_photo` trong\n"
        "   `manifest.csv` de tach hai loai nay; tuyet doi khong duoc gop chung.\n"
        "3. Quy mo nho (hang chuc anh), khong du lam tap kiem dinh.\n\n"
        "Dung dung cho: **kiem tra do bao phu** (he thong co xu ly duoc bien quan doi khong?)\n"
        "va **phan tich loi theo loai bien**.\n\n"
        "## Ghi cong\n\n"
        "Moi anh deu co giay phep va tac gia trong `manifest.csv`. Anh nao dua vao quyen do an\n"
        "**bat buoc** phai ghi cong theo dung cot `artist` va `license_name`.\n",
        encoding="utf-8",
    )

    LOGGER.info("Ghi %s", manifest)
    LOGGER.info("Ghi %s", out_dir / "SOURCE.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
