# -*- coding: utf-8 -*-
"""第 1 章 p8/p9/p28：把程式碼方框加高，並在語句之間插入空行。"""
import sys, json, re

END_RE = r"^(SHOW|ARCHIVE\s+LOG\s+LIST|EXIT|HOST|SET|SPOOL|DESC|DESCRIBE)\b"

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SPEC = "work/spec/01.json"
PAGES = (8, 9, 28)
START = ("SELECT", "SHOW ", "ARCHIVE ", "WITH ", "GRANT ", "ALTER ", "CREATE ")


def is_end(t):
    u = (t or "").strip()
    if u.endswith(";"):
        return True
    return bool(re.match(END_RE, u, re.I))


def is_start(t):
    u = (t or "").strip().upper()
    return any(u.startswith(k) for k in START)


def text_of(p):
    return "".join(r.get("t") or "" for r in (p.get("runs") or []))


spec = json.load(open(SPEC, encoding="utf-8"))
for pg in PAGES:
    sl = spec["slides"][pg - 1]
    for sh in sl["shapes"]:
        paras = sh.get("paras") or []
        texts = [text_of(p) for p in paras]
        if sum(1 for t in texts if is_start(t)) < 2:
            continue

        # 1) 先算出加空行後的段落數
        out, last = [], None
        for p, t in zip(paras, texts):
            fresh = bool(t.strip())
            if (fresh and is_start(t) and last is not None
                    and is_end(last)
                    and (not out or text_of(out[-1]).strip())):
                out.append({"a": "l", "runs": []})
            out.append(p)
            if fresh:
                last = t

        sizes = [r.get("size") for p in paras for r in (p.get("runs") or []) if r.get("size")]
        size = max(sizes) if sizes else 12.0
        need = len(out) * size * 1.34 / 72.0 + 0.12

        # 2) 加高方框（上限：不碰到下方的說明文字）
        below = [o for o in sl["shapes"] if o is not sh and o["y"] > sh["y"] + 0.5]
        limit = min((o["y"] for o in below), default=9.0) - sh["y"] - 0.06
        new_h = min(max(need, sh["h"]), limit)
        old_h = sh["h"]
        sh["h"] = round(new_h, 2)
        sh["paras"] = out
        print("p%-2d 方框 %.2f → %.2f in（需要 %.2f）｜插入 %d 空行"
              % (pg, old_h, sh["h"], need, len(out) - len(paras)))

json.dump(spec, open(SPEC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已更新", SPEC)
