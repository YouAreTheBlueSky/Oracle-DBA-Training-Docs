# -*- coding: utf-8 -*-
"""Verify every chapter's check pages use the verification format and respect the limits.

CLI:  python work/verify_check_format.py [ch05 ...]
API:  check_module("ch05") -> list[str]
"""
import sys, os, importlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "content"))

LIM_CMDS = 6
LIM_CMD_LEN = 88
LIM_CONDS = 4
LIM_LABEL = 20
LIM_EXPECT = 50
LIM_PIT = 46


def check_module(name):
    """Return a list of format issues for one chapter module (empty = clean)."""
    path = os.path.join(HERE, "content", name + ".py")
    if not os.path.exists(path):
        return [f"{name}: MISSING"]
    sp = importlib.import_module(name).CHAPTER
    issues = []
    for i, t in enumerate(sp["topics"], 1):
        c = t["check"]
        tag = f"{name} T{i} {c['title'][:16]}"
        if "items" in c and "commands" not in c:
            issues.append(f"{tag}: 還是舊格式（items）")
            continue
        if "commands" not in c or "conds" not in c:
            issues.append(f"{tag}: 缺少 commands／conds")
            continue
        if len(c["commands"]) > LIM_CMDS:
            issues.append(f"{tag}: 指令 {len(c['commands'])} 行（上限 {LIM_CMDS}）")
        for cmd in c["commands"]:
            if len(cmd) > LIM_CMD_LEN:
                issues.append(f"{tag}: 指令 {len(cmd)} 字元（上限 {LIM_CMD_LEN}）：{cmd[:24]}…")
        if len(c["conds"]) > LIM_CONDS:
            issues.append(f"{tag}: 通過條件 {len(c['conds'])} 條（上限 {LIM_CONDS}）")
        for label, expect in c["conds"]:
            if len(label) > LIM_LABEL:
                issues.append(f"{tag}: 標籤「{label}」{len(label)} 字（上限 {LIM_LABEL}）")
            if len(expect) > LIM_EXPECT:
                issues.append(f"{tag}: 說明 {len(expect)} 字（上限 {LIM_EXPECT}）：{expect[:20]}…")
        pits = c.get("pitfalls") or []
        if not 2 <= len(pits) <= 3:
            issues.append(f"{tag}: 常見錯誤 {len(pits)} 條（應為 2–3）")
        for p in pits:
            if len(p) > LIM_PIT:
                issues.append(f"{tag}: 常見錯誤 {len(p)} 字（上限 {LIM_PIT}）：{p[:20]}…")
        if "自我檢核" in c["title"]:
            issues.append(f"{tag}: 標題仍含「自我檢核」")
    return issues


def report(names=None):
    names = names or [f"ch{n:02d}" for n in range(2, 15)]
    total_pages = total_issues = 0
    lines = []
    for name in names:
        path = os.path.join(HERE, "content", name + ".py")
        if not os.path.exists(path):
            lines.append(f"{name}: MISSING")
            continue
        sp = importlib.import_module(name).CHAPTER
        issues = check_module(name)
        conv = sum(1 for t in sp["topics"]
                   if "commands" in t["check"] and "conds" in t["check"])
        total_pages += conv
        total_issues += len(issues)
        lines.append(f"{name}: {conv}/{len(sp['topics'])} converted, issues={len(issues)}")
        for it in issues:
            lines.append("  - " + it)
    lines.append("")
    lines.append(f"converted check pages: {total_pages}")
    lines.append(f"issues: {total_issues}")
    txt = "\n".join(lines)
    open(os.path.join(HERE, "check_format_report.txt"), "w", encoding="utf-8").write(txt)
    print(txt.encode("ascii", "replace").decode())
    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(report(sys.argv[1:] or None))
