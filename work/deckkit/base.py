"""Deck builder: reproduces the visual system of Oracle_Storage_Memory_Process_zhTW.pptx.

Design tokens were read out of the template's own XML, so generated slides match it:
  bg #F7F5F0 / cover #132E38 / ink #16333D / body #52656B / teal #147A7E
  mint #E5EDEB, alt row #EDF1EF, code panel #E6EDEB, rule #BACAC8, warn #B44435
  display font Microsoft JhengHei, code font Consolas 21pt
"""
from pptx import Presentation
from pptx.util import Emu, Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from copy import deepcopy
import math
import re

EMU = 914400
SLIDE_W = 16.667
SLIDE_H = 9.375

C = {
    "bg": "F7F5F0", "cover": "132E38", "ink": "16333D", "body": "52656B",
    "teal": "147A7E", "mint": "E5EDEB", "mint2": "EDF1EF", "panel": "E6EDEB",
    "rule": "BACAC8", "warn": "B44435", "white": "FFFFFF",
    "cover_meta": "AFCACB", "cover_sub": "E7A391",
}
ZH = "Microsoft JhengHei"
MONO = "Consolas"

LEFT = 0.79          # content left margin
WIDTH = 15.10        # content width
TITLE_TOP = 0.62
TITLE_H = 0.91
BODY_TOP = 2.02
BODY_BOTTOM = 7.72   # keep clear of takeaway/warning/footer band

LINE_BODY = 1.42   # exact line spacing factor for CJK body text
LINE_CODE = 1.34   # exact line spacing factor for monospace code

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


# ------------------------------------------------------------------ low level
def _rgb(hexstr):
    return RGBColor.from_string(hexstr)


def blank_deck(template):
    """Template theme, master and layouts, but no slides."""
    prs = Presentation(template)
    lst = prs.slides._sldIdLst
    for sldId in list(lst):
        rId = sldId.get(qn("r:id"))
        prs.part.drop_rel(rId)
        lst.remove(sldId)
    return prs


def _set_font(run, name=ZH, size=21.0, bold=False, color="16333D", italic=False):
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.italic = italic
    f.name = name
    f.color.rgb = _rgb(color)
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", name)


def _noline(shape):
    shape.line.fill.background()


def textbox(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP, wrap=True,
            margins=(0, 0, 0, 0), inset_lr=None):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    ml, mt, mr, mb = margins
    tf.margin_left = Inches(ml)
    tf.margin_top = Inches(mt)
    tf.margin_right = Inches(mr)
    tf.margin_bottom = Inches(mb)
    return tb


def para(tf, text, size=21.0, color="16333D", bold=False, font=ZH,
         align=PP_ALIGN.LEFT, space_before=0, space_after=0, line=LINE_BODY,
         first=False, exact=0.0):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    # exact spacing keeps predicted and rendered heights identical
    p.line_spacing = Pt(exact if exact else size * line)
    if space_before:
        p.space_before = Pt(space_before)
    if space_after:
        p.space_after = Pt(space_after)
    r = p.add_run()
    r.text = text
    _set_font(r, font, size, bold, color)
    return p


def rect(slide, l, t, w, h, fill=None, line=None, line_w=0.75, radius=None):
    shp = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    if radius is not None:
        shp.adjustments[0] = radius
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = _rgb(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = _rgb(line)
        shp.line.width = Pt(line_w)
    else:
        _noline(shp)
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    return shp


def hline(slide, x1, y1, x2, y2, color="BACAC8", width=1.25):
    from pptx.enum.shapes import MSO_CONNECTOR
    cn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
                                    Inches(x2), Inches(y2))
    cn.line.color.rgb = _rgb(color)
    cn.line.width = Pt(width)
    return cn


def add_bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(color)


# ------------------------------------------------------------------ text metrics
def _char_w(ch):
    o = ord(ch)
    if o < 0x2E80:
        if ch in " .,:;'|!il":
            return 0.30
        return 0.55
    return 1.0


def text_w_pt(text, size, mono=False):
    if mono:
        # Consolas advance is 0.55em, but CJK glyphs fall back to a full-width face
        return sum((size if ord(c) >= 0x2E80 else size * 0.55) for c in text)
    return sum(_char_w(c) for c in text) * size




def wrap_lines(text, width_in, size, mono=False):
    """Approximate greedy wrap in a box of width_in inches (7% safety margin)."""
    limit = width_in * 72.0 * 0.93
    if text_w_pt(text, size, mono) <= limit:
        return 1
    lines, cur = 1, 0.0
    units = text.split(" ")
    for i, u in enumerate(units):
        wpt = text_w_pt(u + (" " if i < len(units) - 1 else ""), size, mono)
        if cur + wpt > limit and cur > 0:
            lines += 1
            cur = wpt
        else:
            cur += wpt
    return lines


def fit_size(lines, width_in, max_pt, min_pt=12.0, mono=False, step=1.5):
    s = max_pt
    while s > min_pt:
        if all(text_w_pt(ln, s, mono) <= width_in * 72.0 for ln in lines):
            return s
        s -= step
    return min_pt


