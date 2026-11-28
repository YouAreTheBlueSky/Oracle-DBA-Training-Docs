# -*- coding: utf-8 -*-
"""把五份 Part 簡報合併成一份（純 python-pptx，無 COM、不依賴 PowerPoint）。

作法：以 Part1 為母檔（沿用其母片與版面），其餘四份逐頁「複製圖形樹」過來。
五份都沒有圖片／表格／圖表／媒體，所以不需要處理關聯檔。
"""
import sys, os, copy
from pptx import Presentation
from pptx.util import Emu

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "deliver_beginner"
PARTS = [
    "Oracle_DBA_Part1_Framework.pptx",
    "Oracle_DBA_Part2_CPU.pptx",
    "Oracle_DBA_Part3_Memory.pptx",
    "Oracle_DBA_Part4_IO.pptx",
    "Oracle_DBA_Part5_ASH_Plan.pptx",
]
OUT = os.path.join(BASE, "06_Oracle_DBA_效能診斷與調校_v2.pptx")

prs = Presentation(os.path.join(BASE, PARTS[0]))
blank = None
for lay in prs.slide_layouts:
    if lay.name.lower() in ("blank", "空白"):
        blank = lay
        break
if blank is None:
    blank = min(prs.slide_layouts, key=lambda l: len(l.placeholders))
print("使用版面:", blank.name, "｜種類", len(prs.slide_layouts))


def copy_slide(src, dst):
    """把 src 的所有圖形（含背景）複製到 dst，並帶上備忘。"""
    # 背景
    src_bg = src._element.cSld.find(
        "{http://schemas.openxmlformats.org/presentationml/2006/main}bg")
    if src_bg is not None:
        dst_bg = dst._element.cSld.find(
            "{http://schemas.openxmlformats.org/presentationml/2006/main}bg")
        if dst_bg is not None:
            dst._element.cSld.remove(dst_bg)
        dst._element.cSld.insert(0, copy.deepcopy(src_bg))
    # 圖形（跳過空佔位符）
    spTree = dst.shapes._spTree
    for shp in src.shapes:
        if shp.is_placeholder and not (shp.has_text_frame and shp.text_frame.text.strip()):
            continue
        spTree.append(copy.deepcopy(shp._element))
    # 備忘
    if src.has_notes_slide:
        text = src.notes_slide.notes_text_frame.text
        if text.strip():
            dst.notes_slide.notes_text_frame.text = text


total = len(prs.slides)
print(f"母檔 {PARTS[0]}: {total} 頁")
for name in PARTS[1:]:
    src_prs = Presentation(os.path.join(BASE, name))
    before = total
    for src_slide in src_prs.slides:
        dst_slide = prs.slides.add_slide(blank)
        for ph in list(dst_slide.placeholders):
            ph._element.getparent().remove(ph._element)
        copy_slide(src_slide, dst_slide)
        total += 1
    print(f"  併入 {name}: {before} → {total} 頁")

prs.save(OUT)
print(f"已儲存 {OUT}（{total} 頁）")
