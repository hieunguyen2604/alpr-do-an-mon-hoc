"""Derive the Pandoc reference deck from the faculty PowerPoint template.

Pandoc builds ``docs/slides/slides.pptx`` from Markdown, but it takes every
visual decision -- theme colours, fonts, background art, the UIT crest, the
footer band -- from a *reference doc* passed with ``--reference-doc``. This
script turns a hand-made PowerPoint file into that reference doc.

Two transformations are needed, and neither is cosmetic.

**Strip the donor slides.** A reference deck contributes its master, layouts
and theme; its actual slides are irrelevant to Pandoc but would ride along in
the file. Leaving them risks a stray slide from an unrelated presentation
surfacing in the defence deck, so every slide, its relationships, its notes
and its content-type override are removed.

**Rename and retype the layouts.** Pandoc looks layouts up **by name**, in
English, and gives up on any it cannot find::

    Title Slide · Title and Content · Section Header · Two Content
    Comparison · Content with Caption · Blank

The source template was authored in Google Slides and exported, which names
layouts in Vietnamese and -- the part that actually breaks things -- emits
every text frame as a generic ``body`` placeholder. A layout with no
``ctrTitle`` has nowhere for Pandoc to put a title, so the cover would render
blank while looking, in PowerPoint, perfectly fine. The mapping below fixes
both: it renames each layout and promotes the right ``body`` placeholders to
the types Pandoc writes into.

Run it after replacing the source template::

    backend/.venv/Scripts/python scripts/make_slide_template.py

The output is committed, so a normal ``build_thesis.py`` run needs neither
this script nor the original file.
"""

from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE: Path = REPO_ROOT / "docs" / "slides" / "source-template.pptx"
OUTPUT: Path = REPO_ROOT / "docs" / "slides" / "template-uit.pptx"

Rect = tuple[int, int, int, int]
"""``(x, y, width, height)`` in pixels on the 1280x720 slide."""

Fix = str | tuple[str, Rect]
"""Either a replacement ``<p:ph>`` tag, or that tag plus new geometry."""

EMU_PER_PIXEL: int = 9525
"""OOXML English Metric Units per pixel at the 96 dpi the template was drawn in."""


LAYOUT_MAP: dict[str, tuple[str, dict[int, Fix]]] = {
    # Vietnamese layout name -> (Pandoc name, {source idx: replacement <p:ph>})
    #
    # The right-hand column is copied from Pandoc's own default reference deck
    # (``pandoc --print-default-data-file reference.pptx``), which is the only
    # authority on what its writer looks for. Two details there are easy to get
    # wrong and both fail loudly rather than visibly:
    #
    # * a *content* placeholder carries **no** ``type`` attribute. Pandoc
    #   rejects ``type="body"`` in that slot -- "Could not find a 0th
    #   placeholder of type obj (or nothing)" -- so the export dies outright;
    # * the indices are positional, and this template numbers them differently
    #   from PowerPoint's convention. See "Comparison" below.
    # The cover is the one layout that also needs new geometry. Its frames were
    # drawn for a one-line title and a one-line strap line; this project's title
    # wraps to three lines at 44 pt and Pandoc packs the subtitle, both authors
    # and the supervisor into the subtitle frame. Left at the original heights
    # the two blocks overlap -- PowerPoint does not clip overflowing text, it
    # spills it across whatever sits below.
    "Tiêu đề": (
        "Title Slide",
        {
            1: ('<p:ph type="ctrTitle"/>', (100, 140, 1080, 200)),
            # PowerPoint expects subTitle to carry idx="1", so this is not a
            # bare type swap. idx 1 is free by then: ctrTitle drops its index.
            2: ('<p:ph type="subTitle" idx="1"/>', (100, 370, 1080, 210)),
        },
    ),
    "OBJECT": ("Title and Content", {1: '<p:ph idx="1"/>'}),
    "Tiêu đề chương": (
        "Section Header",
        {
            1: '<p:ph type="title"/>',  # 44 pt divider heading
            2: '<p:ph type="body" idx="1"/>',  # 28 pt strap line
        },
    ),
    "So sanh 1": (
        "Two Content",
        {
            1: '<p:ph sz="half" idx="1"/>',  # left column
            2: '<p:ph sz="half" idx="2"/>',  # right column
        },
    ),
    # A permutation, not a retyping. The template puts the two bodies at idx
    # 1-2 and the two column headings at idx 3-4; PowerPoint -- and therefore
    # Pandoc -- interleaves them as heading, body, heading, body. Applying
    # these one at a time would collide, which is why the rewrite is a single
    # pass keyed on the original index.
    "So sanh 2": (
        "Comparison",
        {
            3: '<p:ph type="body" idx="1"/>',  # left heading  (24 pt)
            1: '<p:ph sz="half" idx="2"/>',  # left body
            4: '<p:ph type="body" sz="quarter" idx="3"/>',  # right heading
            2: '<p:ph sz="quarter" idx="4"/>',  # right body
        },
    ),
    # Also swapped: the template's picture frame is the big right-hand box at
    # idx 2 and the prose column is idx 1, whereas Pandoc writes the content
    # into idx 1 and the caption into idx 2. Left as-is, every figure would be
    # squeezed into the narrow text column and its caption sprawled across the
    # image area.
    "Hình ảnh": (
        "Content with Caption",
        {
            2: '<p:ph idx="1"/>',  # picture frame -> content
            1: '<p:ph type="body" sz="half" idx="2"/>',  # text column -> caption
        },
    ),
    "BLANK": ("Blank", {}),
}

