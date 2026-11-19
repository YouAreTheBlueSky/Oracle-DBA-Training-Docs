# -*- coding: utf-8 -*-
"""Build the course overview / index deck (00).

Reads actual slide counts from deliver_full/*.pptx so the index never drifts from the files.
"""
import os, sys, glob, re

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "deckkit"))
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from base import (C, ZH, MONO, LEFT, WIDTH, LINE_BODY, blank_deck, textbox, para, rect,
                  hline, title, footer, takeaway, warning, table, fit_size, _rgb)
import base

TEMPLATE = os.path.join(os.path.dirname(HERE), "Oracle_Storage_Memory_Process_zhTW.pptx")
DELIVER = os.path.join(os.path.dirname(HERE), "deliver_full")

CHAPTERS = [
    (1,  "儲存、記憶體與程序架構", "Storage, Memory & Process", "架構自編", "—", "01_Oracle_DBA_儲存記憶體與程序架構.pptx"),
    (2,  "資料庫建置與日常管理", "Oracle DBA Fundamentals", "Part 1", "p.36–237", "02_Oracle_DBA_建置與日常管理.pptx"),
    (3,  "Oracle Net Services 與連線設定", "Oracle Net Services", "Part 2", "p.238–246", "03_Oracle_DBA_Net_Services.pptx"),
    (4,  "備份與復原", "Backup and Recovery", "Part 3", "p.247–310", "04_Oracle_DBA_備份與復原.pptx"),
    (5,  "安全性管理", "Security Management", "Part 4", "p.311–339", "05_Oracle_DBA_安全性管理.pptx"),
    (6,  "效能診斷與調校", "Performance Tuning", "Part 5", "p.340–395", "06_Oracle_DBA_效能診斷與調校.pptx"),
    (7,  "Automatic Storage Management", "ASM", "Part 6", "p.396–409", "07_Oracle_DBA_ASM.pptx"),
    (8,  "Real Application Clusters", "RAC", "Part 7", "p.410–528", "08_Oracle_DBA_RAC.pptx"),
    (9,  "RAC One Node", "RAC One Node", "Part 8", "p.529–550", "09_Oracle_DBA_RAC_One_Node.pptx"),
    (10, "資料倉儲", "Warehousing", "Part 9", "p.551–555", "10_Oracle_DBA_資料倉儲.pptx"),
    (11, "資料庫公用程式", "Database Utilities", "Part 10", "p.556–581", "11_Oracle_DBA_公用程式.pptx"),
    (12, "其他資料庫主題", "Miscellaneous Topics", "Part 11", "p.582–595", "12_Oracle_DBA_其他主題.pptx"),
    (13, "PL/SQL 範例", "PL/SQL Samples", "Part 12", "p.596–673", "13_Oracle_DBA_PLSQL.pptx"),
    (14, "附錄與診斷工具", "Appendices", "Part 13", "p.674–707", "14_Oracle_DBA_附錄.pptx"),
]


def chapter_meta():
    """Real titles/parts from the chapter modules, with fixed file names."""
    sys.path.insert(0, os.path.join(HERE, "content"))
    meta = []
    for no, name, en, part, pages, fn in CHAPTERS:
        if no > 1:
            try:
                mod = __import__(f"ch{no:02d}")
                sp = mod.CHAPTER
                name, en = sp["title"], sp["en"]
                part, pages = sp["part"], sp["source"].split("pdf")[-1].strip()
            except Exception:
                pass
        meta.append((no, name, en, part, pages, fn))
    return meta


def slide_count(path):
    if not os.path.exists(path):
        return 0
    try:
        return len(Presentation(path).slides)
    except Exception:
        return 0


