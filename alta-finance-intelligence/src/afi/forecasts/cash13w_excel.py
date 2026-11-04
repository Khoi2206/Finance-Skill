"""Excel output for the 13-week cash forecast.

The weekly bridge sheets are formulas: each line = SUMIFS over `Chi_tiet` (one row per forecast item,
with its placed week and amount per scenario); opening = SUMIFS over verified rows in `Tien_dau_ky`;
closing = opening + receipts + payments (+ intercompany for an entity). Editing an amount or week in
`Chi_tiet` (blue input cells) flows through the bridge.
"""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .cash13w import CONF_LABEL, GROUP, LINES, WEEKS

NUM = '#,##0;(#,##0);"-"'
BLUE = Font(color="0000FF")
BOLD = Font(bold=True)
HEAD = PatternFill("solid", fgColor="DDE4EE")
TOTAL = PatternFill("solid", fgColor="F2F2F2")
RED = Font(bold=True, color="C00000")
SC_LABEL = {"base": "Base", "downside": "Downside"}
SEV = {"LOAI_TRU": "Loại khỏi dự báo", "THIEU_TT": "Đã tính — thiếu thông tin", "THONG_TIN": "Thông tin"}


def _hdr(ws, row, values):
    for i, v in enumerate(values, 1):
        c = ws.cell(row, i, v)
        c.font, c.fill = BOLD, HEAD
        c.alignment = Alignment(wrap_text=True, vertical="top")


