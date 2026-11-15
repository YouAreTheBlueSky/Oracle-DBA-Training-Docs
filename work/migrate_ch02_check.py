# -*- coding: utf-8 -*-
"""Chapter 2: rewrite every check page into the verification format
(commands + pass conditions), as the reference implementation for other chapters."""
import re

SPECS = [
    dict(  # 1 最佳實務
        title="檢核：基準線是否成立",
        cmds=[
            "SELECT name, value FROM v$parameter WHERE name = 'spfile';",
            "SELECT tablespace_name, extent_management, segment_space_management",
            "FROM   dba_tablespaces WHERE tablespace_name IN ('SYSTEM','SYSAUX','USERS');",
            "SELECT log_mode FROM v$database;",
            "SELECT COUNT(*) AS ctl_files FROM v$controlfile;",
        ],
        conds=[
            ("spfile", "有路徑（非空）。空值＝仍用 PFILE，重開機參數會漂移"),
            ("extent / segment", "皆為 LOCAL／AUTO。出現 MANUAL 即有 freelist 競爭"),
            ("log_mode", "ARCHIVELOG。NOARCHIVELOG 不能做時間點復原"),
            ("控制檔份數", "≥2。只有 1 份就是單點故障"),
        ],
        pits=[
            "只看 log_mode 就結案，沒確認歸檔目的地還有空間",
            "控制檔兩份放同一顆磁碟，壞一顆兩份一起走",
        ],
        warn="把這四項寫成開庫檢查表，納入每次新建資料庫的交付文件。",
    ),
    dict(  # 2 OFA
        title="檢核：目錄結構是否符合 OFA",
        cmds=[
            "echo $ORACLE_BASE $ORACLE_HOME",
            "df -h /u01 /u02 /u04        # 看 mount point 數與剩餘空間",
            "ls -l $ORACLE_BASE/flash_recovery_area",
            "SELECT name FROM v$datafile FETCH FIRST 3 ROWS ONLY;",
            "SELECT name FROM v$controlfile;",
        ],
        conds=[
            ("ORACLE_BASE", "固定前綴（/u01/app/oracle），不與作業系統根目錄共用"),
            ("mount point", "至少 4 個，oradata 不在根目錄"),
            ("FRA 位置", "與資料檔不同磁碟，或不同 ASM 磁碟群"),
            ("控制檔路徑", "分散在不同 mount point，不集中同一顆"),
        ],
        pits=[
            "全部放 /u01，容量與 I/O 都變單點",
            "ORACLE_HOME 不含版本，升級後舊版無法並存",
        ],
        warn=None,
    ),
    dict(  # 3 安裝交付
        title="檢核：安裝交付清單",
        cmds=[
            "lsnrctl status             # 服務是否註冊、狀態是否 READY",
            "SELECT instance_name, status, startup_time FROM v$instance;",
            "SELECT value FROM nls_database_parameters",
            "WHERE  parameter = 'NLS_CHARACTERSET';",
            "SELECT name, value FROM v$parameter",
            "WHERE  name IN ('db_name','db_domain');",
        ],
        conds=[
            ("listener", "READY，Services 列出正確 SERVICE_NAME"),
            ("instance", "status＝OPEN，startup_time 為本次開機時間"),
            ("字元集", "NLS_CHARACTERSET 與應用需求一致"),
            ("db_name / domain", "與 tnsnames 及應用連線字串一致"),
        ],
        pits=[
            "只測本機 sqlplus，沒測遠端 listener",
            "建庫用預設字元集，上線才發現存不了特定字元",
        ],
        warn=None,
    ),
    dict(  # 4 Instance 資訊
        title="檢核：能不能說出這台資料庫的現況",
        cmds=[
            "SELECT * FROM v$version;",
            "SELECT component, ROUND(current_size/1024/1024) mb",
            "FROM   v$memory_dynamic_components WHERE current_size > 0;",
            "SELECT COUNT(*) bg_procs FROM v$bgprocess WHERE paddr <> '00';",
            "SELECT name, value FROM v$parameter WHERE name = 'sga_target';",
        ],
        conds=[
            ("版本", "與預期版本相符，含 patchset 末四碼"),
            ("SGA 各區", "DEFAULT buffer cache 與 shared pool 皆大於 0"),
            ("背景程序數", "與作業系統 ps 的 ora_ 程序數相符"),
            ("sga_target", "與實際配置相符；為 0 表示改用個別參數"),
        ],
        pits=[
            "把 sga_target 當實際用量，忽略元件未用滿",
            "在生產環境隨手 flush buffer cache 或 shared pool",
        ],
        warn=None,
    ),
    dict(  # 5 啟動關閉
        title="檢核：資料庫現在處於哪個階段",
        cmds=[
            "SELECT instance_name, status, shutdown_pending FROM v$instance;",
            "SELECT name, open_mode, database_status FROM v$database;",
            "SELECT name, open_mode, restricted FROM v$containers;   -- CDB 才需要",
            "SELECT COUNT(*) active_sessions FROM v$session WHERE status = 'ACTIVE';",
        ],
        conds=[
            ("instance status", "OPEN／MOUNTED／STARTED 對應當時階段"),
            ("open_mode", "READ WRITE 才接受一般 DML"),
            ("shutdown_pending", "平時 NO；關庫過程才變 YES"),
            ("restricted", "NO。YES 表示 RESTRICTED SESSION 沒關"),
        ],
        pits=[
            "以 SHUTDOWN ABORT 當日常關庫手段",
            "QUIESCE 後忘記 UNQUIESCE，應用連線全被擋",
        ],
        warn=None,
    ),
    dict(  # 6 參數檔
        title="檢核：參數是否真的生效",
        cmds=[
            "SELECT name, value FROM v$parameter WHERE name = 'spfile';",
            "SHOW PARAMETER undo_retention",
            "SELECT name, isspecified FROM v$spparameter",
            "WHERE  isspecified = 'TRUE' ORDER BY name FETCH FIRST 10 ROWS ONLY;",
            "SELECT name, value, issys_modifiable FROM v$parameter",
            "WHERE  name = 'undo_retention';",
        ],
        conds=[
            ("spfile", "非空。空值表示仍在用 PFILE"),
            ("issys_modifiable", "IMMEDIATE 可即改；FALSE 必須重啟"),
            ("v$spparameter", "isspecified＝TRUE 才是寫進 SPFILE 的項目"),
            ("SHOW 現值", "等於預期值，代表 MEMORY 已生效"),
        ],
        pits=[
            "只改 MEMORY，重開機後設定消失",
            "直接編輯 spfile，導致 instance 開不起來",
        ],
        warn=None,
    ),
    dict(  # 7 Control File
        title="檢核：控制檔是否可靠",
        cmds=[
            "SELECT name, status FROM v$controlfile ORDER BY name;",
            "SELECT value FROM v$parameter WHERE name = 'control_files';",
            "SELECT type, records_used, records_total FROM v$controlfile_record_section",
            "WHERE  type IN ('DATAFILE','REDO LOG','ARCHIVED LOG');",
            "SELECT name, block_size, file_size_blks FROM v$controlfile;",
        ],
        conds=[
            ("份數", "≥2，且路徑分散在不同磁碟"),
            ("control_files 參數", "與 v$controlfile 實際清單一致"),
            ("record section", "records_used 接近 records_total 就該加大保留期"),
            ("備份狀態", "近期有 BACKUP CONTROLFILE 的副本或 trace"),
        ],
        pits=[
            "兩份控制檔同目錄，磁碟故障一起失效",
            "重建控制檔時漏列 tempfile 或 redo 成員",
        ],
        warn=None,
    ),
    dict(  # 8 Redo
        title="檢核：redo 設定是否穩健",
        cmds=[
            "SELECT group#, thread#, members, bytes/1024/1024 mb, status, archived",
            "FROM   v$log ORDER BY group#;",
            "SELECT group#, member, status FROM v$logfile ORDER BY group#, member;",
            "SELECT thread#, sequence#, first_time FROM v$log_history",
            "ORDER BY first_time DESC FETCH FIRST 5 ROWS ONLY;",
        ],
        conds=[
            ("group 數", "≥3；少於 3 容易在切換時等待"),
            ("members", "每 group ≥2，且位於不同磁碟"),
            ("status", "同時只有 1 個 CURRENT，其餘 ACTIVE／INACTIVE"),
            ("log switch 間隔", "尖峰至少 15–20 分鐘一次，過密代表日誌太小"),
        ],
        pits=[
            "為省空間只留單一成員，一次壞軌就丟失 redo",
            "group 為 CURRENT 或 ACTIVE 時嘗試刪除",
        ],
        warn=None,
    ),
    dict(  # 9 歸檔
        title="檢核：歸檔鏈是否閉環",
        cmds=[
            "ARCHIVE LOG LIST",
            "SELECT dest_id, status, destination, error FROM v$archive_dest",
            "WHERE  status <> 'INACTIVE';",
            "SELECT COUNT(*) archived_24h FROM v$archived_log",
            "WHERE  deleted = 'NO' AND completion_time > SYSDATE - 1;",
            "SELECT * FROM v$recovery_area_usage;        -- FRA 使用率",
        ],
        conds=[
            ("log_mode", "ARCHIVELOG"),
            ("dest 狀態", "VALID 且 error 為空；有錯代表寫入失敗"),
            ("近 24 小時歸檔數", "大於 0，且與 log switch 次數相符"),
            ("FRA 使用率", "未達 db_recovery_file_dest_size 上限"),
        ],
        pits=[
            "開歸檔但 FRA 滿了，歸檔停擺導致資料庫掛起",
            "所有目的地都設 OPTIONAL，失敗卻無人察覺",
        ],
        warn=None,
    ),
    dict(  # 10 Tablespace 建立
        title="檢核：tablespace 設計是否合理",
        cmds=[
            "SELECT tablespace_name, extent_management, allocation_type,",
            "       segment_space_management, bigfile FROM dba_tablespaces;",
            "SELECT tablespace_name, file_name, bytes/1024/1024 mb, autoextensible",
            "FROM   dba_data_files ORDER BY tablespace_name;",
            "SELECT property_value FROM database_properties",
            "WHERE  property_name = 'DEFAULT_PERMANENT_TABLESPACE';",
        ],
        conds=[
            ("extent / segment", "LOCAL 與 AUTO；MANUAL 會有 freelist 競爭"),
            ("allocation_type", "AUTOALLOCATE 或 UNIFORM，與設計一致"),
            ("bigfile", "NO／YES 與用途相符，bigfile 不可再切分"),
            ("預設 tablespace", "不是 SYSTEM，且該 tablespace 存在"),
        ],
        pits=[
            "把應用資料放進 SYSTEM 或 SYSAUX",
            "bigfile 與 smallfile 混用又沒紀錄，日後誤判",
        ],
        warn=None,
    ),
    dict(  # 11 Tablespace 維運
        title="檢核：維運動作是否可逆",
        cmds=[
            "SELECT tablespace_name, status, contents FROM dba_tablespaces;",
            "SELECT file_name, status, online_status FROM dba_data_files;",
            "SELECT tablespace_name, ROUND(SUM(bytes)/1024/1024) free_mb",
            "FROM   dba_free_space GROUP BY tablespace_name ORDER BY 2;",
            "SELECT property_value FROM database_properties",
            "WHERE  property_name = 'DEFAULT_PERMANENT_TABLESPACE';",
        ],
        conds=[
            ("status", "ONLINE；READ ONLY 需確認是刻意設定"),
            ("online_status", "全部 ONLINE，沒有 OFFLINE 殘留"),
            ("free_mb", "足夠撐到下一次擴充，避免臨時加檔"),
            ("預設 tablespace", "更名或刪除後仍指向存在的 tablespace"),
        ],
        pits=[
            "用 OFFLINE IMMEDIATE 停 tablespace，之後忘記要恢復",
            "DROP TABLESPACE 忘記 INCLUDING CONTENTS，指令失敗",
        ],
        warn=None,
    ),
    dict(  # 12 Datafile
        title="檢核：檔案層級是否一致",
        cmds=[
            "SELECT file_name, bytes/1024/1024 mb, autoextensible,",
            "       maxbytes/1024/1024 max_mb, increment_by",
            "FROM   dba_data_files ORDER BY tablespace_name, file_id;",
            "SELECT file#, status, error, recover FROM v$datafile_header;",
            "SELECT file#, online_status FROM v$datafile",
            "WHERE  online_status <> 'ONLINE';",
        ],
        conds=[
            ("autoextensible", "ON 時 MAX_MB 必須有值，否則會長滿磁碟"),
            ("v$datafile_header", "error 為空、recover 為 NO"),
            ("online_status", "全部 ONLINE；OFFLINE 需確認原因"),
            ("路徑一致性", "dba_data_files 與作業系統實際路徑相同"),
        ],
        pits=[
            "只用作業系統 mv 改檔名，沒執行 RENAME FILE",
            "autoextend 不設 maxsize，資料檔把磁碟吃滿",
        ],
        warn=None,
    ),
    dict(  # 13 Undo
        title="檢核：undo 是否撐得住長查詢",
        cmds=[
            "SHOW PARAMETER undo",
            "SELECT tablespace_name, status, ROUND(SUM(bytes)/1024/1024) mb",
            "FROM   dba_undo_extents GROUP BY tablespace_name, status;",
            "SELECT MAX(maxquerylen) max_qry, MAX(tuned_undoretention) tuned",
            "FROM   v$undostat;",
            "SELECT begin_time, undoblks, txncount FROM v$undostat",
        ],
        conds=[
            ("undo_management", "AUTO"),
            ("EXPIRED 佔比", "不宜過高；ACTIVE 過大代表有長交易未提交"),
            ("maxquerylen", "≤ undo_retention（秒），否則會遇 ORA-01555"),
            ("tuned_undoretention", "與 undo_retention 相符或略高"),
        ],
        pits=[
            "undo 固定大小又開 guarantee，DML 隨機失敗",
            "把 ORA-01555 當資料損毀，急著做恢復",
        ],
        warn=None,
    ),
    dict(  # 14 空間回收
        title="檢核：回收是否真的有效",
        cmds=[
            "SELECT segment_name, segment_type, bytes/1024/1024 mb, blocks",
            "FROM   dba_segments WHERE owner = 'HR' ORDER BY bytes DESC",
            "FETCH FIRST 10 ROWS ONLY;",
            "SELECT tablespace_name, segment_name, recommendations",
            "FROM   TABLE(dbms_space.asa_recommendations('TRUE','TRUE','TRUE'));",
            "SELECT table_name, blocks, empty_blocks FROM dba_tables WHERE owner = 'HR';",
        ],
        conds=[
            ("dba_segments.blocks", "shrink 後應下降，否則空間沒真的還回去"),
            ("asa_recommendations", "有建議才值得 shrink；沒有就先別動"),
            ("empty_blocks", "偏高表示 HWM 之下有空洞，可考慮 shrink"),
            ("DEALLOCATE 後", "只釋放尾端空間，blocks 下降幅度有限"),
        ],
        pits=[
            "對資料仍多的表直接 shrink，效果有限還鎖表",
            "忘記 ENABLE ROW MOVEMENT，SHRINK 直接報錯",
        ],
        warn=None,
    ),
]


