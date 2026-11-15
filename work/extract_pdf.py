"""Minimal layout-aware text extractor for the Oracle DBA Code Examples PDF.

Strategy: every page's content stream carries a "(Page N )" label, so page order can be
derived from the label itself. Text is reconstructed from the text matrix (Tm/Td/TD/T*),
grouped into lines by baseline y, and ordered by x with gap-derived spacing.
"""
import re, zlib, sys, json, collections

PDF = r"oracle_dba_code_examples.pdf"
data = open(PDF, "rb").read()

# ---------------------------------------------------------------- stream inventory
streams = []
for m in re.finditer(rb"stream\r?\n", data):
    start = m.end()
    end = data.find(b"endstream", start)
    if end == -1:
        continue
    raw = data[start:end]
    try:
        streams.append(zlib.decompress(raw))
    except Exception:
        pass

# ---------------------------------------------------------------- ToUnicode CMaps
cid_map = {}
for s in streams:
    if b"beginbfchar" in s or b"beginbfrange" in s:
        for blk in re.findall(rb"beginbfchar(.*?)endbfchar", s, re.S):
            for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                try:
                    cid_map[int(src, 16)] = bytes.fromhex(dst.decode()).decode("utf-16-be", "replace")
                except Exception:
                    pass
        for blk in re.findall(rb"beginbfrange(.*?)endbfrange", s, re.S):
            for lo, hi, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", blk):
                lo, hi = int(lo, 16), int(hi, 16)
                base = bytes.fromhex(dst.decode()).decode("utf-16-be", "replace")
                for i in range(hi - lo + 1):
                    if ord(base[0]) + i <= 0x10FFFF:
                        cid_map[lo + i] = chr(ord(base[0]) + i)

# ---------------------------------------------------------------- tokenizer
TOKEN = re.compile(
    rb"""
    (?P<ws>\s+)
  | (?P<comment>%[^\r\n]*)
  | (?P<str>\()          # literal string, handled by scanner
  | (?P<hex><[0-9A-Fa-f\s]*>)
  | (?P<name>/[^\s/\[\]<>(){}]+)
  | (?P<num>[-+]?(?:\d+\.\d*|\.\d+|\d+))
  | (?P<arr>[\[\]])
  | (?P<dict><<|>>)
  | (?P<op>[A-Za-z'"*][A-Za-z0-9'"*]*)
    """,
    re.X | re.S,
)

ESC = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f",
       b"(": b"(", b")": b")", b"\\": b"\\"}


def read_literal(buf, i):
    """buf[i] == '(' ; return (bytes, next_index)."""
    depth = 1
    i += 1
    out = bytearray()
    n = len(buf)
    while i < n:
        c = buf[i:i + 1]
        if c == b"\\":
            nxt = buf[i + 1:i + 2]
            if nxt in ESC:
                out += ESC[nxt]
                i += 2
            elif nxt.isdigit():
                oct_digits = b""
                i += 1
                while len(oct_digits) < 3 and buf[i:i + 1].isdigit():
                    oct_digits += buf[i:i + 1]
                    i += 1
                out.append(int(oct_digits, 8) & 0xFF)
            elif nxt in (b"\r", b"\n"):
                i += 2
                if nxt == b"\r" and buf[i:i + 1] == b"\n":
                    i += 1
            else:
                out += nxt
                i += 2
        elif c == b"(":
            depth += 1
            out += c
            i += 1
        elif c == b")":
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
            out += c
            i += 1
        else:
            out += c
            i += 1
    return bytes(out), i


def decode_str(raw, is_hex):
    if is_hex:
        h = re.sub(rb"[^0-9A-Fa-f]", b"", raw)
        if len(h) % 2:
            h += b"0"
        b = bytes.fromhex(h.decode())
        # Identity-H: two-byte codes
        if b and any(c >= 0x80 or c == 0 for c in b):
            chars = []
            for j in range(0, len(b) - 1, 2):
                code = (b[j] << 8) | b[j + 1]
                chars.append(cid_map.get(code, ""))
            if any(chars):
                return "".join(chars)
        return b.decode("cp1252", "replace")
    return raw.decode("cp1252", "replace")


def mat_mul(a, b):
    return [a[0] * b[0] + a[1] * b[2], a[0] * b[1] + a[1] * b[3],
            a[2] * b[0] + a[3] * b[2], a[2] * b[1] + a[3] * b[3],
            a[4] * b[0] + a[5] * b[2] + b[4], a[4] * b[1] + a[5] * b[3] + b[5]]


