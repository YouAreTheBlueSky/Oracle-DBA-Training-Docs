# -*- coding: utf-8 -*-
"""重建以原檔為底、只記錄文字覆寫的簡報（01_v2、06_v2）。

用法：
    python work/snap_build.py 01
    python work/snap_build.py 06
"""
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "content"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import snap_build

MODS = {"01": "snap01", "06": "snap06"}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force = "--force" in sys.argv
    for key in args:
        mod = importlib.import_module(MODS[key])
        out = os.path.join(snap_build.HERE, mod.OUT)
        n = snap_build.build(mod, out, force=force)
        print("%s → %s（%d 頁）" % (mod.TITLE, os.path.basename(out), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
