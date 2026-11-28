# -*- coding: utf-8 -*-
"""比對「底稿＋覆寫」重建的結果與你手改的檔案，並把差異寫回模組的 OVERRIDES。

用法：
    python work/snap_diff.py 01 --apply
    python work/snap_diff.py 06 --apply
"""
import os, sys, importlib, re

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "deckkit"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import diff_pptx
import snap_build

MODS = {"01": "snap01", "06": "snap06"}


def diff_files(a_path, b_path):
    return diff_pptx.diff(diff_pptx.dump(a_path), diff_pptx.dump(b_path))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODS:
        print(__doc__)
        return 2
    key = sys.argv[1]
    do_apply = "--apply" in sys.argv
    mod = importlib.import_module(MODS[key])
    out = os.path.join(snap_build.HERE, mod.OUT)

    # 以「底稿＋目前覆寫」重建到暫存，再與現有檔比對
    tmp = os.path.join(snap_build.HERE, "work", "proto", "_snap_cmp.pptx")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    snap_build.build(mod, tmp, force=True)
    changes, warns = diff_files(tmp, out)

    print("比對 %s：%d 頁 vs %d 頁" % (mod.TITLE, len(diff_pptx.dump(tmp)),
                                    len(diff_pptx.dump(out))))
    if not changes and not warns:
        print("沒有差異（兩者一致）")
        return 0

    for c in changes:
        print("  [%s] 第 %02d 頁｜形狀 %d｜段 %d\n    - %s\n    + %s"
              % (c["kind"], c["slide"], c["shape"], c["para"],
                 diff_pptx.cut(c["old"]), diff_pptx.cut(c["new"])))
    if not do_apply:
        print("\n（加 --apply 會寫回模組）")
        return 1

    overrides = dict(getattr(mod, "OVERRIDES", {}))
    for c in changes:
        overrides[(c["slide"], c["shape"], c["para"])] = c["new"]

    path = os.path.join(snap_build.HERE, "work", "content", MODS[key] + ".py")
    src = open(path, encoding="utf-8").read()
    lines = ["", "OVERRIDES = {"]
    for (sno, shi, pi) in sorted(overrides):
        lines.append("    (%d, %d, %d): %r," % (sno, shi, pi, overrides[(sno, shi, pi)]))
    lines.append("}")
    src = re.sub(r"\nOVERRIDES = \{.*?\n\}", "\n".join(lines), src, flags=re.S)
    if "OVERRIDES = {" not in src:
        src = src.rstrip() + "\n" + "\n".join(lines) + "\n"
    open(path, "w", encoding="utf-8").write(src)
    print("已寫回 %d 筆覆寫到 %s" % (len(overrides), os.path.basename(path)))

    importlib.reload(mod)
    snap_build.build(mod, out, force=True)
    again, _ = diff_files(tmp, out)
    print("重新驗證：%s" % ("一致 [OK]" if not again else "仍有 %d 處差異" % len(again)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
