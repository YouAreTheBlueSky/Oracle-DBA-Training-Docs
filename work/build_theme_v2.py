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

# 模組 → (初階版章號, 輸出路徑)
OUT = {
    "ch02": (2, r"deliver_beginner\02_Oracle_DBA_建置與日常管理_v2.pptx"),
    "ch03": (3, r"deliver_beginner\03_Oracle_DBA_Net_Services_v2.pptx"),
    "ch04": (4, r"deliver_beginner\04_Oracle_DBA_備份與復原_v2.pptx"),
    "ch05": (5, r"deliver_beginner\05_Oracle_DBA_安全性管理_v2.pptx"),
    "ch11": (7, r"deliver_beginner\07_Oracle_DBA_公用程式_v2.pptx"),
    "ch12": (8, r"deliver_beginner\08_Oracle_DBA_作業系統與EM工具_v2.pptx"),
    "ch13": (9, r"deliver_beginner\09_Oracle_DBA_PLSQL_v2.pptx"),
    "ch14": (10, r"deliver_beginner\10_Oracle_DBA_附錄_v2.pptx"),
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
        no, out = OUT.get(name, (sp.get("no"), "deliver_beginner/%s_v2.pptx" % name))
        sp["no"] = no
        sp["chap_label"] = "%02d" % no
        apply_overrides(mod, sp)
        last = build_v2(sp, out)
        print("%s → %s（第 %02d 章）" % (name, os.path.basename(out), no))


if __name__ == "__main__":
    main(sys.argv[1:] or ["ch02", "ch03", "ch04"])
