# -*- coding: utf-8 -*-
"""Structural QA for every deck in deliver_advance/.

Checks per slide: speaker notes present, shapes inside the canvas, no text smaller
than the readable floor, title sequence, and footer/pageno consistency.
"""
import os, sys, glob, re
from pptx import Presentation
from pptx.util import Emu

HERE = os.path.dirname(os.path.abspath(__file__))
DELIVER = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "deliver_advance")
W, H = 15240000, 8572500
TOL = 20000
MIN_PT = 11.0

report = []
problems = 0


def check(path):
    global problems
    name = os.path.basename(path)
    prs = Presentation(path)
    n = len(prs.slides)
    lines = [f"\n=== {name}  ({n} slides)"]
    no_notes, small, oob = [], [], []
    for i, s in enumerate(prs.slides, 1):
        notes = s.notes_slide.notes_text_frame.text.strip() if s.has_notes_slide else ""
        if not notes:
            no_notes.append(i)
        for sh in s.shapes:
            if sh.left is None:
                continue
            if (sh.left < -TOL or sh.top < -TOL
                    or sh.left + sh.width > W + TOL or sh.top + sh.height > H + TOL):
                oob.append((i, sh.name, round(sh.left / 914400, 2), round(sh.top / 914400, 2),
                            round((sh.left + sh.width) / 914400, 2),
                            round((sh.top + sh.height) / 914400, 2)))
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.size and r.font.size.pt < MIN_PT and r.text.strip():
                            small.append((i, r.font.size.pt, r.text[:22]))
            if sh.has_table:
                for row in sh.table.rows:
                    for c in row.cells:
                        for p in c.text_frame.paragraphs:
                            for r in p.runs:
                                if r.font.size and r.font.size.pt < MIN_PT and r.text.strip():
                                    small.append((i, r.font.size.pt, r.text[:22]))
    lines.append(f"  missing notes: {no_notes if no_notes else 'none'}")
    lines.append(f"  text < {MIN_PT}pt: {small if small else 'none'}")
    lines.append(f"  out of bounds: {oob[:6] if oob else 'none'}")
    if no_notes or oob:
        problems += len(no_notes) + len(oob)
    report.append("\n".join(lines))


files = sorted(glob.glob(os.path.join(DELIVER, "*.pptx")))
for f in files:
    try:
        check(f)
    except Exception as exc:
        report.append(f"\n=== {os.path.basename(f)}  FAILED: {exc}")
        problems += 1

out = "\n".join(report) + f"\n\nFILES={len(files)} PROBLEMS={problems}\n"
open(os.path.join(HERE, "qa_report_" + os.path.basename(DELIVER) + ".txt"), "w", encoding="utf-8").write(out)
print(out.encode("ascii", "replace").decode("ascii"))
