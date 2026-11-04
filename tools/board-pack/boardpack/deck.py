"""Dựng deck PPTX theo core/board-management-pack: action title, biểu đồ native, ghi chú nguồn trong speaker notes."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

from .commentary import Rules, Variance, bridge, variances
from .facts import BAL_LABEL, LABEL, PL_ROWS, SHORT, Facts, Status, month_end, months_for, prior_year, shift
from .fmt import bn, change, lower1, month_label, pct, period_label, pts, ratio, signed_bn, vnd, vs, vs_amt, vs_pts

FONT = "Calibri"
NAVY, INK, MUTED, LINE, PALE = RGBColor(0x1F, 0x38, 0x64), RGBColor(0x26, 0x26, 0x26), RGBColor(0x6B, 0x72, 0x80), RGBColor(0xD0, 0xD5, 0xDD), RGBColor(0xF2, 0xF4, 0xF7)
GREEN, AMBER, RED, BLUE, ORANGE = RGBColor(0x2E, 0x7D, 0x32), RGBColor(0xF5, 0xA6, 0x23), RGBColor(0xC6, 0x28, 0x28), RGBColor(0x15, 0x65, 0xC0), RGBColor(0xE6, 0x51, 0x00)
SERIES = {"Thực tế": NAVY, "Kế hoạch": RGBColor(0x8E, 0xA9, 0xC1), "Cùng kỳ": RGBColor(0xBF, 0xBF, 0xBF)}
STATUS_COLOR = {"APPROVED": GREEN, "RECONCILED": BLUE, "SƠ BỘ": ORANGE}
RAG_COLOR = {"Xanh": GREEN, "Vàng": AMBER, "Đỏ": RED}
W, H = Inches(13.333), Inches(7.5)
NUMFMT = '#,##0.0;(#,##0.0)'
PLACEHOLDER = "[CFO điền]"


def rag_for(a: dict | None, b: dict | None) -> tuple[str, str]:
    """Quy tắc đánh giá (ghi ở Phụ lục): EBITDA ≥ 95% so sánh → Xanh; 85–95% → Vàng; < 85% hoặc LNST âm → Đỏ."""
    if not a:
        return "Vàng", "thiếu số liệu"
    if a["net_profit"] < 0:
        return "Đỏ", "LNST âm"
    if not b or not b["ebitda"]:
        return "Vàng", "không có số so sánh"
    r = a["ebitda"] / b["ebitda"] if b["ebitda"] > 0 else None
    if r is None:
        return "Vàng", "EBITDA so sánh ≤ 0"
    return ("Xanh" if r >= 0.95 else "Vàng" if r >= 0.85 else "Đỏ"), f"EBITDA đạt {r * 100:.0f}%".replace(".", ",")


class Deck:
    def __init__(self, facts: Facts, month: str, mode: str = "month", rules: Rules | None = None, sample: bool = False,
                 company_name: str = "ALTA GROUP"):
        self.f, self.month, self.mode = facts, month, mode
        self.months = months_for(month, mode)
        self.py = prior_year(self.months)
        self.rules = rules or Rules()
        self.sample = sample
        self.company_name = company_name
        self.per = period_label(month, mode)
        self.PER = self.per[0].upper() + self.per[1:]
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.index: list[tuple[str, str]] = []   # (mã trang, tiêu đề) — dùng cho test & mục lục
        if not facts.pl(None, self.months):
            raise ValueError(f"Không có dữ liệu sổ cái cho {self.per} trong warehouse")
        self.A = {c: facts.pl(c, self.months) for c in [None, *facts.companies]}
        self.KH = {c: facts.plan_pl(c, self.months) for c in [None, *facts.companies]}
        self.CK = {c: facts.pl(c, self.py) for c in [None, *facts.companies]}
        self.ST = {c: facts.status(c, self.months) for c in [None, *facts.companies]}
        self.VAR = {c: variances(facts, c, self.months, mode, self.rules) for c in [None, *facts.companies]}

    # ------------------------------------------------------------------ primitives
    def _base(self, c):
        """So sánh chính: KH nếu có, nếu không thì cùng kỳ."""
        return ("KH", self.KH[c]) if self.KH[c] else ("CK", self.CK[c])

    def slide(self, code: str, title: str, status: Status | None, kicker: str = ""):
        s = self.prs.slides.add_slide(self.blank)
        s._notes: list[str] = []
        s._seen: set = set()
        if kicker:
            self.text(s, kicker.upper(), Inches(0.45), Inches(0.22), Inches(9), Inches(0.3), 10, MUTED, bold=True)
        self.text(s, title, Inches(0.45), Inches(0.45), Inches(12.4), Inches(0.85), 20, NAVY, bold=True, anchor=MSO_ANCHOR.TOP)
        ln = s.shapes.add_connector(1, Inches(0.45), Inches(1.32), Inches(12.88), Inches(1.32))
        ln.line.color.rgb, ln.line.width = LINE, Pt(1)
        self._footer(s, status)
        self.index.append((code, title))
        return s

    def _footer(self, s, status: Status | None):
        y = Inches(7.08)
        unit = "Đơn vị: tỷ đồng (số âm trong ngoặc)"
        self.text(s, f"{self.company_name} · Báo cáo quản trị {self.per} · {unit} · Số liệu quản trị, chưa kiểm toán",
                  Inches(0.45), y, Inches(8.4), Inches(0.3), 9, MUTED)
        x = Inches(8.9)
        if self.sample:
            self.badge(s, "DỮ LIỆU MẪU", x, y, Inches(1.25), RED)
            x += Inches(1.35)
        if status:
            self.badge(s, f"Số liệu: {status.label}", x, y, Inches(1.95), STATUS_COLOR[status.label])
            s._notes.append(f"Trạng thái dữ liệu trang này: {status.label} — theo afi reconcile (run_controls + period_status): "
                            + ", ".join(f"{k.replace('|', ' ')}={v}" for k, v in sorted(status.detail.items())))
        self.text(s, str(len(self.prs.slides)), Inches(12.45), y, Inches(0.45), Inches(0.3), 9, MUTED, align=PP_ALIGN.RIGHT)

    def badge(self, s, txt, x, y, w, color, h=Inches(0.28), size=9):
        b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
        b.fill.solid()
        b.fill.fore_color.rgb = color
        b.line.fill.background()
        tf = b.text_frame
        tf.margin_left = tf.margin_right = Inches(0.04)
        tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = txt
        r.font.size, r.font.bold, r.font.name = Pt(size), True, FONT
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF) if color != AMBER else INK
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        return b

    def text(self, s, txt, x, y, w, h, size=12, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, wrap=True):
        tb = s.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = wrap
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(0.02)
        tf.margin_top = tf.margin_bottom = Inches(0.01)
        lines = txt if isinstance(txt, list) else [txt]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            self._runs(p, line, size, color, bold)
        return tb

    @staticmethod
    def _runs(p, line, size, color, bold):
        """line: str hoặc list[(text, {bold, color, size})]."""
        parts = line if isinstance(line, list) else [(line, {})]
        for t, st in parts:
            r = p.add_run()
            r.text = t
            r.font.name = FONT
            r.font.size = Pt(st.get("size", size))
            r.font.bold = st.get("bold", bold)
            r.font.italic = st.get("italic", False)
            r.font.color.rgb = st.get("color", color)

    def box(self, s, x, y, w, h, fill=PALE, line=None):
        b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
        b.fill.solid()
        b.fill.fore_color.rgb = fill
        if line:
            b.line.color.rgb = line
            b.line.width = Pt(0.75)
        else:
            b.line.fill.background()
        b.shadow.inherit = False
        return b

    def table(self, s, rows, x, y, widths, row_h=Inches(0.3), size=10, bold_rows=(), header=True, align_num=True, shade_rows=()):
        nr, nc = len(rows), len(rows[0])
        gt = s.shapes.add_table(nr, nc, x, y, sum(widths, Emu(0)), row_h * nr)
        tbl = gt.table
        tblPr = gt._element.graphic.graphicData.tbl.tblPr
        tblPr.set("bandRow", "0")
        tblPr.set("firstRow", "0")
        for j, w in enumerate(widths):
            tbl.columns[j].width = w
        for i in range(nr):
            tbl.rows[i].height = row_h
            for j in range(nc):
                cell = tbl.cell(i, j)
                cell.margin_left = cell.margin_right = Inches(0.05)
                cell.margin_top = cell.margin_bottom = Inches(0.02)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                v = rows[i][j]
                tf = cell.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                hdr = header and i == 0
                is_num = align_num and j > 0 and not hdr
                p.alignment = PP_ALIGN.RIGHT if (is_num or (hdr and j > 0 and align_num)) else PP_ALIGN.LEFT
                col = RGBColor(0xFF, 0xFF, 0xFF) if hdr else INK
                if isinstance(v, tuple):  # (text, color)
                    v, col = v
                self._runs(p, "" if v is None else str(v), size, col, hdr or i in bold_rows)
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY if hdr else (PALE if i in shade_rows or i in bold_rows else RGBColor(0xFF, 0xFF, 0xFF))
        return tbl

    def chart(self, s, kind, cats, series: dict, x, y, w, h, legend=True, labels=False, colors=None, fmt=NUMFMT, size=9, gap=80):
        cd = CategoryChartData(number_format=fmt)
        cd.categories = cats
        for name, vals in series.items():
            cd.add_series(name, [None if v is None else round(v, 3) for v in vals])
        ch = s.shapes.add_chart(kind, x, y, w, h, cd).chart
        ch.has_title = False
        ch.font.size, ch.font.name = Pt(size), FONT
        ch.has_legend = legend
        if legend:
            ch.legend.position = XL_LEGEND_POSITION.TOP
            ch.legend.include_in_layout = False
            ch.legend.font.size = Pt(size)
        colors = colors or {}
        for ser in ch.plots[0].series:
            c = colors.get(ser.name) or SERIES.get(ser.name)
            if c is not None:
                if kind == XL_CHART_TYPE.LINE_MARKERS or kind == XL_CHART_TYPE.LINE:
                    ser.format.line.color.rgb = c
                    ser.format.line.width = Pt(2)
                else:
                    ser.format.fill.solid()
                    ser.format.fill.fore_color.rgb = c
        if kind in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.COLUMN_STACKED):
            ch.plots[0].gap_width = gap
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = LINE
        va.tick_labels.font.size = Pt(size)
        va.tick_labels.number_format, va.tick_labels.number_format_is_linked = fmt, False
        va.format.line.fill.background()
        ch.category_axis.tick_labels.font.size = Pt(size)
        ch.category_axis.format.line.color.rgb = LINE
        if labels:
            pl = ch.plots[0]
            pl.has_data_labels = True
            pl.data_labels.number_format, pl.data_labels.number_format_is_linked = fmt, False
            pl.data_labels.font.size = Pt(size - 1)
            pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
        return ch

    def sparkline(self, s, vals, x, y, w, h):
        if not any(v is not None for v in vals):
            return None
        cd = CategoryChartData(number_format="0.0")
        cd.categories = [str(i) for i in range(len(vals))]
        cd.add_series("6 kỳ", [None if v is None else round(v, 3) for v in vals])
        ch = s.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, x, y, w, h, cd).chart
        ch.has_title = False
        ch.has_legend = False
        ch.value_axis.visible = False
        ch.value_axis.has_major_gridlines = False
        ch.category_axis.visible = False
        ser = ch.plots[0].series[0]
        ser.format.line.color.rgb = NAVY
        ser.format.line.width = Pt(1.25)
        ser.smooth = False
        ser.marker.size = 3
        ser.marker.format.fill.solid()
        ser.marker.format.fill.fore_color.rgb = NAVY
        ser.marker.format.line.color.rgb = NAVY
        return ch

    def waterfall(self, s, start: tuple[str, float], steps: list[tuple[str, float]], end: tuple[str, float], x, y, w, h):
        """Waterfall native (cột chồng có chuỗi nền ẩn) — sửa số trong dữ liệu biểu đồ được."""
        cats, kinds, spans = [], [], []
        run = start[1]
        cats.append(start[0]); kinds.append("total"); spans.append((0.0, start[1]))
        for name, d in steps:
            cats.append(name); kinds.append("up" if d >= 0 else "down"); spans.append((run, run + d)); run += d
        cats.append(end[0]); kinds.append("total"); spans.append((0.0, end[1]))
        names = ["nền+", "nền−", "Tăng", "Tăng−", "Giảm", "Giảm−", "Tổng", "Tổng−"]
        data = {k: [0.0] * len(cats) for k in names}
        lab = {"up": "Tăng", "down": "Giảm", "total": "Tổng"}
        for i, ((a, b), kd) in enumerate(zip(spans, kinds)):
            lo, hi = min(a, b) / 1e9, max(a, b) / 1e9
            if lo >= 0:
                data["nền+"][i], data[lab[kd]][i] = lo, hi - lo
            elif hi <= 0:
                data["nền−"][i], data[lab[kd] + "−"][i] = hi, lo - hi
            else:
                data[lab[kd]][i], data[lab[kd] + "−"][i] = hi, lo
        cd = CategoryChartData(number_format=NUMFMT)
        cd.categories = cats
        for k in names:
            cd.add_series(k, data[k])
        ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, x, y, w, h, cd).chart
        ch.has_title = False
        ch.font.size, ch.font.name = Pt(10), FONT
        ch.has_legend = False
        pl = ch.plots[0]
        pl.gap_width, pl.overlap = 45, 100
        col = {"Tăng": GREEN, "Giảm": RED, "Tổng": NAVY}
        for ser in pl.series:
            base = ser.name.rstrip("−")
            if base.startswith("nền"):
                ser.format.fill.background()
                ser.format.line.fill.background()
            else:
                ser.format.fill.solid()
                ser.format.fill.fore_color.rgb = col[base]
        # nhãn: đặt trên điểm dương (hoặc âm nếu chỉ có phần âm) của đúng chuỗi màu
        for i, ((a, b), kd) in enumerate(zip(spans, kinds)):
            v = b - a if kd != "total" else b
            nm = lab[kd] if data[lab[kd]][i] != 0 else lab[kd] + "−"
            ser = next(se for se in pl.series if se.name == nm)
            dl = ser.points[i].data_label
            dl.has_text_frame = True
            dl.text_frame.text = bn(v) if kd == "total" else signed_bn(v)
            small = abs(v) < 0.12 * max(abs(x) for x in (start[1], end[1], 1))
            dl.position = XL_LABEL_POSITION.INSIDE_END if kd == "total" else (XL_LABEL_POSITION.INSIDE_BASE if small else XL_LABEL_POSITION.CENTER)
            for p in dl.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size, r.font.bold = Pt(10), True
                    r.font.color.rgb = INK if small and kd != "total" else RGBColor(0xFF, 0xFF, 0xFF)
        va = ch.value_axis
        va.has_major_gridlines = True
        va.major_gridlines.format.line.color.rgb = LINE
        va.tick_labels.number_format, va.tick_labels.number_format_is_linked = NUMFMT, False
        va.tick_labels.font.size = Pt(9)
        ch.category_axis.tick_labels.font.size = Pt(9)
        return ch

    # ------------------------------------------------------------------ source notes
    def _mtxt(self, months):
        return month_label(months[0]) if len(months) == 1 else f"{months[0][5:7]}–{months[-1][5:7]}/{months[-1][:4]}"

    def note_pl(self, s, label, cid, line, kind="A"):
        key = (label, cid, line, kind)
        if key in s._seen:
            return
        s._seen.add(key)
        months = self.py if kind == "CK" else self.months
        src = {"A": self.A, "CK": self.CK, "KH": self.KH}[kind][cid]
        if not src or src.get(line) is None:
            return
        v = src[line]
        who = SHORT[cid] + (" (cộng ALTA+APL+AME)" if cid is None else "")
        head = f"• {label} [{ {'A': 'Thực tế', 'CK': 'Cùng kỳ', 'KH': 'Kế hoạch'}[kind]}] {who} {self._mtxt(months)} = {vnd(v)} đ"
        if kind == "KH":
            s._notes.append(head + f" ← file kế hoạch {Path(self.f.plan_path).name if self.f.plan_path else ''} (company, month, line"
                            + (f"={line})" if line not in ("gross_profit", "profit_before_tax", "net_profit", "ebitda") else ") — tính từ các dòng KH theo account_map.yaml"))
            return
        formula = {"gross_profit": "= net_revenue − cogs (account_map.yaml: derived)",
                   "profit_before_tax": "= DT + DT tài chính + TN khác − GV − CP tài chính − CPBH − CPQL − CP khác (derived)",
                   "net_profit": "= profit_before_tax − income_tax (derived)",
                   "ebitda": "= LNTT + lãi vay (P3) + phát sinh Có TK 214 (P4)",
                   "external_revenue": "= net_revenue − doanh thu có mã đối tượng là MST công ty trong tập đoàn (P5)"}
        cmd = f"afi pl{' --company ' + cid if cid else ''} --month {months[-1]}" + (f" --lineage {line}" if line not in formula else "")
        if line in formula:
            s._notes.append(f"{head} {formula[line]} · kiểm tra: {cmd} (lặp từng tháng nếu lũy kế)")
            return
        rows, n = self.f.source_rows(line, cid, months, 3)
        tab = "fact_gl_lines (quy tắc lãi vay P3)" if line == "interest_expense" else f"mart_pl_monthly / pl_lines_lineage [{line}]"
        s._notes.append(f"{head} ← {tab}; dòng Excel chính: " + ("; ".join(f"{r.text()} = {vnd(r.amount)}" for r in rows) or "không có dòng")
                        + f" (tổng {n} dòng) · kiểm tra: {cmd}")

    def note_bal(self, s, label, cid, month, group, value):
        rows = self.f.balance_rows(cid, month, group, 3)
        s._notes.append(f"• {label} {SHORT[cid]} cuối {month_label(month)} = {vnd(value)} đ ← fact_tb (CĐPS, TK lá, số dư cuối kỳ); dòng chính: "
                        + ("; ".join(f"{r.file} · dòng {r.row} (TK {r.account}) = {vnd(r.amount)}" for r in rows) or "không có"))

    def note(self, s, txt):
        s._notes.append(txt)

    def _flush_notes(self):
        for s in self.prs.slides:
            body = [f"Nguồn số liệu — {self.company_name} · {self.per} · tạo lúc {dt.datetime.now():%d/%m/%Y %H:%M} bởi tools/board-pack."]
            body += s._notes or ["(Trang không có số liệu.)"]
            s.notes_slide.notes_text_frame.text = "\n".join(body)

    # ------------------------------------------------------------------ helpers for numbers
    def cmp_cells(self, a, b, kind="bn"):
        if kind == "pctpt":
            return [pct(a, signed=False), pct(b, signed=False) if b is not None else "–", pts(a - b) if a is not None and b is not None else "–"]
        return [bn(a), bn(b), pct(change(a, b))]

    def disp(self, line, v):
        from .facts import SIGN
        return None if v is None else SIGN.get(line, 1) * v

    # ================================================================== slides
    def build(self) -> Presentation:
        self.s_cover()
        self.s_exec()
        self.s_kpi()
        self.s_pl()
        self.s_commentary(None, "VAR-HN")
        self.s_bridge()
        for c in self.f.companies:
            self.s_entity(c)
        self.s_cash()
        self.s_risks()
        self.s_resolutions()
        self.s_app_entities()
        self.s_app_variances()
        self.s_app_status()
        self.s_app_method()
        self._flush_notes()
        return self.prs

    def s_cover(self):
        s = self.prs.slides.add_slide(self.blank)
        s._notes, s._seen = [], set()
        self.box(s, 0, 0, W, H, fill=NAVY)
        title = "BÁO CÁO QUẢN TRỊ " + (f"THÁNG {month_label(self.month)}" if self.mode == "month" else f"{int(self.month[5:7])} THÁNG NĂM {self.month[:4]}")
        self.text(s, self.company_name, Inches(0.8), Inches(1.6), Inches(11), Inches(0.5), 18, RGBColor(0xC9, 0xD6, 0xE8), bold=True)
        self.text(s, title, Inches(0.8), Inches(2.15), Inches(11.5), Inches(1.0), 38, RGBColor(0xFF, 0xFF, 0xFF), bold=True)
        self.text(s, "Tài liệu họp Hội đồng Quản trị · Kết quả kinh doanh, tiền, rủi ro và đề xuất nghị quyết",
                  Inches(0.8), Inches(3.15), Inches(11), Inches(0.5), 16, RGBColor(0xDD, 0xE5, 0xF0))
        st = self.ST[None]
        self.text(s, [f"Kỳ báo cáo: {self.per} · So sánh: kế hoạch{' (có)' if self.KH[None] else ' (chưa có file KH)'} và cùng kỳ {self._mtxt(self.py)}",
                      f"Trạng thái số liệu: {st.label} · Số liệu quản trị, chưa kiểm toán · Đơn vị: tỷ đồng",
                      f"Người trình: Giám đốc Tài chính · Ngày lập: {dt.date.today():%d/%m/%Y}"],
                  Inches(0.8), Inches(4.3), Inches(11), Inches(1.2), 13, RGBColor(0xDD, 0xE5, 0xF0))
        self.badge(s, f"Số liệu: {st.label}", Inches(0.8), Inches(5.65), Inches(2.4), STATUS_COLOR[st.label], h=Inches(0.42), size=13)
        if self.sample:
            self.badge(s, "DỮ LIỆU MẪU — số liệu tổng hợp, không phải số thật của Alta", Inches(3.4), Inches(5.65), Inches(6.6), RED, h=Inches(0.42), size=13)
        self.index.append(("COVER", title))
        self.note(s, f"Bìa. Trạng thái số liệu hợp nhất: {st.label} ("
                  + ", ".join(f"{k.replace('|', ' ')}={v}" for k, v in sorted(st.detail.items())) + ")."
                  + (" DỮ LIỆU MẪU: số liệu sinh bởi tests/fixtures.py (group_dataset), không phải số thật." if self.sample else ""))

    # ---------- 2. tóm tắt điều hành
    def s_exec(self):
        a, (bk, b), ck = self.A[None], self._base(None), self.CK[None]
        rag, why = rag_for(a, b)
        refname = "kế hoạch" if bk == "KH" else "cùng kỳ"
        ach = f"{a['ebitda'] / b['ebitda'] * 100:.0f}% {refname}".replace(".", ",") if b and b["ebitda"] > 0 else f"so với {refname}: –"
        title = (f"{self.PER}: doanh thu hợp nhất {bn(a['net_revenue'])} tỷ, {vs(a['net_revenue'], b and b['net_revenue'], refname)}; "
                 f"EBITDA {bn(a['ebitda'])} tỷ đạt {ach} — đánh giá {rag.upper()}")
        s = self.slide("EXEC", title, self.ST[None], "Tóm tắt điều hành")
        bal = self.f.balances(None, self.month)
        bal_prev = self.f.balances(None, shift(self.month, -1))
        tiles = [("Doanh thu thuần", "net_revenue"), ("EBITDA", "ebitda"), ("Tiền & tương đương tiền", "cash")]
        x0, wtile = Inches(0.45), Inches(2.9)
        for i, (lbl, key) in enumerate(tiles):
            x = x0 + i * (wtile + Inches(0.15))
            self.box(s, x, Inches(1.55), wtile, Inches(1.95))
            self.text(s, lbl, x + Inches(0.15), Inches(1.62), wtile, Inches(0.3), 12, MUTED, bold=True)
            if key == "cash":
                v = bal["cash"] if bal else None
                self.text(s, bn(v), x + Inches(0.15), Inches(1.92), wtile, Inches(0.7), 34, NAVY, bold=True)
                sub = [f"Đầu tháng: {bn(bal_prev['cash']) if bal_prev else '–'} · Δ {signed_bn(v - bal_prev['cash']) if bal_prev and v is not None else '–'}",
                       f"Nợ vay ròng: {bn(bal['net_debt']) if bal else '–'}"]
                if bal:
                    self.note_bal(s, "Tiền & tương đương tiền", None, self.month, "cash", bal["cash"])
            else:
                v = a[key]
                self.text(s, bn(v), x + Inches(0.15), Inches(1.92), wtile, Inches(0.7), 34, NAVY, bold=True)
                sub = [f"Kế hoạch: {bn(self.KH[None][key]) if self.KH[None] else '–'} · Δ {pct(change(v, self.KH[None][key])) if self.KH[None] else '–'}",
                       f"Cùng kỳ: {bn(ck[key]) if ck else '–'} · Δ {pct(change(v, ck[key])) if ck else '–'}"]
                if key == "ebitda":
                    sub.append(f"Biên EBITDA: {pct(a['ebitda_margin'], signed=False)}")
                for kd in ("A", "KH", "CK"):
                    self.note_pl(s, lbl, None, key, kd)
            self.text(s, sub, x + Inches(0.15), Inches(2.62), wtile - Inches(0.2), Inches(0.85), 11, INK)
        # RAG
        xr = Inches(9.9)
        self.box(s, xr, Inches(1.55), Inches(2.98), Inches(1.95), fill=RAG_COLOR[rag])
        tc = INK if rag == "Vàng" else RGBColor(0xFF, 0xFF, 0xFF)
        self.text(s, "ĐÁNH GIÁ CHUNG", xr + Inches(0.15), Inches(1.62), Inches(2.7), Inches(0.3), 12, tc, bold=True)
        self.text(s, rag.upper(), xr + Inches(0.15), Inches(1.92), Inches(2.7), Inches(0.7), 34, tc, bold=True)
        self.text(s, [f"Quy tắc: {why}", "≥95% Xanh · 85–95% Vàng · <85% hoặc lỗ Đỏ"], xr + Inches(0.15), Inches(2.62), Inches(2.75), Inches(0.8), 10, tc)
        # theo pháp nhân
        rows = [["Pháp nhân", "Doanh thu", f"% {bk}", "EBITDA", f"% {bk}", "Đánh giá"]]
        for c in self.f.companies:
            ac, (k2, bc) = self.A[c], self._base(c)
            r, _ = rag_for(ac, bc)
            rows.append([SHORT[c], bn(ac["net_revenue"]), self._achv(ac["net_revenue"], bc and bc["net_revenue"]),
                         bn(ac["ebitda"]), self._achv(ac["ebitda"], bc and bc["ebitda"]), (r, RAG_COLOR[r])])
            for kd in ("A", "KH", "CK"):
                self.note_pl(s, "Doanh thu", c, "net_revenue", kd)
                self.note_pl(s, "EBITDA", c, "ebitda", kd)
        self.text(s, "Kết quả theo pháp nhân", Inches(0.45), Inches(3.7), Inches(6), Inches(0.3), 12, NAVY, bold=True)
        self.table(s, rows, Inches(0.45), Inches(4.02), [Inches(1.6), Inches(1.05), Inches(0.85), Inches(1.05), Inches(0.85), Inches(0.95)], Inches(0.32), 10)
        # quyết định + rủi ro
        xq = Inches(7.0)
        self.text(s, "Quyết định cần HĐQT", xq, Inches(3.7), Inches(5.9), Inches(0.3), 12, NAVY, bold=True)
        self.text(s, [f"1. Thông qua KQKD {self.per} (số liệu {self.ST[None].label}, chưa kiểm toán).", f"2. {PLACEHOLDER} nội dung cần HĐQT quyết định.",
                      "Chi tiết dự thảo: trang Đề xuất nghị quyết."], xq, Inches(4.02), Inches(5.9), Inches(0.9), 11)
        self.text(s, "3 rủi ro hàng đầu (tín hiệu từ dữ liệu)", xq, Inches(5.0), Inches(5.9), Inches(0.3), 12, NAVY, bold=True)
        risks = self.risk_flags()[:3]
        self.text(s, [f"• {r[0]}" for r in risks] or [f"• {PLACEHOLDER}"], xq, Inches(5.32), Inches(5.9), Inches(1.6), 11)

    def _achv(self, a, b):
        return f"{a / b * 100:.0f}%".replace(".", ",") if a is not None and b else "–"

    # ---------- 3. KPI
    def kpi_rows(self, c):
        a, kh, ck = self.A[c], self.KH[c], self.CK[c]
        bal = self.f.balances(c, self.month)
        bal_py = self.f.balances(c, shift(self.month, -12))
        cf = self.f.cash_flows(c, self.months)
        cf_py = self.f.cash_flows(c, self.py)
        wc, wc_py = self.f.working_capital_days(c, self.month), self.f.working_capital_days(c, shift(self.month, -12))
        lt, lt_py = self.f.ltm_ebitda(c, self.month), self.f.ltm_ebitda(c, shift(self.month, -12))
        nd = lambda b, e: b["net_debt"] / e if b and e and e > 0 else None  # noqa: E731
        trend_m = [shift(self.month, -i) for i in range(5, -1, -1)]
        tr = {m: self.f.pl(c, [m]) for m in trend_m}
        trb = {m: self.f.balances(c, m) for m in trend_m}
        tw = {m: self.f.working_capital_days(c, m) for m in trend_m}
        g = lambda k: [tr[m][k] / 1e9 if tr[m] and tr[m].get(k) is not None else None for m in trend_m]  # noqa: E731
        gm = lambda k: [tr[m][k] * 100 if tr[m] and tr[m].get(k) is not None else None for m in trend_m]  # noqa: E731
        rows = [
            ("Doanh thu thuần", "bn", a["net_revenue"], kh and kh["net_revenue"], ck and ck["net_revenue"], g("net_revenue"), "net_revenue"),
            ("Doanh thu ngoài tập đoàn", "bn", a["external_revenue"], kh and kh.get("external_revenue"), ck and ck["external_revenue"], g("external_revenue"), "external_revenue"),
            ("Lợi nhuận gộp", "bn", a["gross_profit"], kh and kh["gross_profit"], ck and ck["gross_profit"], g("gross_profit"), "gross_profit"),
            ("Biên lợi nhuận gộp", "pp", a["gross_margin"], kh and kh["gross_margin"], ck and ck["gross_margin"], gm("gross_margin"), None),
            ("EBITDA", "bn", a["ebitda"], kh and kh["ebitda"], ck and ck["ebitda"], g("ebitda"), "ebitda"),
            ("Biên EBITDA", "pp", a["ebitda_margin"], kh and kh["ebitda_margin"], ck and ck["ebitda_margin"], gm("ebitda_margin"), None),
            ("Lợi nhuận sau thuế", "bn", a["net_profit"], kh and kh["net_profit"], ck and ck["net_profit"], g("net_profit"), "net_profit"),
            ("Dòng tiền hoạt động KD (P7)", "bn", cf and cf["operating"], None, cf_py and cf_py["operating"],
             [(self.f.cash_flows(c, [m]) or {}).get("operating", 0) / 1e9 if tr[m] else None for m in trend_m], None),
            ("Tiền cuối kỳ", "bn", bal and bal["cash"], None, bal_py and bal_py["cash"], [trb[m]["cash"] / 1e9 if trb[m] else None for m in trend_m], None),
            ("Nợ vay ròng / EBITDA 12T (lần)", "x", nd(bal, lt), None, nd(bal_py, lt_py), [None] * 6, None),
            ("DSO (ngày)", "d", wc["dso"], None, wc_py["dso"], [tw[m]["dso"] for m in trend_m], None),
            ("DIO (ngày)", "d", wc["dio"], None, wc_py["dio"], [tw[m]["dio"] for m in trend_m], None),
            ("DPO (ngày)", "d", wc["dpo"], None, wc_py["dpo"], [tw[m]["dpo"] for m in trend_m], None),
        ]
        return rows, bal, lt, cf

    def s_kpi(self):
        rows, bal, lt, cf = self.kpi_rows(None)
        a, (bk, b) = self.A[None], self._base(None)
        gm_d = a["gross_margin"] - b["gross_margin"] if b and b.get("gross_margin") is not None else None
        ndx = rows[9][2]
        title = (f"KPI {self.per}: biên gộp {pct(a['gross_margin'], signed=False)}, {vs_pts(gm_d, 'kế hoạch' if bk == 'KH' else 'cùng kỳ')}; "
                 f"tiền cuối kỳ {bn(bal['cash']) if bal else '–'} tỷ, nợ vay ròng/EBITDA 12T: {self._x(ndx)}")
        s = self.slide("KPI", title, self.ST[None], "Dashboard KPI hợp nhất")
        hdr = ["Chỉ tiêu", "Thực tế", "Kế hoạch", "Δ vs KH", "Cùng kỳ", "Δ vs CK", "Xu hướng 6 tháng"]
        tab = [hdr]
        for lbl, kind, av, kv, cv, _, line in rows:
            if kind == "bn":
                tab.append([lbl, bn(av), bn(kv), pct(change(av, kv)), bn(cv), pct(change(av, cv)), ""])
            elif kind == "pp":
                tab.append([lbl, pct(av, signed=False), pct(kv, signed=False), pts(av - kv) if av is not None and kv is not None else "–",
                            pct(cv, signed=False), pts(av - cv) if av is not None and cv is not None else "–", ""])
            elif kind == "x":
                tab.append([lbl, self._x(av), "–", "–", self._x(cv), "–", ""])
            else:
                tab.append([lbl, self._d(av), "–", "–", self._d(cv), self._dd(av, cv), ""])
            if line:
                for kd in ("A", "KH", "CK"):
                    self.note_pl(s, lbl, None, line, kd)
        widths = [Inches(3.0), Inches(1.25), Inches(1.25), Inches(1.25), Inches(1.25), Inches(1.25), Inches(3.1)]
        rh = Inches(0.33)
        y0 = Inches(1.5)
        self.table(s, tab, Inches(0.45), y0, widths, rh, 9.5, shade_rows=(1, 3, 5, 7, 9, 11, 13))
        xs = Inches(0.45) + sum(widths[:-1], Emu(0)) + Inches(0.1)
        for i, r in enumerate(rows):
            self.sparkline(s, r[5], xs, y0 + rh * (i + 1) + Inches(0.02), widths[-1] - Inches(0.2), rh - Inches(0.04))
        trend_m = [shift(self.month, -i) for i in range(5, -1, -1)]
        self.text(s, f"Xu hướng: {month_label(trend_m[0])} → {month_label(trend_m[-1])} (theo tháng). Dòng tiền HĐKD phân loại theo TK đối ứng của TK 111/112/113 (P7); "
                     "DSO/DIO/DPO theo P8 (số dư cuối kỳ ÷ doanh thu/giá vốn 3 tháng × 91). Hợp nhất = cộng 3 pháp nhân, chưa loại trừ nội bộ.",
                  Inches(0.45), Inches(6.62), Inches(12.4), Inches(0.4), 9, MUTED)
        if bal:
            self.note_bal(s, "Tiền cuối kỳ", None, self.month, "cash", bal["cash"])
            for g in ("receivables", "inventory", "payables", "debt"):
                self.note_bal(s, BAL_LABEL[g], None, self.month, g, bal[g])
        if cf:
            self.note(s, f"• Dòng tiền HĐKD {self._mtxt(self.months)} = {vnd(cf['operating'])} đ ← fact_gl_lines TK 111/112/113 phân loại theo cash_flow_map.yaml (P7); "
                         f"chưa phân loại: {vnd(cf['unclassified'])} đ")
        self.note(s, f"• EBITDA 12 tháng đến {month_label(self.month)} = {vnd(lt) if lt is not None else '–'} đ (cộng afi pl 12 tháng); Nợ vay ròng = TK 311+341 − tiền.")

    @staticmethod
    def _x(v):
        return "–" if v is None else (f"{v:.1f}".replace(".", ",") + "x" if v >= 0 else "tiền ròng")

    @staticmethod
    def _d(v):
        return "–" if v is None else f"{v:.0f}"

    @staticmethod
    def _dd(a, b):
        if a is None or b is None:
            return "–"
        d = a - b
        return f"+{d:.0f} ngày" if d > 0 else (f"({abs(d):.0f} ngày)" if d < 0 else "0 ngày")

    # ---------- 4. KQKD hợp nhất
    def pl_table_rows(self, c):
        a, kh, ck = self.A[c], self.KH[c], self.CK[c]
        rows = [["Chỉ tiêu", "Thực tế", "Kế hoạch", "Δ vs KH", "Δ%", "Cùng kỳ", "Δ vs CK", "Δ%"]]
        bold = []
        for k, lbl, sg, b in PL_ROWS:
            A = sg * a[k]
            K = sg * kh[k] if kh and kh.get(k) is not None else None
            C = sg * ck[k] if ck else None
            rows.append([lbl, bn(A), bn(K), signed_bn(A - K) if K is not None else "–", pct(change(A, K)),
                         bn(C), signed_bn(A - C) if C is not None else "–", pct(change(A, C))])
            if b:
                bold.append(len(rows) - 1)
        for k, lbl in (("gross_margin", "Biên lợi nhuận gộp"), ("ebitda_margin", "Biên EBITDA")):
            A, K, C = a[k], kh and kh.get(k), ck and ck[k]
            rows.append([lbl, pct(A, signed=False), pct(K, signed=False), pts(A - K) if K is not None else "–", "",
                         pct(C, signed=False), pts(A - C) if C is not None else "–", ""])
        return rows, bold

    def s_pl(self):
        a, kh, ck = self.A[None], self.KH[None], self.CK[None]
        title = (f"KQKD hợp nhất {self.per}: LNST {bn(a['net_profit'])} tỷ, {vs(a['net_profit'], kh and kh['net_profit'], 'kế hoạch')} "
                 f"và {vs(a['net_profit'], ck and ck['net_profit'], 'cùng kỳ')}")
        s = self.slide("PL", title, self.ST[None], "Kết quả kinh doanh hợp nhất")
        rows, bold = self.pl_table_rows(None)
        w = [Inches(2.55), Inches(0.9), Inches(0.9), Inches(0.85), Inches(0.75), Inches(0.9), Inches(0.85), Inches(0.75)]
        self.table(s, rows, Inches(0.45), Inches(1.5), w, Inches(0.29), 9.5, bold_rows=bold)
        for k, lbl, _, _ in PL_ROWS:
            for kd in ("A", "KH", "CK"):
                self.note_pl(s, lbl.strip(), None, k, kd)
        keys = [("net_revenue", "Doanh thu"), ("gross_profit", "LN gộp"), ("ebitda", "EBITDA"), ("net_profit", "LNST")]
        ser = {"Thực tế": [a[k] / 1e9 for k, _ in keys]}
        if kh:
            ser["Kế hoạch"] = [kh[k] / 1e9 for k, _ in keys]
        if ck:
            ser["Cùng kỳ"] = [ck[k] / 1e9 for k, _ in keys]
        self.chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, [n for _, n in keys], ser, Inches(9.0), Inches(1.45), Inches(3.9), Inches(3.4), labels=False)
        ic = a["ic_revenue"]
        self.text(s, [[("Ghi chú hợp nhất: ", {"bold": True}), (f"số cộng gộp 3 pháp nhân, chưa loại trừ giao dịch nội bộ (P5 chưa triển khai trong pipeline). "
                       f"Doanh thu nội bộ nhận diện theo MST đối tượng: {bn(ic)} tỷ ({pct(ratio(ic, a['net_revenue']), signed=False)} doanh thu).", {})],
                       [("Dấu: ", {"bold": True}), ("chi phí hiển thị số âm; Δ dương = thuận lợi.", {})]],
                  Inches(9.0), Inches(5.0), Inches(3.9), Inches(1.9), 10, MUTED)
        self.note_pl(s, "Doanh thu nội bộ", None, "ic_revenue")
        self.note_pl(s, "Doanh thu ngoài tập đoàn", None, "external_revenue")

    # ---------- 5. giải trình
    def var_block(self, s, v: Variance, x, y, w, h, size=10):
        self.box(s, x, y, w, h, fill=PALE)
        self.box(s, x, y, Inches(0.07), h, fill=GREEN if v.favourable else RED)
        ref = "KH" if v.base == "KH" else "cùng kỳ"
        lines = [[("Cái gì: ", {"bold": True, "color": NAVY}), (v.what, {"bold": True})]]
        for i, wtxt in enumerate(v.why):
            lines.append([("Tại sao (dữ liệu): " if i == 0 else "   ", {"bold": True, "color": NAVY}), (wtxt, {})])
        lines.append([("Một lần/lặp lại: ", {"bold": True, "color": NAVY}), (v.recurring, {})])
        lines.append([("Hành động: ", {"bold": True, "color": NAVY}), (v.action, {"color": ORANGE, "bold": True})])
        self.text(s, lines, x + Inches(0.15), y + Inches(0.05), w - Inches(0.25), h - Inches(0.1), size)
        self.note_pl(s, LABEL[v.line], v.cid, v.line, "A")
        self.note_pl(s, LABEL[v.line], v.cid, v.line, "KH" if v.base == "KH" else "CK")
        _ = ref

    def s_commentary(self, c, code):
        vl = self.VAR[c]
        if vl:
            v = vl[0]
            title = (f"{len(vl)} biến động vượt ngưỡng; lớn nhất: {lower1(LABEL[v.line])} {vs_amt(v.delta, 'kế hoạch' if v.base == 'KH' else 'cùng kỳ')} "
                     f"({'thuận lợi' if v.favourable else 'bất lợi'})")
        else:
            title = f"Không có biến động hợp nhất nào vượt ngưỡng giải trình ({self.rules.text()})"
        s = self.slide(code, title, self.ST[c], f"Giải trình biến động · {SHORT[c]}")
        y, hb = Inches(1.5), Inches(1.62)
        for v in vl[:3]:
            self.var_block(s, v, Inches(0.45), y, Inches(12.43), hb)
            y += hb + Inches(0.08)
        more = len(vl) - 3
        self.text(s, f"Ngưỡng giải trình: {self.rules.text()} (sửa bằng --threshold-pct/--threshold-amount). Nguyên nhân chỉ lấy từ dữ liệu; "
                     f"ô [CFO điền] phải được hoàn thiện trước khi gửi HĐQT." + (f" Còn {more} biến động: xem Phụ lục." if more > 0 else ""),
                  Inches(0.45), Inches(6.72), Inches(12.4), Inches(0.3), 9, MUTED)

    # ---------- 6. bridge
    def s_bridge(self):
        a, (bk, b) = self.A[None], self._base(None)
        if not b:
            s = self.slide("BRIDGE", "Chưa có số so sánh (kế hoạch/cùng kỳ) để dựng cầu nối EBITDA", self.ST[None], "Cầu nối EBITDA")
            return
        steps = bridge(a, b)
        top = max(steps, key=lambda x: abs(x[1]))
        ref = "kế hoạch" if bk == "KH" else "cùng kỳ"
        d = a["ebitda"] - b["ebitda"]
        title = (f"EBITDA {self.per} {bn(a['ebitda'])} tỷ, {'cao' if d >= 0 else 'thấp'} hơn {ref} {bn(abs(d))} tỷ; "
                 f"yếu tố lớn nhất: {lower1(top[0])} ({'tăng' if top[1] >= 0 else 'giảm'} {bn(abs(top[1]))} tỷ)")
        s = self.slide("BRIDGE", title, self.ST[None], f"Cầu nối EBITDA hợp nhất · {('Kế hoạch' if bk == 'KH' else 'Cùng kỳ')} → Thực tế")
        self.waterfall(s, (f"EBITDA {'KH' if bk == 'KH' else 'cùng kỳ'}", b["ebitda"]), steps, ("EBITDA thực tế", a["ebitda"]),
                       Inches(0.45), Inches(1.5), Inches(8.6), Inches(5.1))
        rows = [["Bước", "Tác động"]] + [[k, signed_bn(v)] for k, v in steps] + [["Tổng chênh lệch", signed_bn(d)]]
        self.table(s, rows, Inches(9.3), Inches(1.6), [Inches(2.45), Inches(1.1)], Inches(0.34), 10, bold_rows=(len(rows) - 1,))
        self.text(s, ["Bước = chênh lệch từng dòng KQKD (chi phí tăng → tác động âm). Khấu hao cộng lại vì EBITDA loại khấu hao (P4); "
                      "tài chính & khác không gồm lãi vay (P3).",
                      "Chưa tách giá/sản lượng/cơ cấu/giá hạt nhựa: cần dữ liệu sản lượng (Phase 4, công cụ #15)."],
                  Inches(9.3), Inches(4.65), Inches(3.6), Inches(2.0), 10, MUTED)
        for k in ("ebitda", "net_revenue", "cogs", "selling_expenses", "admin_expenses", "depreciation", "interest_expense", "finance_income", "finance_expense", "other_income", "other_expense"):
            self.note_pl(s, LABEL[k], None, k, "A")
            self.note_pl(s, LABEL[k], None, k, bk)

    # ---------- 7. pháp nhân
    def s_entity(self, c):
        a, kh, ck = self.A[c], self.KH[c], self.CK[c]
        bk, b = self._base(c)
        vl = self.VAR[c]
        tail = ""
        if vl:
            v = vl[0]
            tail = f"; cần giải trình: {lower1(LABEL[v.line])} {vs_amt(v.delta, 'KH' if v.base == 'KH' else 'cùng kỳ')}"
        ref = "KH" if bk == "KH" else "cùng kỳ"
        title = (f"{SHORT[c]}: doanh thu {bn(a['net_revenue'])} tỷ, {vs(a['net_revenue'], b and b['net_revenue'], ref)}; "
                 f"EBITDA {bn(a['ebitda'])} tỷ, {vs(a['ebitda'], b and b['ebitda'], ref)}{tail}")
        s = self.slide(f"ENT-{c}", title, self.ST[c], f"Kết quả theo pháp nhân · {self.f.names.get(c, c)}")
        rows = [["Chỉ tiêu", "Thực tế", "Kế hoạch", "Δ% KH", "Cùng kỳ", "Δ% CK"]]
        spec = [("net_revenue", "Doanh thu thuần"), ("cogs", "Giá vốn hàng bán"), ("gross_profit", "Lợi nhuận gộp"), ("gross_margin", "Biên gộp"),
                ("selling_expenses", "Chi phí bán hàng"), ("admin_expenses", "Chi phí QLDN"), ("ebitda", "EBITDA"), ("ebitda_margin", "Biên EBITDA"), ("net_profit", "LNST")]
        for k, lbl in spec:
            if k.endswith("margin"):
                A, K, C = a[k], kh and kh.get(k), ck and ck[k]
                rows.append([lbl, pct(A, signed=False), pct(K, signed=False), pts(A - K) if K is not None else "–", pct(C, signed=False), pts(A - C) if C is not None else "–"])
            else:
                sg = -1 if k in ("cogs", "selling_expenses", "admin_expenses") else 1
                A, K, C = sg * a[k], (sg * kh[k] if kh else None), (sg * ck[k] if ck else None)
                rows.append([lbl, bn(A), bn(K), pct(change(A, K)), bn(C), pct(change(A, C))])
                for kd in ("A", "KH", "CK"):
                    self.note_pl(s, lbl, c, k, kd)
        self.table(s, rows, Inches(0.45), Inches(1.5), [Inches(2.0), Inches(0.95), Inches(0.95), Inches(0.9), Inches(0.95), Inches(0.9)], Inches(0.27), 9.5, bold_rows=(1, 3, 7, 9))
        # biểu đồ 6 tháng
        tr = self.f.trend(c, self.month, 6)
        cats = [month_label(m) for m, _ in tr]
        self.chart(s, XL_CHART_TYPE.COLUMN_CLUSTERED, cats, {"Doanh thu": [p["net_revenue"] / 1e9 if p else None for _, p in tr],
                                                             "EBITDA": [p["ebitda"] / 1e9 if p else None for _, p in tr]},
                   Inches(7.3), Inches(1.4), Inches(5.6), Inches(2.55), colors={"Doanh thu": NAVY, "EBITDA": RGBColor(0x5B, 0x9B, 0xD5)}, gap=60)
        self.note(s, "• Biểu đồ 6 tháng: doanh thu và EBITDA từng tháng " + ", ".join(f"{month_label(m)}: {bn(p['net_revenue'])}/{bn(p['ebitda'])}" for m, p in tr if p)
                  + f" (afi pl --company {c} --month <tháng>)")
        # khách hàng lớn
        cust = self.f.top_customers(c, self.months, 5)
        py_c = {k: v for k, v in self.f.top_customers(c, self.py, 50)} if ck else {}
        crow = [["Khách hàng lớn (doanh thu)", "Thực tế", "Cùng kỳ", "Δ"]]
        for name, v in cust:
            p = py_c.get(name)
            crow.append([name, bn(v), bn(p), signed_bn(v - p) if p is not None else "–"])
        self.table(s, crow, Inches(7.3), Inches(4.1), [Inches(2.9), Inches(0.9), Inches(0.9), Inches(0.9)], Inches(0.28), 9.5)
        share = cust[0][1] / a["net_revenue"] if cust and a["net_revenue"] else None
        self.note(s, f"• Khách hàng lớn: pl_lines_lineage line=net_revenue nhóm theo Tên khách (company {c}, {self._mtxt(self.months)}); "
                     f"khách lớn nhất chiếm {pct(share, signed=False)} doanh thu.")
        # vấn đề & hành động
        y = Inches(4.62)
        self.text(s, "Vấn đề & hành động", Inches(0.45), y, Inches(6.6), Inches(0.3), 12, NAVY, bold=True)
        lines = []
        for v in vl[:2]:
            lines.append([("■ ", {"color": GREEN if v.favourable else RED, "bold": True}), (v.what, {"bold": True})])
            if v.why:
                lines.append([("   ", {}), (v.why[0] if len(v.why[0]) < 230 else v.why[0][:227] + "…", {"size": 9})])
            lines.append([("   Hành động: ", {"bold": True, "color": NAVY, "size": 9}), (PLACEHOLDER + " ai · khi nào · tác động cả năm", {"color": ORANGE, "bold": True, "size": 9})])
            self.note_pl(s, LABEL[v.line], c, v.line, "A")
            self.note_pl(s, LABEL[v.line], c, v.line, v.base)
        if not vl:
            lines = [f"Không có biến động vượt ngưỡng ({self.rules.text()}).", f"{PLACEHOLDER} động lực chính, vấn đề cần lưu ý."]
        self.text(s, lines, Inches(0.45), y + Inches(0.32), Inches(6.6), Inches(2.0), 10)

    # ---------- 8. tiền & vốn lưu động
    def s_cash(self):
        m = self.month
        cols = [("Cuối kỳ", m), ("Đầu tháng", shift(m, -1)), ("Đầu năm", f"{int(m[:4]) - 1}-12"), ("Cùng kỳ", shift(m, -12))]
        bals = [(lbl, mm, self.f.balances(None, mm)) for lbl, mm in cols]
        cur, prev = bals[0][2], bals[1][2]
        cf = self.f.cash_flows(None, self.months)
        title = (f"Tiền cuối kỳ {bn(cur['cash'])} tỷ ({signed_bn(cur['cash'] - prev['cash']) if prev else '–'} trong tháng); "
                 f"dòng tiền HĐKD {self.per} {bn(cf['operating']) if cf else '–'} tỷ; nợ vay ròng {bn(cur['net_debt'])} tỷ")
        s = self.slide("CASH", title, self.ST[None], "Tiền & vốn lưu động")
        rows = [["Chỉ tiêu (tỷ đồng)"] + [f"{lbl} {month_label(mm)}" for lbl, mm, _ in bals]]
        for g in ("cash", "receivables", "inventory", "payables", "debt", "net_debt"):
            rows.append([BAL_LABEL.get(g, "Nợ vay ròng (vay − tiền)")] + [bn(b[g]) if b else "–" for _, _, b in bals])
        rows.append(["Vốn lưu động (PT + HTK − PTr)"] + [bn(b["receivables"] + b["inventory"] - b["payables"]) if b else "–" for _, _, b in bals])
        for k, lbl in (("dso", "DSO (ngày)"), ("dio", "DIO (ngày)"), ("dpo", "DPO (ngày)")):
            rows.append([lbl] + [self._d(self.f.working_capital_days(None, mm)[k]) for _, mm, _ in bals])
        self.table(s, rows, Inches(0.45), Inches(1.5), [Inches(2.7), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.0)], Inches(0.3), 9.5, bold_rows=(1, 6))
        for lbl, mm, b in bals:
            if b:
                for g in ("cash", "receivables", "inventory", "payables", "debt"):
                    self.note_bal(s, f"{BAL_LABEL[g]} [{lbl}]", None, mm, g, b[g])
        # dòng tiền kỳ
        if cf:
            frows = [["Dòng tiền " + self.per, "Tỷ đồng"], ["Hoạt động kinh doanh", bn(cf["operating"])], ["Hoạt động đầu tư", bn(cf["investing"])],
                     ["Hoạt động tài chính", bn(cf["financing"])], ["Nội bộ tập đoàn", bn(cf["intercompany"])], ["Chưa phân loại (cần xử lý)", bn(cf["unclassified"])],
                     ["Thay đổi tiền", bn(sum(v for v in cf.values()))]]
            self.table(s, frows, Inches(0.45), Inches(5.0), [Inches(2.7), Inches(1.0)], Inches(0.26), 9.5, bold_rows=(6,))
            self.note(s, "• Dòng tiền: fact_gl_lines TK 111/112/113, phân loại theo TK đối ứng (cash_flow_map.yaml, P7); chuyển tiền nội bộ giữa TK tiền bị loại. "
                         + ", ".join(f"{k}={vnd(v)}" for k, v in cf.items()))
        # biểu đồ tiền theo pháp nhân
        tm = [shift(m, -i) for i in range(5, -1, -1)]
        ser = {SHORT[c]: [(self.f.balances(c, mm) or {}).get("cash", 0) / 1e9 for mm in tm] for c in self.f.companies}
        self.chart(s, XL_CHART_TYPE.COLUMN_STACKED, [month_label(x) for x in tm], ser, Inches(7.45), Inches(1.4), Inches(5.45), Inches(3.3),
                   colors=dict(zip([SHORT[c] for c in self.f.companies], [NAVY, RGBColor(0x5B, 0x9B, 0xD5), RGBColor(0xA5, 0xC8, 0xE4)])), gap=60)
        self.note(s, "• Biểu đồ tiền cuối tháng theo pháp nhân: fact_tb TK 111/112/113 (số dư cuối kỳ) từng tháng.")
        self.text(s, [[("Dòng tiền 13 tuần: ", {"bold": True}), ("chưa có — sẽ lấy từ công cụ #3 (cash-13-week-treasury) khi hoàn thành.", {})],
                      [("Covenant: ", {"bold": True}), (f"{PLACEHOLDER} (sổ nợ vay & covenant — công cụ #5).", {})],
                      [("Ghi chú: ", {"bold": True}), ("vốn lưu động hợp nhất gồm cả công nợ nội bộ (chưa loại trừ).", {})]],
                  Inches(7.45), Inches(4.9), Inches(5.45), Inches(1.9), 10, MUTED)

    # ---------- 9. rủi ro
    def risk_flags(self) -> list[tuple[str, str]]:
        """Tín hiệu rủi ro rút từ dữ liệu: (mô tả, số liệu). Không tự gán nguyên nhân."""
        out = []
        for c in [None, *self.f.companies]:
            st = self.ST[c]
            if c is not None and st.label == "SƠ BỘ":
                bad = [k.split("|")[1] for k, v in st.detail.items() if v not in ("APPROVED", "RECONCILED")]
                out.append((f"Số liệu {SHORT[c]} chưa đối chiếu xong ({', '.join(month_label(x) for x in bad)})", "Trạng thái SƠ BỘ — xem Phụ lục trạng thái dữ liệu"))
        for c in self.f.companies:
            a, ck, kh = self.A[c], self.CK[c], self.KH[c]
            if a["net_profit"] < 0:
                out.append((f"{SHORT[c]} lỗ trong kỳ", f"LNST {bn(a['net_profit'])} tỷ"))
            if kh and kh["ebitda"] > 0 and a["ebitda"] < 0.9 * kh["ebitda"]:
                out.append((f"EBITDA {SHORT[c]} dưới 90% kế hoạch", f"{bn(a['ebitda'])} / {bn(kh['ebitda'])} tỷ ({self._achv(a['ebitda'], kh['ebitda'])})"))
            if ck and a["gross_margin"] is not None and ck["gross_margin"] is not None and a["gross_margin"] < ck["gross_margin"] - 0.02:
                out.append((f"Biên gộp {SHORT[c]} giảm > 2 điểm so với cùng kỳ", f"{pct(a['gross_margin'], signed=False)} so với {pct(ck['gross_margin'], signed=False)} ({pts(a['gross_margin'] - ck['gross_margin'])})"))
            cust = self.f.top_customers(c, self.months, 1)
            if cust and a["net_revenue"] and cust[0][1] / a["net_revenue"] > 0.30:
                out.append((f"Tập trung khách hàng tại {SHORT[c]}", f"{cust[0][0]} chiếm {pct(cust[0][1] / a['net_revenue'], signed=False)} doanh thu"))
            w, wp = self.f.working_capital_days(c, self.month), self.f.working_capital_days(c, shift(self.month, -12))
            if w["dso"] is not None and wp["dso"] is not None and w["dso"] - wp["dso"] > 10:
                out.append((f"DSO {SHORT[c]} tăng > 10 ngày so với cùng kỳ", f"{w['dso']:.0f} so với {wp['dso']:.0f} ngày"))
        bal, lt = self.f.balances(None, self.month), self.f.ltm_ebitda(None, self.month)
        if bal and lt and lt > 0 and bal["net_debt"] / lt > 3:
            out.append(("Nợ vay ròng/EBITDA 12T > 3 lần", self._x(bal["net_debt"] / lt)))
        cf = self.f.cash_flows(None, self.months)
        if cf and abs(cf["unclassified"]) > 1e6:
            out.append(("Dòng tiền chưa phân loại theo cash_flow_map", f"{bn(cf['unclassified'], 2)} tỷ"))
        return out

    def s_risks(self):
        fl = self.risk_flags()
        title = (f"{len(fl)} tín hiệu rủi ro từ dữ liệu cần HĐQT lưu ý; nổi bật: {lower1(fl[0][0])}" if fl
                 else "Không có tín hiệu rủi ro nào từ dữ liệu vượt ngưỡng; CFO bổ sung rủi ro ngoài dữ liệu")
        s = self.slide("RISK", title, self.ST[None], "Rủi ro & tuân thủ")
        rows = [["#", "Rủi ro / tín hiệu từ dữ liệu", "Số liệu", "Khả năng", "Tác động", "Chủ rủi ro", "Biện pháp"]]
        for i, (r, v) in enumerate(fl[:8], 1):
            rows.append([str(i), r, v, PLACEHOLDER, PLACEHOLDER, PLACEHOLDER, PLACEHOLDER])
        n = len(rows)
        rows.append([str(n), f"{PLACEHOLDER} rủi ro ngoài dữ liệu (thuế, pháp lý, nhân sự, thị trường)", "", "", "", "", ""])
        rows.append([str(n + 1), f"{PLACEHOLDER} lịch thuế/kiểm toán sắp tới (vn-finance-compliance)", "", "", "", "", ""])
        self.table(s, rows, Inches(0.45), Inches(1.5), [Inches(0.4), Inches(4.1), Inches(3.0), Inches(1.1), Inches(1.1), Inches(1.2), Inches(1.53)],
                   Inches(0.42), 10, align_num=False)
        self.text(s, "Tín hiệu được sinh theo quy tắc cố định: số liệu SƠ BỘ; pháp nhân lỗ; EBITDA < 90% KH; biên gộp giảm > 2 điểm so với cùng kỳ; khách hàng lớn nhất > 30% doanh thu; "
                     "DSO tăng > 10 ngày; nợ vay ròng/EBITDA 12T > 3 lần; dòng tiền chưa phân loại. Khả năng × tác động và biện pháp do CFO đánh giá.",
                  Inches(0.45), Inches(6.55), Inches(12.4), Inches(0.45), 9, MUTED)
        self.note(s, "Nguồn tín hiệu: các số trên trang này lấy từ cùng hàm với trang KPI/pháp nhân (afi pl, fact_tb). " + " | ".join(f"{r}: {v}" for r, v in fl))

    # ---------- 10. nghị quyết
    def s_resolutions(self):
        st = self.ST[None]
        title = f"Đề nghị HĐQT biểu quyết 3 nội dung, trong đó thông qua KQKD {self.per} với số liệu {st.label}"
        s = self.slide("RESOLUTION", title, st, "Đề xuất nghị quyết")
        items = [
            ("Nội dung 1 — Thông qua kết quả kinh doanh", f"HĐQT thông qua báo cáo kết quả kinh doanh {self.per} của Tập đoàn: doanh thu thuần hợp nhất (cộng gộp) {bn(self.A[None]['net_revenue'])} tỷ đồng, "
             f"EBITDA {bn(self.A[None]['ebitda'])} tỷ đồng, lợi nhuận sau thuế {bn(self.A[None]['net_profit'])} tỷ đồng (số liệu quản trị, trạng thái {st.label}, chưa kiểm toán)."),
            ("Nội dung 2 — Hành động khắc phục", "HĐQT giao Ban Điều hành thực hiện các hành động tại trang Giải trình biến động và báo cáo tiến độ tại kỳ họp sau. "
             f"{PLACEHOLDER} người chịu trách nhiệm, thời hạn."),
            ("Nội dung 3 — " + PLACEHOLDER, f"{PLACEHOLDER} văn bản cụ thể cần biểu quyết (ví dụ: hạn mức tín dụng, khoản đầu tư, điều chỉnh kế hoạch) — số tiền, điều kiện, người được ủy quyền."),
        ]
        y = Inches(1.55)
        for head, body in items:
            self.box(s, Inches(0.45), y, Inches(12.43), Inches(1.35), fill=PALE)
            self.text(s, [[(head, {"bold": True, "color": NAVY, "size": 13})], [(body, {"color": ORANGE if body.startswith(PLACEHOLDER) else INK})]],
                      Inches(0.65), y + Inches(0.1), Inches(12.0), Inches(1.2), 12)
            y += Inches(1.5)
        self.text(s, "Biểu quyết: Tán thành / Không tán thành / Ý kiến khác — ghi vào biên bản. Tài liệu gửi trước họp ≥ 5 ngày làm việc kèm biên bản kỳ trước.",
                  Inches(0.45), Inches(6.2), Inches(12.4), Inches(0.4), 10, MUTED)
        for k in ("net_revenue", "ebitda", "net_profit"):
            self.note_pl(s, LABEL[k], None, k, "A")

    # ---------- phụ lục
    def s_app_entities(self):
        cs = self.f.companies
        title = f"Phụ lục A1 — KQKD {self.per} từng pháp nhân và số cộng gộp (chưa loại trừ nội bộ {bn(self.A[None]['ic_revenue'])} tỷ doanh thu)"
        s = self.slide("APP-ENT", title, self.ST[None], "Phụ lục")
        rows = [["Chỉ tiêu"] + [SHORT[c] for c in cs] + ["Cộng gộp", "trong đó nội bộ"]]
        bold = []
        for k, lbl, sg, b in PL_ROWS:
            rows.append([lbl] + [bn(sg * self.A[c][k]) for c in cs] + [bn(sg * self.A[None][k]), bn(self.A[None]["ic_revenue"]) if k == "net_revenue" else ""])
            if b:
                bold.append(len(rows) - 1)
            for c in [*cs, None]:
                self.note_pl(s, lbl.strip(), c, k, "A")
        self.table(s, rows, Inches(0.45), Inches(1.5), [Inches(3.2)] + [Inches(1.6)] * len(cs) + [Inches(1.6), Inches(1.6)], Inches(0.32), 10, bold_rows=bold)

    def s_app_variances(self):
        allv = [v for c in [None, *self.f.companies] for v in self.VAR[c]]
        per_page = 6
        pages = max(1, (len(allv) + per_page - 1) // per_page)
        for p in range(pages):
            chunk = allv[p * per_page:(p + 1) * per_page]
            title = f"Phụ lục A2 — Bảng biến động vượt ngưỡng ({len(allv)} mục, trang {p + 1}/{pages}); diễn giải đầy đủ trong ghi chú trang"
            s = self.slide("APP-VAR", title, self.ST[None], "Phụ lục")
            rows = [["Phạm vi", "Chỉ tiêu", "So với", "Thực tế", "So sánh", "Δ", "Δ%", "Tại sao (từ dữ liệu, rút gọn)", "Hành động"]]
            for v in chunk:
                sg = -1 if v.line in ("cogs", "selling_expenses", "admin_expenses", "finance_expense") else 1
                why = v.why[0] if v.why else ""
                why = why if len(why) <= 150 else why[:147] + "…"
                rows.append([SHORT[v.cid], LABEL[v.line], "KH" if v.base == "KH" else "Cùng kỳ", bn(sg * v.actual), bn(sg * v.compare),
                             (signed_bn(sg * v.delta), GREEN if v.favourable else RED), pct(change(sg * v.actual, sg * v.compare)), why, (PLACEHOLDER, ORANGE)])
                self.note(s, f"[{SHORT[v.cid]} · {LABEL[v.line]} · so với {v.base}] Cái gì: {v.what} | Tại sao: {' '.join(v.why)} | "
                             f"Một lần/lặp lại: {v.recurring} | Hành động: {v.action}")
                self.note_pl(s, LABEL[v.line], v.cid, v.line, "A")
                self.note_pl(s, LABEL[v.line], v.cid, v.line, v.base)
            if len(rows) == 1:
                rows.append(["", f"Không có biến động vượt ngưỡng ({self.rules.text()})", "", "", "", "", "", "", ""])
            tbl = self.table(s, rows, Inches(0.45), Inches(1.5), [Inches(1.15), Inches(1.45), Inches(0.75), Inches(0.8), Inches(0.8), Inches(0.75),
                                                                  Inches(0.75), Inches(4.65), Inches(1.33)], Inches(0.78), 9)
            tbl.rows[0].height = Inches(0.32)
            for i in range(len(rows)):
                for j in (1, 2, 7, 8):
                    tbl.cell(i, j).text_frame.paragraphs[0].alignment = PP_ALIGN.LEFT

    def s_app_status(self):
        st = self.ST[None]
        trend = [shift(self.month, -i) for i in range(5, -1, -1)]
        title = f"Phụ lục A3 — Trạng thái dữ liệu: hợp nhất {st.label}; {sum(1 for r in self.f.controls if r['status'] == 'FAIL')} kiểm soát FAIL trên toàn warehouse"
        s = self.slide("APP-DQ", title, st, "Phụ lục")
        months = sorted(set(self.months) | set(trend))
        rows = [["Pháp nhân"] + [month_label(m) for m in months]]
        for c in self.f.companies:
            r = [SHORT[c]]
            for m in months:
                v = self.f.status_map.get(f"{c}|{m}", "CHƯA CÓ")
                col = GREEN if v == "APPROVED" else BLUE if v == "RECONCILED" else ORANGE
                r.append((v.replace("RECONCILIATION_FAILED", "FAILED"), col))
            rows.append(r)
        wcol = min(Inches(1.15), int((Inches(12.4) - Inches(1.6)) / len(months)))
        self.table(s, rows, Inches(0.45), Inches(1.5), [Inches(1.6)] + [wcol] * len(months), Inches(0.34), 8.5, align_num=False)
        fails = [r for r in self.f.controls if r["status"] != "PASS" and (r["company_id"], r["period"][:7]) and any(m in r["period"] for m in months)]
        lines = [f"Kiểm soát (afi reconcile): FILE_TOTALS, GL_DR_EQ_CR, TB_DR_EQ_CR, TB_ROLLFORWARD, TB_EQ_GL_MOVEMENT, REVENUE_BRIDGE; GL_VOUCHER_BALANCE là cảnh báo.",
                 "APPROVED = đã đối chiếu và CFO duyệt trong data/approvals.yaml · RECONCILED = qua mọi kiểm soát, chưa duyệt · SƠ BỘ = có kiểm soát FAIL hoặc thiếu dữ liệu."]
        lines += [f"• {r['status']} {r['control']} {r['company_id']} {r['period']}: {r['detail'][:140]}" for r in fails[:8]] or ["• Không có kiểm soát FAIL/WARN trong các tháng hiển thị."]
        self.text(s, lines, Inches(0.45), Inches(1.6) + Inches(0.34) * (len(rows)), Inches(12.4), Inches(3.2), 10)
        self.note(s, "Bảng trạng thái lấy từ period_status(run_controls(warehouse), data/approvals.yaml) — giống lệnh afi reconcile; chi tiết: data/dq/dq_report.md.")

    def s_app_method(self):
        title = "Phụ lục A4 — Phương pháp: số liệu đọc từ warehouse alta-finance-intelligence, chính sách P1–P8 đang ở trạng thái đề xuất"
        s = self.slide("APP-METHOD", title, None, "Phụ lục")
        miss = self.f.plan_lines_missing()
        lines = [
            [("Nguồn: ", {"bold": True}), ("KQKD = mart_pl_monthly (afi pl), cộng từng tháng; số dư = fact_tb (CĐPS, TK lá); dòng tiền = fact_gl_lines TK 111/112/113. "
                                           "Mỗi số có ghi chú nguồn (file, dòng Excel) trong speaker notes.", {})],
            [("Chính sách: ", {"bold": True}), ("P1 loại bút toán kết chuyển 911 · P2 doanh thu thuần 511−521 · P3 lãi vay (TK 635 có diễn giải lãi vay hoặc đối ứng 335/341/3388/311) · "
                                                "P4 EBITDA = LNTT + lãi vay + Có TK 214 · P5 doanh thu nội bộ theo MST (chưa loại trừ) · P7 dòng tiền theo TK đối ứng · P8 DSO/DIO/DPO. "
                                                "Tất cả đang [PROPOSED POLICY] — docs/accounting_policies.md.", {})],
            [("So sánh: ", {"bold": True}), (f"Kế hoạch = {Path(self.f.plan_path).name if self.f.plan_path else 'không có file'}"
                                             + (f" (thiếu dòng: {', '.join(miss)})" if miss else "") + f"; cùng kỳ = {self._mtxt(self.py)}.", {})],
            [("Bình luận biến động: ", {"bold": True}), (f"chỉ khi {self.rules.text()}. Cái gì → Tại sao (tách thành phần, khách hàng/tài khoản, dòng gốc) → "
                                                         "Một lần/lặp lại (so tháng trước) → Hành động (CFO điền). Không suy đoán nguyên nhân ngoài dữ liệu.", {})],
            [("Đánh giá Xanh/Vàng/Đỏ: ", {"bold": True}), ("EBITDA ≥ 95% kế hoạch (hoặc cùng kỳ nếu chưa có KH) → Xanh; 85–95% → Vàng; < 85% hoặc LNST âm → Đỏ.", {})],
            [("Định dạng: ", {"bold": True}), ("tỷ đồng, 1 chữ số thập phân, số âm trong ngoặc; chi phí hiển thị âm trong bảng KQKD; Δ% = (A − B) / |B|.", {})],
            [("Hạn chế: ", {"bold": True}), ("chưa loại trừ nội bộ trong số hợp nhất; chưa có sản lượng (không tách giá/lượng); chưa có dòng tiền 13 tuần và covenant; "
                                             "khách hàng theo 'Tên khách' trên sổ cái (chưa có danh mục đối tượng — Phase 1).", {})],
        ]
        self.text(s, lines, Inches(0.45), Inches(1.55), Inches(12.4), Inches(5.3), 12)
        self.note(s, "Trang phương pháp — không có số liệu.")


def build_deck(facts: Facts, month: str, mode: str, out: Path, rules: Rules | None = None, sample: bool = False) -> tuple[Path, Deck]:
    d = Deck(facts, month, mode, rules, sample)
    prs = d.build()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(out)
    return out, d
