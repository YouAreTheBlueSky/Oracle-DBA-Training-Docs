# -*- coding: utf-8 -*-
"""Build the ADVANCED course: the four advanced chapters (ASM / RAC / RAC One Node / Warehousing)
taken from the full 14-chapter set, renumbered 01-04.

Output replaces deliver_advance/. Chapters 1-6 and 11-14 are removed from that folder.
Content modules are untouched, so the full 14-chapter set can always be rebuilt with
work/build_all.py + work/build_index.py.
"""
import os, sys, importlib, shutil, hashlib, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, os.path.join(HERE, "content"))
sys.path.insert(0, HERE)

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from base import (C, ZH, MONO, LEFT, WIDTH, LINE_BODY, blank_deck, textbox, para, rect,
                  hline, title, footer, takeaway, warning, table, _set_font, _rgb)
import base
import build_chapter

TEMPLATE = os.path.join(ROOT, "Oracle_Storage_Memory_Process_zhTW.pptx")
OUT = os.path.join(ROOT, "deliver_advance")
INDEX_PATH = os.path.join(OUT, "00_Oracle_DBA_進階課程總覽.pptx")
BEGINNER = os.path.join(ROOT, "deliver_beginner")

# (advanced no, source module, output file, PDF part label, page range)
FORCE = "--force" in sys.argv
ONLY = set()
if "--only" in sys.argv:
    ONLY = {a for a in sys.argv[sys.argv.index("--only") + 1:] if not a.startswith("--")}


DECK_DEP = [os.path.join(HERE, "deckkit", f) for f in ("base.py", "slides.py")]


def newest_dep():
    return max(os.path.getmtime(f) for f in DECK_DEP if os.path.exists(f))


def needs_build(dst, mod):
    """簡報不存在，或內容模組／版面程式比簡報新，才需要重建。"""
    if FORCE or mod in ONLY:
        return True
    if not os.path.exists(dst):
        return True
    src_newest = max(os.path.getmtime(os.path.join(HERE, "content", mod + ".py")), newest_dep())
    return src_newest > os.path.getmtime(dst) + 1


CHAPTERS = [
    (1, "ch07", "01_Oracle_DBA_ASM.pptx", "Part 6", "p.396–409"),
    (2, "ch08", "02_Oracle_DBA_RAC.pptx", "Part 7", "p.410–528"),
    (3, "ch09", "03_Oracle_DBA_RAC_One_Node.pptx", "Part 8", "p.529–550"),
    (4, "ch10", "04_Oracle_DBA_資料倉儲.pptx", "Part 9", "p.551–555"),
]

KEEP = {"README.md"} | {fn for _, _, fn, _, _ in CHAPTERS} | {"00_Oracle_DBA_進階課程總覽.pptx"}


def chapters_meta():
    meta = []
    for no, mod, fn, part, pages in CHAPTERS:
        sp = importlib.import_module(mod).CHAPTER
        meta.append((no, sp["title"], sp["en"], part, pages, fn, len(sp["topics"])))
    return meta


def prune():
    """Remove every file in deliver_advance that is not part of the advanced course."""
    removed = []
    for path in sorted(glob.glob(os.path.join(OUT, "*"))):
        name = os.path.basename(path)
        if name not in KEEP:
            os.remove(path)
            removed.append(name)
    print(f"  removed {len(removed)} file(s): {removed if removed else 'none'}")


