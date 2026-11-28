# -*- coding: utf-8 -*-
"""第 1 章 _v2 的來源。

版面以 work/base/01_v2_base.pptx 為底（原樣保留），
這裡只記錄你對「文字」的修改：

    OVERRIDES = {(投影片編號, 該頁第幾個有文字的形狀, 第幾段): "新文字"}

索引皆從 0 開始；執行 python work/snap_build.py 01 可重建。
"""

BASE = r"work\base\01_v2_base.pptx"
OUT = r"deliver_beginner\01_Oracle_DBA_儲存記憶體與程序架構_v2.pptx"
KEY = "01"
TITLE = "第 1 章 儲存、記憶體與程序架構"

OVERRIDES = {}
