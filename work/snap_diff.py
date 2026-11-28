# -*- coding: utf-8 -*-
"""比對「JSON 規格重建」與手改檔，並把差異寫回 JSON。

用法：
    python work/snap_diff.py 01 --apply
    python work/snap_diff.py 06 --apply
"""
import os, sys, json, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "content"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import diff_pptx
import snap_build

MODS = {"01": "snap01", "02": "snap02", "03": "snap03", "06": "snap06", "07": "snap07", "08": "snap08"}


def strip_markup(t):
    bold = False
    out = []
    for token in ("***", "**", "__"):
        if token in t:
            if token in ("**", "***"):
                bold = t.count(token) % 2 == 1
    for token in ("***", "**", "__"):
        t = t.replace(token, "")
    return t, bold


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODS:
        print(__doc__)
        return 2
    key = sys.argv[1]
    do_apply = "--apply" in sys.argv
    mod = importlib.import_module(MODS[key])
    ROOT = os.path.dirname(HERE)
    out = os.path.join(ROOT, mod.OUT)
    spec_path = os.path.join(ROOT, mod.SPEC)

    tmp = os.path.join(os.path.dirname(HERE), "work", "proto", "_spec_cmp.pptx")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    snap_build.build(mod, tmp, force=True)

    changes, warns = diff_pptx.diff(diff_pptx.dump(tmp), diff_pptx.dump(out))
    print("比對 %s：%d 頁 vs %d 頁" % (mod.TITLE, len(diff_pptx.dump(tmp)),
                                    len(diff_pptx.dump(out))))
    if not changes and not warns:
        print("沒有差異（兩者一致）")
        return 0

    for c in changes:
        print("  [%s] 第 %02d 頁｜形狀 %d｜段 %d\n    - %s\n    + %s"
              % (c["kind"], c["slide"], c["shape"], c["para"],
                 diff_pptx.cut(c["old"]), diff_pptx.cut(c["new"])))
    for w in warns:
        print("  ! " + w)
    if not do_apply:
        print("\n（加 --apply 會寫回 JSON）")
        return 1

    spec = json.load(open(spec_path, encoding="utf-8"))
    applied = 0
    for c in changes:
        try:
            shape = spec["slides"][c["slide"] - 1]["shapes"][c["shape"]]
            paras = shape.get("paras") or []
            para = paras[c["para"]]
        except (IndexError, KeyError):
            continue
        text, bold = strip_markup(c["new"])
        runs = para.get("runs") or []
        if runs:
            runs[0]["t"] = text
            if bold:
                runs[0]["bold"] = True
            for r in runs[1:]:
                r["t"] = ""
        else:
            para["runs"] = [{"t": text, "size": para.get("dsz"),
                             "bold": bold or para.get("db"),
                             "color": para.get("dc"), "font": None}]
        applied += 1

    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=1)
    print("已寫回 %d 筆到 %s" % (applied, os.path.basename(spec_path)))

    importlib.reload(mod)
    snap_build.build(mod, out, force=True)
    snap_build.build(mod, tmp, force=True)
    again, _ = diff_pptx.diff(diff_pptx.dump(tmp), diff_pptx.dump(out))
    print("重新驗證：%s" % ("一致 [OK]" if not again else "仍有 %d 處差異" % len(again)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
