# -*- coding: utf-8 -*-
"""把使用者在 v2 簡報手動調整的「程式碼／檢核指令」段落寫回內容模組。

    python work/apply_manual.py ch04 4

作法是比對 first-line：模組裡每個 code.lines / check.commands 的第一個元素，
在使用者檔案中找出對應的文字框，若段落數不同就以使用者的段落取代。
"""
import sys, json, importlib

sys.path.insert(0, "work/content")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation

MOD = sys.argv[1]
DECK = {
    "ch02": r"deliver_beginner\02_Oracle_DBA_建置與日常管理_v2.pptx",
    "ch03": r"deliver_beginner\03_Oracle_DBA_Net_Services_v2.pptx",
    "ch04": r"deliver_beginner\04_Oracle_DBA_備份與復原_v2.pptx",
    "ch05": r"deliver_beginner\05_Oracle_DBA_安全性管理_v2.pptx",
    "ch11": r"deliver_beginner\07_Oracle_DBA_公用程式_v2.pptx",
    "ch12": r"deliver_beginner\08_Oracle_DBA_作業系統與EM工具_v2.pptx",
    "ch13": r"deliver_beginner\09_Oracle_DBA_PLSQL_v2.pptx",
    "ch14": r"deliver_beginner\10_Oracle_DBA_附錄_v2.pptx",
}

mod = importlib.import_module(MOD)
spec = mod.CHAPTER
prs = Presentation(DECK[MOD])
src = open("work/content/%s.py" % MOD, encoding="utf-8").read()


def find_list_span(text, start_pos, key):
    marker = '"%s": [' % key
    i = text.find(marker, start_pos)
    if i < 0:
        raise SystemExit("找不到 %s" % marker)
    open_at = i + len(marker) - 1
    depth, in_str, esc = 0, False, False
    for j in range(open_at, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return open_at, j
    raise SystemExit("括號不匹配")


def norm(t):
    return "".join((t or "").split())


# 收集每頁的文字框段落
pages = []
for sl in prs.slides:
    row = []
    for sh in sl.shapes:
        if sh.has_text_frame:
            row.append(["".join(r.text for r in q.runs) for q in sh.text_frame.paragraphs])
        else:
            row.append(None)
    pages.append(row)

changes = []
for ti, t in enumerate(spec["topics"]):
    for kind, key in (("code", "lines"), ("check", "commands")):
        if kind not in t:
            continue
        target = t[kind][key]
        if not target:
            continue
        first = norm(target[0])
        for pi, paras in enumerate(pages):
            for si, texts in enumerate(paras):
                if not texts:
                    continue
                if norm(texts[0]) != first:
                    continue
                if len(texts) == len(target):
                    continue
                changes.append((pi + 1, ti, kind, key, texts))
                break
            else:
                continue
            break

if not changes:
    print("沒有需要回寫的段落")
    raise SystemExit(0)

titles = [t["title"] for t in spec["topics"]]
for pg, ti, kind, key, texts in sorted(changes, reverse=True):
    tpos = src.find(titles[ti])
    a, b = find_list_span(src, tpos, key)
    inner = src[a + 1:b].split("\n")
    indent = " " * (len(inner[1]) - len(inner[1].lstrip())) if len(inner) > 1 else " " * 22
    body = "\n" + "".join('%s%s,\n' % (indent, json.dumps(x, ensure_ascii=False)) for x in texts)
    src = src[:a + 1] + body + indent + src[b:]
    print("p%-2d → topics[%d].%s.%s：%d 段" % (pg, ti, kind, key, len(texts)))

open("work/content/%s.py" % MOD, "w", encoding="utf-8").write(src)
print("已寫回 work/content/%s.py（%d 處）" % (MOD, len(changes)))
