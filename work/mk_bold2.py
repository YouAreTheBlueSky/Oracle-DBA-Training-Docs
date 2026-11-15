import shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation
src = "deliver_beginner/02_Oracle_DBA_建置與日常管理.pptx"
dst = "work/proto/test_bold.pptx"
shutil.copyfile(src, dst)
prs = Presentation(dst)
s = prs.slides[13]          # p14
done = []
for sh in s.shapes:
    if not sh.has_text_frame: continue
    for p in sh.text_frame.paragraphs:
        for r in p.runs:
            if r.text.startswith("與預期版本"):
                r.font.bold = True
                r.font.underline = True
                done.append(r.text[:20])
prs.save(dst)
print("已對以下文字加粗體＋底線:", done)
