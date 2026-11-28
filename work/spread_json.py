# -*- coding: utf-8 -*-
"""在 JSON 規格中，為同一文字框內緊鄰的語句插入空行；空間不足時先加高方框。

    python work/spread_json.py 01              # 只報告
    python work/spread_json.py 01 --apply      # 寫回並加高
"""
import sys, json, re

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

START = ("SELECT", "WITH ", "INSERT", "UPDATE ", "DELETE ", "MERGE", "CREATE ",
         "ALTER ", "DROP ", "GRANT ", "REVOKE ", "BACKUP ", "RESTORE ", "RECOVER ",
         "SHOW ", "ARCHIVE LOG LIST", "RMAN>", "SQL>", "orapwd", "srvctl", "crsctl",
         "asmcmd", "sqlplus", "ls ", "df ", "echo ")
END_RE = re.compile(r";\s*(--.*)?$")


def is_start(t):
    u = (t or "").strip().upper()
    return any(u.startswith(k.upper()) for k in START)


def is_end(t):
    u = (t or "").strip()
    if END_RE.search(u):
        return True
    return bool(re.match(r"^(SHOW|EXIT|HOST|SET|SPOOL|DESC|DESCRIBE)\b", u, re.I))


def text_of(p):
    return "".join(r.get("t") or "" for r in (p.get("runs") or []))


def spread(paras):
    out, last = [], None
    for p in paras:
        t = text_of(p)
        fresh = bool(t.strip())
        is_cmt = bool(re.match(r"--(?!-)", t.strip()))
        gap = False
        if fresh and is_start(t) and last is not None and is_end(last):
            gap = True
        if fresh and is_cmt and last is not None and not re.match(r"--(?!-)", last.strip()):
            gap = True
        if gap and (not out or text_of(out[-1]).strip()):
            out.append({"a": "l", "runs": []})
        out.append(p)
        if fresh:
            last = t
    return out


def main():
    spec_path = "work/spec/%s.json" % sys.argv[1]
    apply = "--apply" in sys.argv
    spec = json.load(open(spec_path, encoding="utf-8"))

    for si, sl in enumerate(spec["slides"], 1):
        for sh in sl["shapes"]:
            paras = sh.get("paras") or []
            if len(paras) < 2:
                continue
            texts = [text_of(p) for p in paras]
            if sum(1 for t in texts if is_start(t)) < 2:
                continue
            out = spread(paras)
            if len(out) == len(paras):
                continue
            sizes = [r.get("size") for p in paras for r in (p.get("runs") or [])
                     if r.get("size")]
            size = max(sizes) if sizes else 12.0
            need = len(out) * size * 1.36 / 72.0 + 0.12
            below = [o["y"] for o in sl["shapes"]
                     if o is not sh and o["y"] > sh["y"] + 0.5]
            limit = min(below, default=9.0) - sh["y"] - 0.03
            if need > limit:
                print("p%-2d 跳過（需要 %.2f、上限 %.2f）" % (si, need, limit))
                continue
            grow = max(0.0, need - sh["h"])
            print("p%-2d 加 %d 空行；方框 %.2f → %.2f in"
                  % (si, len(out) - len(paras), sh["h"], min(max(need, sh["h"]), limit)))
            if apply:
                sh["paras"] = out
                sh["h"] = round(min(max(need, sh["h"]), limit), 2)

    if apply:
        json.dump(spec, open(spec_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("已更新", spec_path)


if __name__ == "__main__":
    main()
