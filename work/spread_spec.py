# -*- coding: utf-8 -*-
"""在 JSON 規格中，為「同一文字框內緊鄰的 SQL 語句」插入空行（空間夠才插）。"""
import sys, json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

START = ("SELECT", "WITH ", "INSERT", "UPDATE ", "DELETE ", "MERGE", "CREATE ",
         "ALTER ", "DROP ", "GRANT ", "REVOKE ", "BACKUP ", "RESTORE ", "RECOVER ",
         "SHOW ", "RMAN>", "SQL>", "orapwd", "srvctl", "crsctl", "asmcmd", "sqlplus")


def is_end(t):
    import re
    u = (t or "").strip()
    if re.search(r";\s*(--.*)?$", u):
        return True
    return bool(re.match(r"^(SHOW|EXIT|HOST|SET|SPOOL|DESC|DESCRIBE)\b", u, re.I))


def is_start(t):
    u = (t or "").strip().upper()
    return any(u.startswith(k.upper()) for k in START)


def para_text(p):
    return "".join((r.get("t") or "") for r in (p.get("runs") or []))


def process(path):
    spec = json.load(open(path, encoding="utf-8"))
    inserted = 0
    skipped = 0
    for sl in spec["slides"]:
        for sh in sl["shapes"]:
            paras = sh.get("paras") or []
            if len(paras) < 4:
                continue
            texts = [para_text(p) for p in paras]
            if sum(1 for t in texts if is_start(t)) < 2:
                continue
            out, last = [], None
            for p, t in zip(paras, texts):
                fresh = bool(t.strip())
                if (fresh and is_start(t) and last is not None
                        and is_end(last)
                        and (not out or para_text(out[-1]).strip())):
                    out.append({"a": "l", "runs": []})
                out.append(p)
                if fresh:
                    last = t
            if len(out) == len(paras):
                continue
            # 空間檢查：以字級估每行高度
            sizes = [r.get("size") for p in paras for r in (p.get("runs") or [])
                     if r.get("size")]
            size = max(sizes) if sizes else 12.0
            need = len(out) * size * 1.40 / 72.0
            avail = sh["h"] - ((sh.get("ins") or {}).get("tIns", 0)
                               + (sh.get("ins") or {}).get("bIns", 0)) - 0.12
            if need > avail:
                skipped += 1
                continue
            sh["paras"] = out
            inserted += len(out) - len(paras)
    json.dump(spec, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s：插入 %d 個空行；%d 個文字框空間不足未處理" % (path, inserted, skipped))


if __name__ == "__main__":
    for f in sys.argv[1:]:
        process(f)