# ------------------------------------------------------------------ chrome
def title(slide, text, size=36.0, top=TITLE_TOP):
    tb = textbox(slide, LEFT, top, WIDTH, TITLE_H)
    s = fit_size([text], WIDTH, size, 24.0)
    if s < size:
        warn(f"title shrunk to {s}pt: {text}")
    para(tb.text_frame, text, size=s, color=C["ink"], bold=True, first=True)
    return tb


def footer(slide, section, pageno, chap):
    tb = textbox(slide, 0.83, 8.74, 13.0, 0.40)
    para(tb.text_frame, f"{chap}  {section}".strip(), size=15.0,
         color=C["body"], first=True)
    tb2 = textbox(slide, 14.55, 8.68, 1.30, 0.44)
    para(tb2.text_frame, str(pageno), size=19.5, color=C["body"], align=PP_ALIGN.RIGHT,
         first=True)


def takeaway(slide, text, y=6.86, color=None):
    color = color or C["body"]
    tb = textbox(slide, 0.89, y, WIDTH - 0.2, 0.62)
    s = fit_size([text], WIDTH - 0.3, 21.75, 15.0)
    para(tb.text_frame, text, size=s, color=color, first=True, line=1.15)


def warning(slide, text, y=7.86):
    tb = textbox(slide, 0.85, y, WIDTH - 0.2, 0.62)
    s = fit_size([text], WIDTH - 0.3, 21.75, 14.0)
    if s < 21.75:
        warn(f"warning shrunk to {s}pt: {text}")
    para(tb.text_frame, text, size=s, color=C["warn"], bold=True, first=True, line=1.15)


def notes(slide, spec, chap_label, source_ref):
    """Three-part speaker note, matching the template's convention."""
    topic = spec.get("_topic", "")
    parts = []
    if spec.get("_note_why"):
        parts.append("【講解重點】\n" + spec["_note_why"].strip())
    if spec.get("_note_scope"):
        parts.append("【適用範圍】\n" + spec["_note_scope"].strip())
    if source_ref:
        parts.append("【資料來源】\n" + source_ref)
    parts.append("【官方來源】\n" + "\n".join(spec.get("_refs") or []))
    slide.notes_slide.notes_text_frame.text = "\n\n".join(p for p in parts if p.strip())


# ------------------------------------------------------------------ table
def _cell_border(cell, color="BACAC8", w=9525):
    """Borders must be the first children of tcPr, in L, R, T, B order."""
    tcPr = cell._tc.get_or_add_tcPr()
    tags = ("a:lnL", "a:lnR", "a:lnT", "a:lnB")
    for tag in tags:
        old = tcPr.find(qn(tag))
        if old is not None:
            tcPr.remove(old)
    for i, tag in enumerate(tags):
        ln = tcPr.makeelement(qn(tag), {"w": str(w), "cap": "flat",
                                        "cmpd": "sng", "algn": "ctr"})
        fill = ln.makeelement(qn("a:solidFill"), {})
        fill.append(fill.makeelement(qn("a:srgbClr"), {"val": color}))
        ln.append(fill)
        tcPr.insert(i, ln)


def table(slide, header, rows, top=2.02, col_w=None, row_h=0.86, sizes=(19.0, 19.0),
          align_center_cols=()):
    ncol = len(header)
    if col_w is None:
        col_w = [WIDTH / ncol] * ncol
    total_w = sum(col_w)
    nrow = len(rows) + 1
    frame = slide.shapes.add_table(nrow, ncol, Inches(LEFT), Inches(top),
                                   Inches(total_w), Inches(row_h * nrow))
    tbl = frame.table
    tblPr = tbl._tbl.tblPr
    tblPr.set("firstRow", "1")
    tblPr.set("bandRow", "0")
    for i, w in enumerate(col_w):
        tbl.columns[i].width = Inches(w)
    for r in range(nrow):
        tbl.rows[r].height = Inches(row_h)

    head_size, body_size = sizes
    for ci, text in enumerate(header):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(C["cover"])
        cell.margin_left = Inches(0.10)
        cell.margin_right = Inches(0.10)
        cell.margin_top = Inches(0.05)
        cell.margin_bottom = Inches(0.05)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf = cell.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER if ci in align_center_cols else PP_ALIGN.LEFT
        r = p.add_run()
        r.text = text
        _set_font(r, ZH, head_size, True, C["white"])
        _cell_border(cell)

    for ri, row in enumerate(rows):
        band = C["mint2"] if ri % 2 == 1 else C["bg"]
        for ci, text in enumerate(row):
            cell = tbl.cell(ri + 1, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = _rgb(band)
            cell.margin_left = Inches(0.10)
            cell.margin_right = Inches(0.10)
            cell.margin_top = Inches(0.05)
            cell.margin_bottom = Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if ci in align_center_cols else PP_ALIGN.LEFT
            p.line_spacing = 1.1
            r = p.add_run()
            r.text = str(text)
            _set_font(r, ZH, body_size, False, C["ink"])
            _cell_border(cell)
    # overflow estimate
    for ri, row in enumerate(rows):
        for ci, text in enumerate(row):
            n = wrap_lines(str(text), col_w[ci] - 0.2, body_size)
            if n * body_size * 1.25 / 72.0 > row_h - 0.1:
                warn(f"table cell may overflow: {str(text)[:24]}")
    return frame
