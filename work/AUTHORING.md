# 教材撰寫規範（給章節作者）

你正在為一套 Oracle DBA 教育訓練教材撰寫**其中一章**的內容資料檔。
教材以繁體中文授課，技術名詞保留英文，版面由既有的 deckkit 產生，**你不需要、也不可以改動版面程式**。

## 一、你的工作

1. 讀 `work/extract/chNN.txt`（該章對應的 PDF 原文，內含 `===== pNNN =====` 頁碼標記）。
2. 建立 `work/content/chNN.py`，內容格式見下方「資料結構」。
3. 執行建置自我檢查（見「建置與驗收」），修正到沒有錯誤。
4. 回報：章節頁數、主題清單、建置警告。

## 二、內容規格（重要）

每章固定結構：封面 → 本章大綱 → 每主題三頁（概念 → 程式碼 → 檢核）→ 本章重點回顧 → 參考資料。

### 三段式的分工

| 頁型 | 內容 | 禁止 |
|---|---|---|
| **概念頁** | 5 個「標籤＋說明」，說明**為什麼**與**判斷依據**，不是指令複述 | 不要放 SQL |
| **程式碼頁** | 從 PDF 原文明確可查的指令，改寫成 19c 可執行語法，附重點句與警示句 | 不可自行發明指令或參數 |
| **檢核頁** | 3–6 行可執行的驗證指令 ＋ 4 條通過條件 ＋ 2–3 個常見錯誤（格式見 `work/AUTHORING_CHECK.md`） | 不要只寫「要注意」這種空話，也不要重貼程式碼頁的 DDL |

### 硬性限制

- 語言：繁體中文（台灣用語），技術名詞用英文：tablespace、datafile、checkpoint 等。
- **程式碼頁最多 12 行**，每行**最多 84 個字元**（含縮排）。超過就要拆或刪。
- 程式碼註解可用中文，但一行不要超過 20 個中文字，否則字會太小。
- 概念頁：`lead`（標籤）≤ 14 字；`desc`（說明）≤ 46 字，超過會自動縮字級。
- 檢核頁：驗證指令 ≤ 6 行、每行 ≤ 82 字元；通過條件 4 條；`pitfalls` 2–3 條、每條 ≤ 26 字。
- 標題 ≤ 26 個中文字。
- 不要使用 emoji、全形標點以外的特殊符號（× 、 ／ 、 ・ 可用）。

## 三、資料結構

```python
# -*- coding: utf-8 -*-
REFS = ["https://docs.oracle.com/en/database/oracle/oracle-database/19/...", ...]
SCOPE = "（適用範圍一句話，說明版本與前提）"

CHAPTER = {
    "no": 4,                       # 章號，整數
    "part": "Part 3",              # PDF 的 Part 編號
    "title": "備份與復原",          # 章名，≤ 16 字
    "en": "Oracle Database Backup and Recovery",   # 英文副標
    "subtitle": "RMAN ／ 備份策略 ／ 復原情境",
    "source": "oracle_dba_code_examples.pdf  p.247–310",
    "chap_label": "04",
    "agenda_title": "本章大綱",
    "agenda": [("小節名", "一句話說明，≤ 50 字"), ...],   # 5 個小節，對應 topics 的 section
    "agenda_note": "一句話，說明本章在整體課程的位置",
    "note_why": "一句話，說明本章編輯策略",
    "refs": REFS,
    "refs_note": "版本提醒一句話",
    "topics": [
        {
            "title": "主題標題",
            "section": "小節名（必須是 agenda 裡的其中一個）",
            "src": "來源 p.xxx",
            "concept": {
                "items": [("標籤", "說明"), ...],     # 5 個
                "note": "重點句（選填）",
            },
            "code": {
                "lines": ["SELECT ...", "", "-- 註解", ...],   # ≤ 12 行
                "takeaway": "重點句，≤ 34 字",
                "warning": "警示句，≤ 40 字（選填，但建議每章至少一半主題要有）",
            },
            "check": {
                "title": "自我檢核：...",
                "commands": ["SELECT ...", ...],      # 3–6 行，見 AUTHORING_CHECK.md
                "conds": [("欄位", "期望值與意義"), ...],   # 4 條
                "pitfalls": ["...", ...],             # 3 條
                "warning": "（選填）",
            },
            "_note_why": "講者備忘：這一主題的講解重點，2–3 句",
            "_note_scope": "講者備忘：適用範圍",
            "_refs": [REFS[0]],
        },
        ...
    ],
    "summary": {
        "items": [("標籤", "說明"), ...],   # 5 條，每條 ≤ 40 字
        "section": "整合複習",
        "note": "一句話",
    },
}
```

`code` 可以換成 `table`（適合流程、對照、清單類主題）：

```python
"table": {
    "header": ["欄一", "欄二", "欄三"],
    "rows": [["...", "...", "..."], ...],   # 4–6 列
    "widths": [2.0, 8.0, 5.1],              # 總和 = 15.1
    "small": True,
    "note": "重點句",
},
```

每章最多 2 個 `table` 主題，其餘用 `code`。

## 四、建置與驗收

```powershell
& 'C:\Users\user\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe' work\build_chapter.py ch04 "deliver\04_Oracle_DBA_備份與復原.pptx"
```

驗收標準：

1. 輸出 `OK  ch04: N slides (expected N)`，不可有 Traceback。
2. 警告（layout warnings）中**不可出現** `title shrunk`、`table cell may overflow`；`code` 字級 ≥ 17pt 為佳；`concept shrunk` 要到 19pt 以上。
3. 頁數 = 2 + 主題數×3 + 2（若某主題用 table，仍算 3）。

出現字級過小的警告時，**優先刪減程式碼行數或縮短說明文字**，不要改版面程式。

## 五、紅線

- 不可修改 `work/deckkit/`、`work/build_chapter.py`、`work/content/ch02.py`。
- 不可修改 `deliver/` 底下別人的檔案。
- 指令必須能在 PDF 原文對應頁碼找到依據；19c 已移除的語法要改寫並在 `warning` 說明。
- 不要把 PDF 的英文條列整段貼上；要轉成中文說明，只保留必要的技術名詞。
