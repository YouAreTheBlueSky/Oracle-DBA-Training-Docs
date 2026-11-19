import sys, difflib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation
fresh = Presentation("work/proto/_diff_fresh.pptx")
theirs = Presentation("work/inbox/05_Oracle_DBA_安全性管理.pptx")
for n in (4, 5, 11, 13):
    a = fresh.slides[n-1].notes_slide.notes_text_frame.text.splitlines()
    b = theirs.slides[n-1].notes_slide.notes_text_frame.text.splitlines()
    print("=== p%d ===" % n)
    for l in difflib.unified_diff(a, b, lineterm="", n=0):
        if l.startswith(("+", "-")) and not l.startswith(("+++", "---")):
            print("  ", l[:100])
