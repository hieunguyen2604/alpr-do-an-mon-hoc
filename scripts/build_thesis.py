#!/usr/bin/env python3
"""Build the full thesis document from its per-chapter Markdown sources.

This script turns the previously-manual "concatenate the chapters" step into a
reproducible build. It joins the front matter and the six chapters — in a fixed,
explicit order — into ``docs/papers/thesis-full.md``. When a Pandoc binary is
available it additionally exports:

* ``docs/papers/thesis-full.docx`` (from the merged Markdown), and
* ``docs/slides/slides.pptx`` (from the slide outline).

Design goals
------------
* **Byte-identical rebuild.** Running this script must reproduce the committed
  ``thesis-full.md`` exactly (see :data:`SECTION_SEPARATOR` for the one subtle
  historical detail). This lets the merged file be regenerated at any time and
  verified with a plain ``diff``.
* **No hard-coded absolute paths.** All paths derive from the repository root,
  which is located relative to this file, so the script runs from anywhere.
* **Explicit file list, never a glob.** Globbing risks silently swallowing a
  stray Markdown file; the chapter order is data the reader can audit here.

Usage
-----
Concatenate only (default output path)::

    python scripts/build_thesis.py --no-docx

Concatenate and, if Pandoc is present, export DOCX + PPTX::

    python scripts/build_thesis.py

Write the merged Markdown somewhere else::

    python scripts/build_thesis.py --out build/thesis-full.md --no-docx
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# --- Repository layout ------------------------------------------------------
# ``__file__`` lives at <repo>/scripts/build_thesis.py, so the repo root is two
# levels up. Everything else is expressed relative to that, never hard-coded.
REPO_ROOT: Path = Path(__file__).resolve().parent.parent
PAPERS_DIR: Path = REPO_ROOT / "docs" / "papers"
SLIDES_DIR: Path = REPO_ROOT / "docs" / "slides"

# Front matter + the six chapters, in binding order. Listed explicitly (not via
# a glob) so that tool files such as ``00-thesis-outline.md`` and
# ``THESIS-README.md`` — and any future stray file — are never merged in by
# accident. Bibliography and appendices are generated separately and are not
# part of this concatenation.
CHAPTER_FILENAMES: tuple[str, ...] = (
    "01-front-matter.md",
    "ch1-mo-dau.md",
    "ch2-tong-quan.md",
    "ch3-phan-tich-thiet-ke.md",
    "ch4-cai-dat.md",
    "ch5-thuc-nghiem.md",
    "ch6-ket-luan.md",
)

# Separator inserted after every section (including the last, matching the
# original manual build).
#
# IMPORTANT — do not "correct" this string. In a normal Python string the "\n"
# sequences are newlines and, crucially, "\newpage" is "\n" (one more newline)
# followed by the literal text "ewpage" — because "\n" is an escape sequence.
# The committed ``thesis-full.md`` was produced this way and therefore contains
# a literal "ewpage" marker between sections, not a LaTeX "\newpage" command.
# We reproduce it verbatim so the rebuild stays byte-for-byte identical to the
# committed file. If a real "\newpage" is ever wanted, change this to the raw
# string ``r"\n\n\newpage\n\n"`` — but that is a deliberate content change and
# will make the output differ from the current document.
SECTION_SEPARATOR: str = "\n\n\newpage\n\n"

# Source outline and target for the slide deck.
SLIDES_SOURCE_FILENAME: str = "10-slides.md"
"""The deck that gets projected: 21 short slides, bullets only.

Deliberately *not* ``10-slides-outline.md``. That file is the presentation
plan -- speaker notes, per-slide timing budget, a table explaining how to read
itself -- and exporting it produced a 51-slide deck in which the audience read
prose off the wall instead of listening. The two files answer different
questions and only one of them belongs on a projector.
"""
SLIDES_OUTPUT_FILENAME: str = "slides.pptx"
SLIDES_TEMPLATE_FILENAME: str = "template-uit.pptx"

# Pandoc arguments shared by every export path.
PANDOC_FROM: str = "gfm"
PANDOC_TOC_DEPTH: str = "3"


def read_section(path: Path) -> str:
    """Read one Markdown source file, preserving its bytes exactly.

    The file is decoded as UTF-8 with newline translation disabled so that the
    original (LF) line endings survive untouched on any platform.

    Args:
        path: Absolute path to the Markdown source file.

    Returns:
        The file's textual content, unchanged.

    Raises:
        FileNotFoundError: If ``path`` does not exist.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Missing thesis source file: {path}")
    return path.read_text(encoding="utf-8")