def _widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def write_excel(res: dict, path: Path) -> Path:
    wb = openpyxl.Workbook()
    sample = "DỮ LIỆU MẪU TỔNG HỢP — KHÔNG PHẢI SỐ THẬT. " if res.get("sample") else ""
    names = {e["id"]: e["name"] for e in res["entities"]}
    cos = [e["id"] for e in res["entities"]]

    # --- Tom_tat
    ws = wb.active
    ws.title = "Tom_tat"
    ws["A1"] = "Dòng tiền 13 tuần (direct method) — Alta Group"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"{sample}Phiên bản {res['version_id']} · bắt đầu {res['start_date']} · {res['status_label']}"
    ws["A3"] = f"Chính sách phân loại thực tế: cash_flow_map.yaml v{res['policy']['cash_flow_map_version']} ({res['policy']['cash_flow_map_status']}). Đơn vị: VND."
    _hdr(ws, 5, ["Pháp nhân", "Kịch bản", "Tiền đầu kỳ (đã xác minh)", "Tiền cuối T13", "Tiền thấp nhất", "Tuần thấp nhất",
                 "Ngưỡng tối thiểu", "Headroom thấp nhất", "Tuần dưới ngưỡng"])
    r = 6
    for co in cos + [GROUP]:
        for sc in ("base", "downside"):
            v = res["views"][co]["scenarios"][sc]
            vals = [res["views"][co]["name"], SC_LABEL[sc], v["opening"][0], v["closing"][-1], v["min_closing"], v["min_closing_week"],
                    v["floor"][0], v["min_headroom"], ", ".join(map(str, v["breach_weeks"])) or "—"]
            for i, x in enumerate(vals, 1):
                c = ws.cell(r, i, x)
                if i in (3, 4, 5, 7, 8):
                    c.number_format = NUM
            if v["breach_weeks"]:
                ws.cell(r, 9).font = RED
            r += 1
    n_block = sum(1 for i in res["data_required"] if i["severity"] == "LOAI_TRU")
    ws.cell(r + 1, 1, f"DATA REQUIRED: {len(res['data_required'])} mục ({n_block} mục bị loại khỏi dự báo) — xem sheet DATA_REQUIRED").font = BOLD
    _widths(ws, [30, 11, 20, 18, 18, 10, 18, 20, 16])

    # --- Tien_dau_ky
    wo = wb.create_sheet("Tien_dau_ky")
    _hdr(wo, 1, ["Công ty", "Ngân hàng", "Số TK", "Ngày", "Số dư", "Bị hạn chế", "Khả dụng", "Người xác minh", "Nguồn", "Dòng", "Dùng làm đầu kỳ"])
    for i, d in enumerate(res["opening_detail"], 2):
        vals = [d["company"], d["bank"], d["bank_account"], d["date"], d["balance"], d["restricted"], None, d["verified_by"], d["source"], d["row"],
                "Có" if d["used"] else "Không"]
        for j, x in enumerate(vals, 1):
            c = wo.cell(i, j, x)
            if j in (5, 6):
                c.font, c.number_format = BLUE, NUM
        wo.cell(i, 7, f"=IF(ISNUMBER(E{i}),E{i}-F{i},0)").number_format = NUM
    _widths(wo, [8, 16, 18, 11, 18, 16, 18, 18, 22, 20, 10])

    # --- Chi_tiet
    wd = wb.create_sheet("Chi_tiet")
    cols = ["Nguồn (file:dòng)", "Công ty", "Dòng", "Đối tác", "Tham chiếu", "Ngày đến hạn", "Ngày dự kiến", "Cơ sở ngày",
            "Số tiền gốc (±)", "Tin cậy", "Người phụ trách", "Nội bộ với", "Được tính", "Tuần Base", "Số tiền Base", "Tuần Downside", "Số tiền Downside"]
    _hdr(wd, 1, cols)
    for i, it in enumerate(res["items"], 2):
        pb, pd = it["placement"].get("base", {}), it["placement"].get("downside", {})
        vals = [it["source"], it["company"], it["line"], it["counterparty"], it["reference"], it["due_date"], it["expected_date"], it["expected_basis"],
                it["amount"], CONF_LABEL.get(it["confidence"], it["confidence"]), it["owner"], it["ic_company"], "Có" if it["included"] else "Không",
                pb.get("week"), pb.get("amount"), pd.get("week"), pd.get("amount")]
        for j, x in enumerate(vals, 1):
            c = wd.cell(i, j, x)
            if j in (9, 15, 17):
                c.number_format = NUM
            if j in (14, 15, 16, 17):
                c.font = BLUE
    last = max(2, len(res["items"]) + 1)
    _widths(wd, [20, 8, 18, 26, 22, 11, 11, 10, 17, 10, 16, 9, 8, 8, 17, 9, 17])
    wd.freeze_panes = "A2"

    # --- bridge sheets with formulas
    rng = lambda col: f"Chi_tiet!${col}$2:${col}${last}"  # noqa: E731
    for sc, wcol, acol in (("base", "N", "O"), ("downside", "P", "Q")):
        for co in cos + [GROUP]:
            title = f"{'Base' if sc == 'base' else 'Down'}_{'HopNhat' if co == GROUP else co}"
            wsb = wb.create_sheet(title)
            v = res["views"][co]["scenarios"][sc]
            wsb["A1"] = f"{res['views'][co]['name']} — {SC_LABEL[sc]} — cầu nối tiền theo tuần"
            wsb["A1"].font = Font(bold=True, size=12)
            wsb["A2"] = sample + ("Hợp nhất: loại trừ dòng nội bộ; tiền đầu kỳ = tổng các pháp nhân." if co == GROUP else "Theo pháp nhân: dòng nội bộ giữ nguyên.")
            _hdr(wsb, 4, ["Khoản mục", "Mã dòng"] + [w["label"] for w in res["weeks"]])
            wsb.cell(5, 1, "Tuần số").font = Font(italic=True, color="808080")
            for w in range(WEEKS):
                wsb.cell(5, 3 + w, w + 1).font = Font(italic=True, color="808080")
            row = 6
            r_open = row
            wsb.cell(row, 1, "Tiền khả dụng đầu kỳ").font = BOLD
            row += 1
            line_rows = {"in": [], "out": [], "ic": []}
            for lid, label, kind in LINES:
                if kind == "un" or (co == GROUP and kind == "ic"):
                    continue
                if kind == "out" and not line_rows["out"]:
                    wsb.cell(row, 1, "Tổng thu").font = BOLD
                    r_in = row
                    row += 1
                if kind == "ic":
                    wsb.cell(row, 1, "Tổng chi").font = BOLD
                    r_out = row
                    row += 1
                wsb.cell(row, 1, ("   " if kind != "ic" else "") + label)
                wsb.cell(row, 2, lid).font = Font(color="808080")
                for w in range(WEEKS):
                    cl = get_column_letter(3 + w)
                    crit = f'{rng("C")},$B{row},{rng(wcol)},{cl}$5' + ("" if co == GROUP else f',{rng("B")},"{co}"')
                    wsb.cell(row, 3 + w, f"=SUMIFS({rng(acol)},{crit})").number_format = NUM
                line_rows[kind].append(row)
                row += 1
            if co == GROUP:
                wsb.cell(row, 1, "Tổng chi").font = BOLD
                r_out = row
                row += 1
            r_ic = None
            if co != GROUP:
                r_ic = line_rows["ic"][0]
            r_close = row
            wsb.cell(row, 1, "Tiền khả dụng cuối kỳ").font = BOLD
            r_floor, r_head, r_und, r_liq = row + 1, row + 2, row + 3, row + 4
            wsb.cell(r_floor, 1, "Ngưỡng thanh khoản tối thiểu")
            wsb.cell(r_head, 1, "Headroom (cuối kỳ − ngưỡng)").font = BOLD
            wsb.cell(r_und, 1, "Hạn mức cam kết chưa sử dụng")
            wsb.cell(r_liq, 1, "Thanh khoản khả dụng (cuối kỳ + hạn mức)").font = BOLD
            wsb.cell(r_liq + 2, 1, "Kiểm tra: đầu + thu + chi" + ("" if co == GROUP else " ± nội bộ") + " − cuối (phải = 0)").font = Font(italic=True)
            for w in range(WEEKS):
                cl = get_column_letter(3 + w)
                if w == 0:
                    if co == GROUP:
                        f = f'=SUMIFS(Tien_dau_ky!$G:$G,Tien_dau_ky!$K:$K,"Có")'
                    else:
                        f = f'=SUMIFS(Tien_dau_ky!$G:$G,Tien_dau_ky!$A:$A,"{co}",Tien_dau_ky!$K:$K,"Có")'
                else:
                    f = f"={get_column_letter(2 + w)}{r_close}"
                wsb.cell(r_open, 3 + w, f).number_format = NUM
                wsb.cell(r_in, 3 + w, f"=SUM({cl}{line_rows['in'][0]}:{cl}{line_rows['in'][-1]})").number_format = NUM
                wsb.cell(r_out, 3 + w, f"=SUM({cl}{line_rows['out'][0]}:{cl}{line_rows['out'][-1]})").number_format = NUM
                ic = f"+{cl}{r_ic}" if r_ic else ""
                wsb.cell(r_close, 3 + w, f"={cl}{r_open}+{cl}{r_in}+{cl}{r_out}{ic}").number_format = NUM
                fl = v["floor"][w]
                c = wsb.cell(r_floor, 3 + w, fl)
                c.number_format, c.font = NUM, BLUE
                wsb.cell(r_head, 3 + w, f'=IF(ISNUMBER({cl}{r_floor}),{cl}{r_close}-{cl}{r_floor},"DATA REQUIRED")').number_format = NUM
                c = wsb.cell(r_und, 3 + w, v["undrawn"][w])
                c.number_format = NUM
                wsb.cell(r_liq, 3 + w, f"={cl}{r_close}+{cl}{r_und}").number_format = NUM
                wsb.cell(r_liq + 2, 3 + w, f"=ROUND({cl}{r_open}+{cl}{r_in}+{cl}{r_out}{ic}-{cl}{r_close},0)").number_format = NUM
            for rr in (r_open, r_in, r_out, r_close, r_head, r_liq):
                for w in range(WEEKS + 2):
                    wsb.cell(rr, 1 + w).fill = TOTAL
            wsb.column_dimensions["A"].width = 40
            wsb.column_dimensions["B"].width = 16
            wsb.column_dimensions["B"].hidden = False
            for w in range(WEEKS):
                wsb.column_dimensions[get_column_letter(3 + w)].width = 15
            wsb.freeze_panes = "C6"

    # --- actuals
    wa = wb.create_sheet("Thuc_te_13T")
    wa["A1"] = sample + "13 tuần thực tế (từ fact_gl_lines, dòng TK 111/112/113; chuyển tiền giữa TK tiền đã loại)."
    row = 3
    for co in cos + [GROUP]:
        av = res["views"][co]["actuals"]
        wa.cell(row, 1, res["views"][co]["name"]).font = BOLD
        _hdr(wa, row + 1, ["Khoản mục", "Mã dòng"] + [w["label"] for w in res["actual_weeks"]])
        r0 = row + 2
        rr = r0
        for lid, label, kind in LINES:
            if co == GROUP and kind == "ic":
                continue
            wa.cell(rr, 1, label)
            wa.cell(rr, 2, lid)
            for w in range(WEEKS):
                wa.cell(rr, 3 + w, av["lines"][lid][w]).number_format = NUM
            rr += 1
        wa.cell(rr, 1, "Dòng tiền thuần").font = BOLD
        wa.cell(rr + 1, 1, "Có dữ liệu sổ?")
        for w in range(WEEKS):
            cl = get_column_letter(3 + w)
            wa.cell(rr, 3 + w, f"=SUM({cl}{r0}:{cl}{rr - 1})").number_format = NUM
            wa.cell(rr + 1, 3 + w, "Có" if av["has_data"][w] else "DATA REQUIRED")
        row = rr + 3
    wa.column_dimensions["A"].width = 34
    wa.column_dimensions["B"].width = 18
    for w in range(WEEKS):
        wa.column_dimensions[get_column_letter(3 + w)].width = 15

    wl = wb.create_sheet("Thuc_te_dong")
    _hdr(wl, 1, ["Công ty", "Ngày", "Tuần", "TK", "TK đ/ư", "Nhóm (cash_flow_map)", "Dòng 13W", "Số tiền (±)", "Đối tượng", "Số CT", "Diễn giải", "File", "Dòng Excel"])
    for i, a in enumerate(res["actual_rows"], 2):
        for j, x in enumerate([a["company"], a["date"], a["week"], a["account"], a["contra"], a["category"], a["line"] or "(loại: nội bộ TK tiền)",
                               a["amount"], a["counterparty"], a["document"], a["description"], a["file"], a["row"]], 1):
            c = wl.cell(i, j, x)
            if j == 8:
                c.number_format = NUM
    _widths(wl, [8, 11, 6, 8, 8, 24, 18, 17, 14, 10, 28, 34, 8])

    # --- comparison
    wc = wb.create_sheet("So_sanh")
    cmp_ = res["comparison"]
    if not cmp_.get("prior_version_id"):
        wc["A1"] = cmp_.get("message")
    else:
        wc["A1"] = f"So với phiên bản {cmp_['prior_version_id']} (bắt đầu {cmp_['prior_start_date']})"
        wc["A1"].font = BOLD
        _hdr(wc, 3, ["Pháp nhân", "Tiền cuối tuần đã qua theo dự báo trước", "Tiền đầu kỳ đã xác minh", "Chênh lệch"])
        r = 4
        for o in cmp_["opening_check"]:
            for j, x in enumerate([o["company"], o["prior_forecast_closing"], o["verified_opening"], None], 1):
                wc.cell(r, j, x).number_format = NUM
            wc.cell(r, 4, f"=C{r}-B{r}").number_format = NUM
            r += 1
        r += 1
        wc.cell(r, 1, f"Thực tế vs dự báo tuần trước (Base) — cần giải thích khi |chênh| > {cmp_['threshold_pct']:.0f}% và ≥ {cmp_['materiality']:,.0f}").font = BOLD
        r += 1
        _hdr(wc, r, ["Pháp nhân", "Tuần", "Dòng", "Dự báo", "Thực tế", "Chênh lệch", "%", "Cần giải thích", "Trạng thái"])
        r += 1
        for x in cmp_["week_variance"]:
            vals = [x["company"], x["week_start"], x["line"], x["forecast"], x["actual"], None, None, "CÓ" if x["needs_explanation"] else "", x["status"]]
            for j, y in enumerate(vals, 1):
                wc.cell(r, j, y).number_format = NUM
            if x["actual"] is not None:
                wc.cell(r, 6, f"=E{r}-D{r}").number_format = NUM
                wc.cell(r, 7, f'=IF(D{r}=0,"",F{r}/ABS(D{r}))').number_format = "0.0%"
            else:
                wc.cell(r, 5, "DATA REQUIRED")
            if x["needs_explanation"]:
                wc.cell(r, 8).font = RED
            r += 1
        r += 1
        wc.cell(r, 1, "Roll-forward tiền cuối tuần (Base): dự báo trước → dự báo này").font = BOLD
        r += 1
        _hdr(wc, r, ["Pháp nhân", "Tuần", "Dự báo trước", "Dự báo này", "Thay đổi"])
        r += 1
        for co, d in cmp_["rollforward"].items():
            for x in d["base"]:
                for j, y in enumerate([co, x["week_start"], x["prior_closing"], x["current_closing"], None], 1):
                    wc.cell(r, j, y).number_format = NUM
                if x["prior_closing"] is not None:
                    wc.cell(r, 5, f"=D{r}-C{r}").number_format = NUM
                r += 1
    _widths(wc, [12, 22, 22, 18, 18, 18, 9, 14, 16])

    # --- DATA_REQUIRED
    wr = wb.create_sheet("DATA_REQUIRED")
    _hdr(wr, 1, ["Mức", "Công ty", "Nguồn", "Trường", "Tham chiếu", "Số tiền", "Nội dung", "Người phụ trách bổ sung", "Hạn"])
    for i, x in enumerate(res["data_required"], 2):
        for j, y in enumerate([SEV.get(x["severity"], x["severity"]), x["company"], x["source"], x["field"], x["reference"], x["amount"], x["message"], "", ""], 1):
            c = wr.cell(i, j, y)
            if j == 6:
                c.number_format = NUM
            if j in (8, 9):
                c.font = BLUE
    _widths(wr, [22, 8, 22, 20, 22, 17, 70, 20, 11])
    wr.freeze_panes = "A2"

    # --- Tham_so
    wp = wb.create_sheet("Tham_so")
    wp["A1"] = "Tham số kịch bản [PROPOSED POLICY] — CFO duyệt"
    wp["A1"].font = BOLD
    rows = []

    def flat(prefix, d):
        for k, v in d.items():
            if isinstance(v, dict):
                flat(f"{prefix}{k}.", v)
            else:
                rows.append((prefix + k, ", ".join(map(str, v)) if isinstance(v, list) else v))
    flat("", res["params"])
    for i, (k, v) in enumerate(rows, 3):
        wp.cell(i, 1, k)
        wp.cell(i, 2, v)
    r = len(rows) + 4
    wp.cell(r, 1, "Khách hàng lớn bị dời thu (Downside)").font = BOLD
    wp.cell(r, 2, ", ".join(res["key_customers_downside"]) or "—")
    _widths(wp, [48, 40])
    for sh in wb.worksheets:
        sh.sheet_view.showGridLines = sh.title not in ("Tom_tat",)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path
