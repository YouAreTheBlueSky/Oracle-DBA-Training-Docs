# -*- coding: utf-8 -*-
"""Build the BEGINNER edition: the advanced set minus Chapters 7-10 (ASM / RAC / RAC One Node / Warehousing).

Reuses the same content modules and the same deckkit, so the visual language is identical.
Beginner chapters are renumbered 01-10; `deliver_advance/` (advanced, 14 chapters) is left untouched.
"""
import os, sys, importlib, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, os.path.join(HERE, "content"))
sys.path.insert(0, HERE)

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from base import (C, ZH, MONO, LEFT, WIDTH, LINE_BODY, blank_deck, textbox, para, rect,
                  hline, title, footer, takeaway, warning, table, _set_font, _rgb,
                  fit_size)
import base
import build_chapter

TEMPLATE = os.path.join(ROOT, "Oracle_Storage_Memory_Process_zhTW.pptx")
ADVANCED = os.path.join(ROOT, "deliver_advance")
OUT = os.path.join(ROOT, "deliver_beginner")

# (beginner no, source module or None for chapter 1, output file name)
CHAPTERS = [
    (1, None,   "01_Oracle_DBA_儲存記憶體與程序架構.pptx"),
    (2, "ch02", "02_Oracle_DBA_建置與日常管理.pptx"),
    (3, "ch03", "03_Oracle_DBA_Net_Services.pptx"),
    (4, "ch04", "04_Oracle_DBA_備份與復原.pptx"),
    (5, "ch05", "05_Oracle_DBA_安全性管理.pptx"),
    (6, "ch06", "06_Oracle_DBA_效能診斷與調校.pptx"),
    (7, "ch11", "07_Oracle_DBA_公用程式.pptx"),
    (8, "ch12", "08_Oracle_DBA_作業系統與EM工具.pptx"),
    (9, "ch13", "09_Oracle_DBA_PLSQL.pptx"),
    (10, "ch14", "10_Oracle_DBA_附錄.pptx"),
]

CH1 = {
    "title": "儲存、記憶體與程序架構", "en": "Storage, Memory & Process",
    "part": "架構自編", "pages": "—",
}

REMOVED = [
    ("ASM（Part 6）", "進階課程 第 1 章"),
    ("RAC（Part 7）", "進階課程 第 2 章"),
    ("RAC One Node（Part 8）", "進階課程 第 3 章"),
    ("資料倉儲（Part 9）", "進階課程 第 4 章"),
]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest().upper()


def chapters_meta():
    """Resolve titles/sources from the modules, with beginner numbering."""
    meta = []
    for no, mod, fn in CHAPTERS:
        if mod is None:
            meta.append((no, CH1["title"], CH1["en"], CH1["part"], CH1["pages"], fn, 0))
            continue
        sp = importlib.import_module(mod).CHAPTER
        meta.append((no, sp["title"], sp["en"], sp["part"],
                     sp["source"].split("pdf")[-1].strip(), fn, len(sp["topics"])))
    return meta


def build_chapters():
    os.makedirs(OUT, exist_ok=True)
    ch1_dst = os.path.join(OUT, CHAPTERS[0][2])
    if os.path.basename(ch1_dst) in build_chapter.frozen_names() and os.path.exists(ch1_dst):
        print(f"  SKIP (frozen) {ch1_dst} — kept as-is")
    else:
        shutil.copyfile(os.path.join(ROOT, "Oracle_Storage_Memory_Process_zhTW.pptx"), ch1_dst)
    print(f"  01 copied, sha matches original: "
          f"{sha(os.path.join(OUT, CHAPTERS[0][2])) == sha(os.path.join(ROOT, 'Oracle_Storage_Memory_Process_zhTW.pptx'))}")
    for no, mod, fn in CHAPTERS[1:]:
        sp = importlib.import_module(mod).CHAPTER
        sp["no"] = no
        sp["chap_label"] = f"{no:02d}"
        slides, warns = build_chapter.build(mod, os.path.join(OUT, fn))
        expect = 2 + 3 * len(sp["topics"]) + 2
        flag = "OK " if slides == expect else "BAD"
        print(f"  {flag} {no:02d} {mod} -> {fn} ({slides} slides, {len(warns)} warnings)")


