#!/usr/bin/env python3
"""Build the full thesis document from its per-chapter Markdown sources."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# --- Repository layout ------------------------------------------------------
# ``__file__`` lives at <repo>/scripts/build_thesis.py, so the repo root is two
# levels up. Everything else is expressed relative to that, never hard-coded.
REPO_ROOT: Path = Path(__file__).resolve().parent.parent
PAPERS_DIR: Path = REPO_ROOT / "docs" / "papers"
SLIDES_DIR: Path = REPO_ROOT / "docs" / "slides"

# Liet ke tuong minh, khong glob: tep lac (outline, THESIS-README) khong
# duoc phep tu chui vao quyen. Tai cau truc 6->7 chuong 02/08 — xem
# docs/papers/00-thesis-outline-v2.md.
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

# Ngat trang bang OpenXML tho (can raw_attribute): '\n' trong chuoi thuong
# la escape — ban cu in ra chu 'ewpage' 8 lan giua quyen; con \newpage that
# thi pandoc chi ton trong khi xuat LaTeX, khong phai DOCX.
SECTION_SEPARATOR: str = (
    "\n\n```{=openxml}\n"
    '<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n'
    "```\n\n"
)

# Source outline and target for the slide deck.
SLIDES_SOURCE_FILENAME: str = "12-slides-mon-hoc.md"
"""The deck that gets projected: 16 short slides, bullets only."""
SLIDES_OUTPUT_FILENAME: str = "12-slides-mon-hoc.pptx"
SLIDES_TEMPLATE_FILENAME: str = "template-uit.pptx"

# --- Bundle nop: ban sao (khong move) duoi ten nguoi doc hieu duoc, lam
# tuoi moi lan dung de khong bao gio om PDF cua tuan truoc ---
BUNDLE_DIR: Path = REPO_ROOT / "nop"

# (duong dan nguon tinh tu goc repo) -> (ten trong bundle). PDF do
# export_thesis_pdf.ps1 sinh; nguon chua ton tai thi bo qua va bao, khong loi.
BUNDLE_FILES: tuple[tuple[str, str], ...] = (
    # .docx KHONG nam trong danh sach nay: ban trong nop/ phai la ban Word DA
    # DIEN SO TRANG, va chi export_thesis_pdf.ps1 (noi goi Fields.Update roi
    # Save) lam duoc dieu do — script ay tu chep .docx sang nop/. De o day thi
    # moi lan build se de mot ban cot-Trang-toan-so-0 len ban tot; loi nay da
    # xay ra BA lan vi canh bao bi >/dev/null nuot.
    # Nhanh `do-an-mon-hoc`: quyen tot nghiep va tai lieu bao ve nam tren
    # nhanh main, goi nop o day chi con hai muc cua do an mon hoc.
    ("docs/papers/mon-hoc/thesis-full.pdf", "01-do-an-mon-hoc.pdf"),
    ("docs/slides/12-slides-mon-hoc.pptx", "02-slide-mon-hoc.pptx"),
    ("docs/slides/12-slides-mon-hoc.pdf", "02-slide-mon-hoc.pdf"),
)

# raw_attribute: SECTION_SEPARATOR toi Word nhu ngat trang that. bracketed_spans:
# neo []{#fig-N} thanh bookmark cho PAGEREF (GFM khong co, tung nuot im lang).
# -autolink_bare_uris: tat de mAP@0.5 khong thanh lien ket mailto.
PANDOC_FROM: str = "gfm+raw_attribute+bracketed_spans-autolink_bare_uris"
# Do sau muc luc khong con o day: truong TOC nam trong 01-front-matter.md
# (muc E) va tu mang tham so `\o "1-2"`. Xem gen_front_matter_lists.py.

# 285 dpi: mermaid xuat rong nhat 1568 px -> 5,5 in = 14 cm, vua cot chu 15,9 cm.
# Khong dung {width=14cm} duoc vi gfm khong ho tro link_attributes.
PANDOC_IMAGE_DPI: str = "285"

# --- Table borders: kieu Table mac dinh cua pandoc chi ke MOT duong duoi
# header. Sua bang cach va DUNG MOT style trong reference.docx cua chinh
# pandoc, moi style khac giu nguyen byte ---
REFERENCE_DOCX_FILENAME: str = "reference-thesis.docx"

# Border weights are in eighths of a point: sz="8" is 1 pt, sz="4" is 0.5 pt.
# Heavier outline, lighter interior grid -- the usual convention, and it keeps a
# dense table from reading as a solid block of lines.
TABLE_BORDERS_XML: str = (
    "<w:tblBorders>"
    '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
    '<w:left w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
    '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
    '<w:right w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
    '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>'
    "</w:tblBorders>"
)

# Anchor -> thay the tren word/styles.xml; moi anchor phai khop DUNG MOT lan,
# thieu la patch_styles nem loi de nang cap Pandoc hong to thay vi im lang.
STYLE_PATCHES: tuple[tuple[str, str], ...] = (
    # 0b. Chu trong o bang 12->10 pt (chuan van ban hoc thuat; than bai van 12).
    #     Pandoc gan kieu Compact cho moi doan trong o bang nen sua mot cho la du.
    #     Anchor phai chep tu `pandoc --print-default-data-file reference.docx`
    #     (thu tu thuoc tinh: type, customStyle, styleId / before, after) — ban
    #     dau chep tu styles.xml cua mot DOCX DA XUAT, noi writer sap xep thuoc
    #     tinh theo abc, nen anchor khop 0 lan va keo ca 6 patch chet chung
    #     tu 30/08 den 03/09.
    (
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Compact">\n    <w:name w:val="Compact" />\n    <w:basedOn w:val="BodyText" />\n    <w:qFormat />\n    <w:pPr>\n      <w:spacing w:before="36" w:after="36" />\n    </w:pPr>',  # noqa: E501 — chuoi khop nguyen van, khong duoc tach
        '<w:style w:type="paragraph" w:customStyle="1" w:styleId="Compact">\n    <w:name w:val="Compact" />\n    <w:basedOn w:val="BodyText" />\n    <w:qFormat />\n    <w:pPr>\n      <w:spacing w:before="20" w:after="20" />\n    </w:pPr>\n    <w:rPr>\n      <w:sz w:val="20" />\n      <w:szCs w:val="20" />\n    </w:rPr>',  # noqa: E501 — chuoi khop nguyen van, khong duoc tach
    ),
    # 0. Khoang cach sau doan 200->120 dxa: ~655 doan van, rieng khoang trong da
    #    ~11,5 trang in. Co chu va gian dong KHONG doi.
    (
        "<w:pPrDefault>\n"
        "      <w:pPr>\n"
        '        <w:spacing w:after="200" />',
        "<w:pPrDefault>\n"
        "      <w:pPr>\n"
        '        <w:spacing w:after="120" />',
    ),
    # 1. Luoi bang: tblBorders phai nam giua tblInd va tblCellMar (Word tu choi
    #    neu sai thu tu). 2. Dem doc 20 dxa — do o 40 dxa quyen phinh 92->95
    #    trang, 20 dxa giu nguyen 92.
    (
        '<w:tblInd w:w="0" w:type="dxa" />\n'
        "      <w:tblCellMar>\n"
        '        <w:top w:w="0" w:type="dxa" />',
        '<w:tblInd w:w="0" w:type="dxa" />\n'
        f"      {TABLE_BORDERS_XML}\n"
        "      <w:tblCellMar>\n"
        '        <w:top w:w="20" w:type="dxa" />',
    ),
    (
        '<w:bottom w:w="0" w:type="dxa" />\n'
        '        <w:right w:w="108" w:type="dxa" />',
        '<w:bottom w:w="20" w:type="dxa" />\n'
        '        <w:right w:w="108" w:type="dxa" />',
    ),
    # 3. Header rule, promoted from the inherited 0.5 pt to 1.5 pt so the
    #    header still separates from the body now that every row has a rule.
    (
        '<w:bottom w:val="single"/>',
        '<w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>',
    ),
    # 4. cantSplit: co luoi thi hang bi cat giua trang ve ra o rong (Bang 2.2
    #    tung mo trang 14 bang mot o chi chua chu 'le'). Dat duoi w:style vi
    #    tblStylePr chi phu vung dat ten; CT_Style xep trPr sau tblPr.
    (
        "</w:tblPr>\n"
        '    <w:tblStylePr w:type="firstRow">',
        "</w:tblPr>\n"
        "    <w:trPr><w:cantSplit /></w:trPr>\n"
        '    <w:tblStylePr w:type="firstRow">',
    ),
)


def patch_styles(styles_xml: str) -> str:
    """Apply :data:`STYLE_PATCHES` to the reference document's ``styles.xml``."""
    # Pandoc 3.10 xuat phan nay voi CRLF; do thuc te roi dich thay vi ghi cung.
    eol = "\r\n" if "\r\n" in styles_xml else "\n"

    for anchor, replacement in STYLE_PATCHES:
        anchor = anchor.replace("\n", eol)
        replacement = replacement.replace("\n", eol)
        found = styles_xml.count(anchor)
        if found != 1:
            raise ValueError(
                f"Table-style anchor matched {found} times, expected exactly 1. "
                f"Pandoc {PANDOC_VERSION}'s default styles may have changed.\n"
                f"  anchor: {anchor[:60]!r}"
            )
        styles_xml = styles_xml.replace(anchor, replacement)
    return styles_xml


