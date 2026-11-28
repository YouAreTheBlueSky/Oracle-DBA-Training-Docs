# -*- coding: utf-8 -*-
"""統一的建置入口：不管章節用哪種來源，都從這裡重建。

    python work/build.py 01          # 第 1 章（JSON 快照）
    python work/build.py 02 03 04    # 語意模組 → v2 版型
    python work/build.py all         # 全部 01–10
    python work/build.py all --force # 必要時強制覆蓋

章節與來源的對應：
    01              JSON  work/spec/01.json         （版面目調，非程式生成）
    02–05           py    ch02–ch05 → v2 版型
    06              JSON  work/spec/06.json         （Part1–5 合併版）
    07–10           py    ch11–ch14 → v2 版型
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, os.path.join(HERE, "content"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import build_theme_v2
import snap_build
import importlib

# 初階章號 → ("theme", 模組名) 或 ("json", snap 模組名)
CHAPTERS = {
    "01": ("json", "snap01"),
    "02": ("json", "snap02"),
    "03": ("json", "snap03"),
    "04": ("theme", "ch04"),
    "05": ("theme", "ch05"),
    "06": ("json", "snap06"),
    "07": ("json", "snap07"),
    "08": ("json", "snap08"),
    "09": ("theme", "ch13"),
    "10": ("theme", "ch14"),
}


def build_one(key, force=False):
    kind, name = CHAPTERS[key]
    if kind == "theme":
        return build_theme_v2.main([name] + (["--force"] if force else []))
    mod = importlib.import_module(name)
    out = os.path.join(os.path.dirname(HERE), mod.OUT)
    pages = snap_build.build(mod, out, force=force)
    print("第 %s 章（JSON）→ %s（%d 頁）" % (key, os.path.basename(out), pages))
    return 0


def main(argv):
    force = "--force" in argv
    keys = [a for a in argv if not a.startswith("--")]
    if not keys or keys == ["all"]:
        keys = sorted(CHAPTERS)
    unknown = [k for k in keys if k not in CHAPTERS]
    if unknown:
        print("不認識的章號：%s（可用 01–10 或 all）" % ", ".join(unknown))
        return 2

    rc = 0
    for k in keys:
        rc |= build_one(k, force=force)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
