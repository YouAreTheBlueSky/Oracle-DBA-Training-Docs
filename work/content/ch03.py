# -*- coding: utf-8 -*-
"""Chapter 3 — Part 2 Oracle Net Services 與連線設定 (source PDF p.238-246)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/netag/index.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/netrf/index.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/index.html",
]

SCOPE = ("以 Oracle Database 19c 為敘述基準，指令取自來源文件 p.238–246 並以 19c 語法校對。"
         "共用伺服器與 DRCP 的細節、以及各平台服務名稱，仍以官方文件為準。")

CHAPTER = {
    "no": 3,
    "part": "Part 2",
    "title": "Oracle Net Services 與連線設定",
    "en": "Oracle Net Services and Connectivity",
    "subtitle": "Listener ／ 名稱解析 ／ 伺服器模式 ／ 連線診斷",
    "source": "oracle_dba_code_examples.pdf  p.238–246",
    "chap_label": "03",
    "agenda_title": "本章大綱",
    "agenda": [
        ("Listener 管理", "listener.ora 的位址、啟動與狀態、服務註冊與佇列長度，是對外連線的第一道關卡。"),
        ("用戶端名稱解析", "tnsnames、TNS_ADMIN、Easy Connect 與預設連線字串，決定連線字串如何被翻譯。"),
        ("伺服器模式", "專用、共用與 DRCP pooled 三種模式的取捨，以及池參數設定與監控。"),
        ("連線問題診斷", "tnsping、lsnrctl services、v$session 三層定位，把 ORA 錯誤對回設定。"),
    ],
    "agenda_note": "本章是 Part 2 的入口：後續備份、效能與安全章節的連線前提，都在這裡建立。",
    "note_why": "來源文件 Part 2 是一堆零散的連線片段，本章收斂成「設定、解析、模式、診斷」四段動線。",
    "refs": REFS,
    "refs_note": "來源為 10g/11g 時代文件；19c 的參數名與動態效能檢視欄位，請以官方文件複核。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "Listener：對外連線的唯一窗口",
            "section": "Listener 管理",
            "src": "來源 p.244–246",
            "concept": {
                "items": [
                    ("獨立背景程序", "TNSLSNR 與 instance 分開，資料庫關閉時仍可回應連線請求。"),
                    ("位址三要素", "每個 ADDRESS 寫明 protocol、host、port，改完必須 reload。"),
                    ("兩種註冊", "動態由 PMON 依 service_names 登記；靜態寫在 SID_LIST。"),
                    ("QUEUESIZE", "同時排隊的連線請求上限，尖峰湧入時不致直接丟棄。"),
                    ("管理密碼", "set password 後，start、stop 等管理指令需先驗證。"),
                ],
                "note": "Listener 掛掉時連線停在解析之後，資料庫本身可能完全正常。",
            },
            "code": {
                "title": "Listener 組態、啟動與狀態",
                "lines": [
                    "-- listener.ora：位址與佇列長度（p.244–245）",
                    "LISTENER = (DESCRIPTION_LIST = (DESCRIPTION =",
                    "  (ADDRESS=(PROTOCOL=TCP)(HOST=myserver)(PORT=1521)(QUEUESIZE=10))",
                    "  (ADDRESS=(PROTOCOL=IPC)(KEY=EXTPROC1))))",
                    "",
                    "-- 啟動、檢視、重新載入（改設定後用 reload）",
                    "lsnrctl start",
                    "lsnrctl status",
                    "lsnrctl reload",
                    "-- 管理指令需先驗證密碼（p.244）",
                    "LSNRCTL> set password",
                ],
                "takeaway": "改完用 reload 套用；status 的 READY 與服務清單才是可用證據。",
                "warning": "HOST 寫死 IP 時，換主機或改 hosts 後連線全斷；優先用可解析的主機名。",
            },
            "check": {
                "title": "檢核：listener 是否真的可用",
                "commands": [
                    "lsnrctl status     # READY、Listening Endpoints、Services Summary",
                    "lsnrctl services   # 每個 service 的 handler 狀態",
                    "lsnrctl status | grep -i \"parameter file\"   # 載入哪份 listener.ora",
                    "echo $TNS_ADMIN    # 應與上一行同一目錄",
                    "SHOW PARAMETER local_listener",
                ],
                "conds": [
                    ("status", "READY 且列出正確 SERVICE_NAME；沒有＝未註冊"),
                    ("handler", "至少一個 READY；全 BLOCKED＝伺服程序或佇列滿"),
                    ("listener.ora", "路徑在 $TNS_ADMIN 下；不同＝改錯檔"),
                    ("LOCAL LISTENER", "空值＝註冊到預設 1521；非空須與 status 的 endpoint 相同"),
                ],
                "pitfalls": [
                    "只開資料庫沒開 listener，遠端全連不上",
                    "改 listener.ora 後沒 reload",
                    "$TNS_ADMIN 不同，改到的不是載入檔",
                ],
            },
            "_note_why": "先讓學生看懂 listener 是獨立程序，才不會把「連不上」一律當成資料庫故障。",
            "_note_scope": SCOPE,
            "_refs": [REFS[1]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "用戶端解析：tnsnames 與 Easy Connect",
            "section": "用戶端名稱解析",
            "src": "來源 p.239–240、p.244–245",
            "concept": {
                "items": [
                    ("解析順序", "NAMES.DIRECTORY_PATH 由左而右嘗試，先命中的方法決定結果。"),
                    ("Local Naming", "tnsnames.ora 把 net service name 對應到完整位址描述。"),
                    ("TNS_ADMIN", "多個 ORACLE_HOME 可共用同一份 tnsnames.ora 與 sqlnet.ora。"),
                    ("Easy Connect", "host:port/service_name 免設定檔，但不支援連線池等進階功能。"),
                    ("預設連線字串", "Unix 用 TWO_TASK、Windows 用 LOCAL，sqlplus 免連線字串。"),
                ],
                "note": "解析錯與密碼錯的錯誤訊息不同，先分清楚是哪一層出問題。",
            },
            "code": {
                "title": "tnsnames.ora 與三種連線寫法",
                "lines": [
                    "-- tnsnames.ora：net service name 對應位址（p.245）",
                    "MYDB =",
                    " (DESCRIPTION =",
                    "  (ADDRESS=(PROTOCOL=TCP)(HOST=myhost.company.com)(PORT=1521))",
                    "  (CONNECT_DATA=(SERVER=DEDICATED)(SERVICE_NAME=mydb)))",
                    "",
                    "-- sqlnet.ora：解析方法與順序（p.240）",
                    "NAMES.DIRECTORY_PATH = (TNSNAMES, EZCONNECT)",
                    "-- 具名 / Easy Connect / 預設連線字串",
                    "sqlplus system/pass@MYDB",
                    "sqlplus system/pass@myhost.company.com:1521/mydb",
                ],
                "takeaway": "tnsnames 與 sqlnet.ora 放同一目錄，並用 TNS_ADMIN 固定它。",
                "warning": "Easy Connect 不支援連線池與外部程序呼叫；要這些功能就得用 tnsnames。",
            },
            "check": {
                "title": "檢核：解析路徑是否唯一",
                "commands": [
                    "echo $TNS_ADMIN",
                    "ls -l $TNS_ADMIN/tnsnames.ora $TNS_ADMIN/sqlnet.ora   # 兩檔同目錄",
                    "grep -i NAMES.DIRECTORY_PATH $TNS_ADMIN/sqlnet.ora   # 解析順序",
                    "tnsping MYDB",
                    "SELECT name FROM v$active_services;",
                ],
                "conds": [
                    ("TNS_ADMIN", "有值且與實際載入目錄相同；空值＝走預設路徑"),
                    ("DIRECTORY_PATH", "含 TNSNAMES，且左而右順序就是實際想用的順序"),
                    ("tnsping", "OK；Attempting to contact 的位址與 tnsnames 一致"),
                    ("service_name", "Easy Connect 的名稱要在 v$active_services 中"),
                ],
                "pitfalls": [
                    "tnsnames 改了沒重跑 tnsping",
                    "多份 sqlnet.ora，改了沒載入那份",
                    "拿 SID 當 Easy Connect 的服務名",
                ],
            },
            "_note_why": "解析是使用者最常怪錯對象的環節；把「查哪個檔、用哪個方法」講成固定順序。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0]],
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "專用、共用與 Pooled 伺服程序",
            "section": "伺服器模式",
            "src": "來源 p.240–241、p.246",
            "concept": {
                "items": [
                    ("DEDICATED", "一連線一伺服程序，行為單純，但連線數直接吃掉 processes。"),
                    ("SHARED", "dispatcher 接收後分派給少量 shared server，適合短交易。"),
                    ("POOLED（DRCP）", "池化伺服程序，為 PHP、Apache 這類多程序架構設計。"),
                    ("回收參數", "INACTIVITY_TIMEOUT、MAX_USE_SESSION 決定何時回收。"),
                    ("容量參數", "MAXSIZE、MINSIZE、INCRSIZE 控制池的上下限與擴充量。"),
                ],
                "note": "池化省的是伺服程序數量，不是 session；每條連線仍各自佔用記憶體。",
            },
            "code": {
                "title": "啟動 DRCP 並調整池參數",
                "lines": [
                    "-- 啟用 DRCP；資料庫重啟後池需重新啟動（p.240）",
                    "EXEC DBMS_CONNECTION_POOL.START_POOL();",
                    "SELECT connection_pool, status, maxsize FROM dba_cpool_info;",
                    "",
                    "-- 閒置 3600 秒的伺服程序即回收（p.241）",
                    "EXEC DBMS_CONNECTION_POOL.ALTER_PARAM('INACTIVITY_TIMEOUT','3600');",
                    "EXEC DBMS_CONNECTION_POOL.RESTORE_DEFAULTS();",
                    "",
                    "-- 監控：開啟數、忙碌數、命中與未命中（p.241）",
                    "SELECT num_open_servers, num_busy_servers, num_hits, num_misses",
                    "FROM   v$cpool_stats;",
                ],
                "takeaway": "DRCP 重啟後要再 START_POOL；以 dba_cpool_info 的 status 確認。",
                "warning": "原文寫 MAX_SIZE／MIN_SZIE，實際參數名是 MAXSIZE／MINSIZE。",
            },
            "check": {
                "title": "檢核：模式與容量是否匹配",
                "commands": [
                    "SELECT server, COUNT(*) AS n FROM v$session",
                    "WHERE  type = 'USER' GROUP BY server;",
                    "SELECT status, maxsize, minsize FROM dba_cpool_info;",
                    "SELECT num_open_servers, num_busy_servers, num_waits FROM v$cpool_stats;",
                    "SELECT resource_name, current_utilization, limit_value FROM v$resource_limit",
                    "WHERE  resource_name IN ('processes','sessions');",
                ],
                "conds": [
                    ("v$session", "server 為 POOLED／SHARED；全 DEDICATED＝字串沒改"),
                    ("dba_cpool_info", "status＝ACTIVE 且 maxsize>0；INACTIVE＝沒啟池"),
                    ("num_waits", "不持續上升；一直長＝池太小或連線沒釋放"),
                    ("resource_limit", "processes／sessions 未接近 limit_value"),
                ],
                "pitfalls": [
                    "只開池沒改連線字串，應用仍走專用",
                    "MAXSIZE 設得比 processes 還大",
                    "重啟後忘了 START_POOL",
                ],
            },
            "_note_why": "三種模式的差異要用「誰配置伺服程序」來解釋，學生才不會把 DRCP 當成連線池萬靈丹。",
            "_note_scope": "19c 仍支援 shared server；多數新建系統改用 DRCP 或中介層連線池。",
            "_refs": [REFS[0]],
        },
        # ---------------------------------------------------------------- 4
        {
            "title": "連線問題診斷：三層定位",
            "section": "連線問題診斷",
            "src": "來源 p.239–240、p.244",
            "concept": {
                "items": [
                    ("先分層再猜", "解析、網路、listener、註冊、認證，逐層排除比亂改設定快。"),
                    ("tnsping 的邊界", "只驗證解析與 listener 是否回應，不驗證帳密。"),
                    ("lsnrctl services", "服務 READY 才算可用；UNKNOWN 代表 instance 沒註冊。"),
                    ("v$session 視角", "從資料庫端看 machine、program、server，確認連線真的進來。"),
                    ("錯誤碼對照", "ORA-12541 無 listener、ORA-12514 未註冊、ORA-12170 逾時。"),
                ],
                "note": "先確認哪一層出錯，再決定改 tnsnames.ora、listener.ora 或資料庫參數。",
            },
            "code": {
                "title": "三層診斷：解析、註冊、連線",
                "lines": [
                    "-- 1) 解析與 listener 是否回應（不驗證帳密）",
                    "tnsping MYDB",
                    "",
                    "-- 2) 服務註冊狀態：READY 才算可用",
                    "lsnrctl services",
                    "",
                    "-- 3) 資料庫端：實際連線與 server 型態",
                    "SELECT sid, username, machine, server, status",
                    "FROM   v$session WHERE type = 'USER';",
                    "-- 4) processes 或 sessions 接近上限時，新連線失敗",
                    "SELECT resource_name, current_utilization, limit_value FROM v$resource_limit;",
                ],
                "takeaway": "從 tnsping 到 v$session，把「連不上」拆成可分別驗證的四段。",
                "warning": "tnsping 成功不代表能登入；它只證明 listener 有回應，服務名可能仍錯。",
            },
            "check": {
                "title": "檢核：錯誤碼能否定位到層",
                "commands": [
                    "tnsping MYDB 3        # 3 次，看回應時間與解析結果",
                    "lsnrctl services      # service 與 handler 狀態",
                    "SELECT sid, username, machine, server, status",
                    "FROM   v$session WHERE type = 'USER';",
                    "oerr ora 12541        # 12541＝無 listener；12514＝未註冊",
                ],
                "conds": [
                    ("tnsping", "OK 且位址正確；ORA-12541＝listener 沒開或埠錯"),
                    ("services", "service 為 READY；UNKNOWN＝只有靜態註冊"),
                    ("v$session", "看得到測試連線，machine 與 server 符合預期"),
                    ("錯誤碼", "已對到分層：解析／listener／註冊／認證其中之一"),
                ],
                "pitfalls": [
                    "看到 ORA-12541 就重裝 client",
                    "只測本機 sqlplus / as sysdba",
                    "tnsping 通了就宣布問題解決，沒測登入",
                ],
            },
            "_note_why": "診斷頁的價值在順序：先便宜且不影響生產的檢查（tnsping、services），再進資料庫查。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[2]],
        },
    ],

    "summary": {
        "items": [
            ("對外窗口", "Listener 的 ADDRESS、QUEUESIZE 與管理密碼，是連線的第一道關卡。"),
            ("名稱解析", "NAMES.DIRECTORY_PATH 決定順序，tnsnames 與 TNS_ADMIN 要放在同一處。"),
            ("伺服模式", "DEDICATED 單純、SHARED 省程序、DRCP 池化，取決於應用架構。"),
            ("DRCP 維運", "START_POOL 後才生效，重啟要再啟；看 v$cpool_stats 的命中與等待。"),
            ("診斷順序", "tnsping、lsnrctl services、v$session，三層把錯誤碼收斂到單一原因。"),
        ],
        "section": "整合複習",
        "note": "連線問題幾乎都能用「先定位、再修改」解決；改設定前先留下現況輸出。",
    },
}
