# -*- coding: utf-8 -*-
"""Verify every chapter's check pages use the verification format and respect the limits."""
import sys, os, io

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "content"))

LIM_CMDS = 6
LIM_CMD_LEN = 88
LIM_CONDS = 4
LIM_LABEL = 20
LIM_EXPECT = 50
LIM_PIT = 46

out = io.StringIO()
tot_pages = 0
legacy = []
issues = []

for n in range(2, 15):
    mod = f"ch{n:02d}"
    path = os.path.join(HERE, "content", mod + ".py")
    if not os.path.exists(path):
        out.write(f"{mod}: MISSING\n")
        continue
    sp = __import__(mod).CHAPTER
    n_ok = 0
    for i, t in enumerate(sp["topics"], 1):
        c = t["check"]
        tag = f"{mod} T{i} {c['title'][:14]}"
        if "items" in c and "commands" not in c:
            legacy.append(tag)
            continue
        if "commands" not in c or "conds" not in c:
            issues.append(f"{tag}: missing commands/conds")
            continue
        n_ok += 1
        tot_pages += 1
        if len(c["commands"]) > LIM_CMDS:
            issues.append(f"{tag}: {len(c['commands'])} commands")
        for cmd in c["commands"]:
            if len(cmd) > LIM_CMD_LEN:
                issues.append(f"{tag}: cmd {len(cmd)} chars")
        if len(c["conds"]) > LIM_CONDS:
            issues.append(f"{tag}: {len(c['conds'])} conds")
        for label, expect in c["conds"]:
            if len(label) > LIM_LABEL:
                issues.append(f"{tag}: label '{label}' {len(label)}")
            if len(expect) > LIM_EXPECT:
                issues.append(f"{tag}: expect {len(expect)} '{expect[:16]}'")
        pits = c.get("pitfalls") or []
        if not 2 <= len(pits) <= 3:
            issues.append(f"{tag}: {len(pits)} pitfalls")
        for p in pits:
            if len(p) > LIM_PIT:
                issues.append(f"{tag}: pitfall {len(p)} '{p[:14]}'")
        for bad in ("自我檢核",):
            if bad in c["title"]:
                issues.append(f"{tag}: title still says {bad}")
    out.write(f"{mod}: {n_ok}/{len(sp['topics'])} converted\n")

out.write("\nconverted check pages: %d\n" % tot_pages)
out.write("still legacy: %d %s\n" % (len(legacy), legacy if legacy else ""))
out.write("issues: %d\n" % len(issues))
for i in issues:
    out.write("  - " + i + "\n")

txt = out.getvalue()
open(os.path.join(HERE, "check_format_report.txt"), "w", encoding="utf-8").write(txt)
print(txt.encode("ascii", "replace").decode())
