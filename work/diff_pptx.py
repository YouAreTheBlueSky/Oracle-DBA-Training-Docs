# -*- coding: utf-8 -*-
"""Compare a hand-edited PPTX with what the content module produces, and optionally
write the changes back into the module.

Recognises text changes AND formatting changes (bold / underline) on otherwise
identical text; formatting is written back as inline markup (**bold**, __underline__).

usage:
  python work/diff_pptx.py ch05 <edited.pptx> [--as 5]          # 只列出差異
  python work/diff_pptx.py ch05 <edited.pptx> [--as 5] --apply  # 回寫模組並重新驗證

Exit codes: 0 = no differences, 1 = differences remain, 3 = applied but format warnings.
"""
import os, sys, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, os.path.join(HERE, "content"))
sys.path.insert(0, HERE)

from pptx import Presentation
import build_chapter
from base import strip_markup

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MAXLEN = 60


def cut(s):
    s = s.replace("\n", "\\n")
    return s if len(s) <= MAXLEN else s[:MAXLEN] + "…"


# ---------------------------------------------------------------- rich text
def para_runs(p):
    return [(r.text, bool(r.font.bold), bool(r.font.underline)) for r in p.runs]


def plain(runs):
    return "".join(t for t, _b, _u in runs)


def default_style(runs):
    total = sum(len(t) for t, _b, _u in runs) or 1
    b = sum(len(t) for t, bb, _u in runs if bb) * 2 > total
    u = sum(len(t) for t, _b, uu in runs if uu) * 2 > total
    return b, u


def markup(runs, def_b, def_u):
    out = []
    for t, b, u in runs:
        if not t:
            continue
        mb, mu = (b != def_b), (u != def_u)
        if mb and mu:
            out.append("***%s***" % t)
        elif mb:
            out.append("**%s**" % t)
        elif mu:
            out.append("__%s__" % t)
        else:
            out.append(t)
    return "".join(out)


def strip_prefix(runs):
    """Renderer prepends "× " to pitfalls; the module stores only the text."""
    if runs and runs[0][0] == "× ":
        return runs[1:], "× "
    return runs, ""


def norm_notes(text):
    """備忘比對時忽略多餘空行與行尾空白（內容相同即可）。"""
    out, blank = [], False
    for line in text.splitlines():
        line = line.rstrip()
        if line == "":
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(line)
            blank = False
    return "\n".join(out).strip()


def dump(path):
    prs = Presentation(path)
    slides = []
    for idx, s in enumerate(prs.slides, 1):
        shapes = []
        for sh in s.shapes:
            if sh.has_text_frame:
                shapes.append([para_runs(p) for p in sh.text_frame.paragraphs])
            else:
                shapes.append(None)
        notes = s.notes_slide.notes_text_frame.text if s.has_notes_slide else ""
        slides.append({"no": idx, "shapes": shapes, "notes": notes})
    return slides


def diff(a, b):
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
            for pi, (ra, rb) in enumerate(zip(pa, pb)):
                ra2, _pre = strip_prefix(ra)
                rb2, _pre2 = strip_prefix(rb)
                ta, tb = plain(ra2), plain(rb2)
                # 你在 PPTX 直接打的 **粗體**／__底線__ 標記，比對時視為同一段文字
                if strip_markup(ta) != strip_markup(tb):
                    changes.append({"slide": n, "shape": si, "para": pi,
                                    "old": ta, "new": tb, "kind": "text"})
                    continue
                db, du = default_style(ra2)
                ma, mb = markup(ra2, db, du), markup(rb2, db, du)
                if ma != mb:
                    changes.append({"slide": n, "shape": si, "para": pi,
                                    "old": ta, "new": mb, "kind": "format"})
        if norm_notes(sa["notes"]) != norm_notes(sb["notes"]):
            warns.append(f"第 {n:02d} 頁講者備忘有差異（不回寫，請人工確認）")
    return changes, warns


