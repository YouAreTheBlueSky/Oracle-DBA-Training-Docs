# -*- coding: utf-8 -*-
"""Chapter 12 — Part 11 Miscellaneous Oracle Database Topics (source PDF p.582-595)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/ladbi/operating-system-checklist-for-installing-oracle-database.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/admqs/getting-started-with-oracle-enterprise-manager-express.html",
]

SCOPE = ("作業系統章節以 Oracle Linux／RHEL 為例；Enterprise Manager 章節以 19c 的 EM Express 為基準，"
         "說明 DB Control 已被移除後的管理替代方案。")

CHAPTER = {
    "no": 12,
    "part": "Part 11",
    "title": "作業系統前置與 EM 管理工具",
    "en": "Miscellaneous Oracle Database Topics",
    "subtitle": "Kernel 參數 ／ Shell Limits ／ DB Control 到 EM Express",
    "source": "oracle_dba_code_examples.pdf  p.582–595",
    "chap_label": "12",
    "agenda_title": "本章大綱",
    "agenda": [
        ("作業系統前置", "核心參數、shell limits、SELinux 與帳號群組，決定資料庫跑不跑得穩。"),
        ("EM 管理工具", "DB Control、Grid Control 到 EM Express 的演進，以及 19c 該用什麼。"),
        ("安裝前檢查", "記憶體、swap、套件與網路名稱解析，一次到位避免重工。"),
        ("工具取捨", "圖形工具與 SQLcl／指令碼的分工，哪些工作不該只靠 GUI。"),
        ("交付檢核", "把環境前置與管理工具設定寫成可驗證的清單。"),
    ],
    "agenda_note": "本章是選修章，適合負責裝機與平台維運的學員；內容偏作業系統與工具，非資料庫內部機制。",
    "note_why": "Part 11 原文以 10g/11g 的 Enterprise Manager 安裝為主，19c 已移除 dbconsole；本章保留作業系統前置知識，工具章節改以「演進與替代方案」呈現。",
    "refs": REFS,
    "refs_note": "19c 已無 Oracle Enterprise Manager Database Control；請改用 EM Express 或 Cloud Control。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "作業系統前置：核心參數與資源限制",
            "section": "作業系統前置",
            "src": "來源 p.586–587",
            "concept": {
                "items": [
                    ("共用記憶體", "kernel.shmmax 要大於 SGA 目標值，否則 instance 起不來。"),
                    ("號誌量 sem", "semmsl、semmns、semopm、semmni 四項決定並行連線數上限。"),
                    ("檔案與程序數", "limits.conf 的 nofile 與 nproc，決定單一帳號能開多少檔案與程序。"),
                    ("安全性設定", "SELinux 需關閉或設定為 permissive，避免 Oracle 檔案被阻擋。"),
                    ("套件與連結", "libaio、compat-libstdc++ 等套件缺失時，安裝程式會在連結階段失敗。"),
                ],
                "note": "這些數值都在 OS 層，資料庫參數調得再好也補不回來。",
            },
            "code": {
                "title": "核心參數與 shell limits 設定",
                "lines": [
                    "# /etc/sysctl.conf",
                    "kernel.shmall = 2097152",
                    "kernel.shmmax = 536870912        # 需 >= SGA 大小",
                    "kernel.shmmni = 4096",
                    "kernel.sem = 250 32000 100 128   # semmsl semmns semopm semmni",
                    "",
                    "sysctl -p                        # 套用設定",
                    "",
                    "# /etc/security/limits.conf",
                    "*   soft  nproc   2047",
                    "*   hard  nproc   16384",
                    "*   soft  nofile  1024",
                    "*   hard  nofile  65536",
                ],
                "takeaway": "19c 的 shmmax 下限已大幅提高，請以官方需求文件的表格為準，不要沿用舊值。",
                "warning": "shmmax 小於 SGA 時，STARTUP 會在配置記憶體階段直接失敗。",
            },
            "check": {
                "title": "自我檢核：作業系統前置是否完成",
                "items": [
                    "shmmax 與 shmall 已依實際 SGA 大小調整並 sysctl -p 生效。",
                    "limits.conf 的 nofile／nproc 對 oracle 帳號已生效（ulimit -a 驗證）。",
                    "SELinux 狀態為 disabled 或已設定正確的 context。",
                    "libaio 等必要套件已安裝且版本符合需求文件。",
                    "主機名稱與 /etc/hosts 的正、反解一致。",
                ],
                "pitfalls": [
                    "只改 sysctl.conf 沒有 sysctl -p，重開機前都以為已生效。",
                    "limits 設定給 root，忘了給 oracle 帳號。",
                    "沿用 10g 時代的 shmmax 值，導致 19c 起不來。",
                ],
                "warning": None,
            },
            "_note_why": "作業系統前置是最容易「低估」的一段：參數不對，後面所有 DBA 工作都無法開始。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "從 DB Control 到 EM Express：管理工具的演進",
            "section": "EM 管理工具",
            "src": "來源 p.583–585",
            "concept": {
                "items": [
                    ("DB Control 已移除", "19c 不再提供 dbconsole 與 emctl，原廠建議改用 EM Express。"),
                    ("EM Express 內建", "隨資料庫安裝，透過 DBMS_XDB_CONFIG 設定 HTTPS 埠即可使用。"),
                    ("Cloud Control 為集中式", "多資料庫、多主機的集中監控與生命週期管理，需另外部署。"),
                    ("圖形工具的分工", "日常操作仍以 SQLcl 與指令碼為主，GUI 用於檢視與教學。"),
                    ("先確認 port", "EM Express 使用 XDB 的 HTTPS 埠，變更前先確認是否已被占用。"),
                ],
                "note": "工具會世代交替，但 DBA 的核心能力是「知道用哪個檢視查什麼」。",
            },
            "table": {
                "header": ["工具", "適用範圍", "19c 狀態"],
                "rows": [
                    ["DB Control（dbconsole）", "單一資料庫的圖形管理主控台", "已移除，emctl 無法使用"],
                    ["EM Express", "內建於資料庫的輕量網頁管理介面", "支援，需設定 XDB HTTPS 埠"],
                    ["Cloud Control（OEM）", "多主機、多資料庫的集中管理平台", "支援，需獨立部署"],
                    ["SQLcl ／ SQL*Plus", "指令碼、自動化、批次作業", "主要工具，建議優先"],
                    ["RMAN ／ Data Pump", "備份還原與資料移轉", "命令列為主"],
                ],
                "widths": [4.15, 6.55, 4.4],
                "small": True,
                "note": "教學環境建議同時展示 EM Express 與 SQLcl，讓學員知道同一個現象有兩種觀察方式。",
                "warning": "19c 的 EM Express 只有監控與基本操作，不提供 DB Control 時代的完整管理工作。",
            },
            "check": {
                "title": "自我檢核：管理工具是否就位",
                "items": [
                    "知道 19c 已無 dbconsole，不會再嘗試 emctl start dbconsole。",
                    "EM Express 的 HTTPS 埠已設定，且可用瀏覽器開啟。",
                    "集中監控需求已評估是否需要 Cloud Control。",
                    "日常維運的指令碼可用 SQLcl 批次執行。",
                    "團隊成員知道每項工作該用哪個工具。",
                ],
                "pitfalls": [
                    "照著舊教材執行 emctl，卻找不到指令。",
                    "把 EM Express 當成萬用工具，期待它有完整管理功能。",
                    "在生產環境隨意變更 XDB 的 HTTPS 埠，影響其他應用。",
                ],
                "warning": None,
            },
            "_note_why": "這一頁的重點不是工具操作，而是「世代交替時如何遷移知識」：工具會消失，檢視與方法不會。",
            "_note_scope": SCOPE,
            "_refs": [REFS[1]],
        },
    ],

    "summary": {
        "items": [
            ("OS 前置", "shmmax／shmall、kernel.sem、limits.conf、SELinux 四項先對，資料庫才跑得起來。"),
            ("驗證方式", "sysctl -p 之後用 ulimit -a 與實際啟動 instance 驗證，不只看設定檔。"),
            ("DB Control", "19c 已移除；舊教材的 emctl 與 RepManager 步驟不可再用。"),
            ("EM Express", "內建、需設定 XDB HTTPS 埠，適合單一資料庫的監控與教學。"),
            ("工具策略", "GUI 用於觀察，SQLcl 與指令碼用於自動化與交付。"),
        ],
        "section": "整合複習",
        "note": "本章雖是選修，但作業系統前置是所有章節的共同前提。",
    },
}
