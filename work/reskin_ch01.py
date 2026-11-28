# -*- coding: utf-8 -*-
"""第 1 章「只換視覺」：保留 30 頁原有結構，套上 v2 的配色與頁尾。

不搬動任何內容形狀，只做：
  1. 底色 F7F5F0 → F1F5F9
  2. 加頂端橘色橫條
  3. 面板 E5EDEB → 白色；強調色 147A7E → 該節主題色
  4. 標題改為 v2 的深墨色
  5. 頁尾改為「書名 ｜ 初級 DBA 訓練課程」＋「Slide n / 30」
"""
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = r"deliver_beginner\01_Oracle_DBA_儲存記憶體與程序架構.pptx"
DST = r"deliver_beginner\01_Oracle_DBA_儲存記憶體與程序架構_v2.pptx"

BG, PANEL, INK, MUTED, WHITE = "F1F5F9", "FFFFFF", "0F172A", "94A3B8", "FFFFFF"
ACCENT = "C74634"
BLUE, TEAL, AMBER = "2563EB", "0D9488", "D97706"
SWAP_FILL = {"E5EDEB": PANEL, "147A7E": None}   # 147A7E 由節點色決定

prs = Presentation(SRC)
E = 914400.0
total = len(prs.slides)


def rgb(h):
    return RGBColor.from_string(h)


def section_color(label):
    if "實體" in label:
        return BLUE
    if "邏輯" in label:
        return TEAL
    if "記憶體" in label:
        return AMBER
    return ACCENT


for idx, slide in enumerate(prs.slides, 1):
    # 1) 底色（封面維持深色，與 v2 封面一致）
    is_cover = (idx == 1)
    try:
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb("0F172A" if is_cover else BG)
    except Exception:
        pass

    # 節點色：先找頁尾的章節標籤
    label = ""
    for sh in slide.shapes:
        if sh.has_text_frame and sh.top is not None and sh.top / E > 8.5 and sh.left / E < 7:
            label = sh.text_frame.text
    color = section_color(label)

    # 2) 頂端橫條
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0,
                                 prs.slide_width, Inches(0.10))
    bar.fill.solid()
    bar.fill.fore_color.rgb = rgb(ACCENT)
    bar.line.fill.background()
    bar.shadow.inherit = False
    bar.text_frame.text = ""

    for sh in list(slide.shapes):
        if sh.left is None:
            continue
        top = sh.top / E
        left = sh.left / E

        # 3) 面板配色
        try:
            if str(sh.fill.type).startswith("SOLID"):
                cur = str(sh.fill.fore_color.rgb)
                if cur in SWAP_FILL:
                    sh.fill.fore_color.rgb = rgb(color if cur == "147A7E" else PANEL)
        except Exception:
            pass

        # 3b) 線條與文字的重點色一起換
        try:
            if str(sh.line.fill.type).startswith("SOLID"):
                if str(sh.line.color.rgb) in ("147A7E", "BACAC8"):
                    sh.line.color.rgb = rgb(color if str(sh.line.color.rgb) == "147A7E" else "CBD5E1")
        except Exception:
            pass

        if not sh.has_text_frame:
            continue
        for para in sh.text_frame.paragraphs:
            for run in para.runs:
                try:
                    if run.font.color and run.font.color.rgb and str(run.font.color.rgb) == "147A7E":
                        run.font.color.rgb = rgb(color)
                except Exception:
                    pass

        sizes = {r.font.size.pt for p in sh.text_frame.paragraphs
                 for r in p.runs if r.font.size}

        if is_cover:
            for para in sh.text_frame.paragraphs:
                for run in para.runs:
                    if sizes and max(sizes) in (48.0,):
                        run.font.color.rgb = rgb("38BDF8")
                    elif sizes and max(sizes) == 24.0:
                        run.font.color.rgb = rgb("CBD5E1")

        # 4) 標題
        if sizes and max(sizes) >= 34 and top < 1.0 and not is_cover:
            for p in sh.text_frame.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = rgb(INK)

        # 5) 頁尾
        if top > 8.5:
            tf = sh.text_frame
            old = tf.text
            tf.clear()
            para = tf.paragraphs[0]
            run = para.add_run()
            if left < 7:
                run.text = "Oracle Database 儲存、記憶體與程序架構 ｜ 初級 DBA 訓練課程"
                run.font.size = Pt(12.5)
                run.font.color.rgb = rgb(MUTED)
                sh.left = Inches(0.75)
                sh.width = Inches(11.0)
            else:
                run.text = "Slide %d / %d" % (idx, total)
                run.font.size = Pt(12.5)
                run.font.color.rgb = rgb(MUTED)
                sh.left = Inches(14.10)
                sh.width = Inches(1.85)
            try:
                run.font.name = "Microsoft JhengHei"
            except Exception:
                pass

prs.save(DST)
print("已輸出:", DST, "（%d 頁）" % len(prs.slides))
