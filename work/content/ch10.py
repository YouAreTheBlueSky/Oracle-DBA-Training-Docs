# -*- coding: utf-8 -*-
"""Chapter 10 — Part 9 Oracle Warehousing (source PDF p.551-555)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dwhsg/",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-tables.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/managing-indexes.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/CREATE-TABLE.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/ALTER-TABLE.html",
]

SCOPE = ("以 Oracle Database 19c 為敘述基準；來源頁 p.551–555 以 OWB 為主，"
         "本章取其倉儲設計與載入概念，指令以 19c SQL 校對。")

CHAPTER = {
    "no": 10,
    "part": "Part 9",
    "title": "資料倉儲",
    "en": "Oracle Data Warehousing",
    "subtitle": "星狀模型 ／ 分區與 bitmap index ／ 大量載入與 ETL",
    "source": "oracle_dba_code_examples.pdf  p.551–555",
    "chap_label": "10",
    "agenda_title": "本章大綱",
    "agenda": [
        ("倉儲 Schema 設計",
         "從維度模型出發：星狀與雪花的取捨、事實表粒度、代理鍵、時間分區與 bitmap index 的適用邊界。"),
        ("大量載入與 ETL",
         "用 NOLOGGING、parallel 與 direct-path insert 縮短載入時間，再以分區交換讓新資料瞬間上線。"),
    ],
    "agenda_note": "倉儲章節把前面學過的 tablespace、分區與索引知識，組成一個可重複執行的載入流程。",
    "note_why": ("來源文件 Part 9 談的是 OWB 這套建模工具，而 OWB 已於 19c 停止支援；"
                 "本章因此改以「建模決策」與「載入技術」兩條主線重寫，"
                 "只保留仍能在 19c 直接執行的 SQL 與資料字典查詢。"),
    "refs": REFS,
    "refs_note": "OWB 自 12c 起不再隨資料庫提供；本章指令皆以 19c 官方文件校對。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "維度模型：星狀、雪花與代理鍵",
            "section": "倉儲 Schema 設計",
            "src": "來源 p.552–553（維度模型與 star schema 實作）",
            "concept": {
                "items": [
                    ("星狀 vs 雪花", "事實表居中、維度單層；雪花把維度再拆表，join 變多。"),
                    ("事實表粒度", "先宣告最細交易層級；粒度定了，度量才可加總。"),
                    ("代理鍵", "維度用無意義整數鍵，來源系統改主鍵時不受影響。"),
                    ("Partition 先做", "事實表依時間 RANGE 分區，載入與查詢都只碰一區。"),
                    ("Bitmap index", "低基數維度欄位用 bitmap；DML 併發會鎖住整個區塊。"),
                ],
                "note": "倉儲的效能八成在建模時就決定了，事後再補索引只是補救。",
            },
            "code": {
                "title": "事實表 DDL：時間分區與 bitmap index",
                "lines": [
                    "-- 事實表：依時間 RANGE 分區，維度以代理鍵關聯",
                    "CREATE TABLE sales_fact (",
                    "  time_id DATE NOT NULL, cust_key NUMBER NOT NULL,",
                    "  prod_key NUMBER NOT NULL, amount NUMBER(12,2))",
                    "PARTITION BY RANGE (time_id) (",
                    "  PARTITION p2024q1 VALUES LESS THAN (DATE '2024-04-01'),",
                    "  PARTITION p2024q2 VALUES LESS THAN (DATE '2024-07-01'));",
                    "-- 低基數維度欄位才建 bitmap index，且指定 LOCAL",
                    "CREATE BITMAP INDEX sales_cust_bix",
                    "  ON sales_fact (cust_key) LOCAL;",
                ],
                "takeaway": "事實表用代理鍵與時間分區；低基數欄位才值得 bitmap index。",
                "warning": "Bitmap index 在並行 DML 下會鎖住整個 bitmap 區塊，載入前常先改為 UNUSABLE。",
            },
            "check": {
                "title": "檢核：維度模型站得住嗎",
                "commands": [
                    "SELECT constraint_type, status FROM dba_constraints WHERE table_name='SALES_FACT';",
                    "SELECT index_type, locality FROM dba_indexes WHERE table_name='SALES_FACT';",
                    "SELECT column_name, data_type, identity_column FROM dba_tab_columns",
                    "WHERE  table_name='CUST_DIM' AND column_name='CUST_KEY';",
                    "SELECT partitioning_type FROM dba_part_tables WHERE table_name='SALES_FACT';",
                ],
                "conds": [
                    ("constraint", "P 與 R 都要有。缺 R＝事實表沒綁維度，會出現孤兒列"),
                    ("bitmap index", "BITMAP 且 LOCAL；GLOBAL 換分區會 UNUSABLE"),
                    ("代理鍵", "NUMBER 型別且 identity_column=YES；沿用來源鍵會斷"),
                    ("partitioning", "RANGE。非 RANGE 無法時間 pruning，每次查都全表掃"),
                ],
                "pitfalls": [
                    "OLTP 表建 bitmap index，會鎖",
                    "事實表不分區，每次載入都全表掃描",
                    "維度沿用來源主鍵，改鍵後事實表整批孤兒",
                ],
                "warning": "分區界線要對上 high_value，否則 pruning 是假的",
            },
            "_note_why": ("星狀與雪花不是對錯問題，而是查詢次數與維護成本的取捨。"
                          "先讓學生講清楚「粒度是什麼」，再談分區與索引，否則後面調校都少了基準。"),
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[2], REFS[3]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "大量載入：NOLOGGING、Parallel 與分區交換",
            "section": "大量載入與 ETL",
            "src": "來源 p.554（mapping 與部署流程）",
            "concept": {
                "items": [
                    ("NOLOGGING 邊界", "只省 redo 不省 undo，且須搭配 direct-path 才生效。"),
                    ("APPEND 的意義", "繞過 buffer cache，直接寫到 HWM 之後的新區塊。"),
                    ("平行 DML 兩步", "ALTER SESSION ENABLE PARALLEL DML 之後才會平行。"),
                    ("分區交換", "EXCHANGE PARTITION 只換資料字典，秒級完成。"),
                    ("載入後統計", "DBMS_STATS 於載入完成後執行，否則計畫會走錯。"),
                ],
                "note": "ETL 的時間要花在「準備區」，正式表只做一次字典切換。",
            },
            "code": {
                "title": "準備區載入與分區交換",
                "lines": [
                    "-- 1) 準備區：NOLOGGING ＋ PARALLEL ＋ APPEND",
                    "ALTER TABLE sales_stg NOLOGGING;",
                    "ALTER TABLE sales_stg PARALLEL 8;",
                    "INSERT /*+ APPEND */ INTO sales_stg",
                    "  SELECT * FROM ext_sales WHERE load_date = DATE '2024-06-30';",
                    "COMMIT;",
                    "-- 2) 先驗筆數與鍵值，再交換；勿跳過",
                    "SELECT COUNT(*) FROM sales_stg;",
                    "-- 3) 分區交換：字典換手，瞬間上線",
                    "ALTER TABLE sales_fact EXCHANGE PARTITION p2024q2",
                    "  WITH TABLE sales_stg INCLUDING INDEXES WITHOUT VALIDATION;",
                ],
                "takeaway": "載入與建索引的成本留在準備區，正式表只換字典。",
                "warning": "WITHOUT VALIDATION 不驗分區界線，日期放錯分區不會報錯，須自行比對。",
            },
            "check": {
                "title": "檢核：載入路徑真的快嗎",
                "commands": [
                    "SELECT table_name, logging, degree FROM dba_tables",
                    "WHERE  table_name IN ('SALES_STG','SALES_FACT');",
                    "SELECT index_name, status FROM dba_indexes WHERE table_name='SALES_FACT';",
                    "SELECT partition_name, num_rows, last_analyzed FROM dba_tab_partitions",
                    "WHERE  table_name='SALES_FACT' ORDER BY partition_position;",
                    "SELECT SUM(bytes)/1048576 mb FROM dba_segments WHERE segment_name='SALES_STG';",
                ],
                "conds": [
                    ("logging", "STG 為 NO、FACT 為 YES；degree=8 才代表平行已開"),
                    ("index status", "全部 VALID。UNUSABLE 就是交換後沒重建索引"),
                    ("筆數 / 統計", "num_rows 等於準備區筆數，last_analyzed 要晚於 COMMIT"),
                    ("segment mb", "載入後應明顯大於載入前；沒成長＝APPEND 沒生效"),
                ],
                "pitfalls": [
                    "對正式表設 NOLOGGING，媒體恢復時救不回",
                    "APPEND 後未 COMMIT 就查，誤判沒資料",
                    "交換前沒比對結構與筆數，指令直接失敗",
                ],
                "warning": "WITHOUT VALIDATION 不驗界線，日期錯放分區不會報錯",
            },
            "_note_why": ("讓學生比較「逐筆 INSERT」與「APPEND ＋ 分區交換」在同一批資料上的差距。"
                          "重點在說明每一個加速手段的代價：可回復性、鎖、以及後續備份。"),
            "_note_scope": SCOPE,
            "_refs": [REFS[1], REFS[3], REFS[4]],
        },
    ],

    "summary": {
        "items": [
            ("模型", "星狀事實表＋單層維度為預設；雪花只在維度共用有實益時採用。"),
            ("設計", "事實表先定粒度再分區；低基數維度欄位才建 bitmap index。"),
            ("載入", "NOLOGGING、APPEND、PARALLEL 三位一體，缺一項就退回慢速路徑。"),
            ("上線", "EXCHANGE PARTITION 把成本留在準備區，正式表只換字典。"),
            ("收尾", "載入後補統計、補備份，否則資料對了但查詢計畫是錯的。"),
        ],
        "section": "整合複習",
        "note": "倉儲的每一個加速手段都對應一個風險；設計階段就把風險寫進 runbook。",
    },
}
