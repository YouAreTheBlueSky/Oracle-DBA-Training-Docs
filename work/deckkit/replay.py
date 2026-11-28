# -*- coding: utf-8 -*-
"""由 JSON 規格重建簡報（extract_spec.py 的逆向）。"""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

ALIGN = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}
ANCHOR = {"top": MSO_ANCHOR.TOP, "mid": MSO_ANCHOR.MIDDLE, "bot": MSO_ANCHOR.BOTTOM}


def rgb(h):
    return RGBColor.from_string(h)


def render(spec, out_path):
    prs = Presentation()
    prs.slide_width = Inches(spec["w"])
    prs.slide_height = Inches(spec["h"])
    blank = prs.slide_layouts[6]
    for s in spec["slides"]:
        slide = prs.slides.add_slide(blank)
        if s.get("bg"):
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = rgb(s["bg"])
        for it in s["shapes"]:
            kind = it["kind"]
            x, y, w, h = (Inches(it["x"]), Inches(it["y"]),
                          Inches(it["w"]), Inches(it["h"]))
            if kind == "table":
                frame = slide.shapes.add_table(len(it["cells"]), len(it["col_w"]), x, y, w, h)
                tbl = frame.table
                for j, cw in enumerate(it["col_w"]):
                    tbl.columns[j].width = Inches(cw)
                for i, rh in enumerate(it["row_h"]):
                    tbl.rows[i].height = Inches(rh)
                for i, row in enumerate(it["cells"]):
                    for j, cell in enumerate(row):
                        c = tbl.cell(i, j)
                        if cell.get("fill"):
                            c.fill.solid()
                            c.fill.fore_color.rgb = rgb(cell["fill"])
                        tf = c.text_frame
                        tf.text = ""
                        p = tf.paragraphs[0]
                        r = p.add_run()
                        r.text = cell["t"]
                        if cell.get("size"):
                            r.font.size = Pt(cell["size"])
                        r.font.bold = cell.get("bold", False)
                        r.font.color.rgb = rgb(cell.get("color") or "0F172A")
                continue
            if kind == "line":
                from lxml import etree
                import copy as _copy
                el = etree.fromstring(it["xml"])
                A_ = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
                P_ = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
                for tag in (A_ + "stCxn", A_ + "endCxn"):
                    for node in el.iter(tag):
                        node.getparent().remove(node)
                cnv = el.find(".//" + P_ + "cNvPr")
                if cnv is not None:
                    cnv.set("id", str(9000 + len(slide.shapes._spTree)))
                    cnv.set("name", "")
                spTree = slide.shapes._spTree
                spTree.append(_copy.deepcopy(el))
                continue
            if kind == "textbox":
                shape = slide.shapes.add_textbox(x, y, w, h)
            else:
                shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE
                                               if it.get("radius") else MSO_SHAPE.RECTANGLE,
                                               x, y, w, h)
                if it.get("radius"):
                    try:
                        shape.adjustments[0] = it["radius"]
                    except Exception:
                        pass
                if it.get("fill"):
                    shape.fill.solid()
                    shape.fill.fore_color.rgb = rgb(it["fill"])
                else:
                    shape.fill.background()
                lc = (it.get("line") or {}).get("color")
                if lc:
                    shape.line.color.rgb = rgb(lc)
                    shape.line.width = Pt((it.get("line") or {}).get("width", 1))
                else:
                    shape.line.fill.background()
                shape.shadow.inherit = False
                if it.get("effect"):
                    from lxml import etree as _et
                    _eff = _et.fromstring(it["effect"])
                    _spPr = shape._element.find(
                        "{http://schemas.openxmlformats.org/presentationml/2006/main}spPr")
                    if _spPr is not None:
                        _spPr.append(_eff)
            tf = shape.text_frame
            tf.word_wrap = True
            ins = it.get("ins") or {}
            tf.margin_left = Inches(ins.get("lIns", 0))
            tf.margin_right = Inches(ins.get("rIns", 0))
            tf.margin_top = Inches(ins.get("tIns", 0))
            tf.margin_bottom = Inches(ins.get("bIns", 0))
            tf.vertical_anchor = ANCHOR.get(it.get("anchor", "top"), MSO_ANCHOR.TOP)
            para_list = it.get("paras") or []
            tf.text = ""
            for i, p in enumerate(para_list):
                para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                al = p.get("a") or it.get("da") or "l"
                para.alignment = ALIGN.get(al, PP_ALIGN.LEFT)
                for r in p["runs"]:
                    run = para.add_run()
                    run.text = r["t"]
                    size = r.get("size") or p.get("dsz")
                    bold = r.get("bold") if r.get("bold") is not None else p.get("db")
                    color = r.get("color") or p.get("dc")
                    if size:
                        run.font.size = Pt(size)
                    if bold is not None:
                        run.font.bold = bool(bold)
                    if color:
                        run.font.color.rgb = rgb(color)
                    if r.get("font"):
                        run.font.name = r["font"]
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]
    prs.save(out_path)
    return len(spec["slides"])


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    spec = json.load(open(src, encoding="utf-8"))
    n = render(spec, dst)
    print("%s → %s（%d 頁）" % (src, dst, n))
