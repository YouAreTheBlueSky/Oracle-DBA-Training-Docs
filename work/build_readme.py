# -*- coding: utf-8 -*-
"""Generate deliver_full/README.md from the built decks and chapter modules."""
import os, sys, glob, importlib
from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "content"))

DELIVER = os.path.join(ROOT, "deliver_full")

FILES = {
    1: ("01_Oracle_DBA_儲存記憶體與程序架構.pptx", "儲存、記憶體與程序架構",
        "Storage, Memory & Process", "架構自編", "—"),
    2: ("02_Oracle_DBA_建置與日常管理.pptx", None, None, None, None),
    3: ("03_Oracle_DBA_Net_Services.pptx", None, None, None, None),
    4: ("04_Oracle_DBA_備份與復原.pptx", None, None, None, None),
    5: ("05_Oracle_DBA_安全性管理.pptx", None, None, None, None),
    6: ("06_Oracle_DBA_效能診斷與調校.pptx", None, None, None, None),
    7: ("07_Oracle_DBA_ASM.pptx", None, None, None, None),
    8: ("08_Oracle_DBA_RAC.pptx", None, None, None, None),
    9: ("09_Oracle_DBA_RAC_One_Node.pptx", None, None, None, None),
    10: ("10_Oracle_DBA_資料倉儲.pptx", None, None, None, None),
    11: ("11_Oracle_DBA_公用程式.pptx", None, None, None, None),
    12: ("12_Oracle_DBA_其他主題.pptx", None, None, None, None),
    13: ("13_Oracle_DBA_PLSQL.pptx", None, None, None, None),
    14: ("14_Oracle_DBA_附錄.pptx", None, None, None, None),
}

rows = []
total = 0
for no in sorted(FILES):
    fn, title, en, part, pages = FILES[no]
    topics = 0
    if no > 1:
        try:
            mod = importlib.import_module(f"ch{no:02d}")
            sp = mod.CHAPTER
            title, en, part, pages = sp["title"], sp["en"], sp["part"], sp["source"]
            topics = len(sp["topics"])
        except Exception:
            pass
    path = os.path.join(DELIVER, fn)
    n = len(Presentation(path).slides) if os.path.exists(path) else 0
    total += n
    rows.append((no, title, en, part, pages, n, topics, fn))

lines = []
lines.append("# Oracle DBA 教育訓練教材（Oracle Database 19c）")
lines.append("")
lines.append("以 `Oracle_Storage_Memory_Process_zhTW.pptx` 為視覺範本、"
             "`oracle_dba_code_examples.pdf`（707 頁）為內容來源編寫。")
lines.append("")
lines.append(f"**共 14 章、{total} 頁。** 每章一個獨立 PPTX，第 1 章沿用既有架構教材。")
lines.append("")
lines.append("> 本資料夾為 **進階版**（14 章）。另有 **初階版** 位於 `deliver_beginner/`"
             "（10 章 228 頁，移除 ASM／RAC／RAC One Node／資料倉儲）。")
lines.append("")
lines.append("## 章節總表")
lines.append("")
lines.append("| 章 | 章名 | 英文 | PDF 來源 | 主題數 | 頁數 | 檔案 |")
lines.append("|---|---|---|---|---:|---:|---|")
for no, title, en, part, pages, n, topics, fn in rows:
    src = f"{part} {pages}" if part and pages and pages != "—" else "架構自編"
    lines.append(f"| {no:02d} | {title} | {en} | {src} | {topics or '—'} | {n} | `{fn}` |")
lines.append("")
lines.append("## 每個主題三頁")
lines.append("")
lines.append("| 頁型 | 內容 |")
lines.append("|---|---|")
lines.append("| 概念頁 | 5 個「標籤＋說明」，講為什麼與判斷依據，不含 SQL |")
lines.append("| 程式碼頁 | 以 PDF 原文為依據、改寫成 19c 可執行語法，附重點句與警示句 |")
lines.append("| 檢核頁 | 4–5 條可驗證的檢查項，加上 3 條常見錯誤 |")
lines.append("")
lines.append("每頁講者備忘採固定三段：**講解重點／適用範圍／資料來源（含官方連結）**，可直接列印為講師手冊。")
lines.append("")
lines.append("## 使用須知")
lines.append("")
lines.append("1. 所有指令請先在測試環境驗證；範例中的路徑、資料庫名稱、容量均為示意。")
lines.append("2. 來源文件為 2011 年、10g/11g 時代版本；教材已改寫為 19c 語法，"
             "並在警示句標明舊寫法與差異。")
lines.append("3. 檔名前綴即章號，依序排列即可作為完整課程；`00_Oracle_DBA_課程總覽.pptx` 為索引。")
lines.append("4. 內容資料模組位於 `work/content/chNN.py`，可用 "
             "`work/build_chapter.py` 重新產生任一章。")
lines.append("")

out = os.path.join(DELIVER, "README.md")
open(out, "w", encoding="utf-8").write("\n".join(lines))
print(f"wrote {out}; total={total}")
for no, title, en, part, pages, n, topics, fn in rows:
    print(f"  {no:02d} {n:>3}p {topics:>2}t {title}")
