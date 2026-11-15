# Oracle DBA 進階課程

完整 14 章教材中的 **第 7–10 章** —— ASM（Part 6）、RAC（Part 7）、RAC One Node（Part 8）、資料倉儲（Part 9）—— 獨立為本課程，重新編號 **01–04**；其餘 10 章（1–6、11–14）已移至初階版 `deliver_beginner/`。

**共 4 章、73 頁。** 內容與完整版完全相同，只重新編號。

## 章節總表

| 章 | 章名 | 英文 | PDF 來源 | 主題數 | 頁數 | 檔案 |
|---|---|---|---|---:|---:|---|
| 01 | ASM 自動儲存管理 | Oracle Automatic Storage Management | Part 6 p.396–409 | 4 | 16 | `01_Oracle_DBA_ASM.pptx` |
| 02 | RAC 叢集資料庫管理 | Oracle Real Application Clusters (RAC) | Part 7 p.410–528 | 10 | 34 | `02_Oracle_DBA_RAC.pptx` |
| 03 | RAC One Node 建置與線上搬移 | Oracle RAC One Node: Deployment and Online Relocation | Part 8 p.529–550 | 3 | 13 | `03_Oracle_DBA_RAC_One_Node.pptx` |
| 04 | 資料倉儲 | Oracle Data Warehousing | Part 9 p.551–555 | 2 | 10 | `04_Oracle_DBA_資料倉儲.pptx` |

## 與初階版的關係

| 版本 | 資料夾 | 章數 ／ 頁數 | 收錄 PDF Part |
|---|---|---|---|
| 初階版 | `deliver_beginner/` | 10 章 ／ 228 頁 | Part 1–5、10–13 |
| 進階課程（本資料夾） | `deliver_advance/` | 4 章 ／ 73 頁 | Part 6–9 |
| 合計 | — | 14 章 ／ 301 頁 | Part 1–13 |

## 先修與順序

1. 先修：初階版第 01–02 章（instance 生命週期、參數檔、tablespace、datafile）。
2. 建議順序：01 ASM → 02 RAC → 03 RAC One Node → 04 資料倉儲。
3. 環境：19c Grid Infrastructure 與共用儲存；RAC 需兩個節點以上。

## 使用須知

1. 所有指令請先在測試叢集驗證；ASM 磁碟群、voting disk、OCR 的操作具不可逆性。
2. 來源文件為 2011 年、10g/11g 時代版本；教材已改寫為 19c 語法並在警示句標明差異。
3. 內容模組位於 `work/content/ch07–ch10.py`；重新產生請執行 `work/build_advanced.py`。
4. 需要完整 14 章時，可用 `work/build_all.py` ＋ `work/build_index.py` 重建。
