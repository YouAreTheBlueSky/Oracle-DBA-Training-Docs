import json, re, os
d = json.load(open("work/pdf_pages.json", encoding="utf-8"))
parts = {3:(238,247),4:(247,311),5:(311,340),6:(340,396),7:(396,410),8:(410,529),
         9:(529,551),10:(551,556),11:(556,582),12:(582,596),13:(596,674),14:(674,708)}
os.makedirs("work/extract", exist_ok=True)
meta = []
for ch,(a,b) in parts.items():
    out=[]
    for p in range(a,b):
        out.append(f"\n===== p{p} =====")
        for y,line in d[str(p)]:
            s=line.strip()
            if not s: continue
            if re.match(r"^Page\s+\d+\s+Oracle DBA Code Examples", s): continue
            if s.startswith("Oracle DBA Code Examples"): continue
            out.append(line.rstrip())
    fn = f"work/extract/ch{ch:02d}.txt"
    open(fn,"w",encoding="utf-8").write("\n".join(out))
    meta.append(f"ch{ch:02d} p{a}-{b-1} lines={len(out)}")
open("work/extract/README.txt","w",encoding="utf-8").write("\n".join(meta))
print("\n".join(meta))
