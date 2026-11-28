# -*- coding: utf-8 -*-
"""把合併檔 Part5（第 39–45 頁）改成深藍底，並把「直接落在底色上」的深色文字改成淺色。

Part5 原始設計是淺灰底 + 白色卡片，卡片內的深色文字沒問題；
但落在頁面底色上的標題／副標在深藍底上會看不見，所以只改這一類。
"""
import sys, copy
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation
from pptx.util import Emu

F = "deliver_beginner/06_Oracle_DBA_效能診斷與調校_v2.pptx"
NS = "{http://schemas.openxmlformats.org/presentationml/2006/main}"

prs = Presentation(F)
ref_bg = prs.slides[8]._element.cSld.find(NS + "bg")
assert ref_bg is not None


def lum(rgb):
    r, g, b = int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16)
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0


def area(sh):
    try:
        return int(sh.width) * int(sh.height)
    except Exception:
        return 0


def inter(a, b):
    x1 = max(int(a.left), int(b.left))
    y1 = max(int(a.top), int(b.top))
    x2 = min(int(a.left) + int(a.width), int(b.left) + int(b.width))
    y2 = min(int(a.top) + int(a.height), int(b.top) + int(b.height))
    return max(0, x2 - x1) * max(0, y2 - y1)


for idx in range(38, 45):                       # 第 39–45 頁
    s = prs.slides[idx]
    cSld = s._element.cSld
    old = cSld.find(NS + "bg")
    if old is not None:
        cSld.remove(old)
    cSld.insert(0, copy.deepcopy(ref_bg))

    light_shapes = []
    for sh in s.shapes:
        try:
            if str(sh.fill.type).startswith("SOLID"):
                c = str(sh.fill.fore_color.rgb)
                if lum(c) > 0.80:
                    light_shapes.append(sh)
        except Exception:
            pass

    changed = 0
    for sh in s.shapes:
        if not sh.has_text_frame or not sh.text_frame.text.strip():
            continue
        a = area(sh)
        covered = 0.0
        if a:
            for ls in light_shapes:
                if ls is sh:
                    continue
                covered = max(covered, inter(sh, ls) / a)
        if covered >= 0.5:          # 文字在淺色卡片上 → 保持深色
            continue
        for para in sh.text_frame.paragraphs:
            for r in para.runs:
                try:
                    if r.font.color and r.font.color.type is not None and r.font.color.rgb:
                        cur = str(r.font.color.rgb)
                        if lum(cur) < 0.55:
                            r.font.color.rgb = __import__("pptx").dml.color.RGBColor.from_string(
                                "F8FAFC" if lum(cur) < 0.25 else "E2E8F0")
                            changed += 1
                except Exception:
                    pass
    print(f"第 {idx+1} 頁：背景改深藍，調整 {changed} 段文字顏色")

prs.save(F)
print("已儲存")
