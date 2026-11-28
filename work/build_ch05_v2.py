# -*- coding: utf-8 -*-
"""建置 v2 版型的第 5 章（含使用者的 NOTE_OVERRIDES）。"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "work/deckkit")
sys.path.insert(0, "work/content")
import ch05
from theme_v2 import build_v2

sp = ch05.CHAPTER
for (ti, kind), val in getattr(ch05, "NOTE_OVERRIDES", {}).items():
    if 0 <= ti < len(sp["topics"]) and kind in sp["topics"][ti]:
        target = sp["topics"][ti][kind]
        if isinstance(val, dict):
            mode, text = val.get("mode", "replace"), val.get("text", "")
        else:
            mode, text = "replace", val
        target["_note_replace" if mode == "replace" else "_note_pre"] = text

last = build_v2(sp, r"deliver_beginner\05_Oracle_DBA_安全性管理_v2.pptx")
print("完成，最後一頁頁碼:", last)
