# Oracle DBA 教育訓練教材（初階版）

完整教材共 14 章 301 頁，拆為兩套：**初階版（本資料夾，10 章）** 與 **進階課程（`deliver_advance/`，4 章 73 頁）**。本版收錄第 1–6、11–14 章並重新編號為 **01–10**；ASM、RAC、RAC One Node、資料倉儲移至進階課程。

**共 10 章、227 頁。** 每章一個獨立 PPTX，內容與進階課程同一套體例。

## 章節總表

| 章 | 章名 | 英文 | PDF 來源 | 主題數 | 頁數 | 檔案 |
|---|---|---|---|---:|---:|---|
| 01 | 儲存、記憶體與程序架構 | Storage, Memory & Process | 架構自編 | — | 30 | `01_Oracle_DBA_儲存記憶體與程序架構.pptx` |
| 02 | 資料庫建置與日常管理 | Oracle DBA Fundamentals | Part 1 p.36–237 | 14 | 46 | `02_Oracle_DBA_建置與日常管理.pptx` |
| 03 | Oracle Net Services 與連線設定 | Oracle Net Services and Connectivity | Part 2 p.238–246 | 4 | 15 | `03_Oracle_DBA_Net_Services.pptx` |
| 04 | 備份與復原 | Oracle Database Backup and Recovery | Part 3 p.247–310 | 8 | 28 | `04_Oracle_DBA_備份與復原.pptx` |
| 05 | 安全性管理 | Oracle Database Security Management | Part 4 p.311–339 | 4 | 16 | `05_Oracle_DBA_安全性管理.pptx` |
| 06 | 效能診斷與調校 | Oracle Database Performance Tuning | Part 5 p.340–395 | 7 | 25 | `06_Oracle_DBA_效能診斷與調校.pptx` |
| 07 | 資料庫公用程式 | Oracle Database Utilities | Part 10 p.556–581 | 5 | 19 | `07_Oracle_DBA_公用程式.pptx` |
| 08 | 作業系統前置與 EM 管理工具 | Miscellaneous Oracle Database Topics | Part 11 p.582–595 | 2 | 10 | `08_Oracle_DBA_作業系統與EM工具.pptx` |
| 09 | PL/SQL 範例 | PL/SQL Samples for Oracle DBAs | Part 12 p.596–673 | 6 | 22 | `09_Oracle_DBA_PLSQL.pptx` |
| 10 | 附錄：小工具與作業系統排程 | Appendixes — Utilities and Scheduling | Part 13 p.674–707 | 4 | 16 | `10_Oracle_DBA_附錄.pptx` |

## 每個主題三頁

| 頁型 | 內容 |
|---|---|
| 概念頁 | 5 個「標籤＋說明」，講為什麼與判斷依據，不含 SQL |
| 程式碼頁 | 以 PDF 原文為依據、改寫成 19c 可執行語法，附重點句與警示句 |
| 檢核頁 | 3–6 行可執行的驗證指令 ＋ 4 條通過條件 ＋ 2–3 個常見錯誤 |

## 兩個版本的關係

| 項目 | 初階版（本資料夾） | 進階課程（`deliver_advance/`） |
|---|---|---|
| 章數 ／ 頁數 | 10 章 ／ 227 頁 | 4 章 ／ 73 頁 |
| 收錄 PDF Part | Part 1–5、10–13（9 個） | Part 6–9（4 個） |
| ASM ／ RAC ／ RAC One Node ／ 倉儲 | 未收錄 | 第 1–4 章 |

## 使用須知

1. 所有指令請先在測試環境驗證；範例中的路徑、資料庫名稱、容量均為示意。
2. 來源文件為 2011 年、10g/11g 時代版本；教材已改寫為 19c 語法，並在警示句標明差異。
3. 內容資料模組位於 `work/content/chNN.py`，重新產生初階版請執行 `work/build_beginner.py`。
