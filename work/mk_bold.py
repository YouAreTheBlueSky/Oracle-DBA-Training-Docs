import shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation
src = "deliver_beginner/02_Oracle_DBA_建置與日常管理.pptx"
dst = "work/proto/test_bold.pptx"
shutil.copyfile(src, dst)
prs = Presentation(dst)
s = prs.slides[4]           # p5 檢核頁
done = 0
for sh in s.shapes:
    if not sh.has_text_frame: continue
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            if r.text.startswith("與預期版本"):
                r.font.bold = True
                done += 1
prs.save(dst)
print("已把 p5 的一條通過條件設為粗體:", done)
