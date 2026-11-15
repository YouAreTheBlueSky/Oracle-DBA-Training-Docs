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


def count_pages(spec):
    n = 2  # cover + agenda
    for t in spec["topics"]:
        for key in ("concept", "code", "check", "table", "diagram"):
            if key in t:
                n += 1
    n += 2  # summary + refs
    return n


def build(mod_name, out_path, template=TEMPLATE):
    base.WARNINGS.clear()
    mod = importlib.import_module(mod_name)
    spec = mod.CHAPTER
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
