"""Build one chapter PPTX from a content module.

usage: python work/build_chapter.py <content_module> <output.pptx>
   e.g. python work/build_chapter.py ch02 out/CH02_fundamentals.pptx
"""
import sys, os, importlib, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "deckkit"))
sys.path.insert(0, os.path.join(HERE, "content"))

import base
from slides import Chapter

TEMPLATE = os.path.join(os.path.dirname(HERE), "Oracle_Storage_Memory_Process_zhTW.pptx")
FROZEN_FILE = os.path.join(HERE, "FROZEN.txt")


def frozen_names():
    """Files the user has hand-edited; builds must not overwrite them."""
    if not os.path.exists(FROZEN_FILE):
        return set()
    names = set()
    for line in open(FROZEN_FILE, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line)
    return names


def count_pages(spec):
    n = 2  # cover + agenda
    for t in spec["topics"]:
        for key in ("concept", "code", "check", "table", "diagram"):
            if key in t:
                n += 1
    n += 1  # summary
    if not spec.get("skip_refs"):
        n += 1  # refs
    return n




def _matches_head(path):
    """檔案內容與 git HEAD 相同 → 代表你的手改已提交，可以安全重建。"""
    import subprocess
    try:
        root = os.path.dirname(HERE)
        rel = os.path.relpath(os.path.abspath(path), root).replace("\\", "/")
        out = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True)
        if out.returncode != 0:
            return False
        with open(path, "rb") as f:
            return f.read() == out.stdout
    except Exception:
        return False



def build(mod_name, out_path, template=TEMPLATE, force=False):
    base.WARNINGS.clear()
    if not force and os.path.exists(out_path) and not _matches_head(out_path):
        raise SystemExit(
            f"拒絕覆蓋：{os.path.basename(out_path)} 與最後一次 commit 不同（可能有未提交的手改）。\n"
            f"  請先執行 work/diff_pptx.py 比對並 --apply、或把檔案 commit，或加 --force 強制覆蓋。")
    if not force and os.path.basename(out_path) in frozen_names() and os.path.exists(out_path):
        from pptx import Presentation
        n = len(Presentation(out_path).slides)
        print(f"SKIP (frozen) {out_path} — kept as-is ({n} slides)")
        return n, ["FROZEN: not rebuilt"]
    mod = importlib.import_module(mod_name)
    spec = mod.CHAPTER
    overrides = getattr(mod, "NOTE_OVERRIDES", {})
    for (ti, kind), val in overrides.items():
        if not (0 <= ti < len(spec["topics"]) and kind in spec["topics"][ti]):
            continue
        target = spec["topics"][ti][kind]
        if isinstance(val, dict):
            mode, text = val.get("mode", "replace"), val.get("text", "")
        else:
            mode, text = "replace", val
        if mode == "prepend":
            target["_note_pre"] = text          # 放在【講解重點】之前
        else:
            target["_note_replace"] = text      # 整段取代

    spec["page_count"] = count_pages(spec)
    ch = Chapter(spec, template)

    ch.cover()
    ch.agenda()
    for i, t in enumerate(spec["topics"]):
        if "concept" in t:
            ch.concept(t, i)
        # the middle slide is the evidence slide: code, table or diagram
        if "code" in t:
            ch.code(t, i)
        elif "table" in t:
            ch.table_slide(t, i)
        elif "diagram" in t:
            ch.diagram(t, i)
        if "check" in t:
            ch.check(t, i)
    ch.summary()
    if not spec.get("skip_refs"):
        ch.refs()

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    ch.prs.save(out_path)

    actual = len(ch.prs.slides)
    status = "OK " if actual == spec["page_count"] else "MISMATCH"
    print(f"{status} {mod_name}: {actual} slides (expected {spec['page_count']}) -> {out_path}")
    if base.WARNINGS:
        print(f"  {len(base.WARNINGS)} layout warnings:")
        for w in base.WARNINGS:
            print("   -", w)
    else:
        print("  no layout warnings")
    return actual, list(base.WARNINGS)


if __name__ == "__main__":
    mod_name, out_path = sys.argv[1], sys.argv[2]
    try:
        build(mod_name, out_path)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
