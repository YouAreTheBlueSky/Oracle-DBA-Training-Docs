# -*- coding: utf-8 -*-
"""Chapter 11 — Part 10 Oracle Database Utilities (source PDF p.556-581)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/oracle-data-pump-overview.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/oracle-data-pump-export-utility.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/oracle-sql-loader-control-file-contents.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/scheduling-jobs-with-oracle-scheduler.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/sutil/toc.htm",
]

SCOPE = ("以 Oracle Database 19c 為敘述基準，指令取自來源文件 p.556–581 並以 19c 語法校對。"
         "SQL*Plus 與 LogMiner 的細節另章處理；Scheduler 與 dbv／adrci 為 19c 實務補充。")

CHAPTER = {
    "no": 11,
    "part": "Part 10",
    "title": "資料庫公用程式",
    "en": "Oracle Database Utilities",
    "subtitle": "Data Pump ／ SQL*Loader ／ Oracle Scheduler ／ 診斷工具",
    "source": "oracle_dba_code_examples.pdf  p.556–581",
    "chap_label": "11",
    "agenda_title": "本章大綱",
    "agenda": [
        ("Data Pump 匯出", "以 DIRECTORY 物件與 expdp 匯出 schema、table 或整個資料庫。"),
        ("Data Pump 匯入", "impdp 的物件重對映、TABLE_EXISTS_ACTION 與 SQLFILE。"),
        ("SQL*Loader 與外部表", "以控制檔載入外部檔案；同一份檔案也能用外部表直接查詢。"),
        ("Oracle Scheduler", "job、program、schedule 與 window 組成資料庫內建排程。"),
        ("診斷工具", "dbv 驗證資料檔區塊，adrci 集中檢視 alert log 並蒐集診斷包。"),
    ],
    "agenda_note": "本章把 Part 10 的零散公用程式，收斂成「搬資料、排時間、找原因」三條日常動線。",
    "note_why": "來源文件 Part 10 從 SQL*Plus 一路講到 LogMiner；本章只留 DBA 每天真的會用到的資料搬移、排程與驗證工具，其餘留在附錄。",
    "refs": REFS,
    "refs_note": "來源文件為 10g/11g 時代版本；exp／imp 已在 19c 退場，dump 檔相容性請以官方文件複核。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "Data Pump 匯出：DIRECTORY 與參數",
            "section": "Data Pump 匯出",
            "src": "來源 p.571–572",
            "concept": {
                "items": [
                    ("三個元件", "DBMS_DATAPUMP 是引擎，expdp 與 impdp 只是命令列前端。"),
                    ("DIRECTORY 物件", "資料庫物件指向伺服器目錄，讀寫權限以 GRANT 個別授予。"),
                    ("伺服器端執行", "dump 檔由伺服器寫入，用戶端自己的路徑不會生效。"),
                    ("四種模式", "FULL、SCHEMAS、TABLES、TABLESPACES，另可搬移 tablespace。"),
                    ("可續跑", "job 中斷後可 attach 回同一個 job 續跑，不必從頭再來。"),
                ],
                "note": "匯出的第一步不是打指令，而是確認 DIRECTORY 指向哪裡、誰有權寫入。",
            },
            "table": {
                "header": ["參數", "作用", "實務要點"],
                "rows": [
                    ["DIRECTORY", "指定 dump 檔落地的目錄物件", "需 CREATE ANY DIRECTORY，並授予 READ, WRITE"],
                    ["DUMPFILE", "輸出檔名，%U 產生流水號", "並行時檔案數要等於 PARALLEL"],
                    ["SCHEMAS／TABLES", "匯出範圍：schema 或個別表格", "預設為 schema 模式；FULL 需 EXP_FULL_DATABASE"],
                    ["CONTENT", "ALL、DATA_ONLY、METADATA_ONLY", "只要結構不搬資料時用 METADATA_ONLY"],
                    ["PARALLEL", "同時工作的 worker 數量", "每個 worker 需要對應一個 dumpfile"],
                ],
                "widths": [3.2, 5.5, 6.4],
                "small": True,
                "note": "DIRECTORY 是資料庫物件，不是作業系統路徑；名稱對不上，匯出連檔案都寫不出來。",
                "warning": "舊的 exp／imp 在 19c 已淘汰，dump 檔與 Data Pump 不能互換。",
            },
            "check": {
                "title": "自我檢核：匯出是否真的落地",
                "items": [
                    "dba_directories 查得到目錄，且與伺服器實際路徑一致。",
                    "執行帳號有 CREATE SESSION、CREATE TABLE 與目錄讀寫權。",
                    "dba_datapump_jobs 沒有 NOT RUNNING 或 FAILED 的 job。",
                    "日誌檔結尾為 successfully completed，且沒有 ORA- 錯誤。",
                    "能說明本次用的是 FULL、SCHEMAS、TABLES 哪一種。",
                ],
                "pitfalls": [
                    "只給 READ 沒給 WRITE，匯出立刻失敗。",
                    "用 NOLOGFILE 省事，失敗時查不到原因。",
                    "dump 路徑寫成本機路徑，伺服器端不存在。",
                ],
                "warning": None,
            },
            "_note_why": "先讓學生理解 Data Pump 是伺服器端 API，DIRECTORY 只是它的「出入口」，才不會把本機路徑當成萬用寫法。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[1]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "Data Pump 匯入：重對映與 DDL 匯出",
            "section": "Data Pump 匯入",
            "src": "來源 p.574–576",
            "concept": {
                "items": [
                    ("重對映三兄弟", "REMAP_SCHEMA 換擁有者、REMAP_TABLESPACE 換資料落點。"),
                    ("表格已存在", "TABLE_EXISTS_ACTION 有 SKIP、APPEND、TRUNCATE、REPLACE。"),
                    ("SQLFILE 只產 DDL", "不匯資料，把建置語句寫成文字檔，可先審查再執行。"),
                    ("NETWORK_LINK", "經資料庫連結直接從來源庫匯入，來源可以是唯讀。"),
                    ("權限門檻", "跨 schema 匯入需 IMP_FULL_DATABASE，SQLFILE 同樣需要。"),
                ],
                "note": "匯入前先想清楚：要覆蓋、要疊加，還是只要一份可審查的 DDL。",
            },
            "code": {
                "title": "impdp：重對映、存在處理與 SQLFILE",
                "lines": [
                    "-- 1) 換 schema 與 tablespace，不動 dump 檔",
                    "impdp system/manager DIRECTORY=dpump_dir1 DUMPFILE=hr.dmp \\",
                    "  REMAP_SCHEMA=hr:oe REMAP_TABLESPACE=users:oe_data",
                    "-- 2) 表格已存在時的處理方式",
                    "impdp system/manager DIRECTORY=dpump_dir1 DUMPFILE=hr.dmp \\",
                    "  TABLES=employees TABLE_EXISTS_ACTION=REPLACE",
                    "-- 3) 只取 DDL：由 DBMS_METADATA 產出建置語句",
                    "impdp system/manager DIRECTORY=dpump_dir1 DUMPFILE=hr.dmp \\",
                    "  SQLFILE=hr_ddl.sql",
                    "-- 4) 檢查 job 狀態",
                    "SELECT job_name, state FROM dba_datapump_jobs;",
                ],
                "takeaway": "先跑 SQLFILE 看清楚 DDL，再決定 TABLE_EXISTS_ACTION，避免覆蓋既有資料。",
                "warning": "REPLACE 會先 DROP 再重建，資料與相依物件一併消失；執行前先確認備份。",
            },
            "check": {
                "title": "自我檢核：匯入結果與預期一致",
                "items": [
                    "impdp 日誌結尾為 successfully completed，無 ORA- 錯誤。",
                    "dba_tables 的 owner 與 tablespace 符合 REMAP 設定。",
                    "SQLFILE 產出的文字檔含完整 CREATE TABLE 與索引語句。",
                    "重複匯入時能以 APPEND 疊加，而非整表重建。",
                    "物件數量與來源端相符，可用 dba_objects 交叉比對。",
                ],
                "pitfalls": [
                    "REMAP_SCHEMA 後沒補授權，應用連不上。",
                    "把 REPLACE 當增量工具，既有資料被清空。",
                    "用 NETWORK_LINK 匯入分割區，只支援整表。",
                ],
                "warning": None,
            },
            "_note_why": "匯入的風險遠高於匯出，這頁把「重對映」與「已存在的表格怎麼辦」拆成兩組參數講，並用 SQLFILE 當安全網。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[1]],
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "SQL*Loader 控制檔與外部表",
            "section": "SQL*Loader 與外部表",
            "src": "來源 p.563–566",
            "concept": {
                "items": [
                    ("兩條路線", "sqlldr 用控制檔載入；外部表用 SQL 直接讀檔，可 JOIN 與篩選。"),
                    ("控制檔三要素", "INFILE 資料檔、INTO TABLE 目標表、欄位型別與分隔方式。"),
                    ("四種輸出檔", "log 日誌、bad 拒收列、dsc 不符條件列，全部要留著查。"),
                    ("兩種路徑", "conventional 走 SQL 引擎可觸發 trigger；direct 直接寫區塊最快。"),
                    ("外部表取捨", "同一份檔案可重複查詢，但檔案被改動時結果也跟著變。"),
                ],
                "note": "載入失敗的答案幾乎都在 bad 與 log 檔；先讀這兩份，再回頭修控制檔。",
            },
            "code": {
                "title": "控制檔與 sqlldr 參數",
                "lines": [
                    "-- persons.ctl：Tab 分隔、允許尾端欄位留空",
                    "OPTIONS (ERRORS=0)",
                    "LOAD DATA",
                    "INFILE '/u01/app/oracle/load/persons.dat'",
                    "BADFILE '/u01/app/oracle/load/persons.bad'",
                    "INTO TABLE hr.persons REPLACE",
                    "FIELDS TERMINATED BY X'9' TRAILING NULLCOLS",
                    "( id INTEGER EXTERNAL, pname CHAR, balance INTEGER EXTERNAL,",
                    "  rate FLOAT EXTERNAL, join_date DATE 'DD-MM-YYYY' )",
                    "-- 執行：控制檔加日誌檔",
                    "$ sqlldr hr/pass CONTROL=persons.ctl LOG=persons.log",
                ],
                "takeaway": "控制檔寫清楚 INFILE、INTO TABLE 與欄位型別；其餘交給 log 與 bad 檔說話。",
                "warning": "UNRECOVERABLE 已不建議使用；大量載入改用 NOLOGGING，事後要補備份。",
            },
            "check": {
                "title": "自我檢核：載入是否乾淨",
                "items": [
                    "log 顯示資料列全部載入，且沒有 ORA- 錯誤。",
                    "bad 檔不存在或為空，代表沒有被拒收的資料列。",
                    "dba_tables 的 num_rows 與實際載入筆數相符。",
                    "控制檔的日期格式與資料檔內容一致。",
                    "外部表查詢結果與載入後的表格抽樣比對一致。",
                ],
                "pitfalls": [
                    "分隔字元寫錯，整列被當成單一欄位。",
                    "日期格式不符，資料全進 bad 檔。",
                    "direct 模式不觸發 trigger，稽核欄位漏填。",
                ],
                "warning": "外部表要先建 DIRECTORY 並授權，否則查詢當下才報 ORA-29913。",
            },
            "_note_why": "學生常把 SQL*Loader 當成「按下去就會進資料」；這頁強調控制檔三要素與兩個輸出檔，把除錯變成標準動作。",
            "_note_scope": "Linux 與 Windows 皆適用；外部表需 9i 以上，19c 另支援 ORACLE_DATAPUMP 與 ORACLE_BIGDATA 驅動程式。",
            "_refs": [REFS[2]],
        },
        # ---------------------------------------------------------------- 4
        {
            "title": "Oracle Scheduler：Job 與 Schedule",
            "section": "Oracle Scheduler",
            "src": "19c 實務補充（來源文件未涵蓋）",
            "concept": {
                "items": [
                    ("四個元件", "job 是執行單位，program 定義做什麼，schedule 定義何時做。"),
                    ("window 與資源", "window 讓資源計畫在指定時段生效，夜間批次取得更多資源。"),
                    ("iCalendar 語法", "repeat_interval 寫 FREQ=DAILY;BYHOUR=2，不必再寫 cron。"),
                    ("執行紀錄", "dba_scheduler_job_run_details 保留每次執行的狀態與錯誤。"),
                    ("RAC 下不重複", "同一個 job 只由一個 instance 執行，不需額外協調。"),
                ],
                "note": "把「做什麼」與「什麼時候做」拆開，換時間不必改程式碼。",
            },
            "code": {
                "title": "建立每日排程 job",
                "lines": [
                    "-- 1) 建立每日 02:00 執行的 job 並直接啟用",
                    "BEGIN",
                    "  DBMS_SCHEDULER.CREATE_JOB(",
                    "    job_name => 'HR_STATS_JOB', job_type => 'PLSQL_BLOCK',",
                    "    job_action => 'BEGIN hr.gather_stats; END;',",
                    "    repeat_interval => 'FREQ=DAILY;BYHOUR=2;BYMINUTE=0',",
                    "    enabled => TRUE);",
                    "END;",
                    "/",
                    "-- 2) 檢視狀態與下次執行時間",
                    "SELECT job_name, state, next_run_date FROM dba_scheduler_jobs;",
                ],
                "takeaway": "建完先驗證 next_run_date；要重複使用就拆成 program 加 schedule。",
                "warning": "job 以建立者身分執行；owner 被鎖定或刪除，排程會靜默失敗。",
            },
            "check": {
                "title": "自我檢核：排程真的會跑",
                "items": [
                    "dba_scheduler_jobs 的 state 為 SCHEDULED。",
                    "dba_scheduler_job_run_details 最近一次為 SUCCEEDED。",
                    "repeat_interval 有誤時 state 會是 FAILED。",
                    "需要資源控管時，job 已指定 job_class 或落在對應 window。",
                    "排程時間與備份、統計收集等其他任務錯開。",
                ],
                "pitfalls": [
                    "忘記 enabled，job 建好卻從未執行。",
                    "只寫 FREQ=DAILY，時區與日光節約時跑錯。",
                    "以 SYS 建 job，之後原 schema 無法管理。",
                ],
                "warning": None,
            },
            "_note_why": "排程章節的重點不是記語法，而是讓學生知道 job／program／schedule／window 四者的分工，以及如何驗證它真的跑了。",
            "_note_scope": "19c 內建 Scheduler 與自動維護任務（autotask）並存；job 需 CREATE JOB 權限。",
            "_refs": [REFS[3]],
        },
        # ---------------------------------------------------------------- 5
        {
            "title": "診斷工具：dbv 與 adrci",
            "section": "診斷工具",
            "src": "19c 實務補充（來源文件未涵蓋）",
            "concept": {
                "items": [
                    ("dbv 檢查什麼", "直接讀資料檔區塊，驗證檔頭、格式與 checksum，不必開庫。"),
                    ("適用時機", "還原備份後、懷疑儲存損壞、資料檔開不起來時先跑一次。"),
                    ("adrci 的角色", "集中管理 alert log 與 trace，依產品與時間定位日誌。"),
                    ("常用指令", "show alert -tail 看尾端，ips pack 蒐集診斷包交 Support。"),
                    ("與 RMAN 互補", "dbv 看單檔實體健康，RMAN BACKUP VALIDATE 看全庫。"),
                ],
                "note": "先分清是檔案壞、還是邏輯壞，再決定還原、修復或重建。",
            },
            "code": {
                "title": "dbv 與 adrci 實作",
                "lines": [
                    "-- 1) dbv：不開資料庫，直接驗證資料檔區塊",
                    "$ dbv file=/u01/oradata/prod1/users01.dbf blocksize=8192",
                    "-- 2) adrci：定位 alert log",
                    "$ adrci",
                    "adrci> show homes",
                    "adrci> set homepath diag/rdbms/orcl/ORCL",
                    "adrci> show alert -tail 30",
                    "-- 3) 蒐集診斷包，交 Oracle Support",
                    "adrci> ips pack problem 1 in /tmp",
                    "-- 4) 資料庫端記錄的壞塊",
                    "SELECT file#, block#, corruption_type FROM v$database_block_corruption;",
                ],
                "takeaway": "檔案層用 dbv 驗，日誌層用 adrci 收；兩者都能在資料庫關閉時進行。",
                "warning": "dbv 只驗單一檔案；跨檔案的邏輯一致性仍要靠 RMAN BACKUP VALIDATE。",
            },
            "check": {
                "title": "自我檢核：分得出檔案壞與邏輯壞",
                "items": [
                    "dbv 輸出的 Total Pages Corrupt 為 0，程序正常結束。",
                    "v$database_block_corruption 沒有新增的壞塊紀錄。",
                    "adrci show alert -tail 看得到最近事件與發生時間。",
                    "ips pack 產出的診斷包已可交付 Oracle Support。",
                    "能說明 dbv 與 RMAN BACKUP VALIDATE 的差別。",
                ],
                "pitfalls": [
                    "資料庫開啟中對資料檔跑 dbv，讀到不一致。",
                    "只看 alert log 尾端，漏掉第一個錯誤。",
                    "把 dbv 當邏輯檢查，忽略 RMAN 驗證。",
                ],
                "warning": None,
            },
            "_note_why": "診斷頁的價值在「先確定壞在哪一層」；dbv 便宜且不影響生產，適合當第一步，adrci 則負責把證據收齊。",
            "_note_scope": "dbv 與 adrci 皆為作業系統命令，需以 oracle 帳號執行；Windows 版本參數相同。",
            "_refs": [REFS[4]],
        },
    ],

    "summary": {
        "items": [
            ("匯出起點", "DIRECTORY 物件指向伺服器目錄，權限與路徑都要先確認。"),
            ("匯入策略", "先產 SQLFILE 審查 DDL，再決定 TABLE_EXISTS_ACTION。"),
            ("載入與外部表", "控制檔管載入，外部表管查詢；log 與 bad 檔是唯一線索。"),
            ("排程", "job 綁 program 與 schedule；驗證 next_run_date 才算完成。"),
            ("驗證", "dbv 看檔案、adrci 看日誌，兩者都不需要資料庫開著。"),
        ],
        "section": "整合複習",
        "note": "工具的目的，是把「搬資料、排時間、找原因」變成可重複的標準動作。",
    },
}
