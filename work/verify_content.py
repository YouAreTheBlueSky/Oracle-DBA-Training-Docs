# -*- coding: utf-8 -*-
"""Content QA: validate every chapter module against the authoring rules."""
import sys, os, importlib, io

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "content"))
sys.path.insert(0, os.path.join(HERE, "deckkit"))

MODULES = [f"ch{n:02d}" for n in list(range(2, 15)) if n != 1]
out = io.StringIO()
problems = 0

for m in MODULES:
    path = os.path.join(HERE, "content", m + ".py")
    if not os.path.exists(path):
        out.write(f"{m}: MISSING\n")
        problems += 1
        continue
    mod = importlib.import_module(m)
    sp = mod.CHAPTER
    issues = []
    agenda_names = [a[0] for a in sp["agenda"]]
    titles = set()
    for i, t in enumerate(sp["topics"], 1):
        tag = f"  T{i} {t['title'][:16]}"
        if t.get("section") not in agenda_names:
            issues.append(f"{tag}: section '{t.get('section')}' not in agenda")
        if t["title"] in titles:
            issues.append(f"{tag}: duplicate title")
        titles.add(t["title"])
        if len(t["title"]) > 26:
            issues.append(f"{tag}: title too long ({len(t['title'])})")
        c = t.get("concept", {})
        if c:
            if not 4 <= len(c.get("items", [])) <= 5:
                issues.append(f"{tag}: concept items={len(c.get('items', []))}")
            for lead, desc in c.get("items", []):
                if len(lead) > 16:
                    issues.append(f"{tag}: lead too long '{lead}'")
                if len(desc) > 58:
                    issues.append(f"{tag}: desc too long ({len(desc)}) '{desc[:18]}'")
        cd = t.get("code")
        if cd:
            lines = cd["lines"]
            if len(lines) > 12:
                issues.append(f"{tag}: code has {len(lines)} lines")
            for ln in lines:
                if len(ln) > 88:
                    issues.append(f"{tag}: code line {len(ln)} chars")
        ck = t.get("check", {})
        if ck:
            if not 4 <= len(ck.get("items", [])) <= 5:
                issues.append(f"{tag}: check items={len(ck.get('items', []))}")
            if "pitfalls" in ck and len(ck["pitfalls"]) != 3:
                issues.append(f"{tag}: pitfalls={len(ck['pitfalls'])}")
        if not t.get("_note_why"):
            issues.append(f"{tag}: missing _note_why")
    if len(sp["topics"]) % 1:
        pass
    out.write(f"{m}: {len(sp['topics'])} topics, agenda={len(agenda_names)}, "
              f"issues={len(issues)}\n")
    for it in issues:
        out.write(it + "\n")
    problems += len(issues)

open(os.path.join(HERE, "content_qa.txt"), "w", encoding="utf-8").write(out.getvalue())
print(out.getvalue().encode("ascii", "replace").decode())
print("TOTAL ISSUES =", problems)