_LAYOUT_NAME_RE = re.compile(r'(<p:cSld[^>]*\bname=")([^"]*)(")')
_PLACEHOLDER_RE = re.compile(r"<p:ph\b[^>]*/>")
_IDX_RE = re.compile(r'\bidx="(\d+)"')
_TYPE_RE = re.compile(r'\btype="([^"]+)"')
_SHAPE_RE = re.compile(r"<p:sp>.*?</p:sp>|<p:pic>.*?</p:pic>", re.DOTALL)
_OFFSET_RE = re.compile(r'<a:off\b[^>]*/>\s*<a:ext\b[^>]*/>')

_REWRITABLE_TYPES = frozenset({"body", "pic", "obj"})
"""Placeholder types the mapping may convert.

Chrome -- ``dt``, ``ftr``, ``sldNum`` -- and any placeholder already correctly
typed are left untouched, so a mapping keyed on an index that happens to also
belong to a footer cannot damage the layout's furniture.
"""


def rewrite_layout(xml: str) -> tuple[str, str | None]:
    """Rename one layout and retype its placeholders.

    Args:
        xml: The layout part, decoded.

    Returns:
        ``(new_xml, pandoc_name)``. ``pandoc_name`` is ``None`` when the layout
        is not one Pandoc asks for, in which case the XML is returned unchanged
        -- unused layouts are kept so the deck still opens as a normal template
        for anyone editing it by hand afterwards.
    """
    match = _LAYOUT_NAME_RE.search(xml)
    if match is None:
        return xml, None
    mapping = LAYOUT_MAP.get(match.group(2))
    if mapping is None:
        return xml, None

    pandoc_name, fixes = mapping
    xml = _LAYOUT_NAME_RE.sub(
        lambda m: f"{m.group(1)}{pandoc_name}{m.group(3)}", xml, count=1
    )

    applied: set[int] = set()

    def convert(match: re.Match[str]) -> str:
        """Rewrite one shape: its placeholder tag and, when given, its frame.

        Whole shapes rather than bare ``<p:ph>`` tags, because geometry lives
        in a sibling ``<a:xfrm>`` and the two have to move together.
        """
        shape = match.group(0)
        tag_match = _PLACEHOLDER_RE.search(shape)
        if tag_match is None:
            return shape
        tag = tag_match.group(0)
        idx_match = _IDX_RE.search(tag)
        type_match = _TYPE_RE.search(tag)
        if idx_match is None:
            return shape
        idx = int(idx_match.group(1))
        if idx not in fixes:
            return shape
        if type_match is not None and type_match.group(1) not in _REWRITABLE_TYPES:
            return shape

        fix = fixes[idx]
        replacement, rect = fix if isinstance(fix, tuple) else (fix, None)
        applied.add(idx)
        shape = shape.replace(tag, replacement, 1)

        if rect is not None:
            x, y, width, height = (value * EMU_PER_PIXEL for value in rect)
            shape, moved = _OFFSET_RE.subn(
                f'<a:off x="{x}" y="{y}"/><a:ext cx="{width}" cy="{height}"/>',
                shape,
                count=1,
            )
            if moved == 0:
                print(
                    f"[warn] {pandoc_name}: placeholder idx={idx} khong co <a:xfrm> "
                    "-- giu nguyen kich thuoc goc, chu co the tran ra ngoai khung",
                    file=sys.stderr,
                )
        return shape

    xml = _SHAPE_RE.sub(convert, xml)

    for idx in sorted(set(fixes) - applied):
        # Loud, because the failure is otherwise invisible: the deck opens
        # fine and the text is simply missing from the rendered slide.
        print(
            f"[warn] {pandoc_name}: khong thay placeholder idx={idx} "
            "-- layout da doi ten nhung o do se trong khi xuat",
            file=sys.stderr,
        )
    return xml, pandoc_name


