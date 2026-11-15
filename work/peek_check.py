# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "work/content")
mods = [2, 3, 8, 11]
for n in mods:
    sp = __import__("ch%02d" % n).CHAPTER
    t = sp["topics"][0]
    print("=" * 70)
    print("ch%02d T1: %s" % (n, t["title"]))
    print("  檢核標題:", t["check"]["title"])
    for it in t["check"]["items"]:
        print("   -", it)
    print("  常見錯誤:")
    for p in t["check"].get("pitfalls", []):
        print("   x", p)
