# -*- coding: utf-8 -*-
"""v2 視覺版型（卡片／徽章／終端機／條件卡），尺寸 16.667 × 9.375 in。

用法：
    from theme_v2 import build_v2
    build_v2(ch05.CHAPTER, "out.pptx")
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

from base import C, ZH, MONO, SLIDE_W, SLIDE_H, text_w_pt, wrap_lines, _set_font, add_runs, warn, notes as base_notes

# ---------------------------------------------------------------- tokens
BG      = "F1F5F9"
INK     = "0F172A"
BODY    = "475569"
MUTED   = "94A3B8"
WHITE   = "FFFFFF"
DARK    = "0F172A"
TERM    = "111827"
TERM_H  = "1E293B"
LINE    = "CBD5E1"
ACCENT  = "C74634"
SKY     = "38BDF8"

BLUE, TEAL, AMBER, VIOLET = "2563EB", "0D9488", "D97706", "7C3AED"
RED, GREEN, GREY = "DC2626", "10B981", "64748B"
TOPIC_COLORS = [BLUE, TEAL, AMBER, VIOLET]

LEFT, RIGHT = 0.75, SLIDE_W - 0.75
CW = RIGHT - LEFT
WIDTH, HEIGHT = SLIDE_W, SLIDE_H
TOP_BAR = 0.10
FOOTER_Y = 8.70
BODY_TOP, BODY_BOT = 2.30, 8.55


def rgb(h):
    return RGBColor.from_string(h)


def box(slide, x, y, w, h, fill=None, line=None, radius=None, shadow=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h))
    if radius:
        try:
            shape.adjustments[0] = radius
        except Exception:
            pass
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(fill)
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = rgb(line)
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    if not shadow:
        shape.shadow.inherit = False
    shape.text_frame.text = ""
    return shape


def text(slide, x, y, w, h, s, size, color=INK, bold=False, font=ZH,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line=1.32, space=0):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    para(tf, s, size, color, bold, font, align, line, space)
    return tb


def para(tf, s, size, color=INK, bold=False, font=ZH,
         align=PP_ALIGN.LEFT, line=1.32, space=0, first=False):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = Pt(size * line)
    if space:
        p.space_before = Pt(space)
    add_runs(p, s, size, color, bold, font)
    return p



def slide_box(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    return tb



def topic_spec(topic, kind):
    """合併主題層級與該頁專屬的備忘設定（與 slides._note_spec 同邏輯）。"""
    merged = dict(topic)
    page = topic.get(kind) or {}
    if page.get("_note_pre"):
        merged["_note_pre"] = page["_note_pre"]
    if page.get("_note_replace"):
        merged["_note_why"] = page["_note_replace"]
    return merged


def put_notes(slide, spec, chap_label, src):
    base_notes(slide, spec, chap_label, src)


def simple_note(slide, text):
    if text and text.strip():
        slide.notes_slide.notes_text_frame.text = text.strip()


# ---------------------------------------------------------------- chrome
def new_slide(prs, bg=BG):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box(s, 0, 0, WIDTH, HEIGHT, fill=bg)
    return s


def chrome(slide, badge, badge_color, title, subtitle, page_no, total):
    box(slide, 0, 0, WIDTH, TOP_BAR, fill=ACCENT)
    # 徽章
    w = 0.55 + text_w_pt(badge, 15.0) / 72.0
    pill = box(slide, LEFT, 0.34, w, 0.44, radius=0.45)
    pill.fill.solid()
    pill.fill.fore_color.rgb = rgb(_tint(badge_color))
    pill.line.color.rgb = rgb(badge_color)
    pill.line.width = Pt(1.25)
    tf = pill.text_frame
    tf.word_wrap = False
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, badge, 15.0, badge_color, True, align=PP_ALIGN.CENTER, first=True)
    # 標題
    text(slide, LEFT, 0.92, CW, 0.64, title, 33.0, INK, True)
    if subtitle:
        text(slide, LEFT, 1.58, CW, 0.40, subtitle, 16.5, BODY)
    box(slide, LEFT, 2.08, CW, 0.025, fill=LINE)
    # 頁尾
    text(slide, LEFT, FOOTER_Y, 10.0, 0.30,
         "Oracle Database 安全性管理實戰 ｜ 初級 DBA 訓練課程", 12.5, MUTED)
    text(slide, RIGHT - 2.2, FOOTER_Y, 2.2, 0.30,
         "Slide %d / %d" % (page_no, total), 12.5, MUTED, align=PP_ALIGN.RIGHT)


def _tint(hexcolor):
    r = int(hexcolor[0:2], 16); g = int(hexcolor[2:4], 16); b = int(hexcolor[4:6], 16)
    r = int(r + (255 - r) * 0.88); g = int(g + (255 - g) * 0.88); b = int(b + (255 - b) * 0.88)
    return "%02X%02X%02X" % (r, g, b)


def card(slide, x, y, w, h, accent, label, desc, lsize=17.0, dsize=15.0,
         label_color=None, pad=0.22):
    box(slide, x, y, w, h, fill=WHITE, radius=0.10)
    box(slide, x, y, 0.15, h, fill=accent)
    tb = slide.shapes.add_textbox(Inches(x + pad), Inches(y + 0.10),
                                  Inches(w - pad - 0.14), Inches(h - 0.20))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0; tf.margin_right = 0
    tf.margin_top = 0; tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para(tf, label, lsize, label_color or INK, True, first=True, line=1.24)
    if desc:
        para(tf, desc, dsize, BODY, line=1.28, space=4)


def dark_panel(slide, x, y, w, h, heading, body, accent=ACCENT, hsize=17.0,
               bsize=15.0):
    box(slide, x, y, w, h, fill=DARK, radius=0.06)
    box(slide, x, y, w, 0.08, fill=accent)
    yy = y + 0.30
    if heading:
        text(slide, x + 0.26, yy, w - 0.5, 0.36, heading, hsize, WHITE, True)
        yy += 0.50
    text(slide, x + 0.26, yy, w - 0.5, h - (yy - y) - 0.2, body, bsize,
         "CBD5E1", line=1.42)


def terminal(slide, x, y, w, h, label, lines, size=14.5, dots=True):
    box(slide, x, y, w, h, fill=TERM, radius=0.045)
    box(slide, x, y, w, 0.44, fill=TERM_H)
    tx = x + 0.22
    if dots:
        for i, c in enumerate(("FF5F57", "FEBC2E", "28C840")):
            d = box(slide, tx + i * 0.17, y + 0.16, 0.11, 0.11, fill=c, radius=0.5)
        tx += 0.62
    text(slide, tx + 0.06, y + 0.07, w - (tx - x) - 0.25, 0.30, label, 13.0, "94A3B8")
    tb = slide.shapes.add_textbox(Inches(x + 0.20), Inches(y + 0.60),
                                  Inches(w - 0.4), Inches(h - 0.75))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = Pt(size * 1.38)
        add_runs(p, ln if ln else " ", size, "E2E8F0", False, MONO)


# ---------------------------------------------------------------- pages
def cover(prs, ch):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    box(s, 0, 0, WIDTH, HEIGHT, fill=DARK)
    box(s, 0, 0, 0.30, HEIGHT, fill=ACCENT)
    box(s, 1.12, 1.62, 3.10, 0.50, fill=ACCENT, radius=0.30)
    text(s, 1.12, 1.62, 3.10, 0.50, "CHAPTER %02d ｜ %s" % (ch["no"], ch.get("part", "")),
         17.0, WHITE, True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 1.12, 2.38, 14.0, 1.05, ch["title"], 52.0, WHITE, True, line=1.10)
    text(s, 1.12, 3.62, 14.0, 0.75, ch.get("subtitle", ""), 28.0, SKY, True)
    box(s, 1.12, 4.92, 8.2, 0.035, fill="334155")
    text(s, 1.12, 5.22, 13.6, 1.00,
         ch.get("agenda_note") or ("Oracle Database %s ｜ %s" % (ch.get("en", ""), ch.get("subtitle", ""))),
         18.0, "CBD5E1", line=1.45)
    chips = [a[0] for a in ch.get("agenda", [])][:4]
    cw, gap = 3.31, 0.36
    for i, name in enumerate(chips):
        x = 1.12 + i * (cw + gap)
        box(s, x, 7.30, cw, 0.72, fill=TERM_H, radius=0.16)
        text(s, x + 0.1, 7.30, cw - 0.2, 0.72, name, 16.0, WHITE, True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    simple_note(s, ch.get("note_why", ""))


def outline(prs, ch, page_no, total):
    s = new_slide(prs)
    chrome(s, "CHAPTER %02d ｜ 課程地圖" % ch["no"], ACCENT,
           ch.get("agenda_title", "本章大綱"), "", page_no, total)
    y = BODY_TOP
    for i, (name, desc) in enumerate(ch.get("agenda", [])[:4]):
        h = 1.28
        card(s, LEFT, y, CW, h, TOPIC_COLORS[i % 4],
             "%02d  %s" % (i + 1, name), desc, lsize=20.0, dsize=15.5, pad=0.30)
        text(s, RIGHT - 1.55, y + 0.16, 1.3, 0.32, "P%d–P%d" % (3 + i * 3, 5 + i * 3),
             13.0, MUTED, align=PP_ALIGN.RIGHT)
        y += h + 0.20
    simple_note(s, ch.get("agenda_note", ""))


def concept(prs, ch, ti, page_no, total):
    t = ch["topics"][ti]
    color = TOPIC_COLORS[ti % 4]
    s = new_slide(prs)
    chrome(s, "T%d ｜ %s" % (ti + 1, t.get("section", "")), color,
           t["title"], "", page_no, total)
    items = t["concept"]["items"][:5]
    n = len(items)
    top, bot = BODY_TOP + 0.06, BODY_BOT
    gap = 0.13
    h = (bot - top - gap * (n - 1)) / n
    for i, (lead, desc) in enumerate(items):
        card(s, LEFT, top + i * (h + gap), 10.30, h, color, lead, desc,
             lsize=17.5, dsize=14.5)
    dark_panel(s, 11.30, top, RIGHT - 11.30, bot - top, "這一頁的重點",
               t["concept"].get("note", ""), color, hsize=17.0, bsize=15.0)
    put_notes(s, topic_spec(t, "concept"), ch.get("chap_label", ""), t.get("src", ""))


def code_page(prs, ch, ti, page_no, total):
    t = ch["topics"][ti]
    color = TOPIC_COLORS[ti % 4]
    c = t["code"]
    s = new_slide(prs)
    chrome(s, "T%d ｜ %s" % (ti + 1, t.get("section", "")), color,
           c.get("title", t["title"]), "", page_no, total)
    terminal(s, LEFT, BODY_TOP, 10.30, BODY_BOT - BODY_TOP,
             "$ sqlplus ／ 實作步驟", c["lines"], size=14.0)
    body = []
    if c.get("takeaway"):
        body.append("◆ " + c["takeaway"])
    if c.get("warning"):
        body.append("⚠ " + c["warning"])
    dark_panel(s, 11.30, BODY_TOP, RIGHT - 11.30, BODY_BOT - BODY_TOP,
               "判讀重點", "\n\n".join(body), color, hsize=17.0, bsize=14.5)
    put_notes(s, topic_spec(t, "code"), ch.get("chap_label", ""), t.get("src", ""))


def check_page(prs, ch, ti, page_no, total):
    t = ch["topics"][ti]
    color = TOPIC_COLORS[ti % 4]
    c = t["check"]
    s = new_slide(prs)
    chrome(s, "T%d ｜ %s" % (ti + 1, t.get("section", "")), color,
           c.get("title", t["title"]), "", page_no, total)

    terminal(s, LEFT, BODY_TOP, 9.55, BODY_BOT - BODY_TOP, "怎麼檢查", c["commands"],
             size=13.5)

    x = 10.55
    w = RIGHT - x
    y = BODY_TOP
    conds = c["conds"][:4]
    pit_h = 1.42
    gap = 0.10
    ch_h = (BODY_BOT - BODY_TOP - pit_h - 0.16 - gap * 3) / 4.0
    for i, (label, expect) in enumerate(conds):
        cy = y + i * (ch_h + gap)
        box(s, x, cy, w, ch_h, fill=WHITE, radius=0.10)
        box(s, x, cy, 0.13, ch_h, fill=color)
        tb = slide_box(s, x + 0.24, cy + 0.08, w - 0.46, ch_h - 0.16)
        tf = tb.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para(tf, label, 15.0, INK, True, first=True, line=1.20)
        para(tf, expect, 12.5, BODY, line=1.22, space=3)

    py = BODY_BOT - pit_h
    box(s, x, py, w, pit_h, fill=DARK, radius=0.07)
    tb = slide_box(s, x + 0.24, py + 0.12, w - 0.48, pit_h - 0.24)
    tf = tb.text_frame
    para(tf, "常見錯誤", 14.0, "FCA5A5", True, first=True, line=1.20)
    for p_text in c.get("pitfalls", [])[:3]:
        para(tf, "× " + p_text, 12.0, "CBD5E1", line=1.24, space=3)
    put_notes(s, topic_spec(t, "check"), ch.get("chap_label", ""), t.get("src", ""))


def summary(prs, ch, page_no, total):
    s = new_slide(prs)
    sm = ch.get("summary", {})
    chrome(s, "整合複習", ACCENT, "本章重點回顧", "", page_no, total)
    items = sm.get("items", [])[:6]
    n = len(items)
    cols = 2
    rows = (n + 1) // 2
    gw = (CW - 0.28) / 2
    gh = (7.86 - BODY_TOP - 0.13 * (rows - 1)) / rows
    for i, (lead, desc) in enumerate(items):
        r, c = i // cols, i % cols
        card(s, LEFT + c * (gw + 0.28), BODY_TOP + r * (gh + 0.13), gw, gh,
             TOPIC_COLORS[i % 4], lead, desc, lsize=17.0, dsize=14.0, pad=0.26)
    if sm.get("note"):
        text(s, LEFT, 8.00, CW, 0.34, sm["note"], 13.0, MUTED, line=1.30)
    simple_note(s, sm.get("note", ""))


def refs_page(prs, ch, page_no, total):
    s = new_slide(prs)
    chrome(s, "資料來源", ACCENT, "官方參考資料與版本說明", "", page_no, total)
    note = ch.get("refs_note") or "以 Oracle Database 19c 官方文件為準；頁碼對應原始教材 PDF。"
    text(s, LEFT, BODY_TOP, CW, 0.62, note, 15.0, BODY, line=1.40)
    refs = ch.get("refs", [])[:6]
    card_h = 0.34 + len(refs) * 0.52
    box(s, LEFT, BODY_TOP + 0.72, CW, card_h, fill=WHITE, radius=0.06)
    y = BODY_TOP + 0.92
    for i, r in enumerate(refs):
        text(s, LEFT + 0.30, y, CW - 0.6, 0.34, "%d.  %s" % (i + 1, r), 13.5, INK)
        y += 0.52
    simple_note(s, ch.get("refs_note", ""))


def build_v2(ch, out_path):
    prs = Presentation()
    prs.slide_width = Inches(WIDTH)
    prs.slide_height = Inches(9.375)
    total = 1 + 1 + len(ch["topics"]) * 3 + 1 + 1
    cover(prs, ch)
    outline(prs, ch, 2, total)
    page = 3
    for ti in range(len(ch["topics"])):
        concept(prs, ch, ti, page, total); page += 1
        code_page(prs, ch, ti, page, total); page += 1
        check_page(prs, ch, ti, page, total); page += 1
    summary(prs, ch, page, total); page += 1
    refs_page(prs, ch, page, total)
    prs.save(out_path)
    return page
