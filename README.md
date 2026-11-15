# Oracle DBA 教育訓練教材（Oracle Database 19c）

以 Oracle DBA Code Examples（Ahmed Baraka, 2011）為內容依據，改寫為**繁體中文、19c 語法**的簡報教材。
視覺規範取自 `Oracle_Storage_Memory_Process_zhTW.pptx`：底色 `#F7F5F0`、封面色 `#132E38`、
青綠 `#147A7E`、程式碼面板 `#E6EDEB`、表頭 `#132E38`，字體 Microsoft JhengHei ＋ Consolas。

## 兩套教材

完整 14 章（301 頁）拆成兩套，章號各自從 01 起算：

| 版本 | 資料夾 | 章數 | 頁數 | 收錄 PDF Part |
|---|---|---:|---:|---|
| 初階版 | [`deliver_beginner/`](deliver_beginner/) | 10 章 | 228 | Part 1–5、10–13 |
| 進階課程 | [`deliver_advance/`](deliver_advance/) | 4 章 | 73 | Part 6–9 |

合計 14 章 301 頁，對應來源文件的 13 個 Part，另加一章自編的架構基礎。

### 初階版 01–10

01 儲存、記憶體與程序架構　02 資料庫建置與日常管理　03 Oracle Net Services　04 備份與復原
05 安全性管理　06 效能診斷與調校　07 資料庫公用程式　08 作業系統前置與 EM 管理工具
09 PL/SQL 範例　10 附錄：小工具與作業系統排程

### 進階課程 01–04

01 ASM 自動儲存管理　02 RAC 叢集資料庫管理　03 RAC One Node 建置與線上搬移　04 資料倉儲

## 每個主題三頁

| 頁型 | 內容 |
|---|---|
| 概念頁 | 5 個「標籤＋說明」，講為什麼與判斷依據，不含 SQL |
| 程式碼頁 | 以來源文件為依據、改寫成 19c 可執行語法，附重點句與警示句 |
| 檢核頁 | 4–5 條可驗證的檢查項，加上 3 條常見錯誤 |

每頁講者備忘固定三段：**講解重點／適用範圍／資料來源（含官方連結）**。

## 專案結構

```
deliver_beginner/     初階版 11 個 PPTX ＋ README
deliver_advance/      進階課程 5 個 PPTX ＋ README
work/content/         章節內容模組 ch02–ch14.py（教材的唯一真實來源）
work/deckkit/         版面產生器（base.py 設計常數、slides.py 頁型）
work/build_*.py       建置腳本
work/verify_*.py      結構與內容檢查
oracle_dba_code_examples.pdf   內容來源（707 頁）
Oracle_Storage_Memory_Process_zhTW.pptx   視覺範本（第 1 章原檔）
```

## 重建

需要 Python 3 與 `python-pptx`：

```powershell
# 初階版（10 章）
python work/build_beginner.py

# 進階課程（4 章）
python work/build_advanced.py

# 完整 14 章（輸出到 deliver_full/，不會覆蓋上面兩套）
python work/build_all.py
python work/build_index.py
python work/build_readme.py

# 版面與內容檢查
python work/verify_decks.py deliver_beginner
python work/verify_content.py
```

`work/pdf_pages.json` 與 `work/extract/` 是從 PDF 抽出的中間檔（已列入 .gitignore），
需要時依序執行 `work/extract_pdf.py`、`work/make_extracts.py` 重新產生。

## 資料來源與授權

- 內容依據：**Oracle DBA Code Examples**, Ahmed Baraka, Version Date 2011/07/30, 707 頁。
  該文件 Usage Terms 允許任何人以任何形式複製並提供給個人或組織作**非商業用途**免費使用；
  商業用途需取得作者書面同意。本教材僅作教育訓練用途，並保留原作者署名。
- 教材改寫：中文說明、19c 語法校正、檢核項目與講者備忘為本專案新增；
  程式碼範例的原始出處頁碼記錄於各章 `src` 欄與講者備忘。
- 免責：範例中的路徑、資料庫名稱、磁碟群名稱與容量均為示意，執行前請自行替換並先在測試環境驗證。
  來源文件為 10g/11g 時代，19c 已變更或移除的語法均在該頁警示句標明差異。
