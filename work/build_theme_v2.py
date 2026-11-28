# -*- coding: utf-8 -*-
"""把指定章節轉成 v2 版型。

用法：python work/build_theme_v2.py ch02 ch03 ch04
輸出：deliver_beginner/<檔名前綴>_v2.pptx
"""
import sys, os, importlib

sys.path.insert(0, "work/deckkit")
sys.path.insert(0, "work/content")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from theme_v2 import build_v2

OUT = {
    "ch02": r"deliver_beginner\02_Oracle_DBA_建置與日常管理_v2.pptx",
    "ch03": r"deliver_beginner\03_Oracle_DBA_Net_Services_v2.pptx",
    "ch04": r"deliver_beginner\04_Oracle_DBA_備份與復原_v2.pptx",
    "ch05": r"deliver_beginner\05_Oracle_DBA_安全性管理_v2.pptx",
}


def apply_overrides(mod, sp):
    for (ti, kind), val in getattr(mod, "NOTE_OVERRIDES", {}).items():
        if 0 <= ti < len(sp["topics"]) and kind in sp["topics"][ti]:
            target = sp["topics"][ti][kind]
            if isinstance(val, dict):
                mode, text = val.get("mode", "replace"), val.get("text", "")
            else:
                mode, text = "replace", val
            target["_note_replace" if mode == "replace" else "_note_pre"] = text


def main(mods):
    for name in mods:
        mod = importlib.import_module(name)
        sp = mod.CHAPTER
        apply_overrides(mod, sp)
        out = OUT.get(name, "deliver_beginner/%s_v2.pptx" % name)
        last = build_v2(sp, out)
        print("%s → %s（%d 頁）" % (name, os.path.basename(out), last))


if __name__ == "__main__":
    main(sys.argv[1:] or ["ch02", "ch03", "ch04"])