def emit(sp):
    ind = " " * 16
    out = ['            "check": {',
           f'{ind}"title": "{sp["title"]}",',
           f'{ind}"commands": [']
    for c in sp["cmds"]:
        out.append(f'{ind}    "{c}",')
    out.append(f'{ind}],')
    out.append(f'{ind}"conds": [')
    for look, expect in sp["conds"]:
        out.append(f'{ind}    ("{look}", "{expect}"),')
    out.append(f'{ind}],')
    out.append(f'{ind}"pitfalls": [')
    for p in sp["pits"]:
        out.append(f'{ind}    "{p}",')
    out.append(f'{ind}],')
    if sp.get("warn"):
        out.append(f'{ind}"warning": "{sp["warn"]}",')
    out.append("            },")
    return "\n".join(out)


def main():
    p = "work/content/ch02.py"
    s = open(p, encoding="utf-8").read()
    pat = re.compile(r'\n            "check": \{.*?\n            \},', re.S)
    blocks = pat.findall(s)
    assert len(blocks) == len(SPECS), f"{len(blocks)} blocks vs {len(SPECS)} specs"
    it = iter(SPECS)
    s2 = pat.sub(lambda m: "\n" + emit(next(it)), s)
    open(p, "w", encoding="utf-8").write(s2)
    print(f"rewrote {len(blocks)} check pages in ch02")
    for spec in SPECS:
        assert max(len(c) for c in spec["cmds"]) <= 82, spec["title"]
        assert len(spec["cmds"]) <= 6, spec["title"]
    print("command length/count limits OK")


if __name__ == "__main__":
    main()