def extract(stream):
    """Return list of (y, x, fontsize, text) show operations in stream order."""
    out = []
    tm = [1, 0, 0, 1, 0, 0]
    tlm = list(tm)
    ctm = [1, 0, 0, 1, 0, 0]
    leading = 0.0
    fsize = 10.0
    i = 0
    n = len(stream)
    pending = []          # operand stack
    gstack = []
    while i < n:
        m = TOKEN.match(stream, i)
        if not m:
            i += 1
            continue
        i = m.end()
        kind = m.lastgroup
        if kind in ("ws", "comment"):
            continue
        if kind == "str":
            # rewind one char: TOKEN matched '(' only
            s, i = read_literal(stream, m.start())
            pending.append(("str", s))
            continue
        tok = m.group()
        if kind == "hex":
            pending.append(("hex", tok))
        elif kind == "num":
            pending.append(("num", float(tok)))
        elif kind in ("name", "arr", "dict"):
            pending.append((kind, tok))
        else:  # operator
            op = tok.decode("latin1")
            if op == "BT":
                tm = [1, 0, 0, 1, 0, 0]
                tlm = list(tm)
            elif op == "Tm" and len(pending) >= 6:
                vals = [p[1] for p in pending[-6:] if p[0] == "num"]
                if len(vals) == 6:
                    tm = vals
                    tlm = list(vals)
            elif op in ("Td", "TD") and len(pending) >= 2:
                vals = [p[1] for p in pending[-2:] if p[0] == "num"]
                if len(vals) == 2:
                    tx, ty = vals
                    if op == "TD":
                        leading = -ty
                    tlm = mat_mul([1, 0, 0, 1, tx, ty], tlm)
                    tm = list(tlm)
            elif op == "T*":
                tlm = mat_mul([1, 0, 0, 1, 0, -leading], tlm)
                tm = list(tlm)
            elif op == "TL" and pending and pending[-1][0] == "num":
                leading = pending[-1][1]
            elif op == "Tf":
                nums = [p[1] for p in pending if p[0] == "num"]
                if nums:
                    fsize = nums[-1]
            elif op == "q":
                gstack.append(list(ctm))
            elif op == "Q":
                if gstack:
                    ctm = gstack.pop()
            elif op == "cm" and len(pending) >= 6:
                vals = [p[1] for p in pending[-6:] if p[0] == "num"]
                if len(vals) == 6:
                    ctm = mat_mul(vals, ctm)
            elif op in ("Tj", "'", '"'):
                if op in ("'", '"'):
                    tlm = mat_mul([1, 0, 0, 1, 0, -leading], tlm)
                    tm = list(tlm)
                for k in range(len(pending) - 1, -1, -1):
                    if pending[k][0] in ("str", "hex"):
                        raw, is_hex = pending[k][1], pending[k][0] == "hex"
                        txt = decode_str(raw, is_hex)
                        out.append((round(tm[5], 1), round(tm[4], 1), fsize, txt, ctm[4], ctm[5]))
                        break
            elif op == "TJ":
                if pending and pending[-1][0] == "arr":
                    pass
                # find last array: tokens between [ and ]
                # rebuild by scanning back for matching bracket
                depth = 0
                j = len(pending) - 1
                start = None
                while j >= 0:
                    if pending[j][0] == "arr" and pending[j][1] == b"]":
                        depth += 1
                        if depth == 1:
                            end_idx = j
                    elif pending[j][0] == "arr" and pending[j][1] == b"[":
                        depth -= 1
                        if depth == 0:
                            start = j
                            break
                    j -= 1
                if start is not None and end_idx is not None:
                    items = pending[start + 1:end_idx]
                    buf = []
                    for it in items:
                        if it[0] == "str":
                            buf.append(decode_str(it[1], False))
                        elif it[0] == "hex":
                            buf.append(decode_str(it[1], True))
                        elif it[0] == "num":
                            if it[1] < -120:
                                buf.append(" ")
                    txt = "".join(buf)
                    if txt:
                        out.append((round(tm[5], 1), round(tm[4], 1), fsize, txt, ctm[4], ctm[5]))
            pending = []
    return out


# ---------------------------------------------------------------- page assembly
pages = {}
nopage = {}
for idx, s in enumerate(streams):
    if b"BT" not in s or (b"Tj" not in s and b"TJ" not in s):
        continue
    runs = extract(s)
    if not runs:
        continue
    joined = "".join(r[3] for r in runs)
    m = re.search(r"Page\s+(\d+)", joined)
    if m:
        pages[int(m.group(1))] = runs
    else:
        nopage[idx] = runs

print("pages with label:", len(pages), "min", min(pages), "max", max(pages))
print("streams without page label:", len(nopage), [len(v) for v in nopage.values()][:10])

# ---------------------------------------------------------------- line building
def build_lines(runs):
    """Group runs by baseline, order by x, derive spacing from gaps."""
    if not runs:
        return []
    # effective x = text matrix e*? For our simple doc, x offset is tm[4]; use it.
    items = []
    for y, x, fs, txt, cx, cy in runs:
        if not txt:
            continue
        items.append([y, x, fs, txt])
    # cluster by y
    items.sort(key=lambda r: (-r[0], r[1]))
    lines = []
    cur = []
    cur_y = None
    for it in items:
        if cur_y is None or abs(it[0] - cur_y) <= 2.0:
            cur.append(it)
            cur_y = it[0] if cur_y is None else cur_y
        else:
            lines.append(cur)
            cur = [it]
            cur_y = it[0]
    if cur:
        lines.append(cur)

    out_lines = []
    for ln in lines:
        ln.sort(key=lambda r: r[1])
        parts = []
        prev_end = None
        for y, x, fs, txt in ln:
            if prev_end is None:
                parts.append(txt)
            else:
                gap = x - prev_end
                avg_w = max(fs * 0.5, 1.0)
                spaces = int(round(gap / avg_w))
                if spaces > 0:
                    parts.append(" " * min(spaces, 40))
                elif gap < -avg_w * 0.3:
                    parts.append(" ")
                parts.append(txt)
            prev_end = x + len(txt) * fs * 0.5
        out_lines.append((ln[0][0], "".join(parts).rstrip()))
    return out_lines


export = {}
for p in sorted(pages):
    export[p] = build_lines(pages[p])

with open("work/pdf_pages.json", "w", encoding="utf-8") as f:
    json.dump({str(k): v for k, v in export.items()}, f, ensure_ascii=False, indent=0)

with open("work/pdf_text.txt", "w", encoding="utf-8") as f:
    for p in sorted(export):
        f.write(f"\n\n===== PDF PAGE {p} =====\n")
        for y, line in export[p]:
            f.write(line + "\n")

print("wrote work/pdf_text.txt")
print("total lines:", sum(len(v) for v in export.values()))
