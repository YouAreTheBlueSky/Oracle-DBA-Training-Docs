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
                    "ALTER USER app_user QUOTA UNLIMITED ON app_data;",
                    "",
                    "-- 別再用 CONNECT，直接授最小系統權限",
                    "GRANT create session, resource TO app_user;",
                    "",
                    "-- 密碼政策：12c 以後的驗證函式是 ORA12C_VERIFY_FUNCTION",
                    "ALTER PROFILE app_prof LIMIT PASSWORD_LIFE_TIME 180",
                    "  PASSWORD_GRACE_TIME 7 FAILED_LOGIN_ATTEMPTS 5",
                    "  PASSWORD_VERIFY_FUNCTION ora12c_verify_function;",
                    "ALTER USER app_user PASSWORD EXPIRE;",
                ],
                "takeaway": "19c 建帳號只需 CREATE SESSION；密碼政策交給 profile 管。",
                "warning": "10g/11g 用 CONNECT 與 verify_function_11g；19c 改授 CREATE SESSION 與 ora12c_verify_function。",
            },
            "check": {
                "title": "檢核：帳號與密碼是否管住",
                "commands": [
                    "SELECT username, account_status, default_tablespace, profile",
                    "FROM   dba_users WHERE username = 'APP_USER';",
                    "SELECT resource_name, limit FROM dba_profiles WHERE profile='APP_PROF';",
                    "SELECT privilege FROM dba_sys_privs WHERE grantee='APP_USER';",
                    "SELECT tablespace_name, max_bytes FROM dba_ts_quotas WHERE username='APP_USER';",
                    "SELECT username, password_versions FROM dba_users WHERE username='APP_USER';",
                ],
                "conds": [
                    ("account_status", "OPEN，default_tablespace 非 SYSTEM，LOCKED＝停用"),
                    ("profile", "APP_PROF 非 DEFAULT；改了沒 ALTER USER 不生效"),
                    ("授權與配額", "無 UNLIMITED TABLESPACE，max_bytes 非 -1"),
                    ("雜湊版本", "password_versions 含 12C；只有 10G／11G 要重設"),
                ],
                "pitfalls": [
                    "改了 profile 沒 ALTER USER 套用",
                    "用 CONNECT 建帳號，權限來源說不清",
                    "配額 -1 等於無上限",
                ],
                "warning": "19c 預設密碼區分大小寫；該參數已 deprecated",
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
                    "-- v$pwfile_users 只有權限欄位；帳號狀態要 join dba_users",
                    "SELECT p.username, p.sysdba, p.sysoper, p.sysasm,",
                    "       u.account_status, u.authentication_type, u.password_versions,",
                    "       u.last_login, u.lock_date",
                    "FROM   v$pwfile_users p JOIN dba_users u ON u.username = p.username;",
                    "",
                    "-- REMOTE_OS_AUTHENT 已 deprecated，OS 驗證僅限本機",
                    "SHOW PARAMETER os_authent_prefix      -- 預設 ops$",
                    "CREATE USER ops$alice IDENTIFIED EXTERNALLY;",
                    "GRANT CREATE SESSION TO ops$alice;",
                    "",
                    "-- 代理連線：appserv 代表 app_user，需帶密碼",
                    "ALTER USER app_user GRANT CONNECT THROUGH appserv",
                ],
                "takeaway": "特權連線靠 password file；一般使用者用密碼或代理，不用 OS 驗證。",
                "warning": "REMOTE_OS_AUTHENT 已 deprecated；orapwd 不要把密碼寫在指令列。",
            },
            "check": {
                "title": "檢核：四種驗證方式是否用對",
                "commands": [
                    "SELECT username, sysdba, sysoper FROM v$pwfile_users;",
                    "SELECT username, authentication_type FROM dba_users",
                    "WHERE  username IN ('OPS$ALICE','APPSERV');",
                    "SELECT proxy, client FROM proxy_users;",
                    "SHOW PARAMETER os_authent_prefix",
                    "SELECT name, value FROM v$parameter WHERE name = 'remote_os_authent';",
                ],
                "conds": [
                    ("v$pwfile_users", "只列真正需要 SYSDBA 的帳號；多一個就多一把鑰匙"),
                    ("驗證方式", "ops$ 帳號為 EXTERNAL；一般使用者應為 PASSWORD\nNONE:通常保留給特定系統內部角色、叢集或背景管理用途。"),
                    ("proxy_users", "proxy 與 client 成對；查不到代表代理授權未生效"),
                    ("遠端 OS 驗證", "FALSE；19c 已 deprecated，遠端 OS 驗證不可用"),
                ],
                "pitfalls": [
                    "把 OS 驗證開到遠端，等於交出 DBA 權限",
                    "密碼檔權限開放給 dba 群組以外的人",
                    "代理連線少了 AUTHENTICATED USING",
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
                "title": "檢核：授權是否停在最小範圍",
                "commands": [
                    "SELECT granted_role, admin_option FROM dba_role_privs",
                    "WHERE  grantee = 'APP_USER';",
                    "SELECT privilege, admin_option FROM dba_sys_privs WHERE grantee='APP_USER';",
                    "SELECT owner, table_name, privilege FROM dba_tab_privs",
                    "WHERE  grantee = 'PUBLIC';",
                    "SELECT privilege FROM dba_sys_privs WHERE grantee='CONNECT';",
                ],
                "conds": [
                    ("dba_role_privs", "只有職務需要的角色，admin_option 為 NO（DBA 除外）"),
                    ("dba_sys_privs", "沒有 ANY 類權限與 ADMIN OPTION；ANY 就是全庫"),
                    ("PUBLIC 授權", "筆數 0 或極少；對 PUBLIC 授權等於對所有帳號開放"),
                    ("CONNECT 內容", "只有 CREATE SESSION；19c 仍存在但僅相容保留"),
                ],
                "pitfalls": [
                    "直接授權給個人，離職或調職漏回收",
                    "對 PUBLIC 授權，等於對所有帳號開放",
                    "Definer rights 程序成了提權後門",
                ],
                "warning": "DBA 是 CDB 的 common role，授權跨所有 PDB。",
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
                    ("稽核三問", "誰、什麼時候、做了什麼；答案分別落在不同稽核視圖。"),
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
                "title": "檢核：連線與稽核是否真的生效",
                "commands": [
                    "SELECT resource_name, limit FROM dba_profiles WHERE profile='APP_PROF';",
                    "SELECT value FROM v$parameter WHERE name = 'resource_limit';",
                    "SELECT policy_name, success, failure FROM audit_unified_enabled_policies;",
                    "SELECT event_timestamp, dbusername, action_name, object_name",
                    "FROM unified_audit_trail ORDER BY event_timestamp DESC FETCH FIRST 5 ROWS ONLY;",
                    "SELECT sid, serial#, status FROM v$session WHERE username='APP_USER';",
                ],
                "conds": [
                    ("limit", "非 UNLIMITED，且 IDLE_TIME 有具體值"),
                    ("value", "TRUE；FALSE 時 profile 只記錄、不真的中斷"),
                    ("稽核政策", "查得到 policy 即已啟用；success／failure : YES: 要記錄 | NO: 不要紀錄"),
                    ("kill session", "查不到或 status＝KILLED；仍 ACTIVE 就是沒斷"),
                ],
                "pitfalls": [
                    "只建 profile 沒指定使用者，限制不生效",
                    "用 kill -9 砍程序，PMON 得回滾交易",
                    "mixed mode 下漏看傳統稽核紀錄",
                ],
                "warning": "清理用 DBMS_AUDIT_MGMT，勿直接 DELETE",
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


# 使用者手改的講者備忘（(主題索引, 頁型) → 內容；prepend 補在前面、replace 整段取代）
NOTE_OVERRIDES = {
    (0, 'code'): {"mode": 'prepend', "text": "密碼管理的預設腳本 $ORACLE_HOME/rdbms/admin/utlpwdmg.sql\n\nALTER PROFILE DEFAULT LIMIT\n      PASSWORD_LIFE_TIME 180\n      PASSWORD_GRACE_TIME 7\n      PASSWORD_REUSE_TIME UNLIMITED        -- 限制密碼都長時間內不可以重複\n      PASSWORD_REUSE_MAX  UNLIMITED       -- 限制相同密碼最近幾次不可以重複\n      FAILED_LOGIN_ATTEMPTS 10                       --容許連續登入失敗的次數上限為 10 次\n      PASSWORD_LOCK_TIME 1                             --當帳號因連續輸錯密碼而被鎖定後，其自動鎖定時間為 1 天\n      INACTIVE_ACCOUNT_TIME UNLIMITED     --針對長期未登入的閒置帳號，不設定自動鎖定\n      PASSWORD_ROLLOVER_TIME 0                   --新/舊密碼過渡期（Rollover Time）設為 0, 過渡期內密碼可以共用\n      PASSWORD_VERIFY_FUNCTION ora12c_verify_function;"},
    (0, 'check'): {"mode": 'prepend', "text": "常見的 PASSWORD_VERSIONS 代碼含義\n不同版本的 Oracle 資料庫在驗證密碼時，會使用不同的雜湊演算法：\n10G：舊版不區分大小寫的雜湊演算法（基於 DES）。安全性較低，在現代資料庫中已不建議使用，甚至可能受限於 SQLNET.ALLOWED_LOGON_VERSION_SERVER 參數而被拒絕連線。\n11G：Oracle 11g 引入的區分大小寫雜湊演算法（基於 SHA-1 加上隨機 Salt）。\n12C：Oracle 12c 引入的更強大雜湊演算法（基於 PBKDF2 與 SHA-512，迭代次數更高）。在 Oracle 12c 及更新版本（如 19c、26ai）中，這是預設且推薦使用的強密碼雜湊版本。"},
    (2, 'check'): {"mode": 'prepend', "text": "ADMIN_OPTION 欄位用來表示被授予該角色(Role)的使用者或角色，是否擁有將此角色「再轉授」給其他使用者或角色的權限，以及是否擁有修改或撤銷該角色的相關管理能力。"},
    (3, 'code'): {"mode": 'prepend', "text": "CREATE PROFILE app_prof LIMIT\n  -- 系統資源限制\n  SESSIONS_PER_USER          3          -- 每個使用者最多同時建立 3 個連線\n  CONNECT_TIME               480        -- 單次連線最長 480 分鐘（8 小時）\n  IDLE_TIME                  30         -- 閒置超過 30 分鐘自動斷線 \n  -- 密碼安全規則\n  FAILED_LOGIN_ATTEMPTS      5          -- 連續登入失敗 5 次鎖定帳號\n  PASSWORD_LIFE_TIME         90         -- 密碼有效期限為 90 天\n  PASSWORD_LOCK_TIME         1          -- 帳號鎖定 1 天後自動解鎖\n  PASSWORD_GRACE_TIME        7;         -- 密碼過期後的寬限期為 7 天\n/\n\nSelect os_username, userhost, terminal, dbusername, action_name, sql_text, sql_binds from unified_audit_trail\nWhere object_schema='HR' AND object_name='EMPLOYEES'"},
}
