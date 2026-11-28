# -*- coding: utf-8 -*-
"""為「沒有內容模組」的簡報（01_v2、06_v2）建立可重建的來源。

作法：原檔（binary）當底稿，模組只記錄「文字覆寫」：
    OVERRIDES = {(投影片編號, 形狀索引, 段落索引): "新文字"}
重建 = 複製底稿 → 套用覆寫 → 存檔。版面 100% 保留，文字改動可回寫。
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pptx import Presentation

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(mod, out_path, force=False):
    """由底稿＋覆寫重建；目標檔若被手改過則拒絕覆蓋。"""
    base = os.path.join(HERE, mod.BASE)
    tmp = os.path.join(HERE, "work", "proto", "_snap_tmp.pptx")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)

    prs = Presentation(base)
    applied = 0
    for (sno, shi, pi), text in getattr(mod, "OVERRIDES", {}).items():
        slide = prs.slides[sno - 1]
        shapes = [s for s in slide.shapes if s.has_text_frame]
        if shi >= len(shapes):
            continue
        tf = shapes[shi].text_frame
        if pi >= len(tf.paragraphs):
            continue
        para = tf.paragraphs[pi]
        if para.runs:
            para.runs[0].text = text
            for r in para.runs[1:]:
                r.text = ""
        else:
            para.text = text
        applied += 1
    prs.save(tmp)

    if os.path.exists(out_path) and not force:
        import snap_diff
        import diff_pptx
        moved = diff_pptx.layout_changed(tmp, out_path)
        if moved:
            raise SystemExit(
                "拒絕覆蓋：%s 的版面與底稿不同（有人移動或縮放了物件，差異頁：%s）。\n"
                "  底稿＋覆寫只保存文字；版面調整請直接另存為新底稿，或加 --force 覆蓋。"
                % (os.path.basename(out_path), ", ".join("p%d" % p for p in moved[:8])))
        changes, _ = snap_diff.diff_files(tmp, out_path)
        if changes:
            raise SystemExit(
                "拒絕覆蓋：%s 與「底稿＋覆寫」重建結果不同（可能是手改過）。\n"
                "  請先執行：python work/snap_diff.py %s --apply\n"
                "  或加 --force 強制覆蓋。" % (os.path.basename(out_path),
                                              getattr(mod, "KEY", "01")))
    shutil.move(tmp, out_path)
    return applied