def merge_sections(papers_dir: Path, filenames: tuple[str, ...]) -> str:
    """Concatenate the ordered section files with the page-break separator.

    Every section (including the final one) is followed by
    :data:`SECTION_SEPARATOR`, reproducing the original manual concatenation.

    Args:
        papers_dir: Directory containing the section Markdown files.
        filenames: Section file names, already in binding order.

    Returns:
        The merged Markdown document as a single string.
    """
    parts: list[str] = []
    for name in filenames:
        parts.append(read_section(papers_dir / name))
        parts.append(SECTION_SEPARATOR)
    return "".join(parts)


def write_text_exact(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` as UTF-8 without newline translation or BOM.

    Args:
        path: Destination file path (parent directories are created).
        text: Content to write verbatim.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" disables translation so embedded "\n" stay as LF bytes.
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def find_pandoc() -> Path | None:
    """Locate a Pandoc executable.

    Prefers the vendored copy under ``tools/pandoc-3.10`` so the build is
    reproducible without a system install, then falls back to ``pandoc`` on the
    PATH.

    Returns:
        The path to a Pandoc executable, or ``None`` if none is found.
    """
    vendored = REPO_ROOT / "tools" / "pandoc-3.10" / "pandoc.exe"
    if vendored.is_file():
        return vendored
    on_path = shutil.which("pandoc")
    return Path(on_path) if on_path else None


PANDOC_VERSION = "3.10"
"""Pinned so a rebuilt document is byte-comparable with an earlier one.

Pandoc changes its DOCX styling between minor versions; letting the version
float would make "the chapter text did not change but the .docx did" a routine
and unexplainable event.
"""

PANDOC_URL = (
    f"https://github.com/jgm/pandoc/releases/download/{PANDOC_VERSION}/"
    f"pandoc-{PANDOC_VERSION}-windows-x86_64.zip"
)


def fetch_pandoc() -> Path | None:
    """Download the pinned Pandoc build into ``tools/`` and return its path.

    Exists so that ``tools/pandoc-3.10`` -- 221 MB of vendored binary, and by far
    the largest thing in the working tree -- can be deleted without stranding the
    document build. Before this, removing it left no record anywhere of which
    version had been used or where it came from, which turns a disk-space clean-up
    into an unbounded archaeology task months later.

    Returns:
        Path to ``pandoc.exe``, or ``None`` when the download or extraction
        failed. Failure is reported and returned rather than raised: the caller
        already knows how to build the Markdown without Pandoc.
    """
    import urllib.request
    import zipfile

    target = REPO_ROOT / "tools"
    target.mkdir(parents=True, exist_ok=True)
    archive = target / f"pandoc-{PANDOC_VERSION}.zip"

    print(f"[info] Downloading Pandoc {PANDOC_VERSION} (~30 MB) ...")
    try:
        urllib.request.urlretrieve(PANDOC_URL, archive)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(target)
    except Exception as error:  # noqa: BLE001 - report and let the caller continue
        print(f"[warn] could not fetch Pandoc: {error}")
        return None
    finally:
        archive.unlink(missing_ok=True)

    found = find_pandoc()
    if found is None:
        print("[warn] Pandoc archive extracted but no pandoc.exe was found")
    return found


def run_pandoc(pandoc: Path, args: list[str]) -> None:
    """Invoke Pandoc with the given arguments, surfacing failures loudly.

    Args:
        pandoc: Path to the Pandoc executable.
        args: Arguments to pass after the executable.

    Raises:
        subprocess.CalledProcessError: If Pandoc exits non-zero.
    """
    subprocess.run([str(pandoc), *args], check=True)


def export_docx(pandoc: Path, markdown_path: Path, docx_path: Path) -> None:
    """Export the merged thesis Markdown to a DOCX file.

    Uses the same conversion parameters the project has standardised on:
    ``--from gfm --toc --toc-depth=3``.

    Args:
        pandoc: Path to the Pandoc executable.
        markdown_path: The merged ``thesis-full.md`` to convert.
        docx_path: Destination ``.docx`` path.
    """
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    run_pandoc(
        pandoc,
        [
            str(markdown_path),
            "--from",
            PANDOC_FROM,
            "--toc",
            f"--toc-depth={PANDOC_TOC_DEPTH}",
            "-o",
            str(docx_path),
        ],
    )


def export_pptx(pandoc: Path, outline_path: Path, pptx_path: Path) -> None:
    """Export the slide outline to a PPTX deck.

    The deck's appearance comes entirely from ``template-uit.pptx``: Pandoc
    contributes the text and takes theme, fonts, background art and the UIT
    crest from the reference doc's master and layouts. See
    :mod:`scripts.make_slide_template` for how that file is derived, and why
    its layouts have to carry English names.

    The reference doc is optional on purpose. A missing template produces a
    plain-looking but complete deck rather than a failed build, which matters
    because the slides are a deliverable in their own right -- losing the
    styling is an inconvenience, losing the deck is not.

    Args:
        pandoc: Path to the Pandoc executable.
        outline_path: The slide outline Markdown source.
        pptx_path: Destination ``.pptx`` path.
    """
    if not outline_path.is_file():
        print(f"[skip] slide outline not found: {outline_path}", file=sys.stderr)
        return
    pptx_path.parent.mkdir(parents=True, exist_ok=True)

    arguments = [
        str(outline_path),
        "--from",
        PANDOC_FROM,
        # Pinned rather than inferred. Pandoc's automatic slide level depends on
        # where the first content happens to sit, so adding one paragraph under
        # a section heading silently re-cuts the whole deck. Level 2 fixes the
        # contract: `#` is a section divider, `##` is one slide.
        "--slide-level=2",
        "-o",
        str(pptx_path),
    ]
    template = SLIDES_DIR / SLIDES_TEMPLATE_FILENAME
    if template.is_file():
        arguments += ["--reference-doc", str(template)]
    else:
        print(
            f"[warn] khong thay {template.name} — deck se dung giao dien mac dinh "
            "cua Pandoc. Chay scripts/make_slide_template.py de dung lai.",
            file=sys.stderr,
        )

    run_pandoc(pandoc, arguments)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional explicit argument list (defaults to ``sys.argv``).

    Returns:
        The parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Merge the thesis chapters into a single Markdown file and, when "
            "Pandoc is available, export DOCX and PPTX."
        )
    )
    parser.add_argument(
        "--fetch-pandoc",
        action="store_true",
        help=(
            f"Download Pandoc {PANDOC_VERSION} into tools/ if it is not already "
            "present. Use after deleting the vendored copy to reclaim disk space."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=PAPERS_DIR / "thesis-full.md",
        help=("Path for the merged Markdown file " "(default: docs/papers/thesis-full.md)."),
    )
    parser.add_argument(
        "--docx",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Also export DOCX (from the merge) and PPTX (from the slide "
            "outline) via Pandoc. Use --no-docx to write only Markdown. "
            "Silently skipped if no Pandoc is found."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Build the thesis document(s).

    Args:
        argv: Optional explicit argument list (defaults to ``sys.argv``).

    Returns:
        Process exit code (0 on success).
    """
    args = parse_args(argv)

    merged = merge_sections(PAPERS_DIR, CHAPTER_FILENAMES)
    write_text_exact(args.out, merged)
    print(f"[ok] wrote merged Markdown -> {args.out}")

    if not args.docx:
        print("[info] --no-docx: skipping DOCX/PPTX export.")
        return 0

    pandoc = find_pandoc()
    if pandoc is None and args.fetch_pandoc:
        pandoc = fetch_pandoc()
    if pandoc is None:
        print(
            "[info] Pandoc not found (checked tools/pandoc-3.10 and PATH); "
            "skipping DOCX/PPTX export. Re-run with --fetch-pandoc to download "
            f"the pinned build ({PANDOC_VERSION}).",
            file=sys.stderr,
        )
        return 0

    print(f"[info] using Pandoc: {pandoc}")

    docx_path = args.out.with_suffix(".docx")
    export_docx(pandoc, args.out, docx_path)
    print(f"[ok] wrote DOCX -> {docx_path}")

    pptx_path = SLIDES_DIR / SLIDES_OUTPUT_FILENAME
    export_pptx(pandoc, SLIDES_DIR / SLIDES_SOURCE_FILENAME, pptx_path)
    if pptx_path.is_file():
        print(f"[ok] wrote PPTX -> {pptx_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
