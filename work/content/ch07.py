# -*- coding: utf-8 -*-
"""Chapter 7 — Part 6 Oracle Automatic Storage Management (source PDF p.396-409)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ostmg/part-ii-oracle-asm-instances-and-disk-groups/administering-oracle-asm-instances.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ostmg/part-ii-oracle-asm-instances-and-disk-groups/administering-oracle-asm-disk-groups.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ostmg/part-ii-oracle-asm-instances-and-disk-groups/using-views-to-display-oracle-asm-information.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ostmg/part-ii-oracle-asm-instances-and-disk-groups/managing-oracle-asm-with-asmcmd.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ostmg/part-ii-oracle-asm-instances-and-disk-groups/performing-oracle-asm-data-migration-with-rman.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ostmg/part-i-introduction/introducing-oracle-automatic-storage-management.html",
]

SCOPE = ("以 Oracle Database 19c 與 Grid Infrastructure 19c 為敘述基準，指令取自來源文件 p.396–409，"
         "並改寫為 Linux／ASMLIB 環境；Windows 專屬的 ASMTOOL 與 ORADIM 手建流程僅作歷史對照。")

CHAPTER = {
    "no": 7,
    "part": "Part 6",
    "title": "ASM 自動儲存管理",
    "en": "Oracle Automatic Storage Management",
    "subtitle": "ASM Instance ／ 磁碟群 ／ Rebalance ／ ASMCMD ／ 搬移",
    "source": "oracle_dba_code_examples.pdf  p.396–409",
    "chap_label": "07",
    "agenda_title": "本章大綱",
    "agenda": [
        ("ASM 概觀", "ASM instance 的角色、與資料庫 instance 的關係，以及五個 V$ASM_* 檢視的判讀。"),
        ("磁碟群管理", "Redundancy、failure group、AU 與 compatible 屬性，以及磁碟增減與 rebalance。"),
        ("ASMCMD 與權限", "lsdg／lsdsk 巡檢、md_backup 與 md_restore，SYSASM 與 OSASM 的分權設計。"),
        ("搬移到 ASM", "以 RMAN copy 與 switch 把資料庫搬進磁碟群，含 redo 與 tempfile 收尾。"),
    ],
    "agenda_note": "本章是儲存層的最小可用知識：先看懂磁碟群，再談增減、權限與搬移。",
    "note_why": ("來源文件 Part 6 僅 14 頁且多為 10g／11g 語法，本章收斂成 4 個主題，"
                 "每個主題依序為概念、程式碼、檢核，並以 19c 語法重寫指令。"),
    "refs": REFS,
    "refs_note": "來源多為 10g／11g 寫法；ASM_POWER_LIMIT 上限與 ASMCMD 選項請以 19c 文件查核。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "ASM Instance：獨立於資料庫的儲存層",
            "section": "ASM 概觀",
            "src": "來源 p.397–398",
            "concept": {
                "items": [
                    ("獨立 instance", "ASM 有自己的 SGA 與背景程序，只負責掛載磁碟群、供應 extent。"),
                    ("先 ASM 後 DB", "磁碟群沒掛上，資料庫就打不開檔；啟動順序與故障判斷由此開始。"),
                    ("磁碟群清單", "V$ASM_DISKGROUP：ASM 端看全部已掛載群，DB 端只看自己在用的。"),
                    ("用戶端清單", "V$ASM_CLIENT：ASM 端列出連上來的資料庫，DB 端列出所用的 ASM。"),
                    ("磁碟與檔案", "V$ASM_DISK 看掛載狀態與 failure group；V$ASM_FILE 看檔案。"),
                ],
                "note": "同一組 V$ASM_* 檢視在兩端查到的範圍不同，這是最常見的誤判來源。",
            },
            "code": {
                "title": "在 ASM 端與 DB 端查同一組檢視",
                "lines": [
                    "-- 在 ASM instance：所有已掛載的磁碟群",
                    "SELECT name, state, total_mb, free_mb FROM v$asm_diskgroup;",
                    "-- 在 ASM instance：目前連上來的資料庫",
                    "SELECT instance_name, db_name, status FROM v$asm_client;",
                    "-- 磁碟的掛載狀態與所屬 failure group",
                    "SELECT name, mount_status, header_status, failgroup FROM v$asm_disk;",
                    "-- 檔案與樣板",
                    "SELECT file_number, type, bytes/1024/1024 mb FROM v$asm_file;",
                    "SELECT name, redundancy, stripe_type FROM v$asm_template;",
                    "-- 確認現在連的是哪一個 instance",
                    "SELECT instance_name, instance_type FROM v$instance;",
                ],
                "takeaway": "在 ASM 端看全貌，在 DB 端看自己；兩邊都查才不會誤判。",
                "warning": "PDF 的 ASMTOOL 與 ORADIM 手建流程僅適用 10g／XP 測試；19c 由 GI 與 DBCA 建立。",
            },
            "check": {
                "title": "檢核：兩端的視野是否一致",
                "commands": [
                    "SELECT instance_name, instance_type FROM v$instance;",
                    "SELECT name, state, total_mb, free_mb FROM v$asm_diskgroup;",
                    "SELECT instance_name, db_name, status FROM v$asm_client;",
                    "SELECT name, mount_status, failgroup FROM v$asm_disk;",
                ],
                "conds": [
                    ("instance_type", "ASM 且 SID 為 +ASM。RDBMS 表示連到資料庫端"),
                    ("磁碟群 state", "CONNECTED。BROKEN／DISMOUNTED 即磁碟群不可用"),
                    ("v$asm_client", "status＝CONNECTED 且 db_name 與預期相符"),
                    ("v$asm_disk", "mount_status 皆 CACHED；MISSING 表示找不到磁碟"),
                ],
                "pitfalls": [
                    "在 DB 端看到部分磁碟群，就以為是全部",
                    "磁碟群沒掛載，卻先怪資料庫開不起來",
                    "用 SYSDBA 連 +ASM，權限邊界逐漸模糊",
                ],
                "warning": "V$ASM_* 需連 ASM 實例或具 SYSASM，否則視野不全。",
            },
            "_note_why": "學生常把 ASM 當成資料庫的一部分，這頁先把「兩個 instance」講清楚，後面的檢視才有意義。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[2]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "磁碟群建立、屬性與 Rebalance",
            "section": "磁碟群管理",
            "src": "來源 p.398–401",
            "concept": {
                "items": [
                    ("Redundancy 三種", "EXTERNAL 靠陣列、NORMAL 兩份、HIGH 三份，磁碟數要先算夠。"),
                    ("Failure group", "同控制器或同機櫃的磁碟歸同一群，故障才會被視為獨立事件。"),
                    ("AU 大小", "AU 可選 1 至 64MB，影響大檔效率；建立後不可再變更。"),
                    ("Power 是油門", "0 暫停，1 至 1024；越大越快，代價是 I/O 與回應時間。"),
                    ("屬性只能往前", "compatible 一旦調高就回不去，升級前先確認版本。"),
                ],
                "note": "建立磁碟群的參數幾乎都不可回頭，先想清楚再按下 Enter。",
            },
            "code": {
                "title": "建立磁碟群、設定屬性與增減磁碟",
                "lines": [
                    "CREATE DISKGROUP data NORMAL REDUNDANCY",
                    "  FAILGROUP fg1 DISK '/dev/asm/disk01', '/dev/asm/disk02'",
                    "  FAILGROUP fg2 DISK '/dev/asm/disk03', '/dev/asm/disk04'",
                    "  ATTRIBUTE 'au_size'='4M', 'compatible.asm'='19.0';",
                    "-- 屬性可事後調整，但相容性調高後不可降回",
                    "ALTER DISKGROUP data SET ATTRIBUTE 'disk_repair_time'='5H';",
                    "-- 加磁碟會自動 rebalance，可指定強度",
                    "ALTER DISKGROUP data ADD FAILGROUP fg1 DISK '/dev/asm/disk05' NAME data05;",
                    "ALTER DISKGROUP data REBALANCE POWER 8;",
                    "-- 移除磁碟；先確認沒有進行中的 rebalance",
                    "ALTER DISKGROUP data DROP DISK data05;",
                ],
                "takeaway": "磁碟增減會自動觸發 rebalance；重點是控制強度。",
                "warning": "AU 建立後不可變更；要用 4M 以上 AU，必須在建立磁碟群時指定。",
            },
            "check": {
                "title": "檢核：磁碟群能不能撐過一次故障",
                "commands": [
                    "SELECT name, type, total_mb, free_mb FROM v$asm_diskgroup;",
                    "SELECT name, failgroup, total_mb, free_mb FROM v$asm_disk;",
                    "SELECT name, value FROM v$asm_attribute",
                    "WHERE  name IN ('au_size','compatible.asm');",
                    "SELECT operation, power, est_minutes FROM v$asm_operation;",
                ],
                "conds": [
                    ("type / free_mb", "NORMAL／HIGH 才有鏡射；free_mb 低於 10% 要擴充"),
                    ("failure group", "NORMAL 至少 2 組，且分屬不同控制器"),
                    ("au_size", "4194304（4M）以上，單位 byte；1M 對大檔不利"),
                    ("asm_operation", "無資料列＝已完成；有列時 est_minutes 應下降"),
                ],
                "pitfalls": [
                    "同控制器的磁碟放進同一個 failure group",
                    "以為 EXTERN 有鏡射，其實完全靠陣列",
                    "POWER 開到最大，不看 I/O 負載",
                ],
                "warning": "DROP DISK 前確認 rebalance 已結束，否則失敗。",
            },
            "_note_why": "Redundancy 與 failure group 是設計題不是指令題；學生要能算出「壞幾顆不會倒」。",
            "_note_scope": SCOPE,
            "_refs": [REFS[1], REFS[2]],
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "ASMCMD 與 SYSASM：把管理權限收斂",
            "section": "ASMCMD 與權限",
            "src": "來源 p.405–407",
            "concept": {
                "items": [
                    ("asmcmd 看檔案面", "以磁碟群與檔案為單位操作，lsdg、lsdsk、lsct 是巡檢第一站。"),
                    ("md_backup", "只備 ASM 組態：磁碟、failure group、樣板與目錄，不含資料。"),
                    ("md_restore 三模式", "full 重建全部、nodg 只還原中繼資料、newdg 換名重建。"),
                    ("SYSASM 分權", "ASM 管理權與 SYSDBA 分開，責任邊界清楚，稽核也容易。"),
                    ("OSASM 群組", "19c 仍保留 OSASM 群組，成員以 OS 認證連入即為 SYSASM。"),
                ],
                "note": "權限設計的重點不是誰能做，而是出事時查得出誰做過。",
            },
            "code": {
                "title": "asmcmd 巡檢、組態備份與 SYSASM 授權",
                "lines": [
                    "export ORACLE_SID=+ASM",
                    "asmcmd",
                    "ASMCMD> lsdg                     -- 容量與屬性總覽",
                    "ASMCMD> lsdsk -d DATA            -- 只列 DATA 的磁碟",
                    "ASMCMD> lsct                     -- 目前連線的資料庫",
                    "ASMCMD> md_backup -b /tmp/asm.mdb -g DATA",
                    "ASMCMD> md_restore -b /tmp/asm.mdb -t full -g DATA",
                    "-- SYSASM 由 ASM instance 授予，再回查",
                    "GRANT SYSASM TO asmadmin;",
                    "SELECT username, sysasm FROM v$pwfile_users;",
                ],
                "takeaway": "asmcmd 負責巡檢與組態備份，資料本身的備份仍交給 RMAN。",
                "warning": "OSASM 群組在安裝 GI 時建立；事後加人須重新登入，既有連線不會自動取得權限。",
            },
            "check": {
                "title": "檢核：權限與組態備份是否到位",
                "commands": [
                    "asmcmd lsdg",
                    "asmcmd lsdsk -d DATA",
                    "asmcmd lsct",
                    "ls -l /tmp/asm.mdb               # md_backup 產出檔",
                    "SELECT username, sysasm FROM v$pwfile_users;",
                    "getent group osasm",
                ],
                "conds": [
                    ("lsdg／lsdsk", "容量與磁碟數與 v$asm_diskgroup／disk 相同"),
                    ("asmcmd lsct", "每個 DB 為 CONNECTED，無殘留連線"),
                    ("備份檔", "存在且非 0 byte，涵蓋所有需保護磁碟群"),
                    ("SYSASM／OSASM", "只給管理帳號；群組成員與名單相符"),
                ],
                "pitfalls": [
                    "把 SYSASM 授予所有 DBA，責任邊界消失",
                    "OSASM 群組加了人卻沒重新登入",
                    "md_backup 覆蓋舊檔，要還原才發現不能用",
                ],
            },
            "_note_why": "權限這頁要讓學生知道 SYSASM 不是裝飾：它把 ASM 管理從資料庫管理切開，也把責任切開。",
            "_note_scope": SCOPE,
            "_refs": [REFS[3], REFS[0]],
        },
        # ---------------------------------------------------------------- 4
        {
            "title": "搬移到 ASM：RMAN copy 與 switch",
            "section": "搬移到 ASM",
            "src": "來源 p.402–403",
            "concept": {
                "items": [
                    ("先設兩個落點", "兩個 OMF 參數分別指向資料磁碟群與 FRA 磁碟群。"),
                    ("copy 不動原檔", "BACKUP AS COPY 在磁碟群產生副本，原檔還在，隨時可以回退。"),
                    ("switch 才生效", "SWITCH DATABASE TO COPY 改寫控制檔，這一步才算真的搬完。"),
                    ("redo 與 temp 另辦", "RMAN 不搬 redo log 與 tempfile，要 rename 或重建。"),
                    ("tablespace 可小搬", "offline、copy、switch、online 四步，影響單一 tablespace。"),
                ],
                "note": "搬移的風險不在指令，而在原檔還在不在、控制檔有沒有更新。",
            },
            "code": {
                "title": "以 RMAN 把整個資料庫複製進磁碟群",
                "lines": [
                    "ALTER SYSTEM SET db_create_file_dest = '+DATA' SCOPE=SPFILE;  -- 資料落點",
                    "ALTER SYSTEM SET db_recovery_file_dest = '+FRA' SCOPE=SPFILE; -- FRA 落點",
                    "-- 還原控制檔、MOUNT、複製、切換、開庫",
                    "RMAN> RESTORE CONTROLFILE FROM '/u01/oradata/prod/control01.ctl';",
                    "RMAN> ALTER DATABASE MOUNT;",
                    "RMAN> BACKUP AS COPY DATABASE FORMAT '+DATA';",
                    "RMAN> SWITCH DATABASE TO COPY;",
                    "RMAN> ALTER DATABASE OPEN;",
                    "-- 只搬單一 tablespace 時，同一套路徑",
                    "RMAN> BACKUP AS COPY TABLESPACE hr FORMAT '+DATA';",
                    "RMAN> SWITCH TABLESPACE hr TO COPY;",
                ],
                "takeaway": "SWITCH 之後原檔仍在；確認新檔可開庫再刪，否則沒有退路。",
                "warning": "RESTORE 前請先清空 control_files，否則控制檔會還原回舊路徑。",
            },
            "check": {
                "title": "檢核：搬移後資料庫真的在 ASM 上",
                "commands": [
                    "SELECT file#, name FROM v$datafile WHERE name NOT LIKE '+%';",
                    "SELECT name FROM v$controlfile;",
                    "SELECT group#, member FROM v$logfile;",
                    "SELECT file#, name FROM v$tempfile;",
                    "SELECT name, value FROM v$parameter WHERE name LIKE '%file_dest';",
                    "asmcmd lsdg                       # 需 ASM 實例或 SYSASM",
                ],
                "conds": [
                    ("datafile 路徑", "無資料列。有列代表還在檔案系統，沒搬完"),
                    ("控制檔", "≥2 份且都在磁碟群；混路徑即不一致"),
                    ("log／tempfile", "成員為 +DATA 開頭；temp 已重建"),
                    ("file_dest", "db_create_file_dest＝+DATA；free_mb 仍夠成長"),
                ],
                "pitfalls": [
                    "COPY 完就宣布搬完，漏了 SWITCH",
                    "控制檔還原回檔案系統，與資料檔不一致",
                    "搬完立刻刪原檔，才發現有 tablespace 漏搬",
                ],
                "warning": "SWITCH 後原檔仍在；確認新檔可開庫再刪，才有退路。",
            },
            "_note_why": "這頁把「複製」與「切換」分成兩步講，因為多數事故都發生在誤以為 copy 等於搬完。",
            "_note_scope": SCOPE,
            "_refs": [REFS[4]],
        },
    ],

    "summary": {
        "items": [
            ("架構", "ASM 是獨立 instance，只掛載磁碟群並供應 extent。"),
            ("磁碟群", "Redundancy 決定能壞幾顆，AU 決定大檔效率。"),
            ("Rebalance", "加減磁碟自動觸發，POWER 控制速度與 I/O 代價。"),
            ("權限", "SYSASM 管 ASM、SYSDBA 管 DB；OSASM 以 OS 認證。"),
            ("搬移", "copy 不動原檔、switch 才生效；redo 與 temp 另外處理。"),
        ],
        "section": "整合複習",
        "note": "四個主題合起來是一條線：看懂現況、建好磁碟群、管好權限、把資料搬進來。",
    },
}