def build_chapters():
    os.makedirs(OUT, exist_ok=True)
    rebuilt = []
    for no, mod, fn, part, pages in CHAPTERS:
        dst = os.path.join(OUT, fn)
        sp = importlib.import_module(mod).CHAPTER
        sp["no"] = no
        sp["chap_label"] = f"{no:02d}"
        if not needs_build(dst, mod):
            print(f"  SKIP (up-to-date) {no:02d} {fn}")
            continue
        slides, warns = build_chapter.build(mod, dst)
        expect = build_chapter.count_pages(sp)
        flag = "OK " if slides == expect else "BAD"
        rebuilt.append(fn)
        print(f"  {flag} {no:02d} {mod} -> {fn} ({slides} slides, {len(warns)} warnings)")
    print(f"  重建 {len(rebuilt)} 章")
    return rebuilt


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
    para(tb.text_frame, "TRAINING MATERIAL   ｜   ADVANCED COURSE", size=19.0,
         color=C["cover_sub"], bold=True, first=True)
    tb = textbox(s, 0.90, 1.78, 14.9, 1.45)
    para(tb.text_frame, "Oracle DBA 進階課程", size=52.0, color=C["white"], bold=True,
         first=True)
    tb = textbox(s, 0.94, 3.32, 14.6, 0.95)
    para(tb.text_frame, "ASM ／ RAC ／ RAC One Node ／ 資料倉儲", size=30.0,
         color=C["cover_meta"], first=True)
    hline(s, 0.94, 4.42, 3.95, 4.42, color=C["teal"], width=2.5)
    tb = textbox(s, 0.94, 4.62, 14.6, 0.55)
    para(tb.text_frame, "4 章 ／ 73 頁 ／ 先修建議：初階版第 01–02 章", size=22.0,
         color=C["cover_meta"], first=True)
    tb = textbox(s, 0.94, 5.22, 14.6, 0.50)
    para(tb.text_frame, f"資料來源：oracle_dba_code_examples.pdf（707 頁）　／　本課程共 {total} 頁",
         size=17.0, color="7E9AA0", first=True)
    tb = textbox(s, 0.83, 8.74, 13.2, 0.35)
    para(tb.text_frame, "Oracle Database 19c ｜ DBA 教育訓練教材（進階課程）", size=15.0,
         color=C["body"], first=True)
    tb = textbox(s, 14.55, 8.68, 1.30, 0.44)
    para(tb.text_frame, "01", size=19.5, color=C["body"], align=PP_ALIGN.RIGHT, first=True)
    s.notes_slide.notes_text_frame.text = (
        "【定位】\n進階課程收錄原完整教材的第 7–10 章：ASM、RAC、RAC One Node、資料倉儲，"
        "重新編號為 01–04。與初階版（10 章）合起來即為完整 14 章。\n\n"
        "【先修】\n第 01–02 章假設學員已能操作單機資料庫：啟動關閉、tablespace、redo、control file。"
        "第 02–03 章另需 Grid Infrastructure 與共用儲存環境。")

    # 2 course map
    s = new()
    title(s, "課程地圖：4 章")
    y = 2.00
    last = len(chapters) - 1
    for idx, (no, name, en, part, pages, fn, topics) in enumerate(chapters):
        nb = textbox(s, 0.85, y, 0.85, 0.55)
        para(nb.text_frame, f"{no:02d}", size=26.0, color=C["teal"], bold=True, first=True)
        tb = textbox(s, 1.75, y - 0.06, 7.4, 0.70)
        para(tb.text_frame, name, size=24.0, color=C["ink"], bold=True, first=True)
        eb = textbox(s, 1.78, y + 0.52, 7.6, 0.45)
        para(eb.text_frame, en, size=16.0, color=C["body"], first=True)
        mb = textbox(s, 9.60, y + 0.02, 3.6, 0.45)
        para(mb.text_frame, f"{part}　{pages}", size=16.0, color=C["body"], first=True)
        pb = textbox(s, 13.60, y + 0.02, 2.10, 0.45)
        para(pb.text_frame, f"{counts[no]} 頁 ／ {topics} 主題", size=16.0, color=C["body"],
             align=PP_ALIGN.RIGHT, first=True)
        if idx < last:
            hline(s, 0.85, y + 1.10, 15.70, y + 1.10, color="E2DFD8", width=0.75)
        y += 1.18
    takeaway(s, f"4 章、{total} 頁；每章皆為「概念 → 程式碼 → 檢核」三段式。")
    footer(s, "課程總覽", "02", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n章序依「儲存層 → 叢集 → 叢集特例 → 應用型態」排列。"
        "ASM 先學，因為 RAC 的叢集檔案多半放在 ASM 磁碟群上；RAC One Node 是 RAC 的單節點特例，"
        "排在 RAC 之後；資料倉儲與前兩者無依賴關係，可獨立選修。")

    # 3 prerequisites and order
    s = new()
    title(s, "先修條件與學習路徑")
    rows = [
        ("必要先修", "初階版第 01–02 章：instance 生命週期、參數檔、tablespace 與 datafile 操作。"),
        ("環境需求", "19c Grid Infrastructure、共用儲存（ASM 磁碟群或 ACFS）；RAC 需 2 節點以上。"),
        ("建議順序", "01 ASM → 02 RAC → 03 RAC One Node → 04 資料倉儲；前兩章請勿顛倒。"),
        ("可獨立選修", "第 04 章資料倉儲不依賴 ASM／RAC，適合 BI 或 ETL 團隊單獨上課。"),
    ]
    y = 2.12
    for lead, desc in rows:
        lb = textbox(s, 0.85, y, 2.95, 0.55)
        para(lb.text_frame, lead, size=21.0, color=C["teal"], bold=True, first=True)
        db = textbox(s, 4.00, y - 0.02, 11.6, 0.95)
        para(db.text_frame, desc, size=20.0, color=C["ink"], first=True)
        y += 1.18
    warning(s, "RAC 與 RAC One Node 的指令會實際變更叢集資源，請在練習叢集操作，勿在生產環境試錯。")
    footer(s, "課程總覽", "03", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n初學者常跳過 ASM 直接學 RAC，結果在建立磁碟群與 voting disk 時卡住。"
        "本課程刻意把 ASM 放第 1 章，就是為了讓 RAC 的儲存前提先到位。")

    # 4 source table
    s = new()
    title(s, "章節與資料來源對照")
    header = ["章", "章名", "PDF Part", "PDF 頁碼", "主題", "頁數"]
    rows = [[f"{no:02d}", name, part, pages, f"{topics}", f"{counts[no]}"]
            for no, name, en, part, pages, fn, topics in chapters]
    nrow = len(rows) + 1
    top = 2.10
    row_h = min(0.92, (6.55 - top) / nrow)
    table(s, header, rows, top=top, col_w=[1.1, 6.9, 2.0, 2.6, 1.3, 1.2],
          row_h=row_h, sizes=(18.5, 18.5), align_center_cols=(0, 2, 3, 4, 5))
    footer(s, "課程總覽", "04", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n四章分別對應 PDF 的 Part 6–9，頁碼可直接回查原文。"
        "Part 1–5 與 Part 10–13 屬於初階版範圍。")

    # 5 relation to beginner
    s = new()
    title(s, "進階課程與初階版的關係")
    header = ["項目", "初階版", "進階課程（本資料夾）"]
    rows = [
        ["章數 ／ 頁數", "10 章 ／ 228 頁", "4 章 ／ 73 頁"],
        ["PDF Part", "Part 1–5、10–13", "Part 6–9"],
        ["收錄章節", "架構、建置、連線、備份、安全、效能、工具、OS/EM、PL/SQL、附錄",
         "ASM、RAC、RAC One Node、資料倉儲"],
        ["合計", "初階 10 章 ＋ 進階 4 章 ＝ 完整 14 章、301 頁", "同左"],
    ]
    nrow = len(rows) + 1
    top = 2.05
    row_h = min(0.95, (6.60 - top) / nrow)
    table(s, header, rows, top=top, col_w=[2.6, 7.0, 5.5], row_h=row_h,
          sizes=(17.5, 17.5), align_center_cols=(0,))
    warning(s, "兩套教材採同一版面與三段式體例，學員可無痛接續；章號各自從 01 起算。")
    footer(s, "課程總覽", "05", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n初階與進階是「同一套教材的兩半」，不是難易兩版。"
        "若學員已有單機維運經驗、只想補高可用與儲存，可直接上進階課程。")

    # 6 editorial notes
    s = new()
    title(s, "版本、來源與編輯原則")
    items = [
        ("資料來源", "Oracle DBA Code Examples（Ahmed Baraka，2011/07/30），共 707 頁、13 個 Part。"),
        ("版本基準", "教材以 Oracle Database 19c 敘述；PDF 為 10g/11g 時代，已移除的語法會改寫並加註。"),
        ("改寫重點", "crs_stat／crs_profile 等 10g 工具已由 crsctl／srvctl 取代，教材以 19c 寫法呈現。"),
        ("免責範圍", "範例路徑、資料庫名稱、磁碟群名稱皆為示意；請依實際環境替換後再執行。"),
    ]
    y = 2.15
    for lead, desc in items:
        lb = textbox(s, 0.85, y, 2.65, 0.55)
        para(lb.text_frame, lead, size=21.0, color=C["teal"], bold=True, first=True)
        db = textbox(s, 3.70, y - 0.01, 11.9, 1.0)
        para(db.text_frame, desc, size=20.0, color=C["ink"], first=True)
        y += 1.16
    warning(s, "ASM 磁碟群、voting disk 與 OCR 的操作具不可逆性，執行前務必確認備份與回復計畫。")
    footer(s, "課程總覽", "06", "")
    s.notes_slide.notes_text_frame.text = (
        "【講解重點】\n進階章節的風險高於初階：磁碟群重建、節點增減、voting disk 置換都可能導致"
        "叢集無法啟動，因此每章都保留「常見錯誤」與「檢核」兩頁。")

    # 7 file list
    s = new()
    title(s, "教材檔案清單")
    tb = textbox(s, 0.85, 2.20, WIDTH - 0.2, 4.6)
    tf = tb.text_frame
    files = [("00", "00_Oracle_DBA_進階課程總覽.pptx", len(prs.slides))] + \
            [(f"{no:02d}", fn, counts[no]) for no, name, en, part, pages, fn, topics in chapters]
    first = True
    for no, fn, n in files:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = Pt(28.0)
        r1 = p.add_run()
        r1.text = f"CH{no}  "
        _set_font(r1, MONO, 15.0, True, C["teal"])
        r2 = p.add_run()
        r2.text = f"{fn}    （{n} 頁）"
        _set_font(r2, MONO, 14.0, False, C["ink"])
    footer(s, "課程總覽", "07", "")
    s.notes_slide.notes_text_frame.text = (
        "【使用說明】\n本資料夾只保留進階課程的 4 章與索引。初階版位於 deliver_beginner/，"
        "兩者章號各自從 01 起算，檔案前綴可區分。")

    path = os.path.join(OUT, "00_Oracle_DBA_進階課程總覽.pptx")
    prs.save(path)
    print(f"OK  index: {len(prs.slides)} slides -> {path}")
    for w in base.WARNINGS:
        print("   -", w)
    return total


