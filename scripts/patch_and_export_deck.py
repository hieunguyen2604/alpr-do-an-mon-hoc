import os
import subprocess
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN

def patch_and_export():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pptx_path = os.path.join(repo_root, "nop", "02-slide-mon-hoc.pptx")
    pdf_path = os.path.join(repo_root, "nop", "02-slide-mon-hoc.pdf")
    new_fig10_path = os.path.join(repo_root, "docs", "slides", "figures", "fig-slide-split-vs-projection.png")

    prs = Presentation(pptx_path)
    total_slides = len(prs.slides)
    print(f"Loaded {pptx_path} with {total_slides} slides.")

    # 1. Slide 3: Ensure bullet prefix "- " on all 4 points
    if total_slides >= 3:
        s3 = prs.slides[2]
        for sh in s3.shapes:
            if sh.has_text_frame and 50 < (sh.top / 914400.0 * 72) < 300:
                tf = sh.text_frame
                for p in tf.paragraphs:
                    txt = p.text.strip()
                    if txt and not txt.startswith("- "):
                        if txt.startswith("-"):
                            txt = "- " + txt.lstrip("-").strip()
                        else:
                            txt = "- " + txt
                        # Apply to first run or rewrite text
                        if len(p.runs) > 0 and not p.runs[0].text.startswith("- "):
                            p.runs[0].text = "- " + p.runs[0].text.lstrip("- ")

    # 2. Slide 9, 11, 17: Thoroughly remove any extraneous overlapping shapes at bottom
    # Slide 9: Exactly 1 Picture (pipeline strip)
    if total_slides >= 9:
        s9 = prs.slides[8]
        pic_count = 0
        shapes_to_del = []
        for sh in s9.shapes:
            w_pt = sh.width / 914400.0 * 72
            h_pt = sh.height / 914400.0 * 72
            l_pt = sh.left / 914400.0 * 72
            t_pt = sh.top / 914400.0 * 72
            if w_pt < 50 and h_pt < 50 and l_pt < 50:
                continue # page num
            if sh.shape_type == 13 or "Picture" in sh.name:
                pic_count += 1
                if pic_count > 1:
                    shapes_to_del.append(sh)
            elif t_pt > 450 or (t_pt + h_pt) > 530:
                shapes_to_del.append(sh)
        for sh in shapes_to_del:
            sp = sh._element
            sp.getparent().remove(sp)
            print(f"  [Slide 9] Deleted extraneous shape: {sh.name}")

    # Slide 11: Has table, MUST NOT have any picture
    if total_slides >= 11:
        s11 = prs.slides[10]
        shapes_to_del = []
        for sh in s11.shapes:
            w_pt = sh.width / 914400.0 * 72
            h_pt = sh.height / 914400.0 * 72
            l_pt = sh.left / 914400.0 * 72
            t_pt = sh.top / 914400.0 * 72
            if w_pt < 50 and h_pt < 50 and l_pt < 50:
                continue
            if sh.shape_type == 13 or "Picture" in sh.name:
                shapes_to_del.append(sh)
            elif t_pt > 460 and not sh.has_table:
                shapes_to_del.append(sh)
        for sh in shapes_to_del:
            sp = sh._element
            sp.getparent().remove(sp)
            print(f"  [Slide 11] Deleted extraneous shape: {sh.name}")

    # Slide 17: Exactly 1 Picture (4 metric cards)
    if total_slides >= 17:
        s17 = prs.slides[16]
        pic_count = 0
        shapes_to_del = []
        for sh in s17.shapes:
            w_pt = sh.width / 914400.0 * 72
            h_pt = sh.height / 914400.0 * 72
            l_pt = sh.left / 914400.0 * 72
            t_pt = sh.top / 914400.0 * 72
            if w_pt < 50 and h_pt < 50 and l_pt < 50:
                continue
            if sh.shape_type == 13 or "Picture" in sh.name:
                pic_count += 1
                if pic_count > 1:
                    shapes_to_del.append(sh)
            elif t_pt > 450 or (t_pt + h_pt) > 530:
                shapes_to_del.append(sh)
        for sh in shapes_to_del:
            sp = sh._element
            sp.getparent().remove(sp)
            print(f"  [Slide 17] Deleted extraneous shape: {sh.name}")

    # 3. Slide 10: Standardize terminology
    if total_slides >= 10:
        s10 = prs.slides[9]
        # Update subtitle text
        for sh in s10.shapes:
            if sh.has_text_frame and 50 < (sh.top / 914400.0 * 72) < 200:
                sh.text_frame.paragraphs[0].text = "Mộc Công an dập nổi và ốc vít gắn biển tạo đỉnh xám giả làm gãy phép chiếu ngang; cắt cố định O(1) bảo vệ nét chữ."
            # Update image blob
            if sh.shape_type == 13:
                blip_rids = sh._element.xpath(".//a:blip/@r:embed")
                if blip_rids:
                    rel = sh.part.rels[blip_rids[0]]
                    with open(new_fig10_path, "rb") as f:
                        rel.target_part._blob = f.read()
                    print("  [Slide 10] Updated figure image blob from", new_fig10_path)

    # 4. Slide 21: Table 'Hướng phát triển' - Fill row 5 and 6 column 3 with '—'
    if total_slides >= 21:
        s21 = prs.slides[20]
        for sh in s21.shapes:
            if sh.has_table:
                tbl = sh.table
                col3_vals = ["1", "1", "3, 4", "2, 5", "—", "—"]
                for r_idx in range(1, min(7, len(tbl.rows))):
                    c3 = tbl.cell(r_idx, 2)
                    c3.text = col3_vals[r_idx - 1]
                    for p in c3.text_frame.paragraphs:
                        p.font.name = "Arial"
                        p.font.size = Pt(12)
                        p.alignment = PP_ALIGN.CENTER
                print("  [Slide 21] Validated table column 'Giải hạn chế nào' with no empty cells.")

    # Save PPTX files
    prs.save(pptx_path)
    docs_pptx = os.path.join(repo_root, "docs", "slides", "12-slides-mon-hoc.pptx")
    prs.save(docs_pptx)
    print(f"Saved {pptx_path}")

    # Export PDF using Keynote via osascript
    print("Exporting PDF using Keynote...")
    osa_cmd = f'''
    set pptxPosix to ((POSIX file "{pptx_path}") as string)
    set pdfPosix to ((POSIX file "{pdf_path}") as string)
    tell application "Keynote"
        set theDoc to open file pptxPosix
        export theDoc to file pdfPosix as PDF
        close theDoc saving no
    end tell
    '''
    subprocess.run(["osascript", "-e", osa_cmd], check=True)
    print(f"Exported {pdf_path}")
    docs_pdf = os.path.join(repo_root, "docs", "slides", "12-slides-mon-hoc.pdf")
    import shutil
    shutil.copyfile(pdf_path, docs_pdf)

if __name__ == "__main__":
    patch_and_export()