def is_donor_slide(name: str) -> bool:
    """Whether a zip entry belongs to the donor deck's own slides."""
    return (
        name.startswith("ppt/slides/")
        or name.startswith("ppt/notesSlides/")
        or name == "docProps/thumbnail.jpeg"
    )


def strip_slide_ids(xml: str) -> str:
    """Empty ``<p:sldIdLst>`` so the presentation declares no slides."""
    return re.sub(r"<p:sldIdLst>.*?</p:sldIdLst>", "<p:sldIdLst/>", xml, flags=re.S)


_SLIDE_REL_RE = re.compile(
    r'<Relationship\b[^>]*Target="(?:\.\./)?(?:notes)?[sS]lides?/[^"]*"[^>]*/>'
)


def strip_slide_rels(xml: str) -> str:
    """Drop relationships pointing at removed slides."""
    return _SLIDE_REL_RE.sub("", xml)


def strip_slide_overrides(xml: str) -> str:
    """Drop content-type overrides for removed parts."""
    xml = re.sub(r'<Override\b[^>]*PartName="/ppt/slides/[^"]*"[^>]*/>', "", xml)
    xml = re.sub(r'<Override\b[^>]*PartName="/ppt/notesSlides/[^"]*"[^>]*/>', "", xml)
    return re.sub(r'<Override\b[^>]*PartName="/docProps/thumbnail[^"]*"[^>]*/>', "", xml)


def build(source: Path, output: Path) -> int:
    """Write the reference deck.

    Args:
        source: The hand-made PowerPoint template.
        output: Destination path.

    Returns:
        Process exit code.
    """
    if not source.is_file():
        print(f"[loi] khong thay template nguon: {source}", file=sys.stderr)
        return 2

    output.parent.mkdir(parents=True, exist_ok=True)
    renamed: list[str] = []
    dropped = 0

    with zipfile.ZipFile(source) as src:
        names = src.namelist()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as dst:
            for name in names:
                if is_donor_slide(name):
                    dropped += 1
                    continue
                data = src.read(name)

                if name.startswith("ppt/slideLayouts/slideLayout") and name.endswith(".xml"):
                    xml, pandoc_name = rewrite_layout(data.decode("utf-8"))
                    if pandoc_name:
                        renamed.append(pandoc_name)
                    data = xml.encode("utf-8")
                elif name == "ppt/presentation.xml":
                    data = strip_slide_ids(data.decode("utf-8")).encode("utf-8")
                elif name == "ppt/_rels/presentation.xml.rels":
                    data = strip_slide_rels(data.decode("utf-8")).encode("utf-8")
                elif name == "[Content_Types].xml":
                    data = strip_slide_overrides(data.decode("utf-8")).encode("utf-8")

                dst.writestr(name, data)

    expected = {pandoc_name for pandoc_name, _ in LAYOUT_MAP.values()}
    missing = sorted(expected - set(renamed))
    print(f"[ok] template -> {output}  ({output.stat().st_size / 1024:.0f} KB)")
    print(
        f"     bo {dropped} phan cua deck goc, "
        f"doi ten {len(renamed)}/{len(expected)} layout"
    )
    if missing:
        print(f"[warn] thieu layout: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    Args:
        argv: Command-line arguments; ``sys.argv[1:]`` when omitted.

    Returns:
        Process exit code.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    source = Path(args[0]) if args else DEFAULT_SOURCE
    if not source.is_absolute():
        source = REPO_ROOT / source
    return build(source, OUTPUT)


if __name__ == "__main__":
    raise SystemExit(main())