def build(out_path):
    base.WARNINGS.clear()
    prs = blank_deck(TEMPLATE)
    page = [0]

    def new(bg=C["bg"]):
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = _rgb(bg)
        page[0] += 1
        return s

    chapters = chapter_meta()
    counts = {}
    for no, *_rest in chapters:
        fn = _rest[-1]
        counts[no] = slide_count(os.path.join(DELIVER, fn))
    total = sum(counts.values())

    # ---------------------------------------------------------------- 1 cover
    s = new(C["cover"])
    rect(s, 0.90, 1.02, 0.10, 0.42, fill=C["cover_sub"])
    tb = textbox(s, 1.12, 0.98, 12.0, 0.5)
    para(tb.text_frame, "TRAINING MATERIAL   ｜   COURSE OVERVIEW", size=19.0,
         color=C["cover_sub"], bold=True, first=True)
    tb = textbox(s, 0.90, 1.78, 14.9, 1.45)
    para(tb.text_frame, "Oracle DBA 教育訓練教材", size=52.0, color=C["white"], bold=True,
         first=True)
    tb = textbox(s, 0.94, 3.32, 14.6, 0.95)
    para(tb.text_frame, "14 章 ／ 課程總覽與使用說明", size=30.0, color=C["cover_meta"],
         first=True)
    hline(s, 0.94, 4.42, 3.95, 4.42, color=C["teal"], width=2.5)
    tb = textbox(s, 0.94, 4.62, 14.6, 0.55)
    para(tb.text_frame, "架構基礎 → 建置 → 連線 → 備份 → 安全 → 效能 → 高可用 → 工具",
         size=22.0, color=C["cover_meta"], first=True)
    tb = textbox(s, 0.94, 5.22, 14.6, 0.50)
    para(tb.text_frame, f"資料來源：oracle_dba_code_examples.pdf（707 頁）　／　全系列共 {total} 頁",
         size=17.0, color="7E9AA0", first=True)
    tb = textbox(s, 0.83, 8.74, 13.2, 0.35)
    para(tb.text_frame, "Oracle Database 19c ｜ DBA 教育訓練教材", size=15.0, color=C["body"],
         first=True)
    tb = textbox(s, 14.55, 8.68, 1.30, 0.44)
    para(tb.text_frame, "01", size=19.5, color=C["body"], align=PP_ALIGN.RIGHT, first=True)
    s.notes_slide.notes_text_frame.text = (
        "【使用說明】\n這一份是課程總覽，說明 14 章的排列邏輯、每章的資料來源頁碼與頁數，"
        "以及每個主題三頁（概念／程式碼／檢核）的編輯體例。\n\n"
        "【授課建議】\n第 1–2 章為共同必修，第 3–14 章可依學員角色（維運、備份、效能、開發）選修。")

    # ---------------------------------------------------------------- 2 course map
    s = new()
    title(s, "課程地圖：14 章")
    rows = chapters
    col_w = (WIDTH - 0.35) / 2
    per_col = 7
    for ci in range(2):
        chunk = rows[ci * per_col:(ci + 1) * per_col]
        x = LEFT + ci * (col_w + 0.35)
        y = 1.70
        for no, name, en, part, pages, fn in chunk:
            nb = textbox(s, x, y, 0.72, 0.42)
            para(nb.text_frame, f"{no:02d}", size=20.0, color=C["teal"], bold=True, first=True)
            tb = textbox(s, x + 0.72, y - 0.02, col_w - 1.55, 0.72)
            para(tb.text_frame, name, size=19.0, color=C["ink"], bold=True, first=True,
                 line=1.1)
            pb = textbox(s, x + col_w - 0.82, y, 0.82, 0.42)
            para(pb.text_frame, f"{counts[no]} 頁", size=16.0, color=C["body"],
                 align=PP_ALIGN.RIGHT, first=True)
            hline(s, x, y + 0.62, x + col_w, y + 0.62, color="E2DFD8", width=0.75)
            y += 0.72
    takeaway(s, f"全部 14 章合計 {total} 頁；第 1 章沿用既有架構教材，其餘 13 章依 PDF 的 13 個 Part 對應。")
    footer(s, "課程總覽", "02", "")
    s.notes_slide.notes_text_frame.text = (
        "章序刻意把「架構」與「建置」放最前面：先知道 instance 與 database 的組成，"
        "後面的參數、檔案、備份才有依附的對象。第 7–9 章（ASM、RAC）屬於高可用選項，可依環境選修。")

    # ---------------------------------------------------------------- 3 structure
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
    para(tb.text_frame, "每頁的講者備忘含重點說明、適用範圍與資料來源，可直接列印為講師手冊。",
         size=19.0, color=C["body"], first=True)
    footer(s, "課程總覽", "03", "")
    s.notes_slide.notes_text_frame.text = (
        "三頁一組的節奏，讓學員每 15 分鐘完成一次「理解 → 看指令 → 自我驗證」的循環。"
        "程式碼頁刻意不加長篇說明，說明放在概念頁；檢核頁則是課後練習與交付檢查表的來源。")

    # ---------------------------------------------------------------- 4-5 source table
    for part_i, (lo, hi) in enumerate(((0, 7), (7, 14)), start=4):
        s = new()
        title(s, f"章節與資料來源對照（{lo + 1}–{hi}）")
        header = ["章", "章名", "PDF Part", "PDF 頁碼", "頁數"]
        rows = []
        for no, name, en, part, pages, fn in chapters[lo:hi]:
            rows.append([f"{no:02d}", name, part, pages, f"{counts[no]}"])
        nrow = len(rows) + 1
        top = 2.05
        row_h = min(0.74, (6.55 - top) / nrow)
        table(s, header, rows, top=top, col_w=[1.05, 7.35, 2.0, 2.75, 1.95],
              row_h=row_h, sizes=(17.5, 17.5), align_center_cols=(0, 2, 3, 4))
        footer(s, "課程總覽", f"{part_i:02d}", "")
        s.notes_slide.notes_text_frame.text = (
            "左表同時是「這頁教材從哪裡來」的追溯紀錄：每一章的 PDF 頁碼可直接回查原文。"
            "第 1 章為自編架構教材，不對應 PDF Part。")

    # ---------------------------------------------------------------- 6 pacing
    s = new()
    title(s, "建議授課節奏")
    header = ["章", "定位", "建議時數", "教學重點"]
    rows = [
        ["01–02", "共同必修", "6 小時", "架構、建置、參數、tablespace、undo"],
        ["03–05", "維運必修", "6 小時", "連線、備份復原、權限與稽核"],
        ["06", "效能必修", "4 小時", "等待事件、ASH、SQL 計畫"],
        ["07–09", "高可用選修", "6 小時", "ASM 磁碟群、RAC 與 RAC One Node"],
        ["10–14", "工具與附錄", "4 小時", "公用程式、PL/SQL、資料字典"],
    ]
    table(s, header, rows, top=2.10, col_w=[1.85, 3.0, 2.5, 7.75],
          row_h=0.80, sizes=(19.0, 19.0), align_center_cols=(0, 1, 2))
    takeaway(s, "合計約 26 小時；若為 3 天班，建議每天 9 小時並將第 10–14 章改為課後自習。")
    footer(s, "課程總覽", "06", "")
    s.notes_slide.notes_text_frame.text = (
        "時數建議以「講授 60%、實作 40%」估算；程式碼頁最好都讓學員在練習環境跑一次。")

    # ---------------------------------------------------------------- 7 editorial notes
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
    footer(s, "課程總覽", "07", "")
    s.notes_slide.notes_text_frame.text = (
        "這一頁是教材的法律與技術邊界：來源授權屬原作者，程式碼由學員自行承擔風險，"
        "版本差異則由講師在課堂上補充。")

    # ---------------------------------------------------------------- 8 file list
    s = new()
    title(s, "教材檔案清單")
    tb = textbox(s, 0.85, 2.05, WIDTH - 0.2, 5.0)
    tf = tb.text_frame
    first = True
    for no, name, en, part, pages, fn in chapters:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = Pt(20.0)
        r1 = p.add_run()
        r1.text = f"CH{no:02d}  "
        from base import _set_font
        _set_font(r1, MONO, 14.0, True, C["teal"])
        r2 = p.add_run()
        r2.text = f"{fn}    （{counts[no]} 頁）"
        _set_font(r2, MONO, 13.0, False, C["ink"])
    footer(s, "課程總覽", "08", "")
    s.notes_slide.notes_text_frame.text = (
        "【使用說明】\n每章一個獨立檔案，方便分堂授課與分發；檔名前綴即章號，依序排列即可。"
        "本檔為索引，建議與各章一併歸檔。")

    prs.save(out_path)
    print(f"OK  index: {len(prs.slides)} slides, total course pages={total} -> {out_path}")
    missing = [no for no, c in counts.items() if c == 0]
    if missing:
        print("  MISSING chapter files for:", missing)
    for w in base.WARNINGS:
        print("   -", w)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1
          else os.path.join(DELIVER, "00_Oracle_DBA_課程總覽.pptx"))
