# -*- coding: utf-8 -*-
"""Chapter 9 — Part 8 Oracle RAC One Node (source PDF p.529-550)."""

REFS = [
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/racad/administering-oracle-rac-one-node.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/racad/server-control-utility-reference.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/racad/converting-single-instance-oracle-databases-to-oracle-rac-and-oracle-rac-one-node.html",
    "https://docs.oracle.com/en/database/oracle/oracle-database/19/racad/introduction-to-oracle-rac.html",
]

SCOPE = ("以 Oracle Database 19c 為敘述基準；指令取自來源文件 p.529–550，"
         "其中 11.2.0.1 專屬工具已改寫為 19c srvctl 語法並加註警示。")

CHAPTER = {
    "no": 9,
    "part": "Part 8",
    "title": "RAC One Node 建置與線上搬移",
    "en": "Oracle RAC One Node: Deployment and Online Relocation",
    "subtitle": "單一節點作用中 ／ 線上搬移 ／ 與 RAC 的取捨",
    "source": "oracle_dba_code_examples.pdf  p.529–550",
    "chap_label": "09",
    "agenda_title": "本章大綱",
    "agenda": [
        ("定位與選型",
         "單一 instance 的 RAC 如何在故障與維護時換手，以及何時該選它。"),
        ("建置與轉換",
         "srvctl add database 與 convert database：候選節點、timeout 與前置條件。"),
        ("線上搬移",
         "srvctl relocate database 的四個步驟、TAF 設定與搬移前的準備。"),
    ],
    "agenda_note": "本章是 Part 8 的全部內容：從選型、建置到搬移，把 11gR2 的舊工具對應到 19c。",
    "note_why": "來源文件 22 頁幾乎都在記安裝步驟；本章收斂成定位、建置轉換、線上搬移三個主題。",
    "refs": REFS,
    "refs_note": "來源文件為 11gR2 時代；raconeinit、Omotion 等工具已由 srvctl 取代，19c 行為請以官方文件為準。",

    "topics": [
        # ---------------------------------------------------------------- 1
        {
            "title": "單一節點作用中的 RAC",
            "section": "定位與選型",
            "src": "來源 p.530、p.543",
            "concept": {
                "items": [
                    ("單一 instance",
                     "同一時間只有一個 instance 在 cluster 的某個節點執行。"),
                    ("共用儲存",
                     "資料檔放 ASM 共用磁碟，多個資料庫共用同一組伺服器。"),
                    ("故障自動接手",
                     "節點失效時 Clusterware 在候選節點重啟 instance 與服務。"),
                    ("線上搬移",
                     "規劃性搬移先開第二個 instance，服務搬完才關掉原來的。"),
                    ("不具擴充性",
                     "沒有跨節點平行處理，要 scale out 只能轉成 RAC。"),
                ],
                "note": "RAC One Node 買的是換手能力與 consolidation，不是多節點的算力。",
            },
            "table": {
                "header": ["面向", "RAC One Node", "RAC", "單機"],
                "rows": [
                    ["作用中 instance", "1 個，可線上換節點", "每節點各 1 個", "1 個，不能換"],
                    ["故障接手", "候選節點重啟 instance", "其他節點繼續服務", "靠人工或外掛 HA"],
                    ["擴充方向", "垂直：加 CPU 與記憶體", "水平：加節點", "垂直"],
                    ["授權", "EE；額外付費選項", "EE 加 RAC 選項", "EE 或 SE2"],
                    ["適用場景", "consolidation、滾動維護", "高負載、需 scale out", "小型或測試"],
                ],
                "widths": [2.3, 4.4, 4.2, 4.2],
                "small": True,
                "note": "三者差別不在功能多寡，而在「換手時誰接手」與「能不能加節點」。",
            },
            "check": {
                "title": "自我檢核：這個資料庫該用哪一種",
                "items": [
                    "能說出目前 instance 跑在哪個節點，候選節點有誰。",
                    "資料檔在 ASM 共用磁碟，任一候選節點都讀得到。",
                    "服務只有一個作用中 instance，用戶端走 SCAN。",
                    "知道節點故障後，instance 幾分鐘內會在他節點起來。",
                    "需要跨節點平行處理時，已規劃轉 RAC 而非硬撐。",
                ],
                "pitfalls": [
                    "把 RAC One Node 當成兩節點 RAC 在用。",
                    "候選節點沒裝同一版本的 Oracle Home。",
                    "只用 IP 連線，節點一換就連不上。",
                ],
                "warning": "RAC One Node 是 EE 的付費選項；SE2 自 19c 起不支援 RAC。",
            },
            "_note_why": "先讓學員分清楚「換手」與「擴充」是兩件事，後面談 relocate 才不會誤以為搬節點等於加速。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[3]],
        },
        # ---------------------------------------------------------------- 2
        {
            "title": "建置與轉換：srvctl 三個動作",
            "section": "建置與轉換",
            "src": "來源 p.543–547",
            "concept": {
                "items": [
                    ("DBCA 或 srvctl",
                     "建庫時選 RAC One Node；既有的庫用 add database 註冊。"),
                    ("候選節點",
                     "-server 列出可執行節點，-timeout 是等連線搬完的分鐘數。"),
                    ("轉換前收斂",
                     "RAC 轉 RAC One Node 前只留一個 instance，服務偏好先改。"),
                    ("OMF 或雙 thread",
                     "轉換要求 OMF 自動配置 thread，或至少兩個 redo thread。"),
                    ("instance 命名",
                     "prefix_1 與 prefix_2 交替，每次線上搬移就換一次名字。"),
                ],
                "note": "srvctl 才是真正管理 RAC One Node 的工具，DBCA 只是幫你呼叫它。",
            },
            "code": {
                "title": "建立、轉換與確認 RAC One Node",
                "lines": [
                    "# 1) 註冊 RAC One Node：候選節點與搬移等待分鐘數",
                    "srvctl add database -db ron -oraclehome $ORACLE_HOME \\",
                    "  -dbtype RACONENODE -instance ron -server \"rac1,rac2\" -timeout 30",
                    "",
                    "# 2) RAC 只剩一個 instance 後轉 RAC One Node",
                    "srvctl convert database -db ron -dbtype RACONENODE -timeout 30",
                    "# 3) 反向轉回 RAC（還原成多 instance 架構）",
                    "srvctl convert database -db ron -dbtype RAC",
                    "",
                    "# 4) 確認型態、候選節點與線上搬移 timeout",
                    "srvctl config database -db ron",
                ],
                "takeaway": "建立與轉換都靠 srvctl；DBCA 只是幫你把設定寫進 Clusterware。",
                "warning": "raconeinit、racone2rac、Omotion 是 11.2.0.1 的補丁工具，19c 一律改用 srvctl。",
            },
            "check": {
                "title": "自我檢核：轉換前後的組態是否正確",
                "items": [
                    "srvctl config database -db ron 的 Type 顯示 RACOneNode。",
                    "Candidate servers 列出所有可能執行 instance 的節點。",
                    "轉換前資料庫只剩一個 instance，服務偏好已指向它。",
                    "資料庫使用 OMF，或已建立兩個以上的 redo thread。",
                    "搬移後 instance 名稱由 prefix_1 換成 prefix_2。",
                ],
                "pitfalls": [
                    "還有兩個 instance 就下 convert，直接失敗。",
                    "只在其中一個節點放 password file。",
                    "把 -timeout 當成指令逾時，而非等連線搬完。",
                ],
                "warning": None,
            },
            "_note_why": "把 raconeinit／racone2rac 的舊流程對應到 add／convert 兩個動作，學員才不會在 19c 找不著工具。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0], REFS[1], REFS[2]],
        },
        # ---------------------------------------------------------------- 3
        {
            "title": "線上搬移：不關機換節點",
            "section": "線上搬移",
            "src": "來源 p.549–550",
            "concept": {
                "items": [
                    ("四個步驟",
                     "開新 instance、移服務、等連線搬完、關掉原 instance。"),
                    ("僅限 RAC One Node",
                     "RAC 資料庫不能線上搬移，只能搬 service。"),
                    ("TAF 與 FAN",
                     "用戶端設 FAILOVER=ON，配合 FAN 可讓連線無感換手。"),
                    ("password file 先備",
                     "搬到非候選節點前，先複製 password file 或改用 ASM 共用。"),
                    ("搬移不是調效能",
                     "換節點不會變快；主場景是滾動維護與節點下架。"),
                ],
                "note": "線上搬移的重點是服務先走、連線後走；順序反了就會斷線。",
            },
            "code": {
                "title": "線上搬移與用戶端 TAF",
                "lines": [
                    "# 1) 搬到 rac2；-timeout 是等連線移轉的分鐘數",
                    "srvctl relocate database -db ron -node rac2 -timeout 30",
                    "",
                    "# 2) 確認 instance 名稱與所在節點已改變",
                    "srvctl status database -db ron -v",
                    "",
                    "# 3) 用戶端 TAF：連 SCAN，失敗時改接另一節點",
                    "#    FAILOVER=ON  METHOD=BASIC  TYPE=SELECT",
                    "",
                    "# 4) 搬移卡住時中止，回到原本的節點",
                    "srvctl relocate database -db ron -abort",
                ],
                "takeaway": "搬移期間新舊 instance 並存，連線全部移轉後舊的才會關閉。",
                "warning": "timeout 到但連線沒搬完，舊 instance 會被強制關閉，長交易因此中斷。",
            },
            "check": {
                "title": "自我檢核：搬移能不能做到無感",
                "items": [
                    "srvctl status database -db ron -v 顯示實例已在新節點。",
                    "搬移後 instance 名稱改變，服務在新節點註冊完成。",
                    "用戶端走 SCAN 並設 TAF，重連不必改連線字串。",
                    "目標節點的 password file 與 ORACLE_HOME 版本一致。",
                    "搬移排在低峰，且已確認沒有長時間交易。",
                ],
                "pitfalls": [
                    "直接關掉原節點，沒有先 relocate。",
                    "用 IP 而非 SCAN 連線，搬完就連不上。",
                    "在尖峰執行搬移，timeout 到被強制斷線。",
                ],
                "warning": None,
            },
            "_note_why": "Omotion 在 19c 已不存在，但四個步驟與 TAF 的觀念完全沒變，值得花時間講順序。",
            "_note_scope": SCOPE,
            "_refs": [REFS[0]],
        },
    ],

    "summary": {
        "items": [
            ("定位", "RAC One Node 是單一 instance 的 RAC，靠候選節點接手而非擴充。"),
            ("選型", "要 consolidation 與滾動維護選它；要 scale out 選 RAC。"),
            ("建置", "DBCA 選 RAC One Node，或用 srvctl add database 註冊。"),
            ("轉換", "用 srvctl convert 互轉，前提是只剩一個 instance。"),
            ("搬移", "srvctl relocate database 開第二個 instance，服務搬完才關舊的。"),
        ],
        "section": "整合複習",
        "note": "add、convert、relocate 三個動作，就撐起 RAC One Node 的日常維運。",
    },
}
