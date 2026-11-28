# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "work/deckkit"); sys.path.insert(0, "work/content")
import ch05
from theme_v2 import build_v2
last = build_v2(ch05.CHAPTER, r"deliver_beginner\05_Oracle_DBA_安全性管理_v2.pptx")
print("完成，最後一頁頁碼:", last)
