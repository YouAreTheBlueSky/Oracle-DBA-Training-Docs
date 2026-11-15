# -*- coding: utf-8 -*-
import sys, os, importlib, io
sys.path.insert(0, os.path.join("work", "deckkit"))
sys.path.insert(0, os.path.join("work", "content"))
sys.path.insert(0, "work")
import base, build_chapter

FILES = {
    2: "02_Oracle_DBA_建置與日常管理.pptx", 3: "03_Oracle_DBA_Net_Services.pptx",
    4: "04_Oracle_DBA_備份與復原.pptx", 5: "05_Oracle_DBA_安全性管理.pptx",
    6: "06_Oracle_DBA_效能診斷與調校.pptx", 7: "07_Oracle_DBA_ASM.pptx",
    8: "08_Oracle_DBA_RAC.pptx", 9: "09_Oracle_DBA_RAC_One_Node.pptx",
    10: "10_Oracle_DBA_資料倉儲.pptx", 11: "11_Oracle_DBA_公用程式.pptx",
    12: "12_Oracle_DBA_其他主題.pptx", 13: "13_Oracle_DBA_PLSQL.pptx",
    14: "14_Oracle_DBA_附錄.pptx",
}
summary = []
for n in sorted(FILES):
    mod = f"ch{n:02d}"
    path = os.path.join("deliver_full", FILES[n])
    try:
        slides, warns = build_chapter.build(mod, path)
        hard = [w for w in warns if "title shrunk" in w or "may overflow" in w]
        tiny = []
        for w in warns:
            import re
            m = re.search(r"(\d+\.\d)pt", w)
            if m and float(m.group(1)) < 17.0:
                tiny.append(w)
        summary.append((n, slides, len(warns), len(hard), len(tiny)))
    except Exception as e:
        summary.append((n, "FAIL", str(e)[:80], "", ""))
out = io.StringIO()
out.write(f"{'ch':>3} {'slides':>7} {'warn':>5} {'hard':>5} {'tiny':>5}\n")
for row in summary:
    out.write(f"{str(row[0]):>3} {str(row[1]):>7} {str(row[2]):>5} {str(row[3]):>5} {str(row[4]):>5}\n")
open("work/build_summary.txt", "w", encoding="utf-8").write(out.getvalue())
print(out.getvalue().encode("ascii", "replace").decode())