def build_reference_docx(pandoc: Path, dest: Path) -> Path | None:
    """Write a reference document whose ``Table`` style draws full borders."""
    import io
    import zipfile

    try:
        default = subprocess.run(
            [str(pandoc), "--print-default-data-file", "reference.docx"],
            capture_output=True,
            check=True,
        ).stdout
        source = zipfile.ZipFile(io.BytesIO(default))
        patched = patch_styles(source.read("word/styles.xml").decode("utf-8"))

        dest.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as out:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename == "word/styles.xml":
                    data = patched.encode("utf-8")
                out.writestr(item, data)
    except (OSError, ValueError, zipfile.BadZipFile,
            subprocess.CalledProcessError) as error:
        print(f"[warn] khong dung duoc reference doc ({error}); "
              "bang se giu dinh dang mac dinh cua Pandoc.", file=sys.stderr)
        return None
    return dest


def read_section(path: Path) -> str:
    """Read one Markdown source file, preserving its bytes exactly."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing thesis source file: {path}")
    return path.read_text(encoding="utf-8")


ORDER_FILENAME: str = "ORDER.txt"
"""Per-directory override for :data:`CHAPTER_FILENAMES`."""


def read_order(papers_dir: Path) -> tuple[str, ...]:
    """Return the binding order for ``papers_dir``."""
    manifest = papers_dir / ORDER_FILENAME
    if not manifest.is_file():
        return CHAPTER_FILENAMES

    names = tuple(
        stripped
        for line in manifest.read_text(encoding="utf-8").splitlines()
        if (stripped := line.split("#", 1)[0].strip())
    )
    if not names:
        raise ValueError(f"{manifest} khong liet ke tep nao")
    return names


def merge_sections(papers_dir: Path, filenames: tuple[str, ...]) -> str:
    """Concatenate the ordered section files with the page-break separator."""
    # join, khong append: dat separator SAU ca phan cuoi tao mot ngat trang
    # thua o cuoi quyen — ca hai ban tung in ra mot to trang cuoi vi the.
    return SECTION_SEPARATOR.join(
        read_section(papers_dir / name) for name in filenames
    ) + "\n"


def write_text_exact(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` as UTF-8 without newline translation or BOM."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" disables translation so embedded "\n" stay as LF bytes.
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def find_pandoc() -> Path | None:
    """Locate a Pandoc executable."""
    exe_name = "pandoc.exe" if os.name == "nt" else "pandoc"
    vendored = REPO_ROOT / "tools" / "pandoc-3.10" / exe_name
    if vendored.is_file():
        return vendored
    on_path = shutil.which("pandoc")
    return Path(on_path) if on_path else None


PANDOC_VERSION = "3.10"
"""Pinned so a rebuilt document is byte-comparable with an earlier one."""

PANDOC_URL = (
    f"https://github.com/jgm/pandoc/releases/download/{PANDOC_VERSION}/"
    f"pandoc-{PANDOC_VERSION}-windows-x86_64.zip"
)


def fetch_pandoc() -> Path | None:
    """Download the pinned Pandoc build into ``tools/`` and return its path."""
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
    """Invoke Pandoc with the given arguments, surfacing failures loudly."""
    subprocess.run([str(pandoc), *args], check=True)


def export_docx(pandoc: Path, markdown_path: Path, docx_path: Path) -> None:
    """Export the merged thesis Markdown to a DOCX file."""
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    reference = build_reference_docx(
        pandoc, docx_path.parent / REFERENCE_DOCX_FILENAME
    )
    run_pandoc(
        pandoc,
        [
            str(markdown_path),
            "--from",
            PANDOC_FROM,
            # Bordered tables; see build_reference_docx. Omitted when the
            # reference document could not be built.
            *(["--reference-doc", str(reference)] if reference else []),
            # Khong dung --toc (pandoc dat muc luc TRUOC trang bia); truong TOC chen
            # thang vao muc E — xem gen_front_matter_lists.py. resource-path gom ca thu
            # muc cha de mon-hoc/ dung chung figures/ — thieu thi DOCX ra 25 o anh vo.
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
    """Export the slide outline to a PPTX deck."""
    if not outline_path.is_file():
        print(f"[skip] slide outline not found: {outline_path}", file=sys.stderr)
        return
    pptx_path.parent.mkdir(parents=True, exist_ok=True)

    arguments = [
        str(outline_path),
        "--from",
        PANDOC_FROM,
        # Ghim slide-level=2: de pandoc tu suy thi them mot doan van la ca bo bi cat lai.
        "--slide-level=2",
        # Duong dan anh resolve theo cwd — them thu muc cua chinh tep nguon de
        # figures/... chay tu bat ky dau (va van render tren GitHub).
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
    patch_script = REPO_ROOT / "scripts" / "patch_pptx_slides.ps1"
    if patch_script.is_file():
        try:
            powershell_cmd = REPO_ROOT / "powershell.cmd"
            cmd = (
                [str(powershell_cmd), "-ExecutionPolicy", "Bypass", "-File", str(patch_script), "-DeckPath", str(pptx_path)]
                if powershell_cmd.is_file()
                else ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(patch_script), "-DeckPath", str(pptx_path)]
            )
            subprocess.run(cmd, check=False)
        except Exception as e:
            print(f"[warn] patch_pptx_slides: {e}", file=sys.stderr)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
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
        "--slides",
        type=Path,
        default=None,
        help=(
            "Slide outline to export (default: docs/slides/12-slides-mon-hoc.md). The "
            "PPTX is written next to it, named after the source file."
        ),
    )
    parser.add_argument(
        "--src",
        type=Path,
        default=PAPERS_DIR / "mon-hoc",
        help=(
            "Directory holding the per-chapter Markdown files (default: "
            "docs/papers/mon-hoc, the course-project edition -- the only "
            "one kept on this branch)."
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


def copy_bundle(bundle_dir: Path = BUNDLE_DIR) -> tuple[int, list[str]]:
    """Refresh the submission folder from whatever build outputs exist."""
    bundle_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing: list[str] = []
    for relative, bundle_name in BUNDLE_FILES:
        source = REPO_ROOT / relative
        if not source.is_file():
            missing.append(relative)
            continue
        shutil.copy2(source, bundle_dir / bundle_name)
        copied += 1
    _canh_bao_truong_chua_dien(bundle_dir)
    return copied, missing


def _canh_bao_truong_chua_dien(bundle_dir: Path) -> None:
    """Bao khi ban .docx trong nop/ con giu gia tri cache cua truong Word."""
    for ten in ("01-do-an-tot-nghiep.docx", "04-do-an-mon-hoc.docx"):
        tep = bundle_dir / ten
        if not tep.is_file():
            continue
        try:
            with zipfile.ZipFile(tep) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
        except (OSError, KeyError, zipfile.BadZipFile):
            continue
        if "PAGEREF" not in xml:
            continue
        # Gia tri cache nam giua fldChar 'separate' va fldChar 'end'.
        cache = re.findall(r"PAGEREF [^<]*?</w:instrText>.*?<w:t[^>]*>([^<]*)</w:t>", xml, re.S)
        if cache and all(x.strip() in {"0", ""} for x in cache[:5]):
            # Khong dau: stdout cua console Windows la cp1252, va moi thong bao
            # khac trong tep nay cung viet khong dau vi cung ly do.
            print(f"     [!] {ten}: muc luc va danh muc hinh/bang CHUA co so trang.")
            print("         Chay scripts/export_thesis_pdf.ps1 de Word dien truong;")
            print("         script do ghi nguoc vao .docx roi chep lai vao nop/.")


def main(argv: list[str] | None = None) -> int:
    """Build the thesis document(s)."""
    args = parse_args(argv)
    out_path = args.out or args.src / "thesis-full.md"

    order = read_order(args.src)
    merged = merge_sections(args.src, order)
    write_text_exact(out_path, merged)
    print(f"[ok] wrote merged Markdown -> {out_path}  ({len(order)} phan)")

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

    slides_src = args.slides or SLIDES_DIR / SLIDES_SOURCE_FILENAME
    # Deck khac nguon thi ghi ra tep khac, de xuat mot bo khong de len bo kia.
    pptx_path = (SLIDES_DIR / SLIDES_OUTPUT_FILENAME if args.slides is None
                 else slides_src.with_suffix(".pptx"))
    export_pptx(pandoc, slides_src, pptx_path)
    if pptx_path.is_file():
        print(f"[ok] wrote PPTX -> {pptx_path}")

    copied, missing = copy_bundle()
    print(f"[ok] ban nop -> {BUNDLE_DIR}  ({copied}/{len(BUNDLE_FILES)} tep)")
    for relative in missing:
        print(f"     (chua co: {relative})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
