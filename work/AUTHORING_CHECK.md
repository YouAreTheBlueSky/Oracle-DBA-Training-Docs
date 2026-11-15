# 檢核頁改版規範（給章節作者）

## 為什麼要改

原本的「自我檢核：…」頁只寫**判斷準則**（例：`v$controlfile 至少兩份`），沒有告訴學員**怎麼查**。
365 條檢核項目中只有 29% 具名視圖／指令、30% 寫出通過條件，導致這一頁無法自學。

新版把檢核頁改成「**怎麼檢查**」：給可直接執行的驗證指令 ＋ 每條的通過條件。

## 新版資料結構

`check` 從 `items` 改為 `commands` ＋ `conds`：

```python
"check": {
    "title": "檢核：<這頁要確認什麼>",          # 保留原本語意，去掉「自我」兩字
    "commands": [                              # 3–6 行，每行 ≤ 82 字元
        "SELECT name, value FROM v$parameter WHERE name = 'spfile';",
        "SELECT log_mode FROM v$database;",
    ],
    "conds": [                                 # 3–4 條，對應 commands 的輸出
        ("spfile", "有路徑（非空）。空值＝仍用 PFILE，重開機參數會漂移"),
        ("log_mode", "ARCHIVELOG。NOARCHIVELOG 不能做時間點復原"),
    ],
    "pitfalls": [                              # 2–3 條，每條 ≤ 46 字（超過會換行）
        "只看 log_mode 就結案，沒確認歸檔目的地還有空間",
    ],
    "warning": "（選填，≤ 34 字）",
},
```

**不要**再使用舊的 `items`（新版版面會忽略它）。

## 寫作規則

1. **指令必須是「驗證」，不是「動作」**：查 `v$`／`dba_`／`lsnrctl status`／`RMAN> SHOW ALL`／`asmcmd ls` 之類，
   不要重貼程式碼頁的 DDL。若程式碼頁本身就是查詢（例如「檔案位置查詢」），
   驗證頁就改成**結果判讀**：同一組查詢、但 `conds` 寫「看到什麼值代表什麼」。
2. **每條 cond 必須有明確的通過值或可判讀的狀態**：
   - 好：「≥2，且路徑分散在不同磁碟」「VALID 且 error 為空」「ARCHIVELOG」
   - 壞：「要注意」「確認正常」（無法判斷）
3. **cond 的標籤（第一項）≤ 14 字**，可以是欄位名、視圖名或中文短語。
4. **cond 的說明（第二項）≤ 64 字**（超過 50 會變兩行，仍可接受），格式建議：`期望值。不符合代表什麼`。
5. 指令一律 19c 可執行；不確定的語法不要寫（寧可少一行）。
6. 每頁最多 6 行指令、4 條 cond；超過請挑重點，不要縮字。

## 參考實作

`work/content/ch02.py` 的 14 個 `check` 區塊即為標準範例（涵蓋 shell、SQL、CDB、RMAN 等不同類型），
寫之前先讀 2–3 個。

## 驗收

```powershell
& 'C:\Users\user\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe' `
  work\build_chapter.py ch0X "work\proto\ch0X_check.pptx"
```

必須看到：

1. `OK  ch0X: N slides (expected N)`，無 Traceback。
2. **沒有** `check condensed` 警告（代表文字塞不下、被縮字）。
3. 其他警告（code 字級、concept 縮字）可接受，但不要新增。

完成後回報：改了幾個檢核頁、有沒有 `check condensed`、哪些 cond 你覺得資料不足（例如來源文件沒對應的檢視）。


## 文字格式：粗體與底線（行內標記）

任何文字欄位（標題、通過條件、常見錯誤、程式碼行、重點句）都可以用：

| 寫法 | 效果 |
|---|---|
| `**文字**` | 粗體 |
| `__文字__` | 底線 |
| `***文字***` | 粗體＋底線 |

例：

```python
("log_mode", "**ARCHIVELOG** 才能做時間點復原；__NOARCHIVELOG__ 不行"),
"SELECT name, value FROM **v$parameter** WHERE name = 'spfile';",
```

量測寬度時會自動剝除標記，不影響換行與縮字判斷。

**也可以反過來**：在 PowerPoint 直接加粗／加底線，再執行
`python work/diff_pptx.py chNN <你的檔案> --as N --apply`，
工具會偵測格式差異並轉成上面的標記寫回模組。

## 單頁與區塊字級

```python
"check": {
    "style": {
        "scale": 1.15,          # 整頁（含指令、條件、常見錯誤）
        "commands_scale": 1.1,  # 只放大驗證指令
        "cond_scale": 1.0,      # 只放大通過條件
        "pitfall_scale": 0.95,  # 只調整常見錯誤
    },
}
```

係數會同時套用在版面計算，字變大不會擠出框外；塞不下時會自動退讓並在 build 時告警。