def _literals(s):
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

    use_v2 = "--theme" in sys.argv and sys.argv[sys.argv.index("--theme") + 1] == "v2"
    if use_v2:
        import theme_v2
        import build_theme_v2
        mod_obj0 = importlib.import_module(mod)
        spec0 = mod_obj0.CHAPTER
        if as_no is not None:
            spec0["no"] = as_no
            spec0["chap_label"] = "%02d" % as_no
        build_theme_v2.apply_overrides(mod_obj0, spec0)
        theme_v2.build_v2(spec0, fresh)
    else:
        build_chapter.build(mod, fresh, force=True)
    a, b = dump(fresh), dump(edited)
    changes, warns = diff(a, b)

    print(f"比對 {mod}（{sp['no']:02d}）：{len(a)} 頁 vs {len(b)} 頁")
    if not changes and not warns:
        print("沒有差異（兩者一致）")
        return 0

    if changes:
        txt_c = [c for c in changes if c["kind"] == "text"]
        fmt_c = [c for c in changes if c["kind"] == "format"]
        print(f"\n文字差異 {len(txt_c)} 處、格式差異（粗體／底線）{len(fmt_c)} 處：")
        for c in changes:
            tag = "文字" if c["kind"] == "text" else "格式"
            print(f"  [{tag}] 第 {c['slide']:02d} 頁｜形狀 {c['shape']}｜段 {c['para']}"
                  f"\n    - {cut(c['old'])}\n    + {cut(c['new'])}")
    if warns:
        print("\n需要人工處理：")
        for w in warns:
            print("  ! " + w)

    if not do_apply:
        print("\n（加 --apply 會把上述差異寫回模組並重新驗證）")
        return 1

    applied, skipped = apply_changes(mod, changes)
    print(f"\n回寫模組：成功 {len(applied)} 處，略過 {len(skipped)} 處")
    for c, why in skipped:
        print(f"  - 第 {c['slide']:02d} 頁「{cut(c['old'])[:24]}」：{why}")

    importlib.invalidate_caches()
    mod_obj = importlib.reload(sys.modules[mod])
    sp2 = mod_obj.CHAPTER
    if as_no is not None:
        sp2["no"] = as_no
        sp2["chap_label"] = f"{as_no:02d}"
    if use_v2:
        import theme_v2
        import build_theme_v2
        spec2 = mod_obj.CHAPTER
        if as_no is not None:
            spec2["no"] = as_no
            spec2["chap_label"] = "%02d" % as_no
        build_theme_v2.apply_overrides(mod_obj, spec2)
        theme_v2.build_v2(spec2, fresh)
        warns_build = []
    else:
        _, warns_build = build_chapter.build(mod, fresh, force=True)
    a2 = dump(fresh)
    changes2, warns2 = diff(a2, b)
    if not changes2 and not warns2:
        print("重新驗證：模組重建後與你的檔案完全一致 [OK]")
        import verify_check_format as fmt
        issues = fmt.check_module(mod)
        if issues:
            print(f"\n體例提醒：有 {len(issues)} 項超出建議長度（版面可能變擠或自動縮字）")
            for it in issues:
                print("  ⚠ " + it)
            print("  建議改寫精簡，或把一條拆成兩條（告訴我即可）")
            return 3
        print("體例檢查：指令與條件長度都在上限內 [OK]")
        condensed = [w for w in warns_build if "condensed" in w]
        if condensed:
            print("\n版面警告：")
            for w in condensed:
                print("  ! " + w)
        return 0
    print(f"重新驗證：仍有 {len(changes2)} 處差異、{len(warns2)} 項警告")
    for c in changes2:
        print(f"  - [{c['kind']}] 第 {c['slide']:02d} 頁｜{cut(c['old'])} → {cut(c['new'])}")
    for w in warns2:
        print("  ! " + w)
    return 1


if __name__ == "__main__":
    sys.exit(main())
