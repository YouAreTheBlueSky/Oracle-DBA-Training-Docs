# -*- coding: utf-8 -*-
"""Prototype: a check page that teaches HOW to check.

Adds a verification-command panel above the pass conditions, so every criterion has
a runnable query and an explicit expected value.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "deckkit"))
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from base import (C, ZH, MONO, LEFT, WIDTH, blank_deck, textbox, para, rect, hline,
                  title, footer, warning, fit_size, _set_font, _rgb, add_bg,
                  wrap_lines, LINE_BODY, LINE_CODE)

TEMPLATE = os.path.join(ROOT, "Oracle_Storage_Memory_Process_zhTW.pptx")
OUT = os.path.join(HERE, "proto", "check_proto.pptx")

SAMPLES = [
    # ---------------------------------------------------------------- 查詢型主題
    {
        "title": "檢核：最佳實務（怎麼驗）",
        "section": "02 建置規劃",
        "commands": [
            "SELECT name, value FROM v$parameter WHERE name = 'spfile';",
            "SELECT tablespace_name, extent_management, segment_space_management",
            "FROM   dba_tablespaces WHERE tablespace_name IN ('SYSTEM','SYSAUX','USERS');",
            "SELECT log_mode FROM v$database;",
            "SELECT COUNT(*) AS files FROM v$controlfile;",
        ],
        "conds": [
            ("spfile 欄位", "有路徑（非空）。空值代表用 PFILE，重開機參數會漂移"),
            ("三個 tablespace", "extent=LOCAL、segment=AUTO。出現 MANUAL 即有 freelist 競爭"),
            ("log_mode", "ARCHIVELOG。NOARCHIVELOG 代表無法做時間點復原"),
            ("控制檔份數", "≥ 2 且在不同磁碟。只有 1 份就是單點"),
        ],
        "pitfalls": [
            "看到 ARCHIVELOG 就結案，沒確認歸檔目的地還有空間",
            "控制檔兩份在同一顆磁碟，壞一顆兩份一起走",
        ],
    },
    # ---------------------------------------------------------------- 動作型主題
    {
        "title": "檢核：RMAN 設定（怎麼驗）",
        "section": "04 RMAN 設定",
        "commands": [
            "RMAN> SHOW ALL;",
            "RMAN> LIST BACKUP SUMMARY;",
            "RMAN> REPORT SCHEMA;",
            "SQL> SELECT * FROM v$rman_configuration;",
            "SQL> SELECT session_key, status, start_time FROM v$rman_backup_job_details",
            "     ORDER BY start_time DESC FETCH FIRST 5 ROWS ONLY;",
        ],
        "conds": [
            ("CONFIGURE 項目", "保留政策、控制檔自動備份、歸檔備份皆有值（非預設空白）"),
            ("LIST BACKUP", "最近一筆狀態為 AVAILABLE，且時間在保留政策內"),
            ("REPORT SCHEMA", "資料檔數量與 dba_data_files 一致，沒有失蹤檔案"),
            ("v$rman_backup_job_details", "最近 5 筆 status 為 COMPLETED，無 FAILED"),
        ],
        "pitfalls": [
            "只設定通道，沒設保留政策，備份無限成長塞滿 FRA",
            "備份成功但從未做過還原測試，災難時才發現缺歸檔",
        ],
    },
]


def build():
    prs = blank_deck(TEMPLATE)
    page = 0
    for sp in SAMPLES:
        page += 1
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = _rgb(C["bg"])
        title(s, sp["title"])

        # --- verification command panel
        lines = sp["commands"]
        inner_w = WIDTH - 0.5
        size = fit_size(lines, inner_w, 18.0, 12.0, mono=True, step=0.5)
        lh = size * LINE_CODE / 72.0
        panel_h = 0.20 + len(lines) * lh + 0.18
        rect(s, LEFT, 1.92, WIDTH, panel_h, fill=C["panel"])
        tb = textbox(s, LEFT + 0.24, 1.92 + 0.18, inner_w, panel_h - 0.36)
        tf = tb.text_frame
        tf.word_wrap = False
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = Pt(size * LINE_CODE)
            r = p.add_run()
            r.text = ln if ln else " "
            _set_font(r, MONO, size, False, C["ink"])

        # --- label
        y = 1.92 + panel_h + 0.22
        lb = textbox(s, 0.85, y, 4.0, 0.36)
        para(lb.text_frame, "通過條件", size=15.0, color=C["teal"], bold=True, first=True)

        # --- conditions (left) + pitfalls (right panel)
        conds = sp["conds"]
        top = y + 0.42
        left_w = 9.55
        size_c, size_e = 17.0, 16.0
        heights = []
        for look, expect in conds:
            h = wrap_lines(expect, left_w - 2.35, size_e) * size_e * LINE_BODY / 72.0
            heights.append(max(0.52, h + 0.16))
        avail = 7.55 - top
        total = sum(heights) + 0.08 * (len(conds) - 1)
        if total > avail:
            k = avail / total
            heights = [h * k for h in heights]
            size_c = max(13.0, size_c * k)
            size_e = max(12.0, size_e * k)
        yy = top
        for (look, expect), h in zip(conds, heights):
            nb = textbox(s, 0.85, yy + 0.02, 2.35, h)
            para(nb.text_frame, look, size=size_c, color=C["ink"], bold=True, first=True)
            tb2 = textbox(s, 3.25, yy, left_w - 2.35, h)
            para(tb2.text_frame, expect, size=size_e, color=C["body"], first=True)
            yy += h + 0.08

        px, pw = 10.95, 4.75
        ph = min(7.55 - top, 3.05)
        rect(s, px, top, pw, ph, fill=C["panel"])
        hb = textbox(s, px + 0.24, top + 0.16, pw - 0.48, 0.36)
        para(hb.text_frame, "常見錯誤", size=14.0, color=C["warn"], bold=True, first=True)
        pb = textbox(s, px + 0.24, top + 0.58, pw - 0.48, ph - 0.72)
        tf2 = pb.text_frame
        for j, ptext in enumerate(sp["pitfalls"]):
            p = tf2.paragraphs[0] if j == 0 else tf2.add_paragraph()
            p.line_spacing = Pt(14.0 * LINE_BODY)
            p.space_before = Pt(0 if j == 0 else 6)
            r1 = p.add_run(); r1.text = "× "
            _set_font(r1, ZH, 13.0, True, C["warn"])
            r2 = p.add_run(); r2.text = ptext
            _set_font(r2, ZH, 13.0, False, C["ink"])

        footer(s, sp["section"], f"{page:02d}", "")
        s.notes_slide.notes_text_frame.text = "【原型】檢核頁加上驗證指令與通過條件，讓學員能自己跑、自己判讀。"

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    prs.save(OUT)
    print("wrote", OUT, len(prs.slides), "slides")


if __name__ == "__main__":
    build()
