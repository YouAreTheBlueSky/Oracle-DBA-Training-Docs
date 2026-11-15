# -*- coding: utf-8 -*-
"""Compare a hand-edited PPTX with what the content module produces, and optionally
write the text changes back into the module.

usage:
  python work/diff_pptx.py ch05 <edited.pptx> [--as 5]          # 只列出差異
  python work/diff_pptx.py ch05 <edited.pptx> [--as 5] --apply  # 回寫模組並重新驗證

Exit codes: 0 = no differences, 1 = differences remain, 2 = usage error.
"""
import os, sys, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, os.path.join(HERE, "content"))
sys.path.insert(0, HERE)

from pptx import Presentation
import build_chapter

MAXLEN = 60


def cut(s):
    s = s.replace("\n", "\\n")
    return s if len(s) <= MAXLEN else s[:MAXLEN] + "…"


def dump(path):
    prs = Presentation(path)
    slides = []
    for idx, s in enumerate(prs.slides, 1):
        shapes = []
        for sh in s.shapes:
            if sh.has_text_frame:
                shapes.append(["".join(r.text for r in p.runs)
                               for p in sh.text_frame.paragraphs])
            else:
                shapes.append(None)
        notes = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
        slides.append({"no": idx, "shapes": shapes, "notes": notes})
    return slides


def diff(a, b):
    """a = freshly built from module, b = user's edited file. Returns (changes, warnings)."""
    changes, warns = [], []
    if len(a) != len(b):
        warns.append(f"頁數不同：模組 {len(a)} 頁，你的檔案 {len(b)} 頁")
    for sa, sb in zip(a, b):
        n = sa["no"]
        if len(sa["shapes"]) != len(sb["shapes"]):
            warns.append(f"第 {n:02d} 頁形狀數不同（{len(sa['shapes'])} vs "
                         f"{len(sb['shapes'])}）——結構被改動，需人工對應")
            continue
        for si, (pa, pb) in enumerate(zip(sa["shapes"], sb["shapes"])):
            if pa is None or pb is None:
                continue
            if len(pa) != len(pb):
                warns.append(f"第 {n:02d} 頁形狀 {si} 段落數不同（{len(pa)} vs {len(pb)}）"
                             f"——結構被改動，需人工對應")
                continue
            for pi, (ta, tb) in enumerate(zip(pa, pb)):
                if ta != tb:
                    changes.append({"slide": n, "shape": si, "para": pi,
                                    "old": ta, "new": tb, "kind": "text"})
        if sa["notes"].strip() != sb["notes"].strip():
            warns.append(f"第 {n:02d} 頁講者備忘有差異（不回寫，請人工確認）")
    return changes, warns


def _literals(s):
    """Possible literal spellings of a string inside the module source."""
    return ['"' + s.replace('"', '\\"') + '"',
            "'" + s.replace("'", "\\'") + "'"]


def apply_changes(mod, changes):
    path = os.path.join(HERE, "content", mod + ".py")
    src = open(path, encoding="utf-8").read()
    applied, skipped = [], []
    for c in changes:
        old, new = c["old"], c["new"]
        if not old.strip():
            skipped.append((c, "原字串為空，無法定位"))
            continue
        hit = None
        for lit in _literals(old):
            if src.count(lit) == 1:
                hit = lit
                break
        if hit is None:
            n = sum(src.count(lit) for lit in _literals(old))
            skipped.append((c, f"模組中找到 {n} 處相同字串，需人工指定"))
            continue
        quote = hit[0]
        replacement = quote + new.replace(quote, "\\" + quote) + quote
        src = src.replace(hit, replacement, 1)
        applied.append(c)
    open(path, "w", encoding="utf-8").write(src)
    return applied, skipped


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    mod, edited = sys.argv[1], sys.argv[2]
    as_no = int(sys.argv[sys.argv.index("--as") + 1]) if "--as" in sys.argv else None
    do_apply = "--apply" in sys.argv

    sp = importlib.import_module(mod).CHAPTER
    if as_no is not None:
        sp["no"] = as_no
        sp["chap_label"] = f"{as_no:02d}"

    os.makedirs(os.path.join(HERE, "proto"), exist_ok=True)
    fresh = os.path.join(HERE, "proto", "_diff_fresh.pptx")

    build_chapter.build(mod, fresh)
    a, b = dump(fresh), dump(edited)
    changes, warns = diff(a, b)

    print(f"比對 {mod}（{sp['no']:02d}）：{len(a)} 頁 vs {len(b)} 頁")
    if not changes and not warns:
        print("沒有差異（兩者一致）")
        return 0

    if changes:
        print(f"\n文字差異 {len(changes)} 處：")
        for c in changes:
            print(f"  第 {c['slide']:02d} 頁｜形狀 {c['shape']}｜段 {c['para']}"
                  f"\n    - {cut(c['old'])}\n    + {cut(c['new'])}")
    if warns:
        print("\n需要人工處理：")
        for w in warns:
            print("  ! " + w)

    if not do_apply:
        print("\n（加 --apply 會把上述文字差異寫回模組並重新驗證）")
        return 1

    applied, skipped = apply_changes(mod, changes)
    print(f"\n回寫模組：成功 {len(applied)} 處，略過 {len(skipped)} 處")
    for c, why in skipped:
        print(f"  - 第 {c['slide']:02d} 頁「{cut(c['old'])[:24]}」：{why}")

    # re-verify: reload the edited module, then rebuild and diff again
    importlib.invalidate_caches()
    mod_obj = importlib.reload(sys.modules[mod])
    sp2 = mod_obj.CHAPTER
    if as_no is not None:
        sp2["no"] = as_no
        sp2["chap_label"] = f"{as_no:02d}"
    build_chapter.build(mod, fresh)
    a2 = dump(fresh)
    changes2, warns2 = diff(a2, b)
    if not changes2 and not warns2:
        print("重新驗證：模組重建後與你的檔案完全一致 ✔")
        return 0
    print(f"重新驗證：仍有 {len(changes2)} 處文字差異、{len(warns2)} 項警告")
    for c in changes2:
        print(f"  - 第 {c['slide']:02d} 頁｜{cut(c['old'])} → {cut(c['new'])}")
    for w in warns2:
        print("  ! " + w)
    return 1


if __name__ == "__main__":
    sys.exit(main())
