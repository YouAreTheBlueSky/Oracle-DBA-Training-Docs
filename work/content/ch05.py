# -*- coding: utf-8 -*-
"""Chapter 5 — Part 4 Oracle Database Security (source PDF p.311-339)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/introduction-to-oracle-database-security.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/managing-security-for-oracle-database-users.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/configuring-authentication.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/configuring-privilege-and-role-authorization.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/configuring-audit-policies.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/dbseg/introduction-to-auditing.html",
]

SCOPE = ("以 Oracle Database 19c 為敘述基準，指令取自來源文件 p.311–339 並以 19c 語法校對。"
         "CDB 與 common user、TDE 金鑰管理、Database Vault 未在此展開。")

CHAPTER = {
    "no": 5,
    "part": "Part 4",
    "title": "安全性管理",
    "en": "Oracle Database Security Management",
    "subtitle": "使用者與密碼 ／ 驗證 ／ 權限與角色 ／ 連線與稽核",
    "source": "oracle_dba_code_examples.pdf  p.311–339",
    "chap_label": "05",
    "agenda_title": "本章大綱",
    "agenda": [
        ("使用者與密碼管理", "建帳號的最小集合、tablespace 配額、profile 密碼政策與帳號停用。"),
        ("驗證方式", "password file、OS 驗證、外部驗證與代理連線，決定誰能進資料庫。"),
        ("權限與角色", "系統權限與物件權限的分界、角色打包、definer 與 invoker rights。"),
        ("連線與稽核控制", "profile 資源限制、KILL SESSION 收回連線、19c 統一稽核政策。"),
    ],
    "agenda_note": "安全性章節排在備份與效能之後：先能守住資料，再談復原與調校。",
    "note_why": "本章只留四個主題，每個主題都對應一組「10g/11g 寫法 → 19c 寫法」的修正，這是教材最主要的價值。",
    "refs": REFS,
    "refs_note": "來源為 10g/11g 時代；CONNECT 僅為相容保留，SEC_CASE_SENSITIVE_LOGON 已 deprecated。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "使用者與密碼：從建帳號到密碼政策",
            "section": "使用者與密碼管理",
            "src": "來源 p.315–318",
            "concept": {
                "items": [
                    ("預設 Tablespace", "每位使用者指定 default 與 temporary，避免物件落進 SYSTEM。"),
                    ("配額與 UNLIMITED", "QUOTA 比 UNLIMITED TABLESPACE 安全；後者等於不設上限。"),
                    ("密碼生命週期", "PASSWORD_LIFE_TIME 決定更換週期，GRACE_TIME 決定寬限天數。"),
                    ("驗證函式", "PASSWORD_VERIFY_FUNCTION 讓資料庫檢查複雜度，不必靠應用層。"),
                    ("帳號停用", "ACCOUNT LOCK 與 PASSWORD EXPIRE 是最快的停用手段，不必刪使用者。"),
                ],
                "note": "帳號管理的每個決定，都會在 dba_users 與 dba_profiles 留下可查的證據。",
            },
            "code": {
                "title": "建立使用者、指定配額與密碼政策",
                "lines": [
                    "-- 19c：建帳號，先指定 tablespace 與配額",
                    "CREATE USER app_user IDENTIFIED BY \"S3cure#Pwd9\"",
                    "  DEFAULT TABLESPACE app_data QUOTA 500M ON app_data",
                    "  PROFILE app_prof;",
                    "-- 別再用 CONNECT，直接授最小系統權限",
                    "GRANT CREATE SESSION TO app_user;",
                    "-- 密碼政策：19c 的驗證函式是 ORA12C_VERIFY_FUNCTION",
                    "ALTER PROFILE app_prof LIMIT PASSWORD_LIFE_TIME 180",
                    "  PASSWORD_GRACE_TIME 7 FAILED_LOGIN_ATTEMPTS 5",
                    "  PASSWORD_VERIFY_FUNCTION ora12c_verify_function;",
                    "ALTER USER app_user PASSWORD EXPIRE;",
                ],
                "takeaway": "19c 建帳號只需 CREATE SESSION；密碼政策交給 profile 管。",
                "warning": "10g/11g 用 CONNECT 與 verify_function_11G；19c 改授 CREATE SESSION 與 ORA12C。",
            },
            "check": {
                "title": "自我檢核：帳號與密碼是否管住",
                "items": [
                    "account_status 與預期一致，default_tablespace 正確。",
                    "dba_users.profile 指向自訂 profile，而不是 DEFAULT。",
                    "dba_profiles 顯示密碼更換週期與失敗次數上限已設定。",
                    "dba_ts_quotas 有該使用者的配額，且未授予 UNLIMITED TABLESPACE。",
                    "連續輸入錯誤密碼後，帳號狀態確實變成 LOCKED(TIMED)。",
                ],
                "pitfalls": [
                    "只靠 GRANT CONNECT 建帳號，權限來源說不清。",
                    "Profile 改了卻沒套用到使用者，政策形同虛設。",
                    "用 user$.password 取雜湊，19c 該欄已空。",
                ],
                "warning": "SEC_CASE_SENSITIVE_LOGON 已 deprecated；19c 預設密碼區分大小寫。",
            },
            "_note_why": "先讓學員把「建帳號」縮到最小集合，再說明每一個多餘的授權都是日後的風險。CONNECT 只剩 CREATE SESSION 這件事最常被誤解。",
            "_note_scope": SCOPE,
            "_refs": [REFS[1], REFS[3]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "四種驗證方式：密碼檔、OS、外部、代理",
            "section": "驗證方式",
            "src": "來源 p.313、p.317–319",
            "concept": {
                "items": [
                    ("密碼檔驗證", "SYSDBA 等特權連線走 password file；檔案遺失就無法遠端管理。"),
                    ("OS 驗證", "靠作業系統帳號與 dba 群組，只適合本機；遠端已不允許。"),
                    ("外部驗證", "把身分查核交給外部服務，使用者不必在資料庫有密碼。"),
                    ("代理連線", "中介層用自己的帳號登入，再切換成終端使用者身分。"),
                    ("選擇依據", "先問連線從哪裡來、誰管密碼，再選四種方式之一。"),
                ],
                "note": "驗證決定誰能進來；進來之後能看什麼，才輪到權限與角色。",
            },
            "code": {
                "title": "建立密碼檔、OS 驗證與代理連線",
                "lines": [
                    "-- 19c：密碼檔預設 12.2 格式，套用 profile 密碼政策",
                    "orapwd file=$ORACLE_HOME/dbs/orapw$ORACLE_SID",
                    "SELECT * FROM v$pwfile_users;",
                    "-- REMOTE_OS_AUTHENT 已 deprecated，OS 驗證僅限本機",
                    "SHOW PARAMETER os_authent_prefix",
                    "CREATE USER ops$alice IDENTIFIED EXTERNALLY;",
                    "GRANT CREATE SESSION TO ops$alice;",
                    "-- 代理連線：appserv 代表 app_user，需帶密碼",
                    "ALTER USER app_user GRANT CONNECT THROUGH appserv",
                    "  AUTHENTICATED USING PASSWORD;",
                ],
                "takeaway": "特權連線靠 password file；一般使用者用密碼或代理，不用 OS 驗證。",
                "warning": "REMOTE_OS_AUTHENT 已 deprecated；orapwd 不要把密碼寫在指令列。",
            },
            "check": {
                "title": "自我檢核：四種驗證方式是否用對",
                "items": [
                    "v$pwfile_users 中的帳號清單與實際需要 SYSDBA 的人一致。",
                    "密碼檔位於 $ORACLE_HOME/dbs，且僅 oracle 帳號可讀。",
                    "sqlnet.ora 的 SQLNET.AUTHENTICATION_SERVICES 與平台相符。",
                    "代理連線可用 sys_context('USERENV','PROXY_USER') 驗證身分。",
                    "os_authent_prefix 與既有 ops$ 使用者的命名一致。",
                ],
                "pitfalls": [
                    "把 OS 驗證開放到遠端，等於把 DBA 權限交給主機。",
                    "密碼檔權限開放給 dba 群組以外的人員。",
                    "代理連線少了 AUTHENTICATED USING，等於無密碼放行。",
                ],
                "warning": None,
            },
            "_note_why": "四種驗證方式是四種信任來源，講解時要不斷回到「誰在管密碼」這個問題，學生才不會混用。",
            "_note_scope": "Windows 以 NTS 與 OPS$ 網域帳號實作；Linux 以 OS 帳號與 dba 群組實作。",
            "_refs": [REFS[2]],
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "權限與角色：系統權限與物件權限的分界",
            "section": "權限與角色",
            "src": "來源 p.313–314、p.320–324",
            "concept": {
                "items": [
                    ("系統權限", "作用在資料庫層級，如 CREATE SESSION、SELECT ANY TABLE。"),
                    ("物件權限", "作用在特定物件，如 SELECT ON hr.employees，可細到欄位。"),
                    ("角色", "把權限打包給角色，人員異動只改成員，不必逐一改授權。"),
                    ("Definer 與 Invoker", "AUTHID DEFINER 用擁有者權限；CURRENT_USER 用呼叫者權限。"),
                    ("最小權限", "能用角色就不直接授權；能不給 ANY 就不給，尤其避開 ADMIN OPTION。"),
                ],
                "note": "系統權限決定能做什麼事，物件權限決定能碰哪些資料。",
            },
            "code": {
                "title": "角色打包權限、欄位級授權與 Invoker Rights",
                "lines": [
                    "-- 改由自訂角色打包，別再依賴 CONNECT／RESOURCE",
                    "CREATE ROLE app_read;",
                    "GRANT CREATE SESSION, CREATE TABLE TO app_read;",
                    "GRANT SELECT, UPDATE ON hr.employees TO app_read;",
                    "GRANT app_read TO app_user;",
                    "-- 欄位級授權存在時，回收仍只能整個物件",
                    "GRANT UPDATE (salary) ON hr.employees TO app_user;",
                    "REVOKE UPDATE ON hr.employees FROM app_read;",
                    "-- Invoker rights：以呼叫者權限執行",
                    "CREATE OR REPLACE PROCEDURE del_emp AUTHID CURRENT_USER AS",
                    "BEGIN DELETE FROM hr.employees WHERE employee_id = 100; END;",
                ],
                "takeaway": "角色打包系統權限，物件權限給到最小；共用程式才用 invoker rights。",
                "warning": "10g/11g 用 GRANT CONNECT／RESOURCE；19c 僅相容保留，請改自訂角色。",
            },
            "check": {
                "title": "自我檢核：授權是否停在最小範圍",
                "items": [
                    "dba_role_privs 中，使用者只擁有職務真正需要的角色。",
                    "dba_sys_privs 查不到帶 ADMIN OPTION 的授權，DBA 角色除外。",
                    "dba_tab_privs 中 GRANTEE 為 PUBLIC 的筆數為零或極少。",
                    "以 AUTHID CURRENT_USER 編譯的程式，呼叫者權限確實不足時會失敗。",
                    "SESSION_PRIVS 與 SESSION_ROLES 的內容與預期一致。",
                ],
                "pitfalls": [
                    "直接授權給個人，離職或調職時漏了回收。",
                    "對 PUBLIC 授權，等於對所有帳號開放。",
                    "Definer rights 程序被當成提權後門，繞過物件權限。",
                ],
                "warning": "19c 的 DBA 角色仍然存在但權限極大；在 CDB 中它更是 common role。",
            },
            "_note_why": "學生最常把「有角色」當成「有權限」。這頁用三個檢核視圖把授權來源拆開來看，順便把 CONNECT 只剩 CREATE SESSION 講清楚。",
            "_note_scope": SCOPE,
            "_refs": [REFS[3]],
        },
        # ---------------------------------------------------------------- 4
        {
            "title": "連線與稽核：Profile、Kill Session 與稽核政策",
            "section": "連線與稽核控制",
            "src": "來源 p.315–316、p.318–319、p.325–326",
            "concept": {
                "items": [
                    ("Resource Limit", "CONNECT_TIME、IDLE_TIME、SESSIONS_PER_USER 以 profile 套用。"),
                    ("要生效的開關", "RESOURCE_LIMIT 為 TRUE 才會強制執行，否則只是記錄。"),
                    ("連線清理", "KILL SESSION 由資料庫收回資源；OS 砍程序會留下孤兒交易。"),
                    ("稽核三問", "誰、做了什麼、什麼時候；答案分別落在不同稽核視圖。"),
                    ("統一稽核", "19c 預設啟用統一稽核；政策與結果都查 unified trail。"),
                ],
                "note": "連線控制管用多少，稽核管做過什麼，兩者都靠事後查詢驗證。",
            },
            "code": {
                "title": "Profile 資源限制、統一稽核與 KILL SESSION",
                "lines": [
                    "-- 19c：profile 資源限制，resource_limit 預設已啟用",
                    "ALTER PROFILE app_prof LIMIT SESSIONS_PER_USER 5",
                    "  IDLE_TIME 30 CONNECT_TIME 480;",
                    "ALTER USER app_user PROFILE app_prof;",
                    "-- 19c 建議改用統一稽核，不再依賴 AUDIT_TRAIL",
                    "CREATE AUDIT POLICY pol_hr ACTIONS LOGON, SELECT ON hr.employees;",
                    "AUDIT POLICY pol_hr;",
                    "SELECT event_timestamp, dbusername, action_name, object_name",
                    "FROM   unified_audit_trail ORDER BY event_timestamp DESC;",
                    "-- 收回逾時連線，不必到 OS 砍程序",
                    "ALTER SYSTEM KILL SESSION '145,28761' IMMEDIATE;",
                ],
                "takeaway": "Profile 限用量、稽核政策留證據、KILL SESSION 收連線，都在 DB 內完成。",
                "warning": "10g/11g 靠 AUDIT_TRAIL 與 AUDIT；19c 預設 mixed mode，請改用稽核政策。",
            },
            "check": {
                "title": "自我檢核：連線與稽核是否真的生效",
                "items": [
                    "dba_profiles 的 limit_value 不是 UNLIMITED，且已套用到使用者。",
                    "RESOURCE_LIMIT 為 TRUE，逾時連線確實被中斷。",
                    "audit_unified_enabled_policies 顯示政策狀態為 ENABLED。",
                    "unified_audit_trail 查得到剛才的 LOGON 或 SELECT 紀錄。",
                    "KILL SESSION 後 v$session 已無該 sid，且無殘留交易。",
                ],
                "pitfalls": [
                    "只建 profile 沒指定給使用者，限制不會生效。",
                    "用 kill -9 砍程序，PMON 需回滾大量交易。",
                    "只看 unified trail，忽略 mixed mode 仍有傳統紀錄。",
                ],
                "warning": "統一稽核紀錄在 AUDSYS.AUD$UNIFIED；清理用 DBMS_AUDIT_MGMT，勿直接 DELETE。",
            },
            "_note_why": "連線控制與稽核常被當成兩件事，其實都是「事後查得到」的證據鏈。從傳統稽核轉到稽核政策，是 19c 最大的寫法改變。",
            "_note_scope": SCOPE,
            "_refs": [REFS[4], REFS[5]],
        },
    ],

    "summary": {
        "items": [
            ("帳號", "建帳號只需 CREATE SESSION；配額與密碼政策另外設定。"),
            ("驗證", "password file 管特權連線，proxy 管中介層，OS 驗證僅限本機。"),
            ("權限", "角色打包系統權限，物件權限給到最小；共用程式才用 invoker rights。"),
            ("連線", "Profile 限制用量，KILL SESSION 收回資源，不要在 OS 層砍程序。"),
            ("稽核", "19c 用稽核政策：CREATE AUDIT POLICY 與 UNIFIED_AUDIT_TRAIL。"),
        ],
        "section": "整合複習",
        "note": "每一個安全性設定，都要能在資料字典或稽核視圖裡被查出來，才算真的生效。",
    },
}