def slide_count(path):
    return len(Presentation(path).slides) if os.path.exists(path) else 0


def build_index(chapters):
    base.WARNINGS.clear()
    prs = blank_deck(TEMPLATE)
    page = [0]
    counts = {no: slide_count(os.path.join(OUT, fn)) for no, *_, fn, _t in
              [(c[0], c[1], c[2], c[3], c[4], c[5], c[6]) for c in chapters]}
    total = sum(counts.values())

    def new(bg=C["bg"]):
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = _rgb(bg)
        page[0] += 1
        return s

    # 1 cover
    s = new(C["cover"])
    rect(s, 0.90, 1.02, 0.10, 0.42, fill=C["cover_sub"])
    tb = textbox(s, 1.12, 0.98, 12.0, 0.5)
    para(tb.text_frame, "TRAINING MATERIAL   ｜   BEGINNER EDITION", size=19.0,
         color=C["cover_sub"], bold=True, first=True)
    tb = textbox(s, 0.90, 1.78, 14.9, 1.45)
    para(tb.text_frame, "Oracle DBA 教育訓練教材", size=52.0, color=C["white"], bold=True,
         first=True)
    tb = textbox(s, 0.94, 3.32, 14.6, 0.95)
    para(tb.text_frame, "初階版 ／ 10 章 ／ 課程總覽與使用說明", size=30.0,
         color=C["cover_meta"], first=True)
    hline(s, 0.94, 4.42, 3.95, 4.42, color=C["teal"], width=2.5)
    tb = textbox(s, 0.94, 4.62, 14.6, 0.55)
    para(tb.text_frame, "架構 → 建置 → 連線 → 備份 → 安全 → 效能 → 工具", size=22.0,
         color=C["cover_meta"], first=True)
    tb = textbox(s, 0.94, 5.22, 14.6, 0.50)
    para(tb.text_frame, f"資料來源：oracle_dba_code_examples.pdf（707 頁）　／　本版共 {total} 頁",
         size=17.0, color="7E9AA0", first=True)
    tb = textbox(s, 0.83, 8.74, 13.2, 0.35)
    para(tb.text_frame, "Oracle Database 19c ｜ DBA 教育訓練教材（初階版）", size=15.0,
         color=C["body"], first=True)
    tb = textbox(s, 14.55, 8.68, 1.30, 0.44)
    para(tb.text_frame, "01", size=19.5, color=C["body"], align=PP_ALIGN.RIGHT, first=True)
    s.notes_slide.notes_text_frame.text = (
        "【使用說明】\n完整教材共 14 章，拆為兩套：初階版（本資料夾，10 章）與進階課程"
        "（deliver_advance/，4 章）。本版收錄第 1–6、11–14 章並重新編號為 01–10。\n\n"
        "【授課建議】\n初階班建議 3 天（約 18–20 小時），第 01–02 章必講，其餘依學員角色選講。")

    # 2 course map
    s = new()
    title(s, "課程地圖：10 章")
    per_col = 5
    col_w = (WIDTH - 0.35) / 2
    for ci in range(2):
        chunk = chapters[ci * per_col:(ci + 1) * per_col]
        x = LEFT + ci * (col_w + 0.35)
        y = 1.86
        for no, name, en, part, pages, fn, topics in chunk:
            nb = textbox(s, x, y, 0.72, 0.42)
            para(nb.text_frame, f"{no:02d}", size=20.0, color=C["teal"], bold=True, first=True)
            tb = textbox(s, x + 0.72, y - 0.02, col_w - 1.55, 0.72)
            para(tb.text_frame, name, size=19.0, color=C["ink"], bold=True, first=True)
            pb = textbox(s, x + col_w - 0.82, y, 0.82, 0.42)
            para(pb.text_frame, f"{counts[no]} 頁", size=16.0, color=C["body"],
                 align=PP_ALIGN.RIGHT, first=True)
            hline(s, x, y + 0.70, x + col_w, y + 0.70, color="E2DFD8", width=0.75)
            y += 0.86
    takeaway(s, f"初階版共 10 章、{total} 頁；ASM、RAC、RAC One Node 與資料倉儲另收錄於進階課程。")
    footer(s, "課程總覽", "02", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n初階版保留「架構 → 建置 → 連線 → 備份 → 安全 → 效能 → 工具」的主線，"
        "把需要多節點或額外授權的 ASM／RAC 移到進階課程，避免初學者同時面對叢集與磁碟群概念。")

    # 3 structure
    s = new()
    title(s, "教材結構：每個主題三頁")
    items = [
        ("① 概念頁", "用 5 個「標籤＋說明」講清楚為什麼、以及判斷依據；不出現 SQL。"),
        ("② 程式碼頁", "以 PDF 原文為依據的指令，改成 19c 可執行語法，附重點句與警示句。"),
        ("③ 檢核頁", "3–6 行驗證指令、4 條通過條件，加上 2–3 個最常見的錯誤。"),
    ]
    y = 2.10
    for lead, desc in items:
        lb = textbox(s, 0.85, y, 3.05, 0.60)
        para(lb.text_frame, lead, size=24.0, color=C["teal"], bold=True, first=True)
        db = textbox(s, 4.15, y + 0.02, 11.4, 0.80)
        para(db.text_frame, desc, size=21.0, color=C["ink"], first=True)
        y += 1.28
    hline(s, 0.85, 6.02, 15.7, 6.02, color=C["rule"], width=0.75)
    tb = textbox(s, 0.85, 6.18, WIDTH - 0.2, 0.75)
    para(tb.text_frame, "每頁講者備忘固定三段：講解重點／適用範圍／資料來源，可直接列印為講師手冊。",
         size=19.0, color=C["body"], first=True)
    footer(s, "課程總覽", "03", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n三頁一組的節奏，讓學員每 15 分鐘完成一次「理解 → 看指令 → 自我驗證」的循環。")

    # 4-5 source tables
    for idx, (lo, hi) in enumerate(((0, 5), (5, 10)), start=4):
        s = new()
        title(s, f"章節與資料來源對照（{lo + 1}–{hi}）")
        header = ["章", "章名", "PDF Part", "PDF 頁碼", "頁數"]
        rows = [[f"{no:02d}", name, part, pages, f"{counts[no]}"]
                for no, name, en, part, pages, fn, topics in chapters[lo:hi]]
        nrow = len(rows) + 1
        top = 2.05
        row_h = min(0.80, (6.55 - top) / nrow)
        table(s, header, rows, top=top, col_w=[1.05, 7.35, 2.0, 2.75, 1.95],
              row_h=row_h, sizes=(18.0, 18.0), align_center_cols=(0, 2, 3, 4))
        footer(s, "課程總覽", f"{idx:02d}", "")
        s.notes_slide.notes_text_frame.text = (
            "【講解重點】\n每一章的 PDF 頁碼可直接回查原文。第 1 章為自編架構教材，不對應 PDF Part；"
            "Part 6–9 未收錄於初階版。")

    # 6 learning path
    s = new()
    title(s, "學習路徑：從初階到進階")
    steps = [
        ("第一輪　架構與建置", "第 01–02 章：先看懂 instance 與 database 的組成，再談參數與檔案。"),
        ("第二輪　維運三件事", "第 03–05 章：連線設定、備份復原、權限與稽核，這是日常工作的主體。"),
        ("第三輪　效能與工具", "第 06–10 章：等待事件與 ASH、Data Pump、OS 前置、PL/SQL、排程。"),
        ("延伸　進階課程", "ASM 磁碟群、RAC 與 RAC One Node、資料倉儲，建議具備單機維運經驗後再學。"),
    ]
    y = 2.10
    for lead, desc in steps:
        lb = textbox(s, 0.85, y, 4.55, 0.62)
        para(lb.text_frame, lead, size=21.0, color=C["teal"], bold=True, first=True)
        db = textbox(s, 5.75, y, 9.95, 1.0)
        para(db.text_frame, desc, size=20.0, color=C["ink"], first=True)
        y += 1.24
    footer(s, "課程總覽", "06", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n四輪的順序對應「先能開庫、再能維運、最後才談調校與高可用」。"
        "初學者若一開始就學 RAC，會同時面對叢集、共享儲存與全域快取三個新概念，學習負荷過重。")

    # 7 edition comparison
    s = new()
    title(s, "初階版與進階課程的差異")
    header = ["項目", "初階版（本版）", "進階課程"]
    rows = [
        ["章數 ／ 頁數", f"{len(chapters)} 章 ／ {total} 頁", "4 章 ／ 73 頁"],
        ["PDF Part 收錄", "Part 1–5、10–13（共 9 個）", "Part 6–9（共 4 個）"],
    ]
    for label, where in REMOVED:
        rows.append([label, "未收錄", where])
    rows.append(["合計", "初階 10 章 ＋ 進階 4 章 ＝ 14 章、301 頁", "同左"])
    nrow = len(rows) + 1
    top = 2.02
    row_h = min(0.62, (6.60 - top) / nrow)
    table(s, header, rows, top=top, col_w=[4.6, 5.25, 5.25], row_h=row_h,
          sizes=(17.0, 17.0), align_center_cols=())
    warning(s, "兩版差異僅在收錄範圍；同一章的文字、程式碼與檢核頁完全相同。")
    footer(s, "課程總覽", "07", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n初階版不是簡化版，而是「範圍較小、深度不變」。若學員已有單機維運經驗，"
        "可直接上進階課程；若完全沒有 Oracle 經驗，建議先完成初階版。")

    # 8 editorial notes
    s = new()
    title(s, "版本、來源與編輯原則")
    items = [
        ("資料來源", "Oracle DBA Code Examples（Ahmed Baraka，2011/07/30），共 707 頁、13 個 Part。"),
        ("版本基準", "教材以 Oracle Database 19c 敘述；PDF 為 10g/11g 時代，已移除的語法會改寫並加註。"),
        ("編輯原則", "PDF 只給任務與程式碼，教材補上「為什麼」與「怎麼驗證」，但不改動指令語意。"),
        ("免責範圍", "範例路徑、資料庫名稱、容量皆為示意；請依實際環境替換後再執行。"),
    ]
    y = 2.15
    for lead, desc in items:
        lb = textbox(s, 0.85, y, 2.65, 0.55)
        para(lb.text_frame, lead, size=21.0, color=C["teal"], bold=True, first=True)
        db = textbox(s, 3.70, y - 0.01, 11.9, 1.0)
        para(db.text_frame, desc, size=20.0, color=C["ink"], first=True)
        y += 1.16
    warning(s, "所有 DDL／DML 範例請先在測試環境驗證；生產環境執行前務必確認備份與回復計畫。")
    footer(s, "課程總覽", "08", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n這一頁是教材的技術邊界：來源授權屬原作者，程式碼由學員自行承擔風險，"
        "版本差異由講師在課堂上補充。")

    # 9 file list
    s = new()
    title(s, "教材檔案清單")
    tb = textbox(s, 0.85, 2.20, WIDTH - 0.2, 4.8)
    tf = tb.text_frame
    first = True
    for no, name, en, part, pages, fn, topics in chapters:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = Pt(24.0)
        r1 = p.add_run()
        r1.text = f"CH{no:02d}  "
        _set_font(r1, MONO, 14.0, True, C["teal"])
        r2 = p.add_run()
        r2.text = f"{fn}    （{counts[no]} 頁）"
        _set_font(r2, MONO, 13.0, False, C["ink"])
    footer(s, "課程總覽", "09", "")
    s.notes_slide.notes_text_frame.text = (
        "【使用說明】\n每章一個獨立檔案，檔名前綴即章號，依序排列即可。本檔為索引，建議與各章一併歸檔。")

    path = os.path.join(OUT, "00_Oracle_DBA_初階課程總覽.pptx")
    prs.save(path)
    print(f"OK  index: {len(prs.slides)} slides -> {path}")
    for w in base.WARNINGS:
        print("   -", w)
    return total


def build_readme(chapters, total):
    rows = []
    for no, name, en, part, pages, fn, topics in chapters:
        src = "架構自編" if no == 1 else f"{part} {pages}"
        rows.append(f"| {no:02d} | {name} | {en} | {src} | {topics or '—'} | "
                    f"{slide_count(os.path.join(OUT, fn))} | `{fn}` |")
    lines = [
        "# Oracle DBA 教育訓練教材（初階版）",
        "",
        "完整教材共 14 章 301 頁，拆為兩套：**初階版（本資料夾，10 章）** 與 "
        "**進階課程（`deliver_advance/`，4 章 73 頁）**。"
        "本版收錄第 1–6、11–14 章並重新編號為 **01–10**；"
        "ASM、RAC、RAC One Node、資料倉儲移至進階課程。",
        "",
        f"**共 10 章、{total} 頁。** 每章一個獨立 PPTX，內容與進階課程同一套體例。",
        "",
        "## 章節總表",
        "",
        "| 章 | 章名 | 英文 | PDF 來源 | 主題數 | 頁數 | 檔案 |",
        "|---|---|---|---|---:|---:|---|",
        *rows,
        "",
        "## 每個主題三頁",
        "",
        "| 頁型 | 內容 |",
        "|---|---|",
        "| 概念頁 | 5 個「標籤＋說明」，講為什麼與判斷依據，不含 SQL |",
        "| 程式碼頁 | 以 PDF 原文為依據、改寫成 19c 可執行語法，附重點句與警示句 |",
        "| 檢核頁 | 3–6 行可執行的驗證指令 ＋ 4 條通過條件 ＋ 2–3 個常見錯誤 |",
        "",
        "## 兩個版本的關係",
        "",
        "| 項目 | 初階版（本資料夾） | 進階課程（`deliver_advance/`） |",
        "|---|---|---|",
        f"| 章數 ／ 頁數 | {len(chapters)} 章 ／ {total} 頁 | 4 章 ／ 73 頁 |",
        "| 收錄 PDF Part | Part 1–5、10–13（9 個） | Part 6–9（4 個） |",
        "| ASM ／ RAC ／ RAC One Node ／ 倉儲 | 未收錄 | 第 1–4 章 |",
        "",
        "## 使用須知",
        "",
        "1. 所有指令請先在測試環境驗證；範例中的路徑、資料庫名稱、容量均為示意。",
        "2. 來源文件為 2011 年、10g/11g 時代版本；教材已改寫為 19c 語法，並在警示句標明差異。",
        "3. 內容資料模組位於 `work/content/chNN.py`，重新產生初階版請執行 `work/build_beginner.py`。",
        "",
    ]
    path = os.path.join(OUT, "README.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"wrote {path}")


if __name__ == "__main__":
    chapters = chapters_meta()
    print("[1/3] chapters")
    build_chapters()
    print("[2/3] index")
    total = build_index(chapters)
    print("[3/3] readme")
    build_readme(chapters, total)
    print(f"DONE: beginner edition in {OUT}")
