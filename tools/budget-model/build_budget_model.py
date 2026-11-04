#!/usr/bin/env python3
"""Sinh mô hình Excel Dự báo cả năm & Ngân sách theo driver cho Alta Group.

Mọi kết quả là CÔNG THỨC Excel thật; ô nhập màu xanh; mỗi giả định có cột nguồn/ghi chú.

    python build_budget_model.py                                # dữ liệu mẫu → output/
    python build_budget_model.py --actuals actuals.csv --opening-bs opening_bs.csv \\
        --assumptions assumptions.csv --actual-through 2026-09 --budget-year 2027 --recalc
    python build_budget_model.py --write-templates templates/   # CSV mẫu đầu vào
    python build_budget_model.py --dump-assumptions gia_dinh.csv # xuất giả định hiện hành để BU sửa

Định dạng CSV (UTF-8, có dòng tiêu đề):
  actuals.csv     company,month,line,amount[,source]   — đúng output `afi export-pl` (đồng)
  opening_bs.csv  company,line,amount                   — số dư cuối tháng thực tế cuối cùng (đồng)
  assumptions.csv key,period,value[,source]             — period = YYYY-MM hoặc D (giá trị cố định)
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
from copy import copy
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sample_data as sd  # noqa: E402

COMPANIES = {  # id (= company_id của afi): sheet BCTC, tên, MST
    "ALTA": ("FS_Me", "Alta (Mẹ)", "0301420079"),
    "APL": ("FS_Plastic", "Alta Plastic", "0312414944"),
    "AME": ("FS_Media", "Alta Media", "0305904835"),
}
CO_LOWER = {"ALTA": "alta", "APL": "apl", "AME": "ame"}
BASE_LINES = ["net_revenue", "cogs", "selling_expenses", "admin_expenses", "finance_income", "finance_expense",
              "other_income", "other_expense", "income_tax", "depreciation"]
IC_LINES = ["ic_revenue", "ic_interest"]
LINE_VN = {
    "net_revenue": "Doanh thu thuần (511−521)", "cogs": "Giá vốn hàng bán (632, gồm khấu hao)",
    "selling_expenses": "Chi phí bán hàng (641)", "admin_expenses": "Chi phí QLDN (642)",
    "finance_income": "Doanh thu tài chính (515)", "finance_expense": "Chi phí tài chính (635)",
    "other_income": "Thu nhập khác (711)", "other_expense": "Chi phí khác (811)",
    "income_tax": "Chi phí thuế TNDN (821)", "depreciation": "Ghi nhớ: Khấu hao (phát sinh Có 214)",
    "gross_profit": "Lợi nhuận gộp", "profit_before_tax": "Lợi nhuận trước thuế", "net_profit": "Lợi nhuận sau thuế",
    "ebitda": "EBITDA (P4: LNTT + CP tài chính + khấu hao)",
    "ic_revenue": "Ghi nhớ: doanh thu nội bộ (loại khỏi DT & GV)", "ic_interest": "Ghi nhớ: lãi vay nội bộ",
}
SCENARIOS = ["Base", "Target", "Downside"]
SCEN_FACTORS = [  # key, diễn giải, kiểu, Base, Target, Downside
    ("f_apl_vol", "Plastic — sản lượng (bao bì, hạt nhựa)", "×", 1.00, 1.05, 0.90),
    ("f_apl_price", "Plastic — giá bán bao bì", "×", 1.00, 1.02, 0.97),
    ("f_resin", "Giá hạt nhựa mua vào", "×", 1.00, 0.97, 1.08),
    ("f_p3d", "In 3D — số đơn hàng", "×", 1.00, 1.10, 0.85),
    ("f_ame_jobs", "Media — số job ký mới", "×", 1.00, 1.10, 0.80),
    ("f_ame_value", "Media — giá trị bình quân/job", "×", 1.00, 1.05, 0.95),
    ("f_ame_gm", "Media — biên gộp (cộng điểm %)", "+", 0.00, 0.02, -0.03),
    ("f_me_occ", "Mẹ — tỷ lệ lấp đầy (cộng điểm %)", "+", 0.00, 0.05, -0.10),
    ("f_me_rent", "Mẹ — đơn giá thuê bên ngoài", "×", 1.00, 1.02, 0.97),
    ("f_me_tech", "Mẹ — doanh thu dự án công nghệ", "×", 1.00, 1.10, 0.80),
    ("f_opex", "Chi phí hoạt động cố định (ngoài nhân sự)", "×", 1.00, 0.98, 1.03),
    ("f_rate", "Lãi suất vay ngân hàng (cộng điểm %)", "+", 0.00, 0.00, 0.01),
    ("f_dso", "Số ngày phải thu khách hàng (cộng ngày)", "+", 0, -5, 10),
]

# ------------------------------------------------------------------ styles
F_TITLE = Font(bold=True, size=14, color="1F3864")
F_BANNER = Font(bold=True, color="C00000")
F_BOLD = Font(bold=True)
F_INPUT = Font(color="0000FF")
F_SEC = Font(bold=True, color="FFFFFF")
FILL_INPUT = PatternFill("solid", fgColor="DDEBF7")
FILL_SEC = PatternFill("solid", fgColor="1F3864")
FILL_HDR = PatternFill("solid", fgColor="D9E1F2")
FILL_TOT = PatternFill("solid", fgColor="F2F2F2")
FILL_BAD = PatternFill("solid", fgColor="FFC7CE")
FILL_OK = PatternFill("solid", fgColor="C6EFCE")
THIN_TOP = Border(top=Side(style="thin"))
FMT = {
    "money": '#,##0;(#,##0);"-"', "money1": '#,##0.0;(#,##0.0);"-"', "pct": '0.0%;(0.0%);"-"',
    "int": '#,##0;(#,##0);"-"', "num": '#,##0.00;(#,##0.00);"-"', "check": '#,##0.000;(#,##0.000);"-"',
    "x": '0.00"x"', "text": "@", "date": "mm/yyyy", "year": "0",
}
FIRST = 5  # cột E = tháng đầu tiên

REF = re.compile(r"\[\[([A-Za-z_0-9]*)\.([A-Za-z_0-9]+)(?:~([A-Za-z_0-9]+))?(?:@(\$?[A-Z]+|p))?\]\]")


def fac(k: str) -> str:
    """Hệ số kịch bản nhân (chỉ áp dụng khi Assumptions.scen_on = 1)."""
    return f"(1+[[Assumptions.scen_on]]*([[Scenarios.{k}@G]]-1))"


def add(k: str) -> str:
    """Điều chỉnh kịch bản cộng thêm."""
    return f"([[Assumptions.scen_on]]*[[Scenarios.{k}@G]])"


class Row:
    def __init__(self, kind, key=None, label="", unit="", note="", f=None, inputs=None, d=None, total="sum",
                 fmt="money", bold=False, d_input=False, months=True):
        self.kind, self.key, self.label, self.unit, self.note = kind, key, label, unit, note
        self.f, self.inputs, self.d, self.total, self.fmt = f, inputs, d, total, fmt
        self.bold, self.d_input, self.months = bold, d_input, months
        self.r = None
        self.percol = None  # danh sách công thức theo từng cột tháng (khi không dùng mẫu chung)


class MSheet:
    """Sheet theo tháng: A nhãn · B ĐVT · C nguồn/ghi chú · D đầu kỳ/cố định · E… tháng · tổng theo năm."""

    def __init__(self, model, name, title, d_header="Đầu kỳ / cố định", start=7):
        self.m, self.name, self.title, self.d_header = model, name, title, d_header
        self.rows: list[Row] = []
        self.next = start
        model.sheets[name] = self
        model.layout[name] = {}

    def _push(self, row: Row):
        row.r = self.next
        self.next += 1
        if row.key:
            if row.key in self.m.layout[self.name]:
                raise KeyError(f"{self.name}.{row.key} trùng")
            self.m.layout[self.name][row.key] = row.r
        self.rows.append(row)
        return row

    def sec(self, label):
        self._push(Row("blank"))
        return self._push(Row("sec", label=label))

    def add(self, key, label, f=None, **kw):
        return self._push(Row("row", key, label, f=f, **kw))


class Model:
    def __init__(self, cfg):
        self.cfg = cfg
        self.sheets: dict[str, MSheet] = {}
        self.layout: dict[str, dict[str, int]] = {}
        y, m = cfg["actual_through"]
        self.months = []
        while True:
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
            if (y, m) > (cfg["budget_year"], 12):
                break
            self.months.append((y, m))
        if not self.months:
            raise SystemExit("Không có tháng dự báo: --actual-through phải trước tháng 12 năm ngân sách")
        self.years = []
        col = FIRST + len(self.months)
        for yr in sorted({y for y, _ in self.months}):
            idx = [i for i, (y, _) in enumerate(self.months) if y == yr]
            lab = f"Năm {yr}" if len(idx) == 12 else f"{yr}: {len(idx)} tháng DB"
            if yr == cfg["budget_year"]:
                lab = f"NGÂN SÁCH {yr}" if len(idx) == 12 else f"NS {yr} ({len(idx)} th)"
            self.years.append(dict(year=yr, label=lab, col=get_column_letter(col), idx=idx))
            col += 1
        self.last_col = col - 1
        self.fy = self.months[0][0]  # năm của tháng dự báo đầu tiên → sheet Forecast_FY

    def mcol(self, i):
        return get_column_letter(FIRST + i)

    def ycol(self, year):
        for y in self.years:
            if y["year"] == year:
                return y["col"]
        return None

    def mi(self, y, m):
        return self.months.index((y, m)) if (y, m) in self.months else None

    def ref(self, sheet, key, col, absolute=False):
        r = self.layout[sheet][key]
        return f"{sheet}!${col}${r}" if absolute else f"{sheet}!{col}{r}"

    def render(self, tpl, cur_sheet, col, prev):
        def sub(mo):
            sh, key, key2, at = mo.groups()
            sh = sh or cur_sheet
            try:
                r = self.layout[sh][key]
            except KeyError:
                raise KeyError(f"Tham chiếu không tồn tại: {sh}.{key} (trong {cur_sheet})")
            pre = "" if sh == cur_sheet else f"{sh}!"
            if at == "p":
                c = prev
                cell = f"{c}{r}"
            elif at:
                c = at.lstrip("$")
                cell = f"${c}${r}"
            else:
                c = col
                cell = f"{c}{r}"
            if key2:
                return f"{pre}{c}{r}:{c}{self.layout[sh][key2]}"
            return pre + cell
        return REF.sub(sub, tpl)


# ================================================================== xây các sheet theo tháng
def build_assumptions(M: Model, specs, overrides):
    S = MSheet(M, "Assumptions", "GIẢ ĐỊNH THEO BU & THEO THÁNG")
    S.add("date", "Tháng", inputs=[dt.date(y, m, 1) for y, m in M.months], fmt="date", total=None)
    S.add("is_bud", "Thuộc năm ngân sách (1/0)", "=IF(YEAR([[.date]])=[[.budget_year@D]],1,0)", fmt="int",
          total=None, note="Công thức")
    S.add("scen_on", "Áp dụng kịch bản (1 = có, 0 = giữ Base)",
          inputs=[1 if y == M.cfg["budget_year"] else 0 for y, _ in M.months], fmt="int", total=None,
          note="Mặc định chỉ áp kịch bản cho các tháng năm ngân sách; Q4 năm hiện hành giữ dự báo Base")
    secs = {"gen": "CHUNG — thuế, BHXH, quy đổi", "apl": "ALTA PLASTIC — bao bì, hạt nhựa, phế liệu, In 3D",
            "ame": "ALTA MEDIA — theo loại vụ việc LED/BA/TTB/DVK/TKL", "me": "ALTA (MẸ) — cho thuê, dự án, bán lại túi",
            "hr": "NHÂN SỰ", "opex": "CHI PHÍ HOẠT ĐỘNG", "fin": "CAPEX, KHẤU HAO, VAY"}
    order = ["gen", "apl", "ame", "me", "hr", "opex", "fin"]
    by = {s: [x for x in specs if x["sec"] == s] for s in order}
    for s in order:
        S.sec(secs[s] + f" · chủ trì: {sd.OWN.get(s, sd.OWN['gen'])}")
        for sp in by[s]:
            k = sp["key"]
            unit = sp["unit"]
            fmt = "pct" if unit.startswith("%") else ("year" if k == "budget_year" else
                                                      "num" if unit in ("kg/kg",) else "money")
            ov = overrides.get(k, {})
            src = ov.get("__source__") or default_source(sp)
            if sp["kind"] == "D":
                val = ov.get("D", M.cfg["budget_year"] if k == "budget_year" else sp["base"])
                S.add(k, sp["label"], unit=unit, note=src, d=val, d_input=True, fmt=fmt, total=None, months=False)
            else:
                vals = [ov.get(f"{y}-{m:02d}", sd.default_value(sp, y, m, M.cfg["budget_year"])) for y, m in M.months]
                tot = "avg" if (unit.startswith("đồng/") or unit.startswith("%") or unit in ("m²", "người")
                                or "/job" in unit or "/đơn" in unit) else "sum"
                S.add(k, sp["label"], unit=unit, note=src, inputs=vals, fmt=fmt, total=tot)
    return S


def default_source(sp):
    if sp["key"] in STRUCTURAL:
        return sp["note"]
    return sp["note"] + (" · " if sp["note"] else "") + "MẪU — thay bằng giả định BU"


STRUCTURAL = ("budget_year", "unit_vnd")


def sample_keys(specs, overrides):
    """Giả định còn là MẪU: không có trong CSV, hoặc nguồn trong CSV vẫn ghi 'MẪU'."""
    return [s["key"] for s in specs if s["key"] not in STRUCTURAL and
            (s["key"] not in overrides or "MẪU" in overrides[s["key"]].get("__source__", "MẪU"))]


def build_plastic(M):
    S = MSheet(M, "Drivers_Plastic", "DRIVER ALTA PLASTIC (MST 0312414944)")
    S.sec("BU Bao bì nhựa (APL-PACK)")
    S.add("vol_ext", "Sản lượng bán ngoài tập đoàn", f"=[[Assumptions.apl_vol_ext]]*{fac('f_apl_vol')}", unit="tấn",
          fmt="money1")
    S.add("vol_ic", "Sản lượng bán cho Alta (Mẹ) — nội bộ", f"=[[Assumptions.apl_vol_ic]]*{fac('f_apl_vol')}",
          unit="tấn", fmt="money1")
    S.add("vol_total", "Tổng sản lượng bao bì", "=[[.vol_ext]]+[[.vol_ic]]", unit="tấn", fmt="money1", bold=True)
    S.add("price_ext", "Giá bán bình quân (ngoài)", f"=[[Assumptions.apl_price_ext]]*{fac('f_apl_price')}",
          unit="đồng/kg", total="avg")
    S.add("price_ic", "Giá bán nội bộ cho Mẹ", f"=[[Assumptions.apl_price_ic]]*{fac('f_apl_price')}", unit="đồng/kg",
          total="avg")
    S.add("rev_pack_ext", "Doanh thu bao bì — ngoài tập đoàn", "=[[.vol_ext]]*[[.price_ext]]/1000", unit="triệu",
          note="tấn × đồng/kg ÷ 1.000 = triệu đồng")
    S.add("rev_ic", "Doanh thu bao bì — bán cho Mẹ (NỘI BỘ)", "=[[.vol_ic]]*[[.price_ic]]/1000", unit="triệu")
    S.add("resin_price", "Giá hạt nhựa mua vào", f"=[[Assumptions.resin_price]]*{fac('f_resin')}", unit="đồng/kg",
          total="avg")
    S.add("unit_cost", "Giá thành/kg = hạt nhựa × định mức + chuyển đổi",
          "=[[.resin_price]]*[[Assumptions.apl_resin_norm@D]]+[[Assumptions.apl_conv_cost]]", unit="đồng/kg",
          total="avg", note="Chưa gồm khấu hao (khấu hao ở sheet Capex)")
    S.add("cogs_pack", "Giá vốn bao bì", "=[[.vol_total]]*[[.unit_cost]]/1000", unit="triệu")
    S.add("gm_pack", "Biên gộp bao bì", "=IF([[.rev_pack_ext]]+[[.rev_ic]]=0,0,1-[[.cogs_pack]]/([[.rev_pack_ext]]+[[.rev_ic]]))",
          unit="%", fmt="pct", total="same")
    S.sec("Phế liệu")
    S.add("scrap_vol", "Phế liệu thu hồi", "=[[.vol_total]]*[[Assumptions.apl_scrap_rate@D]]", unit="tấn",
          fmt="money1")
    S.add("rev_scrap", "Doanh thu phế liệu", "=[[.scrap_vol]]*[[Assumptions.apl_scrap_price]]/1000", unit="triệu",
          note="Giá vốn đã nằm trong giá thành bao bì")
    S.sec("BU Thương mại hạt nhựa (APL-RESIN)")
    S.add("resin_vol", "Sản lượng hạt nhựa bán", f"=[[Assumptions.apl_resin_vol]]*{fac('f_apl_vol')}", unit="tấn",
          fmt="money1")
    S.add("resin_sell", "Giá bán hạt nhựa = giá mua × (1 + biên cộng)",
          "=[[.resin_price]]*(1+[[Assumptions.apl_resin_markup@D]])", unit="đồng/kg", total="avg")
    S.add("rev_resin", "Doanh thu thương mại hạt nhựa", "=[[.resin_vol]]*[[.resin_sell]]/1000", unit="triệu")
    S.add("cogs_resin", "Giá vốn thương mại hạt nhựa", "=[[.resin_vol]]*[[.resin_price]]/1000", unit="triệu")
    S.sec("BU In 3D (APL-3D) — tách riêng, KHÔNG phân bổ chi phí chung (chính sách P11)")
    S.add("p3d_orders", "Số đơn hàng In 3D", f"=[[Assumptions.p3d_orders]]*{fac('f_p3d')}", unit="đơn", fmt="money1")
    S.add("rev_3d", "Doanh thu In 3D", "=[[.p3d_orders]]*[[Assumptions.p3d_value]]", unit="triệu")
    S.add("cogs_3d", "Giá vốn In 3D", "=[[.rev_3d]]*(1-[[Assumptions.p3d_gm@D]])", unit="triệu")
    S.sec("Tổng hợp Plastic")
    S.add("rev_total", "Tổng doanh thu Plastic", "=[[.rev_pack_ext]]+[[.rev_ic]]+[[.rev_scrap]]+[[.rev_resin]]+[[.rev_3d]]",
          unit="triệu", bold=True)
    S.add("cogs_total", "Tổng giá vốn (chưa gồm khấu hao)", "=[[.cogs_pack]]+[[.cogs_resin]]+[[.cogs_3d]]",
          unit="triệu", bold=True)
    return S


def build_media(M):
    S = MSheet(M, "Drivers_Media", "DRIVER ALTA MEDIA (MST 0305904835) — theo tiền tố mã vụ việc")
    for code, name, *_ in sd.MEDIA_TYPES:
        c = code.lower()
        S.sec(f"{code} — {name}")
        S.add(f"{c}_jobs", "Số job ký mới", f"=[[Assumptions.ame_{c}_jobs]]*{fac('f_ame_jobs')}", unit="job",
              fmt="money1")
        S.add(f"{c}_value", "Giá trị bình quân/job", f"=[[Assumptions.ame_{c}_value]]*{fac('f_ame_value')}",
              unit="triệu/job", total="avg")
        S.add(f"{c}_orders", "Giá trị hợp đồng ký mới", f"=[[.{c}_jobs]]*[[.{c}_value]]", unit="triệu")
        S.add(f"{c}_bl_open", "Backlog đầu kỳ", f"=[[.{c}_bl_close@p]]", unit="triệu", total="first")
        S.add(f"{c}_rev", "Doanh thu ghi nhận",
              f"=[[.{c}_bl_open]]*[[Assumptions.ame_{c}_burn@D]]+[[.{c}_orders]]*[[Assumptions.ame_{c}_inm@D]]",
              unit="triệu", bold=True, note="backlog đầu kỳ × % ghi nhận + ký mới × % ghi nhận trong tháng")
        S.add(f"{c}_bl_close", "Backlog cuối kỳ", f"=[[.{c}_bl_open]]+[[.{c}_orders]]-[[.{c}_rev]]", unit="triệu",
              d=f"=[[Assumptions.ame_{c}_bl0@D]]", total="last")
        S.add(f"{c}_gm", "Biên lợi nhuận gộp", f"=[[Assumptions.ame_{c}_gm@D]]+{add('f_ame_gm')}", unit="%",
              fmt="pct", total=None)
        S.add(f"{c}_cogs", "Giá vốn (chi phí trực tiếp job)", f"=[[.{c}_rev]]*(1-[[.{c}_gm]])", unit="triệu")
    S.sec("Tổng hợp Media")
    codes = [c.lower() for c, *_ in sd.MEDIA_TYPES]
    S.add("rev_total", "Tổng doanh thu Media", "=" + "+".join(f"[[.{c}_rev]]" for c in codes), unit="triệu", bold=True)
    S.add("cogs_total", "Tổng giá vốn Media", "=" + "+".join(f"[[.{c}_cogs]]" for c in codes), unit="triệu", bold=True)
    S.add("backlog_total", "Tổng backlog cuối kỳ", "=" + "+".join(f"[[.{c}_bl_close]]" for c in codes), unit="triệu",
          total="last", d="=" + "+".join(f"[[.{c}_bl_close@D]]" for c in codes))
    return S


def build_me(M):
    S = MSheet(M, "Drivers_Me", "DRIVER ALTA (MẸ) (MST 0301420079)")
    S.sec("BU Cho thuê mặt bằng (ALTA-RENT)")
    S.add("area_total", "Tổng diện tích cho thuê được", "=[[Assumptions.me_area_total]]", unit="m²", total="avg")
    S.add("area_apl", "— cho Alta Plastic thuê (nội bộ)", "=[[Assumptions.me_area_apl]]", unit="m²", total="avg")
    S.add("area_ame", "— cho Alta Media thuê (nội bộ)", "=[[Assumptions.me_area_ame]]", unit="m²", total="avg")
    S.add("area_avail", "Diện tích dành cho bên ngoài", "=[[.area_total]]-[[.area_apl]]-[[.area_ame]]", unit="m²",
          total="avg")
    S.add("occ", "Tỷ lệ lấp đầy (bên ngoài)", f"=MIN(1,MAX(0,[[Assumptions.me_occ]]+{add('f_me_occ')}))", unit="%",
          fmt="pct", total="avg")
    S.add("area_let", "Diện tích bên ngoài đã thuê", "=[[.area_avail]]*[[.occ]]", unit="m²", total="avg")
    S.add("rent_ext", "Đơn giá thuê (ngoài)", f"=[[Assumptions.me_rent_ext]]*{fac('f_me_rent')}", unit="đồng/m²",
          total="avg")
    S.add("rev_rent_ext", "Doanh thu cho thuê — bên ngoài", "=[[.area_let]]*[[.rent_ext]]/1000000", unit="triệu",
          note="m² × đơn giá × lấp đầy")
    S.add("rev_rent_apl", "Doanh thu cho thuê — Alta Plastic (NỘI BỘ)", "=[[.area_apl]]*[[Assumptions.me_rent_ic]]/1000000",
          unit="triệu")
    S.add("rev_rent_ame", "Doanh thu cho thuê — Alta Media (NỘI BỘ)", "=[[.area_ame]]*[[Assumptions.me_rent_ic]]/1000000",
          unit="triệu")
    S.add("cogs_rent", "Chi phí vận hành mặt bằng", "=[[.area_total]]*[[Assumptions.me_opcost]]/1000000", unit="triệu",
          note="Chưa gồm khấu hao")
    S.sec("BU Thiết bị & dự án công nghệ (ALTA-TECH)")
    S.add("rev_tech", "Doanh thu thiết bị & dự án", f"=[[Assumptions.me_tech_rev]]*{fac('f_me_tech')}", unit="triệu")
    S.add("cogs_tech", "Giá vốn thiết bị & dự án", "=[[.rev_tech]]*(1-[[Assumptions.me_tech_gm@D]])", unit="triệu")
    S.sec("Bán lại túi bao bì (mua từ Alta Plastic)")
    S.add("bag_vol", "Sản lượng túi mua từ Plastic & bán ra", "=[[Drivers_Plastic.vol_ic]]", unit="tấn", fmt="money1",
          note="Giả định bán hết trong tháng (không tồn kho nội bộ → không có lãi chưa thực hiện)")
    S.add("rev_bag", "Doanh thu bán lại túi", "=[[.bag_vol]]*[[Assumptions.me_bag_price]]/1000", unit="triệu")
    S.add("cogs_bag", "Giá vốn túi = giá mua nội bộ từ Plastic (NỘI BỘ)", "=[[Drivers_Plastic.rev_ic]]", unit="triệu")
    S.sec("Tổng hợp Mẹ")
    S.add("rev_total", "Tổng doanh thu Mẹ",
          "=[[.rev_rent_ext]]+[[.rev_rent_apl]]+[[.rev_rent_ame]]+[[.rev_tech]]+[[.rev_bag]]", unit="triệu", bold=True)
    S.add("cogs_total", "Tổng giá vốn Mẹ", "=[[.cogs_rent]]+[[.cogs_tech]]+[[.cogs_bag]]", unit="triệu", bold=True)
    return S


def build_headcount(M):
    S = MSheet(M, "Headcount", "NHÂN SỰ & CHI PHÍ LƯƠNG (gián tiếp: bán hàng, QLDN, BU In 3D)")
    S.sec("Ghi chú: nhân công trực tiếp sản xuất (Plastic) và dự án (Media) nằm trong giá thành/biên gộp ở sheet Driver")
    S.add("factor", "Hệ số chi phí trên lương = 1 + BHXH phần DN + thưởng/12",
          d="=1+[[Assumptions.bhxh_rate@D]]+[[Assumptions.bonus_months@D]]/12", unit="lần", fmt="num", total=None,
          months=False, note="BHXH 21,5% — CẦN XÁC NHẬN với kế toán")
    for key, co, name, cls, bu, n, sal in sd.HEADCOUNT:
        S.sec(f"{name} · TK {cls}" + (" · BU In 3D" if bu == "3D" else ""))
        S.add(f"{key}_n", "Số người", f"=[[Assumptions.{key}_n]]", unit="người", fmt="money1", total="avg")
        S.add(f"{key}_sal", "Lương bình quân", f"=[[Assumptions.{key}_sal@D]]*(1+[[Assumptions.raise_rate@D]]*[[Assumptions.is_bud]])",
              unit="triệu/người", fmt="money1", total="avg")
        S.add(f"{key}_cost", "Chi phí nhân sự (lương + BHXH + thưởng)", f"=[[.{key}_n]]*[[.{key}_sal]]*[[.factor@D]]",
              unit="triệu", bold=True)
    S.sec("Tổng hợp theo công ty & tài khoản")
    for co in COMPANIES:
        for cls in ("641", "642"):
            ks = [k for k, c, _, cl, *_ in sd.HEADCOUNT if c == co and cl == cls]
            S.add(f"hc_{CO_LOWER[co]}_{cls}", f"{COMPANIES[co][1]} — nhân sự TK {cls}",
                  "=" + "+".join(f"[[.{k}_cost]]" for k in ks) if ks else "=0", unit="triệu", bold=True)
    S.add("hc_total", "Tổng chi phí nhân sự gián tiếp tập đoàn",
          "=" + "+".join(f"[[.hc_{CO_LOWER[co]}_{cls}]]" for co in COMPANIES for cls in ("641", "642")), unit="triệu",
          bold=True)
    S.add("hc_heads", "Tổng số người (gián tiếp)", "=" + "+".join(f"[[.{k}_n]]" for k, *_ in sd.HEADCOUNT), unit="người",
          fmt="money1", total="avg")
    return S


def rev_ext_ref(co):
    return {"ALTA": "([[Drivers_Me.rev_total]]-[[Drivers_Me.rev_rent_apl]]-[[Drivers_Me.rev_rent_ame]])",
            "APL": "([[Drivers_Plastic.rev_total]]-[[Drivers_Plastic.rev_ic]])",
            "AME": "[[Drivers_Media.rev_total]]"}[co]


def build_opex(M):
    S = MSheet(M, "Opex", "CHI PHÍ BÁN HÀNG (641) & QUẢN LÝ DOANH NGHIỆP (642)")
    for co in COMPANIES:
        lc = CO_LOWER[co]
        for cls, nm in (("641", "Chi phí bán hàng"), ("642", "Chi phí QLDN")):
            S.sec(f"{COMPANIES[co][1]} — {nm} (TK {cls})")
            parts = [f"[[.{lc}_{cls}_hc]]"]
            S.add(f"{lc}_{cls}_hc", "Nhân sự (từ Headcount)", f"=[[Headcount.hc_{lc}_{cls}]]", unit="triệu")
            for key, c, name, cl, kind, val, bu in sd.OPEX:
                if c != co or cl != cls:
                    continue
                if kind == "pct":
                    f = f"=[[Assumptions.{key}@D]]*{rev_ext_ref(co)}"
                    note = "% × doanh thu ngoài tập đoàn"
                else:
                    f = f"=[[Assumptions.{key}]]*{fac('f_opex')}"
                    note = "Giả định × hệ số kịch bản chi phí"
                S.add(key, name, f, unit="triệu", note=note)
                parts.append(f"[[.{key}]]")
            if cls == "642" and co in ("APL", "AME"):
                k = f"{lc}_ox_rent_ic"
                S.add(k, "Thuê mặt bằng của Alta (Mẹ) — NỘI BỘ", f"=[[Drivers_Me.rev_rent_{lc}]]", unit="triệu",
                      note="Bằng doanh thu cho thuê nội bộ của Mẹ")
                parts.append(f"[[.{k}]]")
            S.add(f"opex_{lc}_{cls}", f"Tổng {nm.lower()} — {COMPANIES[co][1]}", "=" + "+".join(parts), unit="triệu",
                  bold=True)
    return S


def build_capex(M, opening):
    S = MSheet(M, "Capex", "ĐẦU TƯ (CAPEX) & KHẤU HAO")
    for co in COMPANIES:
        lc = CO_LOWER[co]
        S.sec(f"{COMPANIES[co][1]}")
        S.add(f"capex_{lc}", "Capex trong tháng", f"=[[Assumptions.capex_{lc}]]", unit="triệu")
        S.add(f"dep_exist_{lc}", "Khấu hao tài sản hiện có", f"=[[Assumptions.dep_exist_{lc}]]", unit="triệu")
        S.add(f"dep_new_{lc}", "Khấu hao tài sản mới (đường thẳng, từ tháng sau khi đầu tư)",
              f"=(SUM([[.capex_{lc}@$E]]:[[.capex_{lc}]])-[[.capex_{lc}]])/([[Assumptions.life_{lc}@D]]*12)",
              unit="triệu")
        S.add(f"dep_{lc}", "Tổng khấu hao", f"=[[.dep_exist_{lc}]]+[[.dep_new_{lc}]]", unit="triệu", bold=True)
        S.add(f"fa_{lc}", "Giá trị còn lại TSCĐ cuối kỳ", f"=[[.fa_{lc}@p]]+[[.capex_{lc}]]-[[.dep_{lc}]]", unit="triệu",
              d=opening[co]["fa"], d_input=True, total="last", note="Đầu kỳ: số dư TSCĐ thuần (211+213−214)")
    return S


def build_debt(M, opening, ic):
    S = MSheet(M, "Debt", "LỊCH VAY & LÃI VAY")
    S.sec("Ghi chú: lãi tính trên dư nợ đầu tháng (tránh vòng lặp); trả gốc không vượt dư nợ")
    for co in COMPANIES:
        lc = CO_LOWER[co]
        S.sec(f"Vay ngân hàng — {COMPANIES[co][1]}")
        S.add(f"open_{lc}", "Dư nợ đầu kỳ", f"=[[.close_{lc}@p]]", unit="triệu", total="first")
        S.add(f"draw_{lc}", "Giải ngân", f"=[[Assumptions.draw_{lc}]]", unit="triệu")
        S.add(f"repay_{lc}", "Trả gốc", f"=MIN([[Assumptions.repay_{lc}]],[[.open_{lc}]]+[[.draw_{lc}]])", unit="triệu")
        S.add(f"close_{lc}", "Dư nợ cuối kỳ", f"=[[.open_{lc}]]+[[.draw_{lc}]]-[[.repay_{lc}]]", unit="triệu",
              d=opening[co]["loan_bank"], d_input=True, total="last", bold=True)
        S.add(f"rate_{lc}", "Lãi suất áp dụng", f"=[[Assumptions.rate_{lc}]]+{add('f_rate')}", unit="%/năm", fmt="pct",
              total="avg")
        S.add(f"int_{lc}", "Lãi vay", f"=[[.open_{lc}]]*[[.rate_{lc}]]/12", unit="triệu")
    S.sec("Vay nội bộ: Alta (Mẹ) cho Alta Media vay")
    S.add("icl_open", "Dư nợ đầu kỳ", "=[[.icl_close@p]]", unit="triệu", total="first")
    S.add("icl_draw", "Mẹ giải ngân thêm", "=[[Assumptions.icl_draw]]", unit="triệu")
    S.add("icl_repay", "Media trả gốc", "=MIN([[Assumptions.icl_repay]],[[.icl_open]]+[[.icl_draw]])", unit="triệu")
    S.add("icl_close", "Dư nợ cuối kỳ", "=[[.icl_open]]+[[.icl_draw]]-[[.icl_repay]]", unit="triệu",
          d=ic["ic_loan"], d_input=True, total="last", bold=True)
    S.add("icl_int", "Lãi vay nội bộ", "=[[.icl_open]]*[[Assumptions.icl_rate]]/12", unit="triệu")
    S.add("bank_total", "Tổng dư nợ ngân hàng tập đoàn", "=" + "+".join(f"[[.close_{CO_LOWER[c]}]]" for c in COMPANIES),
          unit="triệu", total="last", bold=True, d="=" + "+".join(f"[[.close_{CO_LOWER[c]}@D]]" for c in COMPANIES))
    return S


def build_fs(M, co, opening):
    sh, name, mst = COMPANIES[co]
    lc = CO_LOWER[co]
    S = MSheet(M, sh, f"BÁO CÁO TÀI CHÍNH THEO THÁNG — {name.upper()} (MST {mst}) · KQKD · CĐKT · LCTT",
               d_header="Số dư đầu kỳ")
    ob = opening[co]
    # --------------------------------------------------- KQKD
    S.sec("KẾT QUẢ KINH DOANH (quản trị)")
    if co == "ALTA":
        rev = [("rev_rent_ext", "Cho thuê mặt bằng — bên ngoài", "=[[Drivers_Me.rev_rent_ext]]"),
               ("rev_rent_apl", "Cho thuê mặt bằng — Alta Plastic (nội bộ)", "=[[Drivers_Me.rev_rent_apl]]"),
               ("rev_rent_ame", "Cho thuê mặt bằng — Alta Media (nội bộ)", "=[[Drivers_Me.rev_rent_ame]]"),
               ("rev_tech", "Thiết bị & dự án công nghệ", "=[[Drivers_Me.rev_tech]]"),
               ("rev_bag", "Bán lại túi bao bì", "=[[Drivers_Me.rev_bag]]")]
        cogs = [("cogs_rent", "Giá vốn cho thuê (vận hành mặt bằng)", "=[[Drivers_Me.cogs_rent]]"),
                ("cogs_tech", "Giá vốn thiết bị & dự án", "=[[Drivers_Me.cogs_tech]]"),
                ("cogs_bag", "Giá vốn túi mua từ Plastic (nội bộ)", "=[[Drivers_Me.cogs_bag]]")]
        rev_ic, cogs_ic = "[[.rev_rent_apl]]+[[.rev_rent_ame]]", "[[.cogs_bag]]"
    elif co == "APL":
        rev = [("rev_pack_ext", "Bao bì nhựa — ngoài tập đoàn", "=[[Drivers_Plastic.rev_pack_ext]]"),
               ("rev_ic", "Bao bì nhựa — bán cho Mẹ (nội bộ)", "=[[Drivers_Plastic.rev_ic]]"),
               ("rev_resin", "Thương mại hạt nhựa", "=[[Drivers_Plastic.rev_resin]]"),
               ("rev_scrap", "Phế liệu", "=[[Drivers_Plastic.rev_scrap]]"),
               ("rev_3d", "BU In 3D", "=[[Drivers_Plastic.rev_3d]]")]
        cogs = [("cogs_pack", "Giá vốn bao bì", "=[[Drivers_Plastic.cogs_pack]]"),
                ("cogs_resin", "Giá vốn hạt nhựa", "=[[Drivers_Plastic.cogs_resin]]"),
                ("cogs_3d", "Giá vốn In 3D", "=[[Drivers_Plastic.cogs_3d]]")]
        rev_ic, cogs_ic = "[[.rev_ic]]", "0"
    else:
        rev = [(f"rev_{c.lower()}", f"{c} — {n}", f"=[[Drivers_Media.{c.lower()}_rev]]") for c, n, *_ in sd.MEDIA_TYPES]
        cogs = [(f"cogs_{c.lower()}", f"Giá vốn {c}", f"=[[Drivers_Media.{c.lower()}_cogs]]") for c, *_ in sd.MEDIA_TYPES]
        rev_ic, cogs_ic = "0", "0"
    for k, lab, f in rev:
        S.add(k, lab, f, unit="triệu")
    S.add("rev_total", "Doanh thu thuần", "=" + "+".join(f"[[.{k}]]" for k, *_ in rev), unit="triệu", bold=True)
    S.add("rev_ic_total", "  trong đó: doanh thu nội bộ", "=" + rev_ic, unit="triệu")
    for k, lab, f in cogs:
        S.add(k, lab, f, unit="triệu")
    S.add("cogs_total", "Giá vốn hàng bán (chưa gồm khấu hao)", "=" + "+".join(f"[[.{k}]]" for k, *_ in cogs),
          unit="triệu", bold=True)
    S.add("cogs_ic", "  trong đó: mua nội bộ", "=" + cogs_ic, unit="triệu")
    S.add("gp", "Lợi nhuận gộp (trước khấu hao)", "=[[.rev_total]]-[[.cogs_total]]", unit="triệu", bold=True)
    S.add("gm", "Biên lợi nhuận gộp", "=IF([[.rev_total]]=0,0,[[.gp]]/[[.rev_total]])", unit="%", fmt="pct",
          total="same")
    S.add("selling", "Chi phí bán hàng (641)", f"=[[Opex.opex_{lc}_641]]", unit="triệu")
    S.add("admin", "Chi phí quản lý doanh nghiệp (642)", f"=[[Opex.opex_{lc}_642]]", unit="triệu")
    S.add("ebitda", "EBITDA", "=[[.gp]]-[[.selling]]-[[.admin]]", unit="triệu", bold=True)
    S.add("dep", "Khấu hao", f"=[[Capex.dep_{lc}]]", unit="triệu")
    S.add("ebit", "EBIT", "=[[.ebitda]]-[[.dep]]", unit="triệu", bold=True)
    S.add("fin_inc_dep", "Lãi tiền gửi", "=MAX(0,[[.cash@p]])*[[Assumptions.deposit_rate@D]]/12", unit="triệu",
          note="Trên số dư tiền đầu tháng")
    fin_inc = "[[.fin_inc_dep]]"
    if co == "ALTA":
        S.add("fin_inc_ic", "Lãi cho Alta Media vay (nội bộ)", "=[[Debt.icl_int]]", unit="triệu")
        fin_inc += "+[[.fin_inc_ic]]"
    S.add("fin_inc", "Doanh thu tài chính", "=" + fin_inc, unit="triệu")
    S.add("fin_exp_bank", "Lãi vay ngân hàng", f"=[[Debt.int_{lc}]]", unit="triệu")
    fin_exp = "[[.fin_exp_bank]]"
    if co == "AME":
        S.add("fin_exp_ic", "Lãi vay Alta (Mẹ) (nội bộ)", "=[[Debt.icl_int]]", unit="triệu")
        fin_exp += "+[[.fin_exp_ic]]"
    S.add("fin_exp", "Chi phí tài chính", "=" + fin_exp, unit="triệu")
    S.add("oth_inc", "Thu nhập khác", f"=[[Assumptions.oth_inc_{lc}]]", unit="triệu")
    S.add("oth_exp", "Chi phí khác", f"=[[Assumptions.oth_exp_{lc}]]", unit="triệu")
    S.add("pbt", "Lợi nhuận trước thuế", "=[[.ebit]]+[[.fin_inc]]-[[.fin_exp]]+[[.oth_inc]]-[[.oth_exp]]", unit="triệu",
          bold=True)
    S.add("tax", "Chi phí thuế TNDN", "=[[.pbt]]*[[Assumptions.tax_rate@D]]", unit="triệu",
          note="Đơn giản: thuế suất × LNTT từng tháng (lỗ tháng bù trừ trong năm)")
    S.add("ni", "Lợi nhuận sau thuế", "=[[.pbt]]-[[.tax]]", unit="triệu", bold=True)
    if co == "APL":
        S.sec("Ghi nhớ: đóng góp BU In 3D (không phân bổ chi phí chung — P11)")
        S.add("p3d_gp", "Lợi nhuận gộp In 3D", "=[[.rev_3d]]-[[.cogs_3d]]", unit="triệu")
        S.add("p3d_direct", "Chi phí trực tiếp In 3D (nhân sự + opex riêng)",
              "=[[Headcount.hc_apl_3d_cost]]+[[Opex.apl_ox_3d]]", unit="triệu")
        S.add("p3d_contrib", "Đóng góp BU In 3D", "=[[.p3d_gp]]-[[.p3d_direct]]", unit="triệu", bold=True)
    # --------------------------------------------------- CĐKT
    S.sec("CÂN ĐỐI KẾ TOÁN (cuối tháng)")
    dso = f"([[Assumptions.{lc}_dso@D]]+{add('f_dso')})"
    S.add("cash", "Tiền và tương đương tiền", "=[[.cf_close]]", unit="triệu", d=ob["cash"], d_input=True, total="last")
    S.add("ar", "Phải thu khách hàng (ngoài tập đoàn)", f"=MAX(0,{dso})/30*([[.rev_total]]-[[.rev_ic_total]])",
          unit="triệu", d=ob["ar"], d_input=True, total="last", note="Số ngày phải thu × doanh thu ngoài ÷ 30")
    ar_ic = {"ALTA": "[[IC_Elims.bal_rent_apl]]+[[IC_Elims.bal_rent_ame]]", "APL": "[[IC_Elims.bal_bag]]", "AME": "0"}[co]
    S.add("ar_ic", "Phải thu nội bộ", "=" + ar_ic, unit="triệu", d="=" + ar_ic.replace("]]", "@D]]"), total="last")
    S.add("inv", "Hàng tồn kho", f"=[[Assumptions.{lc}_dio@D]]/30*[[.cogs_total]]", unit="triệu", d=ob["inv"],
          d_input=True, total="last")
    loan_a = "[[Debt.icl_close]]" if co == "ALTA" else "0"
    S.add("loan_ic_a", "Cho vay nội bộ (Mẹ → Media)", "=" + loan_a, unit="triệu",
          d="=" + loan_a.replace("]]", "@D]]"), total="last")
    S.add("invest_sub", "Đầu tư vào công ty con", "=[[.invest_sub@p]]", unit="triệu", d=ob.get("invest_sub", 0),
          d_input=True, total="last")
    S.add("fa", "Tài sản cố định (giá trị còn lại)", f"=[[Capex.fa_{lc}]]", unit="triệu", d=f"=[[Capex.fa_{lc}@D]]",
          total="last")
    S.add("oth_asset", "Tài sản khác (giữ nguyên)", "=[[.oth_asset@p]]", unit="triệu", d=ob["oth_asset"], d_input=True,
          total="last")
    S.add("assets", "TỔNG TÀI SẢN", "=SUM([[.cash~oth_asset]])",
          unit="triệu", d="=SUM([[.cash~oth_asset@D]])", total="last", bold=True)
    S.add("ap", "Phải trả người bán (ngoài tập đoàn)",
          f"=[[Assumptions.{lc}_dpo@D]]/30*([[.cogs_total]]-[[.cogs_ic]])", unit="triệu", d=ob["ap"], d_input=True,
          total="last")
    ap_ic = {"ALTA": "[[IC_Elims.bal_bag]]", "APL": "[[IC_Elims.bal_rent_apl]]", "AME": "[[IC_Elims.bal_rent_ame]]"}[co]
    S.add("ap_ic", "Phải trả nội bộ", "=" + ap_ic, unit="triệu", d="=" + ap_ic.replace("]]", "@D]]"), total="last")
    S.add("tax_pay", "Thuế TNDN phải nộp", "=[[.tax_pay@p]]+[[.tax]]-[[.tax_paid]]", unit="triệu", d=ob["tax_pay"],
          d_input=True, total="last")
    S.add("loan_bank", "Vay ngân hàng", f"=[[Debt.close_{lc}]]", unit="triệu", d=f"=[[Debt.close_{lc}@D]]", total="last")
    loan_l = "[[Debt.icl_close]]" if co == "AME" else "0"
    S.add("loan_ic_l", "Vay nội bộ (Media vay Mẹ)", "=" + loan_l, unit="triệu", d="=" + loan_l.replace("]]", "@D]]"),
          total="last")
    S.add("oth_liab", "Nợ phải trả khác (giữ nguyên)", "=[[.oth_liab@p]]", unit="triệu", d=ob["oth_liab"],
          d_input=True, total="last")
    S.add("liab", "TỔNG NỢ PHẢI TRẢ", "=SUM([[.ap~oth_liab]])", unit="triệu", d="=SUM([[.ap~oth_liab@D]])",
          total="last", bold=True)
    S.add("capital", "Vốn góp chủ sở hữu", "=[[.capital@p]]", unit="triệu", d=ob["capital"], d_input=True, total="last")
    div = "[[Assumptions.div_alta]]" if co == "ALTA" else "0"
    S.add("re", "LNST chưa phân phối", f"=[[.re@p]]+[[.ni]]-{div}", unit="triệu", d=ob["re"], d_input=True,
          total="last")
    S.add("equity", "VỐN CHỦ SỞ HỮU", "=[[.capital]]+[[.re]]", unit="triệu", d="=[[.capital@D]]+[[.re@D]]",
          total="last", bold=True)
    S.add("le", "TỔNG NGUỒN VỐN", "=[[.liab]]+[[.equity]]", unit="triệu", d="=[[.liab@D]]+[[.equity@D]]",
          total="last", bold=True)
    S.add("bs_diff", "Kiểm tra: Tài sản − Nguồn vốn (phải = 0)", "=ROUND([[.assets]]-[[.le]],3)", unit="triệu",
          d="=ROUND([[.assets@D]]-[[.le@D]],3)", total=None, fmt="check")
    # --------------------------------------------------- LCTT
    S.sec("LƯU CHUYỂN TIỀN TỆ (gián tiếp)")
    S.add("cf_ni", "Lợi nhuận sau thuế", "=[[.ni]]", unit="triệu")
    S.add("cf_dep", "Cộng: khấu hao", "=[[.dep]]", unit="triệu")
    S.add("cf_ar", "(Tăng)/giảm phải thu khách hàng", "=-([[.ar]]-[[.ar@p]])", unit="triệu")
    S.add("cf_ar_ic", "(Tăng)/giảm phải thu nội bộ", "=-([[.ar_ic]]-[[.ar_ic@p]])", unit="triệu")
    S.add("cf_inv", "(Tăng)/giảm hàng tồn kho", "=-([[.inv]]-[[.inv@p]])", unit="triệu")
    S.add("cf_ap", "Tăng/(giảm) phải trả người bán", "=[[.ap]]-[[.ap@p]]", unit="triệu")
    S.add("cf_ap_ic", "Tăng/(giảm) phải trả nội bộ", "=[[.ap_ic]]-[[.ap_ic@p]]", unit="triệu")
    S.add("cf_tax", "Tăng/(giảm) thuế phải nộp", "=[[.tax_pay]]-[[.tax_pay@p]]", unit="triệu")
    S.add("cfo", "Lưu chuyển tiền từ hoạt động kinh doanh", "=SUM([[.cf_ni~cf_tax]])", unit="triệu", bold=True)
    S.add("cf_capex", "Mua sắm TSCĐ (capex)", f"=-[[Capex.capex_{lc}]]", unit="triệu")
    S.add("cf_icl_a", "Cho vay nội bộ (tăng)/thu hồi", "=-([[.loan_ic_a]]-[[.loan_ic_a@p]])", unit="triệu")
    S.add("cfi", "Lưu chuyển tiền từ hoạt động đầu tư", "=[[.cf_capex]]+[[.cf_icl_a]]", unit="triệu", bold=True)
    S.add("cf_bank", "Vay ngân hàng: giải ngân − trả gốc", "=[[.loan_bank]]-[[.loan_bank@p]]", unit="triệu")
    S.add("cf_icl_l", "Vay nội bộ: nhận − trả", "=[[.loan_ic_l]]-[[.loan_ic_l@p]]", unit="triệu")
    S.add("cf_div", "Cổ tức đã trả", f"=-{div}", unit="triệu")
    S.add("cff", "Lưu chuyển tiền từ hoạt động tài chính", "=[[.cf_bank]]+[[.cf_icl_l]]+[[.cf_div]]", unit="triệu",
          bold=True)
    S.add("cf_net", "Lưu chuyển tiền thuần", "=[[.cfo]]+[[.cfi]]+[[.cff]]", unit="triệu", bold=True)
    S.add("cf_open", "Tiền đầu kỳ", "=[[.cash@p]]", unit="triệu", total="first")
    S.add("cf_close", "Tiền cuối kỳ", "=[[.cf_open]]+[[.cf_net]]", unit="triệu", total="last", bold=True)
    S.add("tax_paid", "Ghi nhớ: thuế TNDN nộp trong tháng",
          "=IF(OR(MONTH([[Assumptions.date]])=1,MONTH([[Assumptions.date]])=4,MONTH([[Assumptions.date]])=7,"
          "MONTH([[Assumptions.date]])=10),MAX(0,[[.tax_pay@p]]),0)", unit="triệu",
          note="Nộp số dư đầu tháng vào T1/T4/T7/T10 (đơn giản hóa lịch tạm nộp)")
    return S


def build_ic(M, ic):
    S = MSheet(M, "IC_Elims", "GIAO DỊCH NỘI BỘ & BÚT TOÁN LOẠI TRỪ (MST 0301420079 · 0312414944 · 0305904835)")
    S.sec("1. Doanh thu – giá vốn/chi phí nội bộ (mỗi cặp: bên bán vs bên mua)")
    S.add("bag_rev", "Plastic bán túi cho Mẹ — doanh thu Plastic", "=[[FS_Plastic.rev_ic]]", unit="triệu",
          note="Bút toán: Nợ Doanh thu / Có Giá vốn")
    S.add("bag_cost", "  — giá vốn túi tại Mẹ", "=[[FS_Me.cogs_bag]]", unit="triệu")
    S.add("rent_apl_rev", "Mẹ cho Plastic thuê — doanh thu Mẹ", "=[[FS_Me.rev_rent_apl]]", unit="triệu",
          note="Bút toán: Nợ Doanh thu cho thuê / Có Chi phí thuê (642)")
    S.add("rent_apl_exp", "  — chi phí thuê tại Plastic", "=[[Opex.apl_ox_rent_ic]]", unit="triệu")
    S.add("rent_ame_rev", "Mẹ cho Media thuê — doanh thu Mẹ", "=[[FS_Me.rev_rent_ame]]", unit="triệu")
    S.add("rent_ame_exp", "  — chi phí thuê tại Media", "=[[Opex.ame_ox_rent_ic]]", unit="triệu")
    S.add("int_inc", "Mẹ cho Media vay — lãi thu tại Mẹ", "=[[FS_Me.fin_inc_ic]]", unit="triệu",
          note="Bút toán: Nợ Doanh thu tài chính / Có Chi phí lãi vay")
    S.add("int_exp", "  — lãi phải trả tại Media", "=[[FS_Media.fin_exp_ic]]", unit="triệu")
    S.add("e_rev", "Loại trừ khỏi doanh thu thuần", "=[[.bag_rev]]+[[.rent_apl_rev]]+[[.rent_ame_rev]]", unit="triệu",
          bold=True)
    S.add("e_cogs", "Loại trừ khỏi giá vốn", "=[[.bag_cost]]", unit="triệu", bold=True)
    S.add("e_admin", "Loại trừ khỏi chi phí QLDN (thuê nội bộ)", "=[[.rent_apl_exp]]+[[.rent_ame_exp]]", unit="triệu",
          bold=True)
    S.add("e_fin", "Loại trừ doanh thu & chi phí tài chính", "=[[.int_inc]]", unit="triệu", bold=True)
    S.add("e_diff", "Kiểm tra: (DT + DTTC loại trừ) − (GV + CP + CPTC loại trừ)",
          "=ROUND([[.e_rev]]+[[.int_inc]]-[[.e_cogs]]-[[.e_admin]]-[[.int_exp]],3)", unit="triệu", fmt="check",
          total=None)
    S.sec("2. Số dư công nợ nội bộ (cuối tháng) — ô D là số dư đầu kỳ đã đối chiếu")
    S.add("bal_bag", "Plastic phải thu Mẹ (tiền túi)", "=[[.bag_rev]]*[[Assumptions.ic_days@D]]/30", unit="triệu",
          d=ic["ic_bag"], d_input=True, total="last", note="Nợ Phải trả (Mẹ) / Có Phải thu (Plastic)")
    S.add("bal_rent_apl", "Mẹ phải thu Plastic (tiền thuê)", "=[[.rent_apl_rev]]*[[Assumptions.ic_days@D]]/30",
          unit="triệu", d=ic["ic_rent_apl"], d_input=True, total="last")
    S.add("bal_rent_ame", "Mẹ phải thu Media (tiền thuê + lãi)",
          "=([[.rent_ame_rev]]+[[.int_inc]])*[[Assumptions.ic_days@D]]/30", unit="triệu", d=ic["ic_rent_ame"],
          d_input=True, total="last")
    S.add("ar_ic_sum", "Tổng phải thu nội bộ (theo 3 BCĐKT)",
          "=[[FS_Me.ar_ic]]+[[FS_Plastic.ar_ic]]+[[FS_Media.ar_ic]]", unit="triệu", total="last",
          d="=[[FS_Me.ar_ic@D]]+[[FS_Plastic.ar_ic@D]]+[[FS_Media.ar_ic@D]]")
    S.add("ap_ic_sum", "Tổng phải trả nội bộ (theo 3 BCĐKT)",
          "=[[FS_Me.ap_ic]]+[[FS_Plastic.ap_ic]]+[[FS_Media.ap_ic]]", unit="triệu", total="last",
          d="=[[FS_Me.ap_ic@D]]+[[FS_Plastic.ap_ic@D]]+[[FS_Media.ap_ic@D]]")
    S.add("loan_a", "Cho vay nội bộ tại Mẹ", "=[[FS_Me.loan_ic_a]]", unit="triệu", total="last",
          d="=[[FS_Me.loan_ic_a@D]]", note="Nợ Vay (Media) / Có Cho vay (Mẹ)")
    S.add("loan_l", "Vay nội bộ tại Media", "=[[FS_Media.loan_ic_l]]", unit="triệu", total="last",
          d="=[[FS_Media.loan_ic_l@D]]")
    S.sec("3. Khoản đầu tư vào công ty con vs vốn góp công ty con (giả định sở hữu 100% — xác nhận tỷ lệ, NCI)")
    S.add("invest", "Đầu tư vào công ty con (sổ Mẹ)", "=[[FS_Me.invest_sub]]", unit="triệu", total="last",
          d="=[[FS_Me.invest_sub@D]]")
    S.add("sub_cap", "Vốn góp của Plastic + Media", "=[[FS_Plastic.capital]]+[[FS_Media.capital]]", unit="triệu",
          total="last", d="=[[FS_Plastic.capital@D]]+[[FS_Media.capital@D]]")
    S.add("inv_diff", "Chênh lệch (→ 'Chênh lệch hợp nhất' trong vốn CSH)", "=[[.invest]]-[[.sub_cap]]", unit="triệu",
          total="last", d="=[[.invest@D]]-[[.sub_cap@D]]",
          note="Ngân sách quản trị: chưa tính lợi thế thương mại/NCI")
    S.sec("4. Dòng tiền vay nội bộ (phải triệt tiêu khi hợp nhất)")
    S.add("cf_ic", "Cho vay (Mẹ, đầu tư) + nhận vay (Media, tài chính)", "=[[FS_Me.cf_icl_a]]+[[FS_Media.cf_icl_l]]",
          unit="triệu", fmt="check")
    return S


def build_consol(M):
    S = MSheet(M, "Consolidated", "HỢP NHẤT QUẢN TRỊ ALTA GROUP (100% sở hữu — giả định)", d_header="Số dư đầu kỳ")
    fs = [COMPANIES[c][0] for c in COMPANIES]

    def ssum(k, at=""):
        return "+".join(f"[[{s}.{k}{at}]]" for s in fs)

    S.sec("KẾT QUẢ KINH DOANH HỢP NHẤT")
    S.add("rev_sum", "Doanh thu cộng gộp 3 công ty", "=" + ssum("rev_total"), unit="triệu")
    S.add("rev_elim", "Loại trừ doanh thu nội bộ", "=-[[IC_Elims.e_rev]]", unit="triệu")
    S.add("rev", "Doanh thu thuần hợp nhất", "=[[.rev_sum]]+[[.rev_elim]]", unit="triệu", bold=True)
    S.add("cogs_sum", "Giá vốn cộng gộp", "=" + ssum("cogs_total"), unit="triệu")
    S.add("cogs_elim", "Loại trừ giá vốn nội bộ", "=-[[IC_Elims.e_cogs]]", unit="triệu")
    S.add("cogs", "Giá vốn hợp nhất (chưa gồm khấu hao)", "=[[.cogs_sum]]+[[.cogs_elim]]", unit="triệu", bold=True)
    S.add("gp", "Lợi nhuận gộp", "=[[.rev]]-[[.cogs]]", unit="triệu", bold=True)
    S.add("gm", "Biên gộp", "=IF([[.rev]]=0,0,[[.gp]]/[[.rev]])", unit="%", fmt="pct", total="same")
    S.add("selling", "Chi phí bán hàng", "=" + ssum("selling"), unit="triệu")
    S.add("admin_sum", "Chi phí QLDN cộng gộp", "=" + ssum("admin"), unit="triệu")
    S.add("admin_elim", "Loại trừ chi phí thuê nội bộ", "=-[[IC_Elims.e_admin]]", unit="triệu")
    S.add("admin", "Chi phí QLDN hợp nhất", "=[[.admin_sum]]+[[.admin_elim]]", unit="triệu")
    S.add("ebitda", "EBITDA hợp nhất", "=[[.gp]]-[[.selling]]-[[.admin]]", unit="triệu", bold=True)
    S.add("ebitda_m", "Biên EBITDA", "=IF([[.rev]]=0,0,[[.ebitda]]/[[.rev]])", unit="%", fmt="pct", total="same")
    S.add("dep", "Khấu hao", "=" + ssum("dep"), unit="triệu")
    S.add("ebit", "EBIT", "=[[.ebitda]]-[[.dep]]", unit="triệu", bold=True)
    S.add("fin_inc", "Doanh thu tài chính (sau loại trừ lãi nội bộ)", f"={ssum('fin_inc')}-[[IC_Elims.int_inc]]",
          unit="triệu")
    S.add("fin_exp", "Chi phí tài chính (sau loại trừ lãi nội bộ)", f"={ssum('fin_exp')}-[[IC_Elims.int_exp]]",
          unit="triệu")
    S.add("oth", "Thu nhập khác − chi phí khác", f"={ssum('oth_inc')}-({ssum('oth_exp')})", unit="triệu")
    S.add("pbt", "Lợi nhuận trước thuế", "=[[.ebit]]+[[.fin_inc]]-[[.fin_exp]]+[[.oth]]", unit="triệu", bold=True)
    S.add("tax", "Thuế TNDN", "=" + ssum("tax"), unit="triệu")
    S.add("ni", "Lợi nhuận sau thuế hợp nhất", "=[[.pbt]]-[[.tax]]", unit="triệu", bold=True)
    S.add("ni_sum", "Ghi nhớ: tổng LNST 3 công ty", "=" + ssum("ni"), unit="triệu")
    S.sec("DOANH THU NGOÀI TẬP ĐOÀN THEO MẢNG")
    S.add("seg_me_rent", "Mẹ — cho thuê mặt bằng", "=[[FS_Me.rev_rent_ext]]", unit="triệu")
    S.add("seg_me_tech", "Mẹ — thiết bị & dự án công nghệ", "=[[FS_Me.rev_tech]]", unit="triệu")
    S.add("seg_me_bag", "Mẹ — bán lại túi bao bì", "=[[FS_Me.rev_bag]]", unit="triệu")
    S.add("seg_apl_pack", "Plastic — bao bì nhựa", "=[[FS_Plastic.rev_pack_ext]]", unit="triệu")
    S.add("seg_apl_resin", "Plastic — thương mại hạt nhựa", "=[[FS_Plastic.rev_resin]]", unit="triệu")
    S.add("seg_apl_scrap", "Plastic — phế liệu", "=[[FS_Plastic.rev_scrap]]", unit="triệu")
    S.add("seg_apl_3d", "Plastic — BU In 3D", "=[[FS_Plastic.rev_3d]]", unit="triệu")
    for c, n, *_ in sd.MEDIA_TYPES:
        S.add(f"seg_ame_{c.lower()}", f"Media — {c} ({n})", f"=[[FS_Media.rev_{c.lower()}]]", unit="triệu")
    S.add("seg_total", "Tổng (phải = doanh thu hợp nhất)", "=SUM([[.seg_me_rent~seg_ame_tkl]])", unit="triệu",
          bold=True)
    S.sec("CÂN ĐỐI KẾ TOÁN HỢP NHẤT")
    bs = [("cash", "Tiền", None), ("ar", "Phải thu khách hàng", None), ("ar_ic", "Phải thu nội bộ", "ar_ic"),
          ("inv", "Hàng tồn kho", None), ("loan_ic_a", "Cho vay nội bộ", "loan_ic_a"),
          ("invest_sub", "Đầu tư vào công ty con", "invest_sub"), ("fa", "Tài sản cố định", None),
          ("oth_asset", "Tài sản khác", None)]
    for k, lab, el in bs:
        f = ssum(k) + (f"-[[{fs[0]}.{k}]]-[[{fs[1]}.{k}]]-[[{fs[2]}.{k}]]" if el else "")
        S.add(k, lab + (" (sau loại trừ = 0)" if el else ""), "=" + f, unit="triệu", total="last",
              d="=" + f.replace("]]", "@D]]"))
    S.add("assets", "TỔNG TÀI SẢN", "=SUM([[.cash~oth_asset]])", unit="triệu", total="last", bold=True,
          d="=SUM([[.cash~oth_asset@D]])")
    for k, lab, el in [("ap", "Phải trả người bán", None), ("ap_ic", "Phải trả nội bộ", 1), ("tax_pay", "Thuế phải nộp", None),
                       ("loan_bank", "Vay ngân hàng", None), ("loan_ic_l", "Vay nội bộ", 1), ("oth_liab", "Nợ khác", None)]:
        f = ssum(k) + (f"-[[{fs[0]}.{k}]]-[[{fs[1]}.{k}]]-[[{fs[2]}.{k}]]" if el else "")
        S.add(k, lab + (" (sau loại trừ = 0)" if el else ""), "=" + f, unit="triệu", total="last",
              d="=" + f.replace("]]", "@D]]"))
    S.add("liab", "TỔNG NỢ PHẢI TRẢ", "=SUM([[.ap~oth_liab]])", unit="triệu", total="last", bold=True,
          d="=SUM([[.ap~oth_liab@D]])")
    S.add("capital", "Vốn góp (Mẹ; đã loại vốn công ty con)", f"={ssum('capital')}-[[IC_Elims.sub_cap]]", unit="triệu",
          total="last", d=f"={ssum('capital', '@D')}-[[IC_Elims.sub_cap@D]]")
    S.add("cons_diff", "Chênh lệch hợp nhất (đầu tư − vốn con)", "=-[[IC_Elims.inv_diff]]", unit="triệu", total="last",
          d="=-[[IC_Elims.inv_diff@D]]")
    S.add("re", "LNST chưa phân phối", "=" + ssum("re"), unit="triệu", total="last", d="=" + ssum("re", "@D"))
    S.add("equity", "VỐN CHỦ SỞ HỮU", "=[[.capital]]+[[.cons_diff]]+[[.re]]", unit="triệu", total="last", bold=True,
          d="=[[.capital@D]]+[[.cons_diff@D]]+[[.re@D]]")
    S.add("le", "TỔNG NGUỒN VỐN", "=[[.liab]]+[[.equity]]", unit="triệu", total="last", bold=True,
          d="=[[.liab@D]]+[[.equity@D]]")
    S.add("bs_diff", "Kiểm tra: Tài sản − Nguồn vốn", "=ROUND([[.assets]]-[[.le]],3)", unit="triệu", fmt="check",
          total=None, d="=ROUND([[.assets@D]]-[[.le@D]],3)")
    S.add("net_debt", "Nợ vay thuần (vay NH − tiền)", "=[[.loan_bank]]-[[.cash]]", unit="triệu", total="last",
          d="=[[.loan_bank@D]]-[[.cash@D]]")
    S.sec("LƯU CHUYỂN TIỀN TỆ HỢP NHẤT")
    S.add("cfo", "Từ hoạt động kinh doanh", "=" + ssum("cfo"), unit="triệu", note="Dòng nội bộ trong vốn lưu động tự triệt tiêu")
    S.add("cfi", "Từ hoạt động đầu tư (capex)", "=" + ssum("cf_capex"), unit="triệu")
    S.add("cff", "Từ hoạt động tài chính (vay NH, cổ tức)", f"={ssum('cf_bank')}+{ssum('cf_div')}", unit="triệu")
    S.add("cf_ic", "Ghi nhớ: dòng tiền vay nội bộ đã loại trừ", "=[[IC_Elims.cf_ic]]", unit="triệu", fmt="check")
    S.add("cf_net", "Lưu chuyển tiền thuần", "=[[.cfo]]+[[.cfi]]+[[.cff]]", unit="triệu", bold=True)
    S.add("cf_open", "Tiền đầu kỳ", "=[[.cash@p]]", unit="triệu", total="first")
    S.add("cf_close", "Tiền cuối kỳ", "=[[.cf_open]]+[[.cf_net]]", unit="triệu", total="last", bold=True)
    S.add("fcf", "Dòng tiền tự do (HĐKD + capex)", "=[[.cfo]]+[[.cfi]]", unit="triệu", bold=True)
    return S


def build_checks(M):
    S = MSheet(M, "Checks", "KIỂM TRA — MỌI Ô PHẢI = 0 (sai số ≤ 0,001 triệu = 1.000 đ, chính sách P10)",
               d_header="Đầu kỳ", start=9)
    ck = []

    def c(key, label, f, d=None):
        S.add(key, label, f, d=d, fmt="check", total=None, unit="triệu")
        ck.append(key)

    S.sec("1. Bảng cân đối kế toán cân")
    for co, (sh, nm, _) in COMPANIES.items():
        c(f"bs_{co}", f"{nm}: Tài sản − Nguồn vốn", f"=[[{sh}.bs_diff]]", d=f"=[[{sh}.bs_diff@D]]")
    c("bs_cons", "Hợp nhất: Tài sản − Nguồn vốn", "=[[Consolidated.bs_diff]]", d="=[[Consolidated.bs_diff@D]]")
    S.sec("2. Tiền trên CĐKT khớp tiền cuối kỳ LCTT")
    for co, (sh, nm, _) in COMPANIES.items():
        c(f"cash_{co}", f"{nm}: Tiền CĐKT − tiền cuối kỳ LCTT", f"=ROUND([[{sh}.cash]]-[[{sh}.cf_close]],3)")
    c("cash_cons", "Hợp nhất: Tiền CĐKT − tiền cuối kỳ LCTT", "=ROUND([[Consolidated.cash]]-[[Consolidated.cf_close]],3)")
    S.sec("3. Giao dịch & số dư nội bộ cân (bên bán = bên mua)")
    c("ic_bag", "Túi: doanh thu Plastic − giá vốn Mẹ", "=ROUND([[IC_Elims.bag_rev]]-[[IC_Elims.bag_cost]],3)")
    c("ic_rent_apl", "Thuê: doanh thu Mẹ − chi phí Plastic", "=ROUND([[IC_Elims.rent_apl_rev]]-[[IC_Elims.rent_apl_exp]],3)")
    c("ic_rent_ame", "Thuê: doanh thu Mẹ − chi phí Media", "=ROUND([[IC_Elims.rent_ame_rev]]-[[IC_Elims.rent_ame_exp]],3)")
    c("ic_int", "Lãi vay nội bộ: thu Mẹ − chi Media", "=ROUND([[IC_Elims.int_inc]]-[[IC_Elims.int_exp]],3)")
    c("ic_total", "Tổng loại trừ thu − tổng loại trừ chi", "=[[IC_Elims.e_diff]]")
    c("ic_bal", "Phải thu nội bộ − phải trả nội bộ", "=ROUND([[IC_Elims.ar_ic_sum]]-[[IC_Elims.ap_ic_sum]],3)",
      d="=ROUND([[IC_Elims.ar_ic_sum@D]]-[[IC_Elims.ap_ic_sum@D]],3)")
    c("ic_loan", "Cho vay nội bộ (Mẹ) − vay nội bộ (Media)", "=ROUND([[IC_Elims.loan_a]]-[[IC_Elims.loan_l]],3)",
      d="=ROUND([[IC_Elims.loan_a@D]]-[[IC_Elims.loan_l@D]],3)")
    c("ic_cf", "Dòng tiền vay nội bộ cộng gộp", "=ROUND([[IC_Elims.cf_ic]],3)")
    c("ic_ni", "LNST hợp nhất − tổng LNST 3 công ty", "=ROUND([[Consolidated.ni]]-[[Consolidated.ni_sum]],3)")
    c("seg", "Doanh thu theo mảng − doanh thu hợp nhất", "=ROUND([[Consolidated.seg_total]]-[[Consolidated.rev]],3)")
    S.sec("4. Dự báo cả năm & dữ liệu thực tế (sheet Forecast)")
    return S, ck


def build_forecast_rows(S, ck, M):
    """Dòng kiểm tra Forecast: cột tháng dương lịch của Forecast → cột timeline của Checks."""
    fsn = M.forecast_name
    items = [(co, f"{nm}: LNTT Forecast − LNTT BCTC (tháng dự báo)") for co, (sh, nm, _) in COMPANIES.items()]
    items.append(("CONS", "Hợp nhất: LNST Forecast − LNST hợp nhất (tháng dự báo)"))
    for co, label in items:
        row = S.add(f"fc_{co}", label, fmt="check", total=None, unit="triệu")
        r = M.layout[fsn][f"chk_{co}"]
        row.percol = [f"={fsn}!{get_column_letter(3 + m)}{r}" if y == M.fy else 0 for y, m in M.months]
        ck.append(f"fc_{co}")
    S.add("act_tie", "Thực tế: tổng CSV đã nhập − tổng đã ánh xạ vào Forecast", d=f"=[[{fsn}.tie@D]]", fmt="check",
          total=None, unit="triệu", months=False)
    ck.append("act_tie")
    S.add("scen_ok", "Ô chọn kịch bản hợp lệ (0 = hợp lệ)", d="=IF(ISNUMBER(Scenarios!$C$6),0,1)", fmt="check",
          total=None, unit="", months=False)
    ck.append("scen_ok")
    S.sec("5. Cảnh báo — KHÔNG tính vào số lỗi, nhưng phải giải trình trước khi trình")
    first, last = M.mcol(0), M.mcol(len(M.months) - 1)
    for co, (sh, nm, _) in COMPANIES.items():
        r = M.layout[sh]["cash"]
        S.add(f"warn_cash_{co}", f"{nm}: số tháng tiền cuối kỳ âm (cần hạn mức/vay bổ sung)",
              d=f'=COUNTIF({sh}!{first}{r}:{last}{r},"<0")', fmt="int", total=None, unit="tháng", months=False)
        r2 = M.layout[sh]["ni"]
        S.add(f"warn_loss_{co}", f"{nm}: số tháng lỗ sau thuế", d=f'=COUNTIF({sh}!{first}{r2}:{last}{r2},"<0")',
              fmt="int", total=None, unit="tháng", months=False)


# ================================================================== ghi workbook
def write_header(ws, M, title, banner, d_header, months=True, unit="Đơn vị: triệu đồng (trừ khi ghi khác)"):
    ws["A1"] = title
    ws["A1"].font = F_TITLE
    ws["A2"] = banner
    ws["A2"].font = F_BANNER
    ws["A3"] = unit + " · Ô nền xanh chữ xanh = ô nhập; còn lại là công thức"
    ws["A3"].font = Font(italic=True, color="595959")
    hdr = ["Chỉ tiêu", "ĐVT", "Nguồn / ghi chú", d_header]
    for i, h in enumerate(hdr):
        cell = ws.cell(5, i + 1, h)
    if months:
        for i, (y, m) in enumerate(M.months):
            ws.cell(4, FIRST + i, "Ngân sách" if y == M.cfg["budget_year"] else "Dự báo")
            ws.cell(5, FIRST + i, f"T{m:02d}/{y}")
        for yr in M.years:
            ws[f"{yr['col']}4"] = "Tổng/cuối kỳ"
            ws[f"{yr['col']}5"] = yr["label"]
    last = M.last_col if months else 4
    for col in range(1, last + 1):
        for r in (4, 5):
            c = ws.cell(r, col)
            c.font = F_BOLD
            c.fill = FILL_HDR
            c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 13
    ws.column_dimensions["C"].width = 44
    ws.column_dimensions["D"].width = 14
    for col in range(FIRST, M.last_col + 1):
        ws.column_dimensions[get_column_letter(col)].width = 12.5
    for yr in M.years:
        ws.column_dimensions[yr["col"]].width = 15
    ws.freeze_panes = "E6"


def write_msheet(wb, M, S: MSheet, banner):
    ws = wb.create_sheet(S.name)
    write_header(ws, M, S.title, banner, S.d_header)
    for row in S.rows:
        r = row.r
        if row.kind == "blank":
            continue
        if row.kind == "sec":
            ws.cell(r, 1, row.label)
            for col in range(1, M.last_col + 1):
                ws.cell(r, col).fill = FILL_SEC
                ws.cell(r, col).font = F_SEC
            continue
        ws.cell(r, 1, row.label)
        ws.cell(r, 2, row.unit)
        ws.cell(r, 3, row.note)
        ws.cell(r, 3).alignment = Alignment(wrap_text=False)
        fmt = FMT[row.fmt]
        if row.d is not None:
            v = M.render(row.d, S.name, "D", "C") if isinstance(row.d, str) else row.d
            cd = ws.cell(r, 4, v)
            cd.number_format = fmt
            if row.d_input:
                cd.font, cd.fill = F_INPUT, FILL_INPUT
        if row.months:
            for i in range(len(M.months)):
                col = M.mcol(i)
                prev = get_column_letter(FIRST + i - 1)
                cell = ws[f"{col}{r}"]
                if row.percol is not None:
                    cell.value = row.percol[i]
                elif row.inputs is not None:
                    cell.value = row.inputs[i]
                    cell.font, cell.fill = F_INPUT, FILL_INPUT
                else:
                    cell.value = M.render(row.f, S.name, col, prev)
                cell.number_format = fmt
            for yr in M.years:
                cols = [M.mcol(i) for i in yr["idx"]]
                t = row.total
                if t == "sum":
                    v = f"=SUM({cols[0]}{r}:{cols[-1]}{r})"
                elif t == "avg":
                    v = f"=AVERAGE({cols[0]}{r}:{cols[-1]}{r})"
                elif t == "last":
                    v = f"={cols[-1]}{r}"
                elif t == "first":
                    v = f"={cols[0]}{r}"
                elif t == "same":
                    v = M.render(row.f, S.name, yr["col"], "")
                else:
                    v = None
                if v is not None:
                    c = ws[f"{yr['col']}{r}"]
                    c.value = v
                    c.number_format = fmt
                    c.fill = FILL_TOT
                    c.font = F_BOLD
        if row.bold:
            for col in range(1, M.last_col + 1):
                c = ws.cell(r, col)
                f = copy(c.font)
                f.b = True
                c.font = f
                c.border = THIN_TOP
    return ws


def write_checks_extra(ws, M, S, ck):
    maxc = get_column_letter(M.last_col + 1)
    ws[f"{maxc}5"] = "Max |sai lệch|"
    ws[f"{maxc}5"].font = F_BOLD
    ws[f"{maxc}5"].fill = FILL_HDR
    ws.column_dimensions[maxc].width = 15
    lastm = M.mcol(len(M.months) - 1)
    rows = []
    for k in ck:
        r = M.layout["Checks"][k]
        ws[f"{maxc}{r}"] = f"=MAX(MAX(D{r}:{lastm}{r}),-MIN(D{r}:{lastm}{r}))"
        ws[f"{maxc}{r}"].number_format = FMT["check"]
        rows.append(r)
    rng = ",".join(f"{maxc}{r}" for r in rows)
    ws["A6"] = "TỔNG SỐ KIỂM TRA LỖI (phải = 0)"
    ws["A6"].font = Font(bold=True, size=12)
    ws["D6"] = f"=COUNTIF({maxc}{rows[0]}:{maxc}{rows[-1]},\">0\")"
    ws["D6"].font = Font(bold=True, size=12)
    ws["A7"] = "Số kiểm tra"
    ws["D7"] = len(rows)
    ws["C6"] = f'=IF(D6=0,"ĐẠT — mọi kiểm tra = 0","CÓ LỖI — xem các dòng tô đỏ")'
    ws["C6"].font = Font(bold=True)
    rule_bad = CellIsRule(operator="notEqual", formula=["0"], fill=FILL_BAD)
    ws.conditional_formatting.add(f"D9:{maxc}{rows[-1]}", rule_bad)
    if S.next - 1 > rows[-1]:
        ws.conditional_formatting.add(f"D{rows[-1] + 1}:D{S.next}", CellIsRule(
            operator="greaterThan", formula=["0"], fill=PatternFill("solid", fgColor="FFEB9C")))
    ws.conditional_formatting.add("D6", CellIsRule(operator="equal", formula=["0"], fill=FILL_OK))
    ws.conditional_formatting.add("D6", CellIsRule(operator="notEqual", formula=["0"], fill=FILL_BAD))
    M.checks_summary = "Checks!$D$6"


def register_scenarios(M):
    M.layout["Scenarios"] = {key: 9 + i for i, (key, *_) in enumerate(SCEN_FACTORS)}


def write_scenarios(wb, M, banner, scenario):
    ws = wb.create_sheet("Scenarios", 1)
    ws["A1"] = "KỊCH BẢN — chọn bằng 1 ô"
    ws["A1"].font = F_TITLE
    ws["A2"] = banner
    ws["A2"].font = F_BANNER
    ws["A3"] = "Hệ số chỉ áp dụng cho các tháng có Assumptions › 'Áp dụng kịch bản' = 1 (mặc định: năm ngân sách)."
    ws["A5"] = "KỊCH BẢN ĐANG CHỌN ►"
    ws["A5"].font = Font(bold=True, size=12)
    ws["C5"] = scenario
    ws["C5"].font = Font(bold=True, size=12, color="0000FF")
    ws["C5"].fill = FILL_INPUT
    dv = DataValidation(type="list", formula1='"Base,Target,Downside"', allow_blank=False)
    ws.add_data_validation(dv)
    dv.add("C5")
    ws["A6"] = "Chỉ số kịch bản (1/2/3)"
    ws["C6"] = "=MATCH(C5,$D$8:$F$8,0)"
    for i, h in enumerate(["Driver", "Kiểu", "Ghi chú", "Base", "Target", "Downside", "ĐANG DÙNG"]):
        c = ws.cell(8, i + 1, h)
        c.font, c.fill = F_BOLD, FILL_HDR
    r = 9
    for key, lab, typ, *vals in SCEN_FACTORS:
        ws.cell(r, 1, lab)
        ws.cell(r, 2, "nhân" if typ == "×" else "cộng")
        ws.cell(r, 3, "MẪU — CFO duyệt mức độ nhạy")
        fmt = FMT["num"] if typ == "×" else (FMT["int"] if key == "f_dso" else FMT["pct"])
        for j, v in enumerate(vals):
            c = ws.cell(r, 4 + j, v)
            c.font, c.fill, c.number_format = F_INPUT, FILL_INPUT, fmt
        g = ws.cell(r, 7, f"=INDEX(D{r}:F{r},$C$6)")
        g.number_format, g.font = fmt, F_BOLD
        assert M.layout["Scenarios"][key] == r
        r += 1
    r += 1
    ws.cell(r, 1, "KẾT QUẢ CHÍNH — kịch bản đang chọn (năm ngân sách, hợp nhất)").font = F_BOLD
    r += 1
    bc = M.ycol(M.cfg["budget_year"])
    kpis = [("Doanh thu thuần hợp nhất", "rev", FMT["money"]), ("EBITDA hợp nhất", "ebitda", FMT["money"]),
            ("Biên EBITDA", "ebitda_m", FMT["pct"]), ("LNST hợp nhất", "ni", FMT["money"]),
            ("Dòng tiền tự do", "fcf", FMT["money"]), ("Tiền cuối năm", "cash", FMT["money"]),
            ("Vay ngân hàng cuối năm", "loan_bank", FMT["money"]), ("Nợ vay thuần cuối năm", "net_debt", FMT["money"])]
    for lab, k, fmt in kpis:
        ws.cell(r, 1, lab)
        ws.cell(r, 2, "triệu" if fmt != FMT["pct"] else "%")
        c = ws.cell(r, 4, f"=Consolidated!{bc}{M.layout['Consolidated'][k]}")
        c.number_format = fmt
        r += 1
    ws.cell(r, 1, "Nợ vay thuần / EBITDA")
    c = ws.cell(r, 4, f"=IF(D{r-7}=0,0,D{r-1}/D{r-7})")
    c.number_format = FMT["x"]
    r += 1
    ws.cell(r, 1, "Kiểm tra mô hình (số lỗi)")
    ws.cell(r, 4, "=Checks!$D$6")
    r += 2
    ws.cell(r, 1, "So sánh 3 kịch bản: đổi ô C5, ghi lại bảng trên (hoặc chạy script với --scenario cho từng kịch bản). "
                  "Mô hình không chứa số kết quả nhập tay.").font = Font(italic=True)
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["C"].width = 30
    for col in "DEFG":
        ws.column_dimensions[col].width = 13


def write_actuals(wb, actuals, banner, M):
    ws = wb.create_sheet("Actuals_Input")
    ws["A1"] = "SỐ THỰC TẾ ĐÃ NHẬP (định dạng `afi export-pl`: company, month, line, amount — đơn vị ĐỒNG)"
    ws["A1"].font = F_TITLE
    ws["A2"] = banner
    ws["A2"].font = F_BANNER
    ws["A3"] = f"Nguồn: {M.cfg['actuals_source']}"
    for i, h in enumerate(["company", "month", "line", "amount", "source", "key_cml (công thức)", "key_ml (công thức)"]):
        c = ws.cell(5, i + 1, h)
        c.font, c.fill = F_BOLD, FILL_HDR
    for j, row in enumerate(actuals):
        r = 6 + j
        ws.cell(r, 1, row["company"])
        ws.cell(r, 2, row["month"])
        ws.cell(r, 3, row["line"])
        c = ws.cell(r, 4, row["amount"])
        c.number_format, c.font, c.fill = FMT["money"], F_INPUT, FILL_INPUT
        ws.cell(r, 5, row.get("source", ""))
        ws.cell(r, 6, f'=A{r}&"|"&B{r}&"|"&C{r}')
        ws.cell(r, 7, f'=B{r}&"|"&C{r}')
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 10
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 20
    ws.column_dimensions["E"].width = 30
    ws.column_dimensions["F"].width = 34
    ws.column_dimensions["G"].width = 26
    ws.freeze_panes = "A6"
    M.act_last = max(6, 5 + len(actuals))


def write_forecast(wb, M, banner):
    fy = M.fy
    name = M.forecast_name
    ws = wb.create_sheet(name)
    M.layout[name] = {}
    ath = M.cfg["actual_through"]
    n_act = ath[1] if ath[0] == fy else 0
    ws["A1"] = f"DỰ BÁO CẢ NĂM {fy}: {n_act} THÁNG THỰC TẾ + {12 - n_act} THÁNG DỰ BÁO" + (
        f" · SO VỚI NGÂN SÁCH {M.cfg['budget_year']}" if M.cfg["budget_year"] != fy else "")
    ws["A1"].font = F_TITLE
    ws["A2"] = banner
    ws["A2"].font = F_BANNER
    ws["A3"] = ("Đơn vị: triệu đồng · Dòng theo `afi` (account_map.yaml). Tháng dự báo: giá vốn = giá vốn tiền + toàn bộ "
                "khấu hao (đơn giản hóa). Hợp nhất thực tế theo P5: loại ic_revenue khỏi DT & GV, ic_interest khỏi 515 & 635.")
    ws["A3"].font = Font(italic=True, color="595959")
    hdr = ["Chỉ tiêu", "line (afi)", "Ghi chú", "—"]
    for i, h in enumerate(hdr):
        ws.cell(5, i + 1, h)
    mcols = [get_column_letter(3 + m) for m in range(1, 13)]  # D..O
    for m in range(1, 13):
        col = mcols[m - 1]
        ws[f"{col}4"] = "Thực tế" if m <= n_act else "Dự báo"
        ws[f"{col}5"] = f"{fy}-{m:02d}"
    fyc, budc, chgc = "P", "Q", "R"
    ws[f"{fyc}5"] = f"Cả năm {fy}"
    has_bud = M.cfg["budget_year"] != fy and M.ycol(M.cfg["budget_year"])
    if has_bud:
        ws[f"{budc}5"] = f"Ngân sách {M.cfg['budget_year']}"
        ws[f"{chgc}5"] = "% thay đổi"
    lastc = chgc if has_bud else fyc
    for col in range(1, ord(lastc) - 64 + 1):
        for r in (4, 5):
            c = ws.cell(r, col)
            c.font, c.fill = F_BOLD, FILL_HDR
            c.alignment = Alignment(horizontal="center")
    ws.column_dimensions["A"].width = 46
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 8
    ws.column_dimensions["D"].width = 12
    for col in mcols[1:] + [fyc, budc, chgc]:
        ws.column_dimensions[col].width = 12.5
    ws.freeze_panes = "D6"
    unit = "Assumptions!$D$" + str(M.layout["Assumptions"]["unit_vnd"])
    D = f"Actuals_Input!$D$6:$D${M.act_last}"
    KF = f"Actuals_Input!$F$6:$F${M.act_last}"  # company|month|line (text → SUMIFS không hiểu nhầm thành ngày)
    KG = f"Actuals_Input!$G$6:$G${M.act_last}"  # month|line
    fs_map = {"net_revenue": "rev_total", "selling_expenses": "selling", "admin_expenses": "admin",
              "finance_income": "fin_inc", "finance_expense": "fin_exp", "other_income": "oth_inc",
              "other_expense": "oth_exp", "income_tax": "tax", "depreciation": "dep"}
    cons_map = {"net_revenue": "rev", "selling_expenses": "selling", "admin_expenses": "admin",
                "finance_income": "fin_inc", "finance_expense": "fin_exp", "income_tax": "tax", "depreciation": "dep"}
    r = 7
    blocks = list(COMPANIES) + ["CONS"]
    act_cells = []
    for co in blocks:
        title = COMPANIES[co][1] if co != "CONS" else "HỢP NHẤT QUẢN TRỊ ALTA GROUP"
        ws.cell(r, 1, title)
        for col in range(1, ord(lastc) - 64 + 1):
            ws.cell(r, col).fill, ws.cell(r, col).font = FILL_SEC, F_SEC
        r += 1
        rows = {}
        lines = BASE_LINES + ["gross_profit", "profit_before_tax", "net_profit", "ebitda"] + (IC_LINES if co == "CONS" else [])
        for ln in lines:
            rows[ln] = r
            r += 1
        r_chk = r
        r += 2
        for ln in lines:
            rr = rows[ln]
            ws.cell(rr, 1, LINE_VN[ln])
            ws.cell(rr, 2, ln)
            bold = ln in ("net_revenue", "gross_profit", "profit_before_tax", "net_profit", "ebitda")
            for m in range(1, 13):
                col = mcols[m - 1]
                y_m = (fy, m)
                derived = {
                    "gross_profit": f"={col}{rows['net_revenue']}-{col}{rows['cogs']}",
                    "profit_before_tax": (f"={col}{rows['net_revenue']}+{col}{rows['finance_income']}+{col}{rows['other_income']}"
                                          f"-{col}{rows['cogs']}-{col}{rows['finance_expense']}-{col}{rows['selling_expenses']}"
                                          f"-{col}{rows['admin_expenses']}-{col}{rows['other_expense']}"),
                    "net_profit": f"={col}{rows['profit_before_tax']}-{col}{rows['income_tax']}",
                    "ebitda": f"={col}{rows['profit_before_tax']}+{col}{rows['finance_expense']}+{col}{rows['depreciation']}",
                }
                if ln in derived:
                    v = derived[ln]
                elif m <= n_act:
                    if co != "CONS":
                        v = f'=SUMIFS({D},{KF},"{co}|"&{col}$5&"|"&$B{rr})/{unit}'
                    elif ln in IC_LINES:
                        v = f'=SUMIFS({D},{KG},{col}$5&"|"&$B{rr})/{unit}'
                    else:
                        v = "=" + "+".join(f"{col}{M.fc_rows[c2][ln]}" for c2 in COMPANIES)
                        if ln in ("net_revenue", "cogs"):
                            v += f"-{col}{rows['ic_revenue']}"
                        if ln in ("finance_income", "finance_expense"):
                            v += f"-{col}{rows['ic_interest']}"
                else:
                    i = M.mi(*y_m)
                    if i is None:
                        v = 0
                    else:
                        mc = M.mcol(i)
                        if co != "CONS":
                            sh = COMPANIES[co][0]
                            if ln == "cogs":
                                v = f"={sh}!{mc}{M.layout[sh]['cogs_total']}+{sh}!{mc}{M.layout[sh]['dep']}"
                            else:
                                v = f"={sh}!{mc}{M.layout[sh][fs_map[ln]]}"
                        else:
                            L = M.layout["Consolidated"]
                            if ln == "cogs":
                                v = f"=Consolidated!{mc}{L['cogs']}+Consolidated!{mc}{L['dep']}"
                            elif ln in cons_map:
                                v = f"=Consolidated!{mc}{L[cons_map[ln]]}"
                            elif ln == "other_income":
                                v = "=" + "+".join(f"{COMPANIES[c2][0]}!{mc}{M.layout[COMPANIES[c2][0]]['oth_inc']}" for c2 in COMPANIES)
                            elif ln == "other_expense":
                                v = "=" + "+".join(f"{COMPANIES[c2][0]}!{mc}{M.layout[COMPANIES[c2][0]]['oth_exp']}" for c2 in COMPANIES)
                            elif ln == "ic_revenue":
                                v = f"=IC_Elims!{mc}{M.layout['IC_Elims']['e_rev']}"
                            elif ln == "ic_interest":
                                v = f"=IC_Elims!{mc}{M.layout['IC_Elims']['e_fin']}"
                c = ws[f"{col}{rr}"]
                c.value = v
                c.number_format = FMT["money"]
                if bold:
                    c.font = F_BOLD
            c = ws[f"{fyc}{rr}"]
            c.value = f"=SUM(D{rr}:O{rr})"
            c.number_format, c.font, c.fill = FMT["money"], F_BOLD, FILL_TOT
            if has_bud:
                bc = M.ycol(M.cfg["budget_year"])
                if co != "CONS":
                    sh = COMPANIES[co][0]
                    LL = M.layout[sh]
                    bmap = dict(fs_map)
                    if ln == "cogs":
                        bv = f"={sh}!{bc}{LL['cogs_total']}+{sh}!{bc}{LL['dep']}"
                    elif ln in bmap:
                        bv = f"={sh}!{bc}{LL[bmap[ln]]}"
                    else:
                        bv = None
                else:
                    L = M.layout["Consolidated"]
                    if ln == "cogs":
                        bv = f"=Consolidated!{bc}{L['cogs']}+Consolidated!{bc}{L['dep']}"
                    elif ln in cons_map:
                        bv = f"=Consolidated!{bc}{L[cons_map[ln]]}"
                    elif ln in ("other_income", "other_expense"):
                        k = "oth_inc" if ln == "other_income" else "oth_exp"
                        bv = "=" + "+".join(f"{COMPANIES[c2][0]}!{bc}{M.layout[COMPANIES[c2][0]][k]}" for c2 in COMPANIES)
                    elif ln == "ic_revenue":
                        bv = f"=IC_Elims!{bc}{M.layout['IC_Elims']['e_rev']}"
                    elif ln == "ic_interest":
                        bv = f"=IC_Elims!{bc}{M.layout['IC_Elims']['e_fin']}"
                    else:
                        bv = None
                if ln in ("gross_profit", "profit_before_tax", "net_profit", "ebitda"):
                    bv = "=" + derived_formula(ln, rows, budc)
                cq = ws[f"{budc}{rr}"]
                cq.value = bv
                cq.number_format, cq.font, cq.fill = FMT["money"], F_BOLD, FILL_TOT
                cr = ws[f"{chgc}{rr}"]
                cr.value = f"=IF({fyc}{rr}=0,\"\",{budc}{rr}/{fyc}{rr}-1)"
                cr.number_format = FMT["pct"]
        # dòng kiểm tra ánh xạ tháng dự báo
        key = f"chk_{co}"
        M.layout[name][key] = r_chk
        ws.cell(r_chk, 1, "Kiểm tra: LNTT/LNST ở đây − BCTC (tháng dự báo, phải = 0)").font = Font(italic=True)
        for m in range(1, 13):
            col = mcols[m - 1]
            i = M.mi(fy, m)
            if m <= n_act or i is None:
                v = 0
            else:
                mc = M.mcol(i)
                if co != "CONS":
                    sh = COMPANIES[co][0]
                    v = f"=ROUND({col}{rows['profit_before_tax']}-{sh}!{mc}{M.layout[sh]['pbt']},3)"
                else:
                    v = f"=ROUND({col}{rows['net_profit']}-Consolidated!{mc}{M.layout['Consolidated']['ni']},3)"
            ws[f"{col}{r_chk}"] = v
            ws[f"{col}{r_chk}"].number_format = FMT["check"]
        if n_act:
            last_act = mcols[n_act - 1]
            if co != "CONS":
                act_cells.append(f"D{rows[BASE_LINES[0]]}:{last_act}{rows[BASE_LINES[-1]]}")
            else:
                act_cells.append(f"D{rows[IC_LINES[0]]}:{last_act}{rows[IC_LINES[-1]]}")
        if co != "CONS":
            M.fc_rows[co] = rows
    # Đối chiếu dữ liệu thực tế
    r += 1
    M.layout[name]["tie"] = r
    ws.cell(r, 1, "Kiểm tra: tổng CSV thực tế (đồng ÷ quy đổi) − tổng đã ánh xạ (phải = 0)").font = Font(italic=True)
    mapped = "+".join(f"SUM({c})" for c in act_cells) if act_cells else "0"  # khối dòng gốc liền nhau
    ws[f"D{r}"] = f"=ROUND(SUM({D})/{unit}-({mapped}),3)"
    ws[f"D{r}"].number_format = FMT["check"]
    return ws


def derived_formula(ln, rows, col):
    return {
        "gross_profit": f"{col}{rows['net_revenue']}-{col}{rows['cogs']}",
        "profit_before_tax": (f"{col}{rows['net_revenue']}+{col}{rows['finance_income']}+{col}{rows['other_income']}"
                              f"-{col}{rows['cogs']}-{col}{rows['finance_expense']}-{col}{rows['selling_expenses']}"
                              f"-{col}{rows['admin_expenses']}-{col}{rows['other_expense']}"),
        "net_profit": f"{col}{rows['profit_before_tax']}-{col}{rows['income_tax']}",
        "ebitda": f"{col}{rows['profit_before_tax']}+{col}{rows['finance_expense']}+{col}{rows['depreciation']}",
    }[ln]


def write_readme(wb, M, banner):
    ws = wb.active
    ws.title = "README"
    cfg = M.cfg
    ath = f"{cfg['actual_through'][1]:02d}/{cfg['actual_through'][0]}"
    lines = [
        ("MÔ HÌNH DỰ BÁO CẢ NĂM & NGÂN SÁCH THEO DRIVER — ALTA GROUP", F_TITLE),
        (banner, F_BANNER),
        ("", None),
        (f"Thực tế đến hết: {ath} · Dự báo/ngân sách: T{M.months[0][1]:02d}/{M.months[0][0]} → T12/{cfg['budget_year']} · "
         f"Năm ngân sách: {cfg['budget_year']} · Sinh lúc: {cfg['generated']}", F_BOLD),
        (f"Số thực tế: {cfg['actuals_source']}", None),
        (f"Số dư đầu kỳ: {cfg['opening_source']}", None),
        (f"Giả định BU: {cfg['assumptions_source']}", None),
        ("", None),
        ("TRẠNG THÁI KIỂM TRA", F_BOLD),
        ("__CHECKS__", None),
        ("", None),
        ("CÁCH DÙNG", F_BOLD),
        ("1. Chọn kịch bản ở sheet Scenarios, ô C5 (Base / Target / Downside). Mọi sheet tính lại theo kịch bản.", None),
        ("2. Sửa giả định ở sheet Assumptions (ô nền xanh chữ xanh). Mỗi dòng có cột 'Nguồn / ghi chú' — ghi người cung cấp và ngày.", None),
        ("3. Số dư đầu kỳ: cột D của FS_Me / FS_Plastic / FS_Media (tiền, phải thu, tồn kho, phải trả…), Capex (TSCĐ), Debt (vay), IC_Elims (công nợ nội bộ).", None),
        ("4. Sau mỗi lần sửa: xem sheet Checks — ô D6 phải = 0. Không trình bản nào có lỗi.", None),
        ("5. Cập nhật hằng quý (rolling forecast): chạy lại script với --actual-through mới và CSV thực tế/số dư mới; "
         "giả định đã sửa trong Excel nên lưu ra CSV (--dump-assumptions) để không mất khi sinh lại.", None),
        ("", None),
        ("CẤU TRÚC", F_BOLD),
        ("Scenarios — ô chọn kịch bản, hệ số Base/Target/Downside, KPI hợp nhất của kịch bản đang chọn", None),
        ("Assumptions — giả định theo BU và theo tháng (Q4 năm hiện hành + 12 tháng ngân sách), có nguồn/ghi chú", None),
        ("Drivers_Plastic — bao bì: tấn × giá/kg; giá vốn = hạt nhựa/kg × định mức + chuyển đổi; hạt nhựa; phế liệu; BU In 3D tách riêng", None),
        ("Drivers_Media — LED/BA/TTB/DVK/TKL: job ký mới × giá trị bq → backlog → doanh thu ghi nhận × biên", None),
        ("Drivers_Me — diện tích × đơn giá × lấp đầy (ngoài + nội bộ), dự án công nghệ, bán lại túi mua từ Plastic", None),
        ("Headcount — số người × lương × (1 + BHXH 21,5% phần DN [cần xác nhận] + thưởng/12)", None),
        ("Opex — chi phí bán hàng (641) & QLDN (642) theo công ty; thuê nội bộ của Plastic/Media", None),
        ("Capex — capex, khấu hao tài sản hiện có + tài sản mới (đường thẳng), giá trị còn lại", None),
        ("Debt — lịch vay ngân hàng từng công ty, vay nội bộ Mẹ → Media, lãi vay", None),
        ("FS_Me / FS_Plastic / FS_Media — KQKD, CĐKT, LCTT theo tháng, liên kết (tiền CĐKT = tiền cuối LCTT)", None),
        ("IC_Elims — giao dịch nội bộ theo cặp, bút toán loại trừ, số dư nội bộ, đầu tư vào công ty con", None),
        ("Consolidated — hợp nhất quản trị (KQKD, doanh thu ngoài theo mảng, CĐKT, LCTT)", None),
        (f"{M.forecast_name} — cả năm {M.fy}: tháng thực tế (từ Actuals_Input) + tháng dự báo; so với ngân sách", None),
        ("Checks — mọi kiểm tra = 0: CĐKT cân, tiền khớp LCTT, nội bộ cân, dự báo khớp BCTC, dữ liệu thực tế khớp", None),
        ("Actuals_Input — số thực tế đã nhập (đồng), đúng định dạng `afi export-pl`", None),
        ("", None),
        ("GIẢ ĐỊNH ĐƠN GIẢN HÓA (đọc trước khi trình)", F_BOLD),
        ("• Không tính VAT trong công nợ; phải thu/tồn kho/phải trả theo số ngày × doanh thu/giá vốn tháng ÷ 30.", None),
        ("• Thuế TNDN = thuế suất × LNTT từng tháng; nộp số dư vào T1/T4/T7/T10. Chưa tính ưu đãi, chuyển lỗ, chi phí không được trừ.", None),
        ("• Lãi vay tính trên dư nợ đầu tháng; không có hạn mức tự động bù thiếu tiền — xem tiền cuối kỳ từng công ty.", None),
        ("• Mẹ bán hết túi mua từ Plastic trong tháng → không có lãi chưa thực hiện trong tồn kho (đúng chính sách P5 hiện hành).", None),
        ("• Hợp nhất giả định sở hữu 100%; chưa tính NCI, lợi thế thương mại; cổ tức con → Mẹ chưa mô hình.", None),
        ("• In 3D: chỉ chi phí trực tiếp, không phân bổ chi phí chung (P11).", None),
        ("• Tháng dự báo trong Forecast: toàn bộ khấu hao đưa vào giá vốn để so sánh với dòng 'cogs' của afi.", None),
        ("", None),
        ("QUY ƯỚC MÀU: ô nhập = nền xanh nhạt, chữ xanh dương · tổng năm = nền xám · ô kiểm tra ≠ 0 = nền đỏ.", None),
        ("Sinh lại file: python tools/budget-model/build_budget_model.py --help", None),
    ]
    for i, (t, f) in enumerate(lines, start=1):
        if t == "__CHECKS__":
            ws.cell(i, 1, '=IF(Checks!$D$6=0,"ĐẠT — "&Checks!$D$7&" kiểm tra đều = 0","CÓ "&Checks!$D$6&" KIỂM TRA LỖI — mở sheet Checks")')
            ws.cell(i, 1).font = Font(bold=True, color="006100")
            continue
        ws.cell(i, 1, t)
        if f:
            ws.cell(i, 1).font = f
    ws.column_dimensions["A"].width = 140


# ================================================================== IO
def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_actuals(path, fy, n_act):
    rows, rejected = [], []
    valid_m = {f"{fy}-{m:02d}" for m in range(1, n_act + 1)}
    for r in read_csv(path):
        co, mo, ln = r["company"].strip(), r["month"].strip(), r["line"].strip()
        if co not in COMPANIES or mo not in valid_m or ln not in BASE_LINES + IC_LINES:
            rejected.append(r)
            continue
        rows.append(dict(company=co, month=mo, line=ln, amount=float(r["amount"]), source=r.get("source") or Path(path).name))
    return rows, rejected


def load_opening(path):
    bs, ic = sd.opening_bs()
    bs = {c: {k: 0 for k in v} for c, v in bs.items()}
    ic = {k: 0 for k in ic}
    for r in read_csv(path):
        co, ln, amt = r["company"].strip(), r["line"].strip(), float(r["amount"]) / 1_000_000
        if ln in ic:
            ic[ln] = amt
        elif co in bs:
            bs[co][ln] = amt
    return bs, ic


def load_overrides(path):
    ov = {}
    for r in read_csv(path):
        k = r["key"].strip()
        d = ov.setdefault(k, {})
        d[r["period"].strip()] = float(r["value"])
        if r.get("source"):
            d["__source__"] = r["source"]
    return ov


def write_templates(d: Path, cfg):
    d.mkdir(parents=True, exist_ok=True)
    fy, n = cfg["actual_through"][0], cfg["actual_through"][1]
    with open(d / "actuals_template.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["company", "month", "line", "amount", "source"])
        for r in sd.sample_actuals(fy, n):
            w.writerow([r["company"], r["month"], r["line"], r["amount"], r["source"]])
    bs, ic = sd.opening_bs()
    with open(d / "opening_bs_template.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["company", "line", "amount"])
        for co, v in bs.items():
            for k, a in v.items():
                w.writerow([co, k, round(a * 1_000_000)])
        owner = {"ic_bag": "APL", "ic_rent_apl": "ALTA", "ic_rent_ame": "ALTA", "ic_loan": "ALTA"}
        for k, a in ic.items():
            w.writerow([owner[k], k, round(a * 1_000_000)])


def dump_assumptions(path, M, specs, overrides):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["key", "period", "value", "source", "label", "unit"])
        for sp in specs:
            ov = overrides.get(sp["key"], {})
            src = ov.get("__source__", default_source(sp))
            if sp["kind"] == "D":
                v = ov.get("D", M.cfg["budget_year"] if sp["key"] == "budget_year" else sp["base"])
                w.writerow([sp["key"], "D", v, src, sp["label"], sp["unit"]])
            else:
                for y, m in M.months:
                    p = f"{y}-{m:02d}"
                    w.writerow([sp["key"], p, ov.get(p, sd.default_value(sp, y, m, M.cfg["budget_year"])), src,
                                sp["label"], sp["unit"]])


def recalc_with_libreoffice(path: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    with tempfile.TemporaryDirectory() as td:
        prof = Path(td) / "profile"
        cmd = [soffice, f"-env:UserInstallation=file://{prof}", "--headless", "--calc", "--convert-to", "xlsx",
               "--outdir", td, str(path)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        out = Path(td) / path.name
        if not out.exists():
            return False
        shutil.copyfile(out, path)
    return True


# ================================================================== main
def build(args) -> Path:
    y, m = map(int, args.actual_through.split("-"))
    cfg = dict(actual_through=(y, m), budget_year=args.budget_year,
               generated=dt.datetime.now().strftime("%Y-%m-%d %H:%M"))
    M = Model(cfg)
    M.forecast_name = f"Forecast_FY{M.fy}"
    M.fc_rows = {}
    n_act = m if y == M.fy else 0
    specs = sd.assumption_specs(args.budget_year)
    overrides = load_overrides(args.assumptions) if args.assumptions else {}
    unknown = set(overrides) - {s["key"] for s in specs}
    if unknown:
        raise SystemExit(f"Khóa giả định không tồn tại: {sorted(unknown)}")
    if args.dump_assumptions:
        dump_assumptions(args.dump_assumptions, M, specs, overrides)
        print(f"Đã xuất giả định → {args.dump_assumptions}")
        return Path(args.dump_assumptions)
    sample_parts = []
    if args.actuals:
        actuals, rej = load_actuals(args.actuals, M.fy, n_act)
        cfg["actuals_source"] = f"{Path(args.actuals).name} ({len(actuals)} dòng; bỏ qua {len(rej)} dòng ngoài kỳ/không nhận diện)"
        if rej:
            print(f"Cảnh báo: bỏ qua {len(rej)} dòng thực tế (công ty/tháng/line không hợp lệ), ví dụ: {rej[0]}")
    else:
        actuals = sd.sample_actuals(M.fy, n_act) if n_act else []
        cfg["actuals_source"] = "DỮ LIỆU MẪU (sinh ngẫu nhiên có kiểm soát — không phải số thật)"
        sample_parts.append("số thực tế")
    if args.opening_bs:
        opening, ic = load_opening(args.opening_bs)
        cfg["opening_source"] = Path(args.opening_bs).name
    else:
        opening, ic = sd.opening_bs()
        cfg["opening_source"] = "DỮ LIỆU MẪU"
        sample_parts.append("số dư đầu kỳ")
    if args.assumptions:
        cfg["assumptions_source"] = (f"{Path(args.assumptions).name} — {len(sample_keys(specs, overrides))} giả định còn là MẪU "
                                     "(không có trong file hoặc cột source còn ghi 'MẪU')")
        missing = sample_keys(specs, overrides)
        if missing:
            sample_parts.append(f"{len(missing)}/{len(specs) - len(STRUCTURAL)} giả định")
    else:
        cfg["assumptions_source"] = "DỮ LIỆU MẪU — chờ giả định từ trưởng BU"
        sample_parts.append("giả định BU")
    if sample_parts:
        banner = ("⚠ DỮ LIỆU MẪU — " + ", ".join(sample_parts) +
                  " là số minh họa, KHÔNG phải số liệu thật của Alta. Không dùng để ra quyết định.")
    else:
        banner = "Số liệu từ file đầu vào — kiểm tra sheet Checks trước khi trình HĐQT."
    cfg["banner"] = banner

    # 1) layout
    register_scenarios(M)
    build_assumptions(M, specs, overrides)
    build_plastic(M)
    build_media(M)
    build_me(M)
    build_headcount(M)
    build_opex(M)
    build_capex(M, opening)
    build_debt(M, opening, ic)
    for co in COMPANIES:
        build_fs(M, co, opening)
    build_ic(M, ic)
    build_consol(M)
    chk, ck = build_checks(M)
    # 2) workbook
    wb = Workbook()
    write_readme(wb, M, banner)
    order = ["Checks", "Assumptions", "Drivers_Plastic", "Drivers_Media", "Drivers_Me", "Headcount", "Opex", "Capex",
             "Debt", "FS_Me", "FS_Plastic", "FS_Media", "IC_Elims", "Consolidated"]
    # Forecast & Actuals cần layout trước khi Checks render → tạo trước, sắp xếp sau
    write_actuals(wb, actuals, banner, M)
    write_forecast(wb, M, banner)
    build_forecast_rows(chk, ck, M)
    for name in order:
        ws = write_msheet(wb, M, M.sheets[name], banner)
        if name == "Checks":
            write_checks_extra(ws, M, M.sheets[name], ck)
    write_scenarios(wb, M, banner, args.scenario)
    # thứ tự sheet
    want = ["README", "Scenarios", "Checks", "Assumptions", "Drivers_Plastic", "Drivers_Media", "Drivers_Me",
            "Headcount", "Opex", "Capex", "Debt", "FS_Me", "FS_Plastic", "FS_Media", "IC_Elims", "Consolidated",
            M.forecast_name, "Actuals_Input"]
    wb._sheets = [wb[n] for n in want]
    wb.active = 0
    for ws in wb.worksheets:
        ws.sheet_properties.tabColor = {"README": "1F3864", "Scenarios": "C00000", "Checks": "C00000",
                                        "Assumptions": "0070C0"}.get(ws.title, "A6A6A6" if ws.title.startswith(("Drivers", "Head", "Opex", "Capex", "Debt")) else "548235")
    wb.calculation.fullCalcOnLoad = True
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    if args.recalc:
        ok = recalc_with_libreoffice(out)
        print("Đã tính lại bằng LibreOffice (lưu kèm giá trị)." if ok else "Không tìm thấy LibreOffice — bỏ qua tính lại.")
    print(f"Đã sinh {out} · kịch bản {args.scenario} · {len(M.months)} tháng dự báo · {len(ck)} kiểm tra")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--actuals", help="CSV thực tế (company,month,line,amount) — output `afi export-pl`")
    ap.add_argument("--opening-bs", help="CSV số dư đầu kỳ (company,line,amount)")
    ap.add_argument("--assumptions", help="CSV giả định (key,period,value[,source])")
    ap.add_argument("--actual-through", default="2026-09", help="Tháng thực tế cuối cùng YYYY-MM (mặc định 2026-09)")
    ap.add_argument("--budget-year", type=int, default=2027)
    ap.add_argument("--scenario", default="Base", choices=SCENARIOS)
    ap.add_argument("--out", default=str(HERE / "output" / "Alta_Forecast2026_Budget2027_MAU.xlsx"))
    ap.add_argument("--recalc", action="store_true", help="Tính lại bằng LibreOffice headless để lưu kèm giá trị")
    ap.add_argument("--dump-assumptions", help="Xuất toàn bộ giả định hiện hành ra CSV rồi thoát")
    ap.add_argument("--write-templates", help="Ghi CSV mẫu đầu vào vào thư mục này rồi thoát")
    a = ap.parse_args(argv)
    if a.write_templates:
        y, m = map(int, a.actual_through.split("-"))
        write_templates(Path(a.write_templates), dict(actual_through=(y, m)))
        print(f"Đã ghi CSV mẫu vào {a.write_templates}")
        return 0
    build(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
