"""Slide renderers for the six recurring page patterns of the template."""
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.enum.shapes import MSO_CONNECTOR
from base import (C, ZH, MONO, LEFT, WIDTH, TITLE_TOP, BODY_TOP, BODY_BOTTOM,
                  LINE_BODY, LINE_CODE,
                  blank_deck, textbox, para, rect, hline, title, footer, takeaway,
                  warning, notes, table, fit_size, wrap_lines, text_w_pt, warn, _rgb,
                  _set_font, _noline, add_bg, EMU, add_runs)


PIT_BASE = 14.0    # 常見錯誤項目字級（原 13）
PIT_HEAD = 14.5    # 常見錯誤標題字級（原 13.5）


class Chapter:
    """Renders one chapter file from a content dict."""

    def __init__(self, spec, template):
        self.spec = spec
        self.prs = blank_deck(template)
        self.page = 0

    # ---------------------------------------------------------------- helpers
    def _new(self, bg=C["bg"]):
        s = self.prs.slides.add_slide(self.prs.slide_layouts[5])  # Blank
        add_bg(s, bg)
        self.page += 1
        return s

    def _chrome(self, s, section):
        footer(s, section, f"{self.page:02d}", self.spec.get("chap_label", ""))

    def _note_spec(self, topic, slide_spec):
        """topic 提供 _note_why／_note_scope／_refs；單頁可覆寫。"""
        merged = dict(topic)
        if slide_spec.get("_note_replace"):
            merged["_note_why"] = slide_spec["_note_replace"]
        for k in ("_note_why", "_note_scope", "_refs"):
            extra = slide_spec.get(k)
            if not extra:
                continue
            base = merged.get(k)
            if not base:
                merged[k] = extra
            elif k == "_refs":
                merged[k] = list(base) + [r for r in extra if r not in base]
            else:
                merged[k] = extra + "\n" + base   # 單頁補充放在主題備忘之前
        return merged

    def _note(self, s, spec, src):
        try:
            notes(s, spec, self.spec.get("chap_label", ""), src)
        except Exception as exc:      # notes must never break the build
            warn(f"notes failed: {exc}")

    # ---------------------------------------------------------------- cover
    def cover(self):
        sp = self.spec
        s = self._new(C["cover"])
        rect(s, 0.90, 1.02, 0.10, 0.42, fill=C["cover_sub"])
        tb = textbox(s, 1.12, 0.98, 10.0, 0.5)
        para(tb.text_frame, f"CHAPTER {sp['no']:02d}   ｜   {sp['part']}", size=19.0,
             color=C["cover_sub"], bold=True, first=True)

        tb = textbox(s, 0.90, 1.78, 14.9, 1.45)
        para(tb.text_frame, sp["title"], size=fit_size([sp["title"]], 14.9, 54.0, 34.0),
             color=C["white"], bold=True, first=True, line=1.05)

        tb = textbox(s, 0.94, 3.34, 14.6, 0.95)
        para(tb.text_frame, sp["en"], size=fit_size([sp["en"]], 14.6, 30.0, 20.0),
             color=C["cover_meta"], first=True)

        hline(s, 0.94, 4.42, 3.95, 4.42, color=C["teal"], width=2.5)

        tb = textbox(s, 0.94, 4.62, 14.6, 0.55)
        para(tb.text_frame, sp["subtitle"], size=22.0, color=C["cover_meta"], first=True)

        tb = textbox(s, 0.94, 5.22, 14.6, 0.50)
        para(tb.text_frame, f"來源：{sp['source']}　／　本檔共 {sp['page_count']} 頁",
             size=17.0, color="7E9AA0", first=True)

        tb = textbox(s, 0.83, 8.74, 13.2, 0.35)
        para(tb.text_frame, "Oracle Database 19c ｜ DBA 教育訓練教材", size=15.0,
             color=C["body"], first=True)
        tb2 = textbox(s, 14.55, 8.68, 1.30, 0.44)
        para(tb2.text_frame, f"{self.page:02d}", size=19.5, color=C["body"],
             align=PP_ALIGN.RIGHT, first=True)
        self._note(s, {"_note_why": sp.get("note_why"), "_refs": sp.get("refs")},
                   sp["source"])

    # ---------------------------------------------------------------- agenda
    def agenda(self, sec=None):
        sp = self.spec
        s = self._new()
        title(s, "本章大綱", 36.0)
        sec = sec or sp["agenda_title"]
        rows = sp["agenda"]
        n = len(rows)
        area_top, area_bot = 2.15, 7.55
        size_l, size_d = 23.0, 20.0
        gap = 0.10
        heights = []
        for i, (name, desc) in enumerate(rows):
            hd = wrap_lines(desc, 10.4, size_d) * size_d * LINE_BODY / 72.0
            heights.append(max(0.66, hd + 0.24))
        total = sum(heights) + gap * (n - 1)
        avail = area_bot - area_top
        if total > avail:
            k = avail / total
            size_l = max(17.0, size_l * k)
            size_d = max(15.0, size_d * k)
            heights = [h * k for h in heights]
            total = sum(heights) + gap * (n - 1)
        y = area_top
        for i, (name, desc) in enumerate(rows):
            num = textbox(s, 0.85, y + 0.02, 0.80, 0.55)
            para(num.text_frame, f"{i + 1:02d}", size=size_l, color=C["teal"], bold=True,
                 first=True)
            nm = textbox(s, 1.62, y, 3.95, heights[i])
            para(nm.text_frame, name, size=size_l, color=C["ink"], bold=True, first=True)
            ds = textbox(s, 5.72, y + 0.03, 10.1, heights[i])
            para(ds.text_frame, desc, size=size_d, color=C["body"], first=True)
            if i < n - 1:
                hline(s, 0.85, y + heights[i] + gap / 2, 15.7, y + heights[i] + gap / 2,
                      color="E2DFD8", width=0.75)
            y += heights[i] + gap
        self._chrome(s, "本章大綱")
        self._note(s, {"_note_why": sp.get("agenda_note"), "_refs": []}, "")

    # ---------------------------------------------------------------- concept
    def concept(self, t, idx):
        s = self._new()
        c = t["concept"]
        title(s, t["title"])
        items = c["items"]
        avail_h = (6.66 if c.get("note") else 7.55) - BODY_TOP
        lead_x, lead_w = 0.85, 4.45
        desc_x, desc_w = 5.62, 10.15
        size_l, size_d = 21.0, 20.0
        heights = []
        for i, (lead, desc) in enumerate(items):
            hl = wrap_lines(lead, lead_w, size_l) * size_l * LINE_BODY / 72.0
            hd = wrap_lines(desc, desc_w, size_d) * size_d * LINE_BODY / 72.0
            heights.append(max(hl, hd) + 0.30)
        total = sum(heights) + 0.12 * (len(items) - 1)
        if total > avail_h:
            k = avail_h / total
            size_l, size_d = max(15.0, size_l * k), max(14.0, size_d * k)
            heights = [h * k for h in heights]
            total = sum(heights) + 0.12 * (len(items) - 1)
            warn(f"C{self.spec['no']} concept shrunk to {size_d:.1f}pt: {t['title']}")

        y = BODY_TOP + max(0.0, (avail_h - total) / 2.0) if total < avail_h - 0.6 else BODY_TOP
        for i, (lead, desc) in enumerate(items):
            lb = textbox(s, lead_x, y + 0.02, lead_w, heights[i])
            para(lb.text_frame, lead, size=size_l, color=C["teal"], bold=True, first=True)
            db = textbox(s, desc_x, y, desc_w, heights[i])
            para(db.text_frame, desc, size=size_d, color=C["ink"], first=True)
            y += heights[i] + 0.12
        if c.get("note"):
            takeaway(s, c["note"])
        if c.get("warning"):
            warning(s, c["warning"], y=7.86)
            self._chrome(s, t.get("section", ""))
            self._note(s, self._note_spec(t, t["concept"]), t.get("src", ""))
            return
        self._chrome(s, t.get("section", ""))
        self._note(s, self._note_spec(t, t["concept"]), t.get("src", ""))

    # ---------------------------------------------------------------- code
    def code(self, t, idx):
        s = self._new()
        c = t["code"]
        title(s, t.get("code_title") or c.get("title") or t["title"])
        lines = c["lines"]
        # panel geometry
        pad_l, pad_r = 0.25, 0.25
        inner_w = WIDTH - pad_l - pad_r
        size = 21.0
        size = fit_size(lines, inner_w, size, 13.0, mono=True, step=0.5)
        while True:
            lh = size * LINE_CODE / 72.0
            need = 0.21 + len(lines) * lh + 0.19
            if need <= 4.85 or size <= 13.0:
                break
            size -= 0.5
        if size < 21.0:
            warn(f"C{self.spec['no']} code {size}pt ({len(lines)} lines): {t['title']}")
        lh = size * LINE_CODE / 72.0
        panel_h = 0.21 + len(lines) * lh + 0.19
        rect(s, LEFT, BODY_TOP, WIDTH, panel_h, fill=C["panel"])
        tb = textbox(s, LEFT + pad_l, BODY_TOP + 0.19, inner_w, panel_h - 0.38,
                     margins=(0, 0, 0, 0))
        tf = tb.text_frame
        tf.word_wrap = False
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = Pt(size * LINE_CODE)
            add_runs(p, ln if ln else " ", size, C["ink"], False, MONO)
        if c.get("takeaway"):
            takeaway(s, c["takeaway"], y=max(6.86, min(7.02, BODY_TOP + panel_h + 0.36)))
        if c.get("warning"):
            warning(s, c["warning"], y=7.86)
        self._chrome(s, t.get("section", ""))
        self._note(s, self._note_spec(t, t["code"]), t.get("src", ""))

    # ---------------------------------------------------------------- check
    def check(self, t, idx):
        s = self._new()
        c = t["check"]
        title(s, c["title"])
        if c.get("commands") and c.get("conds"):
            self._check_verify(s, c)
        else:
            self._check_legacy(s, c)
        if c.get("warning"):
            warning(s, c["warning"], y=7.86)
        self._chrome(s, t.get("section", ""))
        self._note(s, self._note_spec(t, c), t.get("src", ""))

    def _check_verify(self, s, c):
        """Verification layout: runnable commands + pass conditions + pitfalls."""
        k = float(c.get("style", {}).get("scale", 1.0))
        k_cmd = k * float(c.get("style", {}).get("commands_scale", 1.0))
        k_cond = k * float(c.get("style", {}).get("cond_scale", 1.0))
        lines = c["commands"][:7]
        inner_w = WIDTH - 0.5
        size = fit_size(lines, inner_w, 17.0 * k_cmd, 11.5, mono=True, step=0.5)
        lh = size * LINE_CODE / 72.0
        panel_h = 0.20 + len(lines) * lh + 0.18

        lb = textbox(s, 0.85, 1.82, 6.0, 0.32)
        para(lb.text_frame, "怎麼檢查", size=14.5 * k, color=C["teal"], bold=True, first=True)

        panel_top = 2.16
        rect(s, LEFT, panel_top, WIDTH, panel_h, fill=C["panel"])
        tb = textbox(s, LEFT + 0.24, panel_top + 0.18, inner_w, panel_h - 0.36)
        tf = tb.text_frame
        tf.word_wrap = False
        for i, ln in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.line_spacing = Pt(size * LINE_CODE)
            add_runs(p, ln if ln else " ", size, C["ink"], False, MONO)

        y = panel_top + panel_h + 0.18
        lb2 = textbox(s, 0.85, y, 6.0, 0.32)
        para(lb2.text_frame, "通過條件", size=14.5 * k, color=C["teal"], bold=True, first=True)

        conds = c["conds"][:4]
        pits = (c.get("pitfalls") or [])[:3]
        conds_top = y + 0.36
        bottom = 7.34 if c.get("warning") else 7.56
        label_w, label_x = 2.55, 0.85
        expect_x, expect_w = 3.50, 7.10

        size_l, size_e = 16.5 * k_cond, 16.0 * k_cond
        heights = []
        for look, expect in conds:
            hl = wrap_lines(look, label_w, size_l) * size_l * LINE_BODY / 72.0
            he = wrap_lines(expect, expect_w, size_e) * size_e * LINE_BODY / 72.0
            heights.append(max(0.50, max(hl, he) + 0.14))
        total = sum(heights) + 0.08 * (len(conds) - 1)
        avail = bottom - conds_top
        if total > avail:
            k = avail / total
            heights = [h * k for h in heights]
            size_l, size_e = max(12.5, size_l * k), max(12.0, size_e * k)
            warn(f"C{self.spec['no']} check condensed to {size_e:.1f}pt: {c['title']}")
        total = sum(heights)
        gap = 0.08 if total >= avail else min(0.42, (avail - total) / max(1, len(conds) - 1))

        yy = conds_top
        for (look, expect), h in zip(conds, heights):
            nb = textbox(s, label_x, yy + 0.01, label_w, h)
            para(nb.text_frame, look, size=size_l, color=C["ink"], bold=True, first=True,
                 line=LINE_BODY)
            eb = textbox(s, expect_x, yy, expect_w, h)
            para(eb.text_frame, expect, size=size_e, color=C["body"], first=True,
                 line=LINE_BODY)
            yy += h + gap

        if pits:
            px, pw = 10.95, 4.75
            inner = pw - 0.48
            avail_p = bottom - conds_top
            pk = float(c.get("style", {}).get("pitfall_scale", 1.0))

            def panel_need(scale):
                n = 0.55 * k * scale
                for pt in pits:
                    n += (wrap_lines(pt, inner, PIT_BASE * k * scale)
                          * PIT_BASE * k * scale * LINE_BODY / 72.0 + 0.10 * k * scale)
                return n

            need = panel_need(pk)
            while need > avail_p and pk > 0.85:
                pk -= 0.05
                need = panel_need(pk)
            if need > avail_p:
                warn(f"C{self.spec['no']} pitfall panel overflow: {c['title']}")
            ph = min(need, avail_p)
            rect(s, px, conds_top, pw, ph, fill=C["panel"])
            hb = textbox(s, px + 0.24, conds_top + 0.14, pw - 0.48, 0.32 * k * pk)
            para(hb.text_frame, "常見錯誤", size=PIT_HEAD * k * pk, color=C["warn"],
                 bold=True, first=True)
            pb = textbox(s, px + 0.24, conds_top + 0.52 * k * pk, pw - 0.48,
                         ph - 0.62 * k * pk)
            tf2 = pb.text_frame
            for j, ptext in enumerate(pits):
                p = tf2.paragraphs[0] if j == 0 else tf2.add_paragraph()
                p.line_spacing = Pt(PIT_BASE * k * pk * LINE_BODY)
                p.space_before = Pt(0 if j == 0 else 5)
                r1 = p.add_run()
                r1.text = "× "
                _set_font(r1, ZH, PIT_BASE * k * pk, True, C["warn"])
                add_runs(p, ptext, PIT_BASE * k * pk, C["ink"], False, ZH)
            if abs(pk - float(c.get("style", {}).get("pitfall_scale", 1.0))) > 0.001:
                warn(f"C{self.spec['no']} pitfall scaled to {PIT_BASE*k*pk:.1f}pt: {c['title']}")

    def _check_legacy(self, s, c):
        items = c["items"]
        pits = c.get("pitfalls") or []
        left_w = 9.15 if pits else WIDTH
        size = 19.5
        heights = [max(0.58, wrap_lines(it, left_w - 1.05, size) * size * LINE_BODY / 72.0 + 0.14)
                   for it in items]
        total = sum(heights) + 0.10 * (len(items) - 1)
        avail = (6.60 if c.get("warning") else 7.55) - BODY_TOP
        if total > avail:
            k = avail / total
            size = max(14.0, size * k)
            heights = [h * k for h in heights]
            total = sum(heights) + 0.10 * (len(items) - 1)
            warn(f"C{self.spec['no']} check shrunk {size:.1f}pt: {c['title']}")
        y = BODY_TOP + ((avail - total) / 2.0 if total < avail - 0.9 else 0.10)
        for i, it in enumerate(items):
            nb = textbox(s, 0.85, y + 0.02, 0.62, 0.5)
            para(nb.text_frame, f"{i + 1:02d}", size=size - 3.5, color=C["teal"],
                 bold=True, first=True)
            tb = textbox(s, 1.58, y, left_w - 1.05, heights[i])
            para(tb.text_frame, it, size=size, color=C["ink"], first=True)
            y += heights[i] + 0.10

        if pits:
            px, pw = 10.55, 5.15
            ph = min(max(2.2, total), (6.60 if c.get("warning") else 7.55) - BODY_TOP)
            rect(s, px, BODY_TOP, pw, ph, fill=C["panel"])
            hb = textbox(s, px + 0.28, BODY_TOP + 0.20, pw - 0.56, 0.45)
            para(hb.text_frame, c.get("pitfall_title", "常見錯誤"), size=18.0,
                 color=C["warn"], bold=True, first=True)
            pb = textbox(s, px + 0.28, BODY_TOP + 0.74, pw - 0.56, ph - 0.90)
            tf = pb.text_frame
            psize = 16.0
            for j, pt in enumerate(pits):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.line_spacing = 1.18
                p.space_before = Pt(0 if j == 0 else 7)
                r1 = p.add_run()
                r1.text = "× "
                _set_font(r1, ZH, psize, True, C["warn"])
                add_runs(p, pt, psize, C["ink"], False, ZH)

    # ---------------------------------------------------------------- table
    def table_slide(self, t, idx):
        s = self._new()
        c = t["table"]
        title(s, t["title"])
        header, rows = c["header"], c["rows"]
        nrow = len(rows) + 1
        top = BODY_TOP + 0.02
        bottom = 6.60 if (c.get("note") or c.get("warning")) else 7.60
        row_h = min(1.06, (bottom - top) / nrow)
        size = 19.0
        if c.get("small"):
            size = 17.0
        table(s, header, rows, top=top, col_w=c.get("widths"), row_h=row_h,
              sizes=(size, size), align_center_cols=tuple(c.get("center", ())))
        if c.get("note"):
            takeaway(s, c["note"], y=6.86)
        if c.get("warning"):
            warning(s, c["warning"], y=7.86)
        self._chrome(s, t.get("section", ""))
        self._note(s, self._note_spec(t, t["table"]), t.get("src", ""))

    # ---------------------------------------------------------------- diagram
    def diagram(self, t, idx):
        s = self._new()
        c = t["diagram"]
        title(s, t["title"])
        boxes = c["boxes"]
        n = len(boxes)
        gap = 0.42
        bw = min(3.6, (WIDTH - gap * (n - 1)) / n)
        total_w = bw * n + gap * (n - 1)
        x0 = LEFT + (WIDTH - total_w) / 2.0
        bh = 1.30
        y0 = c.get("top", 2.55)
        for i, b in enumerate(boxes):
            x = x0 + i * (bw + gap)
            filled = b.get("filled", False)
            shp = rect(s, x, y0, bw, bh, fill=C["teal"] if filled else C["mint"])
            tf = shp.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_right = Inches(0.12)
            lines = b["text"].split("\n")
            for j, ln in enumerate(lines):
                p = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
                p.alignment = PP_ALIGN.CENTER
                add_runs(p, ln, 19.0 if j == 0 else 16.0,
                         C["white"] if filled else C["ink"], j == 0, ZH)
            if i < n - 1:
                cx1 = x + bw
                cx2 = x + bw + gap
                cn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(cx1),
                                            Inches(y0 + bh / 2), Inches(cx2),
                                            Inches(y0 + bh / 2))
                cn.line.color.rgb = _rgb(C["rule"])
                cn.line.width = Pt(1.75)
                ln = cn.line._get_or_add_ln()
                tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle",
                                                        "w": "med", "len": "med"})
                ln.append(tail)
        if c.get("caption"):
            tb = textbox(s, LEFT, y0 + bh + 0.45, WIDTH, 0.9)
            para(tb.text_frame, c["caption"], size=21.0, color=C["ink"], first=True)
        if c.get("note"):
            takeaway(s, c["note"], y=6.86)
        if c.get("warning"):
            warning(s, c["warning"], y=7.86)
        self._chrome(s, t.get("section", ""))
        self._note(s, self._note_spec(t, t["diagram"]), t.get("src", ""))

    # ---------------------------------------------------------------- refs
    def refs(self):
        sp = self.spec
        s = self._new()
        title(s, "官方參考資料與版本說明")
        tb = textbox(s, 0.85, 2.10, WIDTH - 0.2, 4.4)
        tf = tb.text_frame
        psize = 17.0
        first = True
        for u in (sp.get("refs_slide") or sp["refs"]):
            p = tf.paragraphs[0] if first else tf.add_paragraph()
            first = False
            p.line_spacing = 1.25
            p.space_before = Pt(0 if p is tf.paragraphs[0] else 5)
            r = p.add_run()
            r.text = u
            _set_font(r, MONO, psize - 2.5, False, C["teal"])
        if sp.get("refs_note"):
            warning(s, sp["refs_note"], y=7.86)
        self._chrome(s, "參考資料")
        self._note(s, {"_note_why": "本章程式碼與指令對照來源文件之原始頁碼；官方文件連結用於查核 19c 行為差異。",
                       "_refs": []}, sp["source"])

    # ---------------------------------------------------------------- summary
    def summary(self):
        sp = self.spec
        sm = sp["summary"]
        s = self._new()
        title(s, "本章重點回顧")
        items = sm["items"]
        size_l, size_d = 21.0, 20.0
        lead_w, desc_w = 4.45, 10.15
        avail = 7.55 - BODY_TOP
        heights = []
        for lead, desc in items:
            hl = wrap_lines(lead, lead_w, size_l) * size_l * LINE_BODY / 72.0
            hd = wrap_lines(desc, desc_w, size_d) * size_d * LINE_BODY / 72.0
            heights.append(max(hl, hd) + 0.30)
        total = sum(heights) + 0.12 * (len(items) - 1)
        if total > avail:
            k = avail / total
            size_l, size_d = max(15.0, size_l * k), max(14.0, size_d * k)
            heights = [h * k for h in heights]
        y = BODY_TOP + 0.15
        for i, (lead, desc) in enumerate(items):
            lb = textbox(s, 0.85, y + 0.02, lead_w, heights[i])
            para(lb.text_frame, lead, size=size_l, color=C["teal"], bold=True, first=True)
            db = textbox(s, 5.62, y, desc_w, heights[i])
            para(db.text_frame, desc, size=size_d, color=C["ink"], first=True)
            y += heights[i] + 0.12
        self._chrome(s, sm.get("section", "整合複習"))
        self._note(s, {"_note_why": sm.get("note"), "_refs": []}, sp["source"])
