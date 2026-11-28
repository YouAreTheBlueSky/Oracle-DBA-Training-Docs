# -*- coding: utf-8 -*-
"""以 JSON 規格為來源的重建（01_v2、06_v2）。

    work/spec/01.json  ← 這才是來源（版面、文字、備忘都在裡面）
            ↓ replay.py
    deliver_beginner/01_…_v2.pptx
"""
import os
import sys
import json
import shutil

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "work", "deckkit"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from replay import render


def build(mod, out_path, force=False):
    spec_path = os.path.join(HERE, getattr(mod, "SPEC"))
    tmp = os.path.join(HERE, "work", "proto", "_spec_tmp.pptx")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)

    spec = json.load(open(spec_path, encoding="utf-8"))
    render(spec, tmp)

    if os.path.exists(out_path) and not force:
        import diff_pptx
        moved = diff_pptx.layout_changed(tmp, out_path)
        if moved:
            raise SystemExit(
                "拒絕覆蓋：%s 的版面與 JSON 規格不同（有人移動或縮放了物件，差異頁：%s）。\n"
                "  請先在 JSON 更新座標，或加 --force 覆蓋。" %
                (os.path.basename(out_path), ", ".join("p%d" % p for p in moved[:8])))
        changes, warns = diff_pptx.diff(diff_pptx.dump(tmp), diff_pptx.dump(out_path))
        if changes:
            raise SystemExit(
                "拒絕覆蓋：%s 與 JSON 規格不同（可能是手改過）。\n"
                "  請先執行：python work/snap_diff.py %s --apply\n"
                "  或加 --force 強制覆蓋。" %
                (os.path.basename(out_path), getattr(mod, "KEY", "01")))
    shutil.move(tmp, out_path)
    return len(spec["slides"])
