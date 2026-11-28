# -*- coding: utf-8 -*-
"""Chapter 14 — Part 13 Appendixes (source PDF p.674-707)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_UTILITY.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/arpls/DBMS_RANDOM.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/configuring-automatic-restart-of-an-oracle-database.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/admin/scheduling-jobs-with-oracle-scheduler.html",
]

SCOPE = ("附錄章收錄來源文件提供的小工具與作業系統排程做法，適用於 Linux 平台；"
         "Oracle Scheduler 為 19c 建議的排程方式，cron 適合 OS 層工作。")

BODY_SIZE = 20.0    # 標題以下內容的字級

CHAPTER = {
    "no": 14,
    "part": "Part 13",
    "title": "附錄：小工具與作業系統排程",
    "en": "Appendixes — Utilities and Scheduling",
    "subtitle": "參數查詢函式 ／ 測試負載產生器 ／ oratab ／ cron 與 Scheduler",
    "source": "oracle_dba_code_examples.pdf  p.674–707",
    "chap_label": "14",
    "agenda_title": "本章大綱",
    "agenda": [
        ("參數查詢函式", "讓沒有 v$parameter 權限的一般使用者也能取得參數值。"),
        ("測試負載工具", "用 DBMS_RANDOM 與 DBMS_LOCK 產生可控的 CPU、I/O 與交易壓力。"),
        ("開機自動啟動", "oratab 與 dbstart 的搭配，以及 19c 的 systemd 做法。"),
        ("作業系統排程", "cron 與 anacron 的格式、範例與常見陷阱。"),
        ("與 Scheduler 的取捨", "資料庫內的工作用 DBMS_SCHEDULER，OS 層工作才用 cron。"),
    ],
    "agenda_note": "本章可作為課後自習材料；工具腳本適合在測試環境先行驗證。",
    "note_why": "Part 13 是原始文件的附錄，收錄作者自用的小工具；本章挑出三個對教學最有用的部分，並補上 19c 的排程建議。",
    "refs": REFS,
    "refs_note": "附錄腳本為測試用途，正式環境請改用 Oracle 支援的工具（DBMS_STATS、Scheduler、RMAN）。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "讓一般使用者讀取參數：GET_PAR 函式",
            "section": "參數查詢函式",
            "src": "來源 p.675",
            "concept": {
                "items": [
                    ("問題起點", "v$parameter 需要 SELECT 權限，一般使用者查不到。"),
                    ("官方替代", "DBMS_UTILITY.GET_PARAMETER_VALUE 可在不需檢視權限下取值。"),
                    ("回傳型別", "第三個參數回傳整數或字串，靠 partype 判斷是哪一種。"),
                    ("包成函式", "把判斷邏輯封裝，前端只要 SELECT get_par('...') FROM dual。"),
                    ("權限控管", "只授權特定參數或包裝成檢視，避免變成權限繞道。"),
                ],
                "note": "這是典型的「用官方 API 取代直接查檢視」做法，安全且穩定。",
            },
            "code": {
                "title": "以 DBMS_UTILITY 封裝參數查詢",
                "lines": [
                    "CREATE OR REPLACE FUNCTION get_par (p_parameter VARCHAR2) RETURN VARCHAR2 IS",
                    "  intval  BINARY_INTEGER;",
                    "  strval  VARCHAR2(256);",
                    "  partype BINARY_INTEGER;",
                    "BEGIN",
                    "  partype := dbms_utility.get_parameter_value(p_parameter, intval, strval);",
                    "  IF partype = 1 THEN",
                    "    RETURN 'STRING - Value: ' || strval;",
                    "  END IF;",
                    "  RETURN 'INTEGER - Value: ' || TO_CHAR(intval);",
                    "END;",
                    "/",
                ],
                "takeaway": "函式建立後執行 SELECT get_par('db_block_size') FROM dual; 即可驗證。",
                "warning": "授予 EXECUTE 前先確認可查詢的參數範圍，避免洩漏敏感設定。",
            },
            "check": {
                "title": "檢核：函式是否可用且安全",
                "commands": [
                    "SELECT object_name, status FROM user_objects WHERE object_name = 'GET_PAR';",
                    "SELECT line, position, text FROM user_errors WHERE name = 'GET_PAR';",
                    "SELECT get_par('db_block_size') FROM dual;",
                    "SELECT get_par('remote_login_passwordfile') FROM dual;   -- 字串類參數",
                    "SELECT grantee, privilege FROM dba_tab_privs",
                    "WHERE  table_name IN ('GET_PAR','DBMS_UTILITY');",
                ],
                "conds": [
                    ("status", "VALID。INVALID 表示編譯失敗，先查 user_errors"),
                    ("user_errors", "0 列。有列就有錯，position 指出發生位置"),
                    ("執行結果", "回傳 INTEGER 或 STRING 文字，不應出現 ORA- 錯誤"),
                    ("EXECUTE 授權", "GET_PAR 只授指定使用者；DBMS_UTILITY 由 owner 持有"),
                ],
                "pitfalls": [
                    "直接開放 v$parameter SELECT",
                    "忽略 partype，整數被當字串回傳",
                    "函式 INVALID 仍上線，沒看編譯錯誤",
                ],
                "warning": "以一般使用者連線測試，才驗得出權限是否真的足夠。",
            },
            "_note_why": "這頁同時教兩件事：官方 API 的用法，以及「不要用授權解決權限問題」的原則。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "測試負載產生器：可控的壓力來源",
            "section": "測試負載工具",
            "src": "來源 p.676–678",
            "concept": {
                "items": [
                    ("為什麼要自製", "正式壓測工具需要授權與安裝；小工具可在測試庫快速驗證監控。"),
                    ("壓力類型", "純 CPU、CPU＋查詢、隨機查詢、隨機 DML 四種，可分開觀察。"),
                    ("隨機性來源", "DBMS_RANDOM 產生數值與字串，讓資料分布接近真實。"),
                    ("節奏控制", "DBMS_LOCK.SLEEP 加入延遲，模擬使用者思考時間。"),
                    ("使用邊界", "僅限測試環境；正式環境執行會產生大量 redo 與鎖。"),
                ],
                "note": "工具的目的不是把系統打掛，而是讓監控畫面出現可解釋的現象。",
            },
            "code": {
                "title": "以 DBMS_RANDOM 產生隨機 DML",
                "lines": [
                    "-- 前置：目標 schema 需有 DBMS_RANDOM 與 DBMS_LOCK 的 EXECUTE 權限",
                    "CREATE OR REPLACE PACKAGE load_generator IS",
                    "  PROCEDURE insert_names (p_rows IN NUMBER);",
                    "  PROCEDURE spin_cpus   (p_iteration IN NUMBER);",
                    "  PROCEDURE random_query(p_iteration IN NUMBER, p_max IN NUMBER);",
                    "  PROCEDURE random_dml  (p_iteration IN NUMBER, p_max IN NUMBER);",
                    "END load_generator;",
                    "/",
                    "",
                    "-- 產生 60~1800 天內的隨機日期與 1000~55000 的隨機薪資",
                    "INSERT INTO names VALUES (s.NEXTVAL, 'TEST',",
                    "  TRUNC(SYSDATE) - DBMS_RANDOM.VALUE(60,1800),",
                    "  ROUND(DBMS_RANDOM.VALUE(1000,55000)), 'N');",
                ],
                "takeaway": "先用小量參數確認行為，再逐步放大；每次執行都記錄開始時間與參數。",
                "warning": "DBMS_RANDOM.VALUE 的 DATE 運算需自行轉型，19c 建議以 NUMBER 天數相加。",
            },
            "check": {
                "title": "檢核：負載產生器是否可控",
                "commands": [
                    "SELECT object_name, object_type, status FROM user_objects",
                    "WHERE  object_name = 'LOAD_GENERATOR';",
                    "SELECT line, position, text FROM user_errors;",
                    "SELECT COUNT(*) AS test_rows FROM names;",
                    "SELECT name, value FROM v$sysstat WHERE name = 'redo size';  -- 前後各一次",
                    "SELECT COUNT(*) FROM v$session WHERE username = USER;",
                ],
                "conds": [
                    ("status", "PACKAGE 與 BODY 皆 VALID。INVALID 要先修"),
                    ("user_errors", "0 列。有列就是編譯錯，程序叫不動"),
                    ("names 筆數", "≥ 測試計畫量。只增加一點代表部分失敗"),
                    ("redo size", "增量與寫入量相符；v$session 應見該帳號連線"),
                ],
                "pitfalls": [
                    "在正式庫執行，redo 與鎖瞬間暴增",
                    "一次開到最大，看不出趨勢",
                    "測試資料沒清，統計與空間被污染",
                ],
                "warning": "僅限測試環境；先記錄起始 SCN 與時間，方便對照 AWR。",
            },
            "_note_why": "教學重點是「可解釋的壓力」：先知道要觀察什麼，再決定施壓方式。",
            "_note_scope": SCOPE,
            "_refs": [REFS[1]],
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "開機自動啟動：oratab 與 dbstart",
            "section": "開機自動啟動",
            "src": "來源 p.698",
            "concept": {
                "items": [
                    ("oratab 的角色", "記錄 SID 與 ORACLE_HOME，第三欄 Y／N 決定 dbstart 是否啟動它。"),
                    ("dbstart 的行為", "讀 oratab，逐一啟動標記為 Y 的執行個體。"),
                    ("漏登記的後果", "非 DBCA 建立的資料庫與 ASM 不會自動寫入 oratab。"),
                    ("19c 的做法", "以 systemd 服務管理，oratab 仍可搭配 dbstart 手動使用。"),
                    ("驗證方式", "重開機後檢查 alert log 與 v$instance 的 startup time。"),
                ],
                "note": "「重開機後資料庫沒起來」幾乎都是 oratab 或服務設定沒做好。",
            },
            "code": {
                "title": "檢查與維護 oratab 設定",
                "lines": [
                    "# /etc/oratab 格式：SID:ORACLE_HOME:Y|N",
                    "+ASM:/u01/app/oracle/product/19.0.0/grid_home:Y",
                    "orcl:/u01/app/oracle/product/19.0.0/dbhome_1:Y",
                    "",
                    "# 由 oracle 帳號測試啟動",
                    "dbstart",
                    "",
                    "# 19c 以 systemd 管理（建議）",
                    "systemctl status oracle-db.service",
                    "systemctl enable --now oracle-db.service",
                    "",
                    "# 驗證啟動時間",
                    "SELECT instance_name, status, startup_time FROM v$instance;",
                ],
                "takeaway": "改完 oratab 一定要實際重開機驗證，而不是只看檔案內容。",
                "warning": "ASM 必須比資料庫先啟動；若順序錯，資料庫會找不到磁碟群。",
            },
            "check": {
                "title": "檢核：重開機後是否自動就緒",
                "commands": [
                    "cat /etc/oratab | grep -v '^#'",
                    "systemctl status oracle-db --no-pager",
                    "systemctl is-enabled oracle-db",
                    "SELECT instance_name, status, startup_time FROM v$instance;",
                    "ps -ef | grep pmon | grep -v grep",
                ],
                "conds": [
                    ("oratab 第三欄", "每個要自啟的 SID 都是 Y。漏登記或 N 就不啟動"),
                    ("systemd 狀態", "active (running)；inactive 或 failed 即沒啟動"),
                    ("is-enabled", "enabled。disabled 代表下次開機不會啟動"),
                    ("startup_time", "等於本次開機時間。ps 也應見 ora_pmon_<SID>"),
                ],
                "pitfalls": [
                    "只改 oratab 沒重開機，事故才發現",
                    "ASM 與資料庫同時啟動，競爭起不來",
                    "以 root 跑 dbstart，權限錯亂",
                ],
                "warning": "ASM 必須先啟動；改完 oratab 一定要實際重開機驗證。",
            },
            "_note_why": "這是維運最常被要求的情境；用「重開機驗證」當驗收標準，學員才會真的去做。",
            "_note_scope": SCOPE,
            "_refs": [REFS[2]],
        },
        # ---------------------------------------------------------------- 4
        {
            "title": "作業系統排程：cron 與 anacron",
            "section": "作業系統排程",
            "src": "來源 p.699–700",
            "concept": {
                "items": [
                    ("cron 的格式", "分 時 日 月 週，五個欄位加上要執行的指令。"),
                    ("特殊關鍵字", "@daily、@hourly、@reboot 讓常見週期不必寫五個欄位。"),
                    ("輸出處理", "預設寄到本機信箱；可設 MAILTO 或改寫入日誌檔。"),
                    ("anacron 的差異", "假設機器不會 24 小時開機，以「天」為最小週期補跑。"),
                    ("與 Scheduler 分工", "資料庫內工作用 DBMS_SCHEDULER，OS 層備份與清理才用 cron。"),
                ],
                "note": "排程失敗通常不是 cron 的問題，而是環境變數與路徑不同。",
            },
            "code": {
                "title": "crontab 常用範例",
                "lines": [
                    "# 分 時 日 月 週  指令",
                    "# 每週五 01:00 執行備份腳本",
                    "0 1 * * 5   /usr/local/bin/rman_backup.sh",
                    "",
                    "# 週一至週五 22:14 以 oracle 身分執行",
                    "14 22 * * 1-5  su - oracle -c /usr/local/bin/backup.cmd",
                    "",
                    "# 每 10 分鐘執行一次，輸出附加到日誌",
                    "*/10 * * * *   /usr/local/bin/check.sh >> /var/log/check.log 2>&1",
                    "",
                    "# 每天一次（等於 0 0 * * *）",
                    "@daily   /usr/local/bin/daily_report.sh",
                ],
                "takeaway": "在 cron 中一律使用絕對路徑，並在腳本內自行設定 ORACLE_HOME 與 PATH。",
                "warning": "cron 的環境變數與互動式登入不同，這是最常見的「手動可以、排程失敗」原因。",
            },
            "check": {
                "title": "檢核：排程是否可靠",
                "commands": [
                    "crontab -l",
                    "ls -l /etc/cron.daily",
                    "grep -v '^#' /etc/anacrontab",
                    "journalctl -u cron --since today | tail -20   # 或 grep CRON /var/log/syslog",
                    "ls -l /var/log/check.log",
                ],
                "conds": [
                    ("crontab -l", "含預期工作；五欄位時間正確，否則不會觸發"),
                    ("cron.daily", "腳本存在且具執行權（-rwx），無 x 就不執行"),
                    ("anacrontab", "週期與 delay 合理；RANDOM_DELAY 有設避免撞在一起"),
                    ("執行證據", "cron 有觸發紀錄，日誌在排程後有新增行"),
                ],
                "pitfalls": [
                    "手動可跑、cron 找不到 sqlplus",
                    "沒導向輸出，失敗時毫無線索",
                    "以 root 執行 DB 腳本，權限混亂",
                ],
                "warning": "cron 環境與互動登入不同，腳本內先設好 PATH。",
            },
            "_note_why": "排程問題十之八九是環境變數；這頁用「絕對路徑＋自行載入環境」當成固定寫法。",
            "_note_scope": SCOPE,
            "_refs": [REFS[3]],
        },
    ],

    "summary": {
        "items": [
            ("小工具", "GET_PAR 以官方 API 解決權限問題；負載產生器只在測試環境使用。"),
            ("啟動", "oratab 第三欄與 dbstart 搭配，ASM 必須先於資料庫啟動。"),
            ("排程", "cron 用五欄位或 @daily 等關鍵字；環境變數要自行載入。"),
            ("驗證", "任何自動化都要用「重開機」或「實際等待下一次觸發」驗證。"),
            ("取捨", "資料庫內工作交給 DBMS_SCHEDULER，OS 層工作才用 cron。"),
        ],
        "section": "整合複習",
        "note": "附錄的工具都很小，但決定了日常維運是自動化還是靠人記得。",
    },
}
