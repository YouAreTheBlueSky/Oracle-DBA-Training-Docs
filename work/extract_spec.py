# -*- coding: utf-8 -*-
"""把現有簡報「資料化」：每一頁的形狀、位置、填色、文字都寫成 JSON 規格。

用途：讓沒有內容模組的簡報（01、06）也能由資料重建，而不是靠 binary 底稿。
"""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation
from pptx.util import Emu

EMU_IN = 914400.0
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def default_run_props(para):
    """段落層級的預設字級／粗體／顏色（很多文字靠這個繼承）。"""
    out = {}
    for tag in ("defRPr", "endParaRPr"):
        el = para._p.find(".//" + A + tag)
        if el is None:
            continue
        if el.get("sz"):
            out.setdefault("size", int(el.get("sz")) / 100.0)
        if el.get("b"):
            out.setdefault("bold", el.get("b") in ("1", "true"))
        clr = el.find(".//" + A + "srgbClr")
        if clr is not None and clr.get("val"):
            out.setdefault("color", clr.get("val"))
    return out


def color_of(fmt):
    try:
        if str(fmt.type).startswith("SOLID"):
            return str(fmt.fore_color.rgb)
    except Exception:
        pass
    return None


def shape_default_align(sh):
    """形狀層級的文字對齊（很多方塊寫在 lstStyle 裡）。"""
    try:
        body = sh.text_frame._txBody
    except Exception:
        return None
    for tag in ("defPPr", "lvl1pPr"):
        el = body.find(".//" + A + tag)
        if el is not None and el.get("algn"):
            return {"ctr": "c", "r": "r", "l": "l", "just": "l"}.get(el.get("algn"))
    return None


def align_of(p):
    if p.alignment is None:
        return None
    a = str(p.alignment).split()[0]          # 例："CENTER (2)" → "CENTER"
    return {"CENTER": "c", "RIGHT": "r", "JUSTIFY": "l"}.get(a, "l")


def extract(path):
    prs = Presentation(path)
    slides = []
    for sl in prs.slides:
        shapes = []
        for sh in sl.shapes:
            st = str(sh.shape_type)
            item = {
                "x": round(sh.left / EMU_IN, 3), "y": round(sh.top / EMU_IN, 3),
                "w": round(sh.width / EMU_IN, 3), "h": round(sh.height / EMU_IN, 3),
            }
            if "TABLE" in st:
                tbl = sh.table
                item["kind"] = "table"
                item["col_w"] = [round(c.width / EMU_IN, 3) for c in tbl.columns]
                item["row_h"] = [round(r.height / EMU_IN, 3) for r in tbl.rows]
                item["cells"] = []
                for r in tbl.rows:
                    row = []
                    for c in r.cells:
                        row.append({"fill": color_of(c.fill),
                                    "t": c.text,
                                    "size": (c.text_frame.paragraphs[0].runs[0].font.size.pt
                                             if c.text_frame.paragraphs[0].runs
                                             and c.text_frame.paragraphs[0].runs[0].font.size else None),
                                    "bold": bool(c.text_frame.paragraphs[0].runs[0].font.bold)
                                            if c.text_frame.paragraphs[0].runs else False})
                    item["cells"].append(row)
            elif "LINE" in st:
                item["kind"] = "line"
                item["line"] = {"color": color_of(sh.line.fill),
                                "width": sh.line.width.pt if sh.line.width else 1.0}
                from lxml import etree
                item["xml"] = etree.tostring(sh._element, encoding="unicode")
            else:
                is_tb = "TEXT_BOX" in st
                item["kind"] = "textbox" if is_tb else "shape"
                if not is_tb:
                    fill = color_of(sh.fill)
                    item["fill"] = fill
                    try:
                        item["radius"] = round(float(sh.adjustments[0]), 3)
                    except Exception:
                        item["radius"] = 0.0
                    item["line"] = {"color": color_of(sh.line.fill),
                                    "width": sh.line.width.pt if sh.line.width else 0}
                from lxml import etree as _et
                _spPr = sh._element.find("{http://schemas.openxmlformats.org/presentationml/2006/main}spPr")
                if _spPr is not None:
                    _eff = _spPr.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}effectLst")
                    if _eff is not None and len(_eff):
                        item["effect"] = _et.tostring(_eff, encoding="unicode")
                if sh.has_text_frame:
                    body = sh.text_frame._txBody.find(A + "bodyPr")
                    if body is not None:
                        ins = {}
                        for k in ("lIns", "rIns", "tIns", "bIns"):
                            if body.get(k) is not None:
                                ins[k] = round(int(body.get(k)) / EMU_IN, 4)
                        if ins:
                            item["ins"] = ins
                        if body.get("anchor"):
                            item["anchor"] = {"ctr": "mid", "t": "top", "b": "bot"}.get(
                                body.get("anchor"), "top")
                    paras = []
                    for p in sh.text_frame.paragraphs:
                        runs = []
                        for r in p.runs:
                            if not r.text:
                                continue
                            c = None
                            try:
                                if r.font.color and r.font.color.rgb:
                                    c = str(r.font.color.rgb)
                            except Exception:
                                pass
                            runs.append({"t": r.text,
                                         "size": r.font.size.pt if r.font.size else None,
                                         "bold": bool(r.font.bold),
                                         "color": c,
                                         "font": r.font.name})
                        dflt = default_run_props(p)
                        paras.append({"a": align_of(p), "runs": runs,
                                      "dsz": dflt.get("size"),
                                      "db": dflt.get("bold"),
                                      "dc": dflt.get("color")})
                    item["paras"] = paras
                    da = shape_default_align(sh)
                    if da:
                        item["da"] = da
                    item["anchor"] = str(sh.text_frame.vertical_anchor or "TOP")[:3].lower()
            shapes.append(item)
        bg = None
        try:
            if sl.background.fill.type is not None:
                bg = str(sl.background.fill.fore_color.rgb)
        except Exception:
            pass
        notes = sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else ""
        slides.append({"bg": bg, "shapes": shapes, "notes": notes})
    return {"w": round(prs.slide_width / EMU_IN, 3),
            "h": round(prs.slide_height / EMU_IN, 3),
            "slides": slides}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    data = extract(src)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("%s → %s（%d 頁、%d 個形狀）" % (src, dst, len(data["slides"]),
                                        sum(len(s["shapes"]) for s in data["slides"])))
