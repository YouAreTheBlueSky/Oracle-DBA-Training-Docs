# -*- coding: utf-8 -*-
"""把 Part5（39–45 頁）落在深藍底上的深色文字改成淺色。

顏色可能寫在 run 的 rPr、段落的 defRPr、或 endParaRPr 裡，
所以直接在 XML 層處理，不動到白色卡片內的文字。
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation

F = "deliver_beginner/06_Oracle_DBA_效能診斷與調校_v2.pptx"
TEXT_HOSTS = {"rPr", "defRPr", "endParaRPr"}
LIGHT = "F8FAFC"
SOFT = "E2E8F0"


def lum(hexval):
    try:
        r, g, b = int(hexval[0:2], 16), int(hexval[2:4], 16), int(hexval[4:6], 16)
    except Exception:
        return 1.0
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def tag(el):
    return el.tag.split("}")[-1]


prs = Presentation(F)


def area(sh):
    try:
        return int(sh.width) * int(sh.height)
    except Exception:
        return 0


def inter(a, b):
    x1 = max(int(a.left), int(b.left)); y1 = max(int(a.top), int(b.top))
    x2 = min(int(a.left) + int(a.width), int(b.left) + int(b.width))
    y2 = min(int(a.top) + int(a.height), int(b.top) + int(b.height))
    return max(0, x2 - x1) * max(0, y2 - y1)


for idx in range(38, 45):
    s = prs.slides[idx]
    lights = []
    for sh in s.shapes:
        try:
            if str(sh.fill.type).startswith("SOLID") and lum(str(sh.fill.fore_color.rgb)) > 0.80:
                lights.append(sh)
        except Exception:
            pass

    n = 0
    for sh in s.shapes:
        if not sh.has_text_frame or not sh.text_frame.text.strip():
            continue
        a = area(sh)
        covered = 0.0
        if a:
            for ls in lights:
                if ls is not sh:
                    covered = max(covered, inter(sh, ls) / a)
        if covered >= 0.5:              # 在白色卡片上 → 保持深色
            continue
        for el in sh._element.iter():
            name = tag(el)
            if name not in ("srgbClr", "schemeClr"):
                continue
            host = el.getparent().getparent()
            if host is None or tag(host) not in TEXT_HOSTS:
                continue
            if name == "srgbClr":
                cur = el.get("val", "")
                if lum(cur) < 0.55:
                    el.set("val", LIGHT if lum(cur) < 0.30 else SOFT)
                    n += 1
            else:
                if el.get("val") in ("tx1", "dk1"):
                    el.set("val", LIGHT) if False else None
                    el.tag = el.tag.replace("schemeClr", "srgbClr")
                    el.attrib.clear()
                    el.set("val", LIGHT)
                    n += 1
    print(f"第 {idx+1} 頁：調整 {n} 處文字顏色")

prs.save(F)
print("已儲存")
