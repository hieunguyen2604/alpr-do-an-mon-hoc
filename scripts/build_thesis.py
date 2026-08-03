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
import os
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

# Front matter + the six chapters, in binding order. Listed explicitly (not
# via a glob) so that tool files such as ``00-thesis-outline-v2.md`` and
# ``THESIS-README.md`` — and any future stray file — are never merged in by
# accident.
#
# Restructured 2026-08-02 from six chapters to seven: technology selection was
# buried as §2.8 at the end of a 1,193-line chapter even though it is what a
# defence committee asks about most, so it became Chapter 3 of its own. See
# ``docs/papers/00-thesis-outline-v2.md`` for the full mapping.
CHAPTER_FILENAMES: tuple[str, ...] = (
    "01-front-matter.md",
    "ch1-gioi-thieu.md",
    "ch2-co-so-ly-thuyet.md",
    "ch3-khao-sat-lua-chon.md",
    "ch4-phan-tich-thiet-ke.md",
    "ch5-thuc-nghiem.md",
    "ch6-ket-luan.md",
    "ch8-tai-lieu-tham-khao.md",
    "ch9-phu-luc.md",
)

# Page break inserted after every section.
#
# This used to be ``"\n\n\newpage\n\n"``, which in a non-raw Python string is
# three newlines followed by the literal text ``ewpage`` — because ``\n`` is an
# escape sequence. The word **ewpage** was therefore printed as a paragraph of
# body text eight times in the delivered thesis, once before each chapter
# heading. The previous comment here documented the bug correctly but chose to
# keep it so rebuilds stayed byte-identical with an earlier committed file; that
# reason expired when the book was restructured.
#
# A raw ``\newpage`` would not have helped either: Pandoc only honours it for
# LaTeX output, and this build targets DOCX. The block below is raw OpenXML,
# which Word renders as an actual page break — hence the ``raw_attribute``
# extension on :data:`PANDOC_FROM`, without which Pandoc would print the XML.
SECTION_SEPARATOR: str = (
    "\n\n```{=openxml}\n"
    '<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n'
    "```\n\n"
)

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
# ``raw_attribute`` is what lets :data:`SECTION_SEPARATOR` reach Word as a real
# page break instead of being printed as XML. Harmless for the slide export,
# which contains no raw blocks.
PANDOC_FROM: str = "gfm+raw_attribute"
# Do sau muc luc khong con o day: truong TOC nam trong 01-front-matter.md
# (muc E) va tu mang tham so `\o "1-2"`. Xem gen_front_matter_lists.py.

# How many image pixels count as one printed inch.
#
# The 25 diagrams are rendered by mermaid-cli at scale 2, so the widest are
# 1568 px. At Pandoc's default of 96 dpi that is 16.3 inches -- four times the
# page width, and each diagram would swallow a page. ``{width=14cm}`` cannot fix
# this here because the sources are read as ``gfm``, which does not support
# ``link_attributes``; the annotation would print verbatim instead.
#
# 285 dpi puts a 1568 px diagram at 1568/285 = 5.5 in = 14.0 cm, which fits
# inside the 15.9 cm text column with margin to spare.
PANDOC_IMAGE_DPI: str = "285"


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
    exe_name = "pandoc.exe" if os.name == "nt" else "pandoc"
    vendored = REPO_ROOT / "tools" / "pandoc-3.10" / exe_name
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
            # Khong dung `--toc`: pandoc luon dat muc luc o DAU tai lieu, tuc
            # la truoc ca trang bia. Truong TOC duoc chen thang vao muc "E. MUC
            # LUC" cua 01-front-matter.md duoi dang OpenXML tho — xem
            # scripts/gen_front_matter_lists.py.
            # The chapters reference diagrams as ``figures/fig-chN-MM.png``,
            # relative to themselves. Pandoc resolves image paths against the
            # working directory, so without this the build silently produces a
            # DOCX with broken image placeholders instead of the 25 diagrams.
            #
            # The parent directory is on the path too: the shortened edition
            # lives in ``docs/papers/compact`` and shares the one ``figures/``
            # folder with the full edition rather than duplicating 25 PNGs.
            "--resource-path",
            os.pathsep.join(
                [str(markdown_path.parent), str(markdown_path.parent.parent)]
            ),
            "--dpi",
            PANDOC_IMAGE_DPI,
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
        # Image paths resolve against the working directory, not against the
        # Markdown file, so `figures/fig-gap.png` fails whenever the build runs
        # from anywhere but docs/slides. Adding the file's own directory lets
        # the source keep paths that are relative to itself -- which is also
        # what makes the images render when the file is read on GitHub.
        "--resource-path",
        str(outline_path.parent),
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
        "--src",
        type=Path,
        default=PAPERS_DIR,
        help=(
            "Directory holding the per-chapter Markdown files (default: "
            "docs/papers). Point it at docs/papers/compact to build the "
            "shortened edition from the same chapter list."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help=(
            "Path for the merged Markdown file (default: thesis-full.md inside "
            "the --src directory)."
        ),
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
    out_path = args.out or args.src / "thesis-full.md"

    merged = merge_sections(args.src, CHAPTER_FILENAMES)
    write_text_exact(out_path, merged)
    print(f"[ok] wrote merged Markdown -> {out_path}")

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

    docx_path = out_path.with_suffix(".docx")
    export_docx(pandoc, out_path, docx_path)
    print(f"[ok] wrote DOCX -> {docx_path}")

    pptx_path = SLIDES_DIR / SLIDES_OUTPUT_FILENAME
    export_pptx(pandoc, SLIDES_DIR / SLIDES_SOURCE_FILENAME, pptx_path)
    if pptx_path.is_file():
        print(f"[ok] wrote PPTX -> {pptx_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
