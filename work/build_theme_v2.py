# -*- coding: utf-8 -*-
"""把指定章節轉成 v2 版型（含「不覆蓋手改檔」保護）。

用法：
    python work/build_theme_v2.py ch11 ch12      # 有手改就拒絕
    python work/build_theme_v2.py ch11 --force   # 強制覆蓋

規則：先建到暫存檔，與現有檔案比對；若現有檔案與剛建好的不一致
（代表你手改過），就停手並提示先跑 diff_pptx.py --theme v2 --apply。
"""
import sys, os, importlib

sys.path.insert(0, "work/deckkit")
sys.path.insert(0, "work/content")
sys.path.insert(0, "work")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from theme_v2 import build_v2
import diff_pptx

TMP = os.path.join("work", "proto", "_v2_build_tmp.pptx")

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


def main(argv):
    force = "--force" in argv
    mods = [a for a in argv if not a.startswith("--")]
    rc = 0
    for name in mods:
        mod = importlib.import_module(name)
        sp = mod.CHAPTER
        no, out = OUT.get(name, (sp.get("no"), "deliver_beginner/%s_v2.pptx" % name))
        sp["no"] = no
        sp["chap_label"] = "%02d" % no
        body = getattr(mod, "BODY_SIZE", None)
        if body:
            sp["body_size"] = body
        apply_overrides(mod, sp)

        os.makedirs(os.path.dirname(TMP), exist_ok=True)
        build_v2(sp, TMP)

        if os.path.exists(out) and not force:
            changes, warns = diff_pptx.diff(diff_pptx.dump(TMP), diff_pptx.dump(out))
            moved = diff_pptx.layout_changed(TMP, out)
            if moved:
                print("拒絕覆蓋：%s 的版面與模組重建結果不同（有人移動或縮放了物件）。" % os.path.basename(out))
                print("  差異頁：%s" % ", ".join("p%d" % p for p in moved[:8]))
                print("  v2 版型的版面由程式產生，無法保留手動調整；請改文字、或加 --force 覆蓋。")
                rc = 1
                continue
            if changes:
                print("拒絕覆蓋：%s 與模組重建結果不同（可能是你手改過）。" % os.path.basename(out))
                print("  差異 %d 處，請先執行：" % len(changes))
                print("    python work/diff_pptx.py %s \"%s\" --as %d --theme v2 --apply" % (name, out, no))
                print("  或加 --force 強制覆蓋。")
                rc = 1
                continue

        os.replace(TMP, out)
        print("%s → %s（第 %02d 章）" % (name, os.path.basename(out), no))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
