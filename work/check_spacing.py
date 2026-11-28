# -*- coding: utf-8 -*-
"""檢查所有 _v2 簡報：同一個文字框內「兩個語句緊鄰卻沒有空行」的頁面。"""
import sys, glob, os, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pptx import Presentation

START = ("SELECT", "WITH ", "INSERT", "UPDATE ", "DELETE ", "MERGE", "CREATE ",
         "ALTER ", "DROP ", "GRANT ", "REVOKE ", "BACKUP ", "RESTORE ", "RECOVER ",
         "SHOW ", "RMAN>", "SQL>", "orapwd", "srvctl", "crsctl", "asmcmd", "sqlplus")
END_RE = re.compile(r";\s*(--.*)?$")


def is_start(t):
    u = (t or "").strip().upper()
    return any(u.startswith(k.upper()) for k in START)


def is_end(t):
    u = (t or "").strip()
    return bool(END_RE.search(u)) or bool(
        re.match(r"^(SHOW|EXIT|HOST|SET|SPOOL|DESC|DESCRIBE)\b", u, re.I))


hits = []
for f in sorted(glob.glob("deliver_beginner/*_v2.pptx")):
    p = Presentation(f)
    for i, s in enumerate(p.slides, 1):
        for sh in p.slides[i - 1].shapes:
            if not sh.has_text_frame:
                continue
            paras = sh.text_frame.paragraphs
            if len(paras) < 3:
                continue
            if not any(r.font.name and "Consolas" in str(r.font.name)
                       for q in paras for r in q.runs):
                continue
            texts = ["".join(r.text for r in q.runs) for q in paras]
            for a, b in zip(range(len(texts) - 1), range(1, len(texts))):
                if is_start(texts[b]) and is_end(texts[a]) and texts[a].strip():
                    hits.append((os.path.basename(f)[:22], i,
                                 texts[a][:26], texts[b][:26]))

print("緊鄰未分開的語句:", len(hits), "處")
for h in hits[:12]:
    print("  %-22s p%-2d  %r → %r" % h)