def build_readme(chapters, total):
    rows = []
    for no, name, en, part, pages, fn, topics in chapters:
        rows.append(f"| {no:02d} | {name} | {en} | {part} {pages} | {topics} | "
                    f"{slide_count(os.path.join(OUT, fn))} | `{fn}` |")
    lines = [
        "# Oracle DBA 進階課程",
        "",
        "完整 14 章教材中的 **第 7–10 章** —— ASM（Part 6）、RAC（Part 7）、"
        "RAC One Node（Part 8）、資料倉儲（Part 9）—— 獨立為本課程，重新編號 **01–04**；"
        "其餘 10 章（1–6、11–14）已移至初階版 `deliver_beginner/`。",
        "",
        f"**共 4 章、{total} 頁。** 內容與完整版完全相同，只重新編號。",
        "",
        "## 章節總表",
        "",
        "| 章 | 章名 | 英文 | PDF 來源 | 主題數 | 頁數 | 檔案 |",
        "|---|---|---|---|---:|---:|---|",
        *rows,
        "",
        "## 與初階版的關係",
        "",
        "| 版本 | 資料夾 | 章數 ／ 頁數 | 收錄 PDF Part |",
        "|---|---|---|---|",
        "| 初階版 | `deliver_beginner/` | 10 章 ／ 228 頁 | Part 1–5、10–13 |",
        f"| 進階課程（本資料夾） | `deliver_advance/` | {len(chapters)} 章 ／ {total} 頁 | Part 6–9 |",
        "| 合計 | — | 14 章 ／ 301 頁 | Part 1–13 |",
        "",
        "## 先修與順序",
        "",
        "1. 先修：初階版第 01–02 章（instance 生命週期、參數檔、tablespace、datafile）。",
        "2. 建議順序：01 ASM → 02 RAC → 03 RAC One Node → 04 資料倉儲。",
        "3. 環境：19c Grid Infrastructure 與共用儲存；RAC 需兩個節點以上。",
        "",
        "## 使用須知",
        "",
        "1. 所有指令請先在測試叢集驗證；ASM 磁碟群、voting disk、OCR 的操作具不可逆性。",
        "2. 來源文件為 2011 年、10g/11g 時代版本；教材已改寫為 19c 語法並在警示句標明差異。",
        "3. 內容模組位於 `work/content/ch07–ch10.py`；重新產生請執行 `work/build_advanced.py`。",
        "4. 需要完整 14 章時，可用 `work/build_all.py` ＋ `work/build_index.py` 重建。",
        "",
    ]
    path = os.path.join(OUT, "README.md")
    open(path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"wrote {path}")


if __name__ == "__main__":
    chapters = chapters_meta()
    print("[0/4] prune")
    prune()
    print("[1/4] chapters")
    rebuilt = build_chapters()
    if not rebuilt and not FORCE and os.path.exists(INDEX_PATH):
        print("  沒有章節變動，索引與 README 不重寫")
        print(f"DONE: advanced course in {OUT}")
        raise SystemExit(0)
    print("[2/4] index")
    total = build_index(chapters)
    print("[3/4] readme")
    build_readme(chapters, total)
    print(f"DONE: advanced course in {OUT}")
