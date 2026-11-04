"""Test mô hình Dự báo & Ngân sách: mở được, công thức thật, mọi ô Checks = 0 cho cả 3 kịch bản.

Bộ tính công thức: LibreOffice headless (ưu tiên) → pycel (dự phòng) → bỏ qua phần tính lại nếu không có cả hai.
"""
from __future__ import annotations

import csv
import os
import shutil
import sys
from pathlib import Path

import openpyxl
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import build_budget_model as bbm  # noqa: E402

# BUDGET_MODEL_EVALUATOR=pycel để ép dùng bộ tính dự phòng
HAS_LO = bool(shutil.which("soffice") or shutil.which("libreoffice")) and os.environ.get("BUDGET_MODEL_EVALUATOR") != "pycel"
try:
    import pycel  # noqa: F401
    HAS_PYCEL = True
except ImportError:
    HAS_PYCEL = False

CALC_SHEETS = ["Drivers_Plastic", "Drivers_Media", "Drivers_Me", "Headcount", "Opex", "Capex", "Debt",
               "FS_Me", "FS_Plastic", "FS_Media", "IC_Elims", "Consolidated", "Checks"]


def build(tmp_path, *extra, name="m.xlsx"):
    out = tmp_path / name
    bbm.main(["--out", str(out), *extra])
    return out


class Evaluator:
    """Giá trị đã tính của workbook: LibreOffice (lưu kèm giá trị) hoặc pycel."""

    def __init__(self, path: Path):
        self.path = path
        if HAS_LO:
            assert bbm.recalc_with_libreoffice(path)
            self.wb = openpyxl.load_workbook(path, data_only=True)
            self.xl = None
        elif HAS_PYCEL:
            from pycel import ExcelCompiler
            self.xl = ExcelCompiler(filename=str(path))
            self.wb = None
        else:
            pytest.skip("Không có LibreOffice hoặc pycel để tính lại công thức")

    def get(self, sheet, cell):
        if self.wb is not None:
            return self.wb[sheet][cell].value
        return self.xl.evaluate(f"{sheet}!{cell}")


def check_rows(path):
    wb = openpyxl.load_workbook(path)
    ws = wb["Checks"]
    maxc = ws.max_column
    rows = [r for r in range(9, ws.max_row + 1)
            if isinstance(ws.cell(r, maxc).value, str) and ws.cell(r, maxc).value.startswith("=MAX(")]
    return rows, openpyxl.utils.get_column_letter(maxc)


# ---------------------------------------------------------------- cấu trúc
def test_opens_with_all_sheets_and_sample_banner(tmp_path):
    out = build(tmp_path)
    wb = openpyxl.load_workbook(out)
    need = {"README", "Assumptions", "Scenarios", "Drivers_Plastic", "Drivers_Media", "Drivers_Me", "Headcount",
            "Opex", "Capex", "Debt", "FS_Me", "FS_Plastic", "FS_Media", "IC_Elims", "Consolidated",
            "Forecast_FY2026", "Checks", "Actuals_Input"}
    assert need <= set(wb.sheetnames)
    for ws in wb.worksheets:
        assert "DỮ LIỆU MẪU" in str(ws["A2"].value), ws.title


def test_calculated_sheets_contain_only_formulas(tmp_path):
    """Không hardcode kết quả: mọi ô tháng của sheet tính toán là công thức (trừ ô nhập màu xanh)."""
    out = build(tmp_path)
    wb = openpyxl.load_workbook(out)
    n_formula = 0
    for name in CALC_SHEETS:
        ws = wb[name]
        for row in ws.iter_rows(min_row=7, min_col=5, max_col=ws.max_column):
            for c in row:
                if c.value is None:
                    continue
                is_input = c.fill.fgColor.rgb in ("00DDEBF7", "FFDDEBF7")
                if isinstance(c.value, str) and c.value.startswith("="):
                    n_formula += 1
                elif not is_input:
                    assert c.value == 0 and name == "Checks", f"{name}!{c.coordinate} = {c.value!r}"
    assert n_formula > 5000


def test_assumptions_have_source_column_and_blue_inputs(tmp_path):
    out = build(tmp_path)
    ws = openpyxl.load_workbook(out)["Assumptions"]
    n = 0
    for r in range(7, ws.max_row + 1):
        lab, unit, src = ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 3).value
        d, e = ws.cell(r, 4), ws.cell(r, 5)
        if not unit or r == 8:  # dòng tiêu đề mục / dòng công thức is_bud
            continue
        inp = d if d.value is not None else e
        if lab == "Tháng":
            continue
        assert src, f"Thiếu nguồn/ghi chú dòng {r}: {lab}"
        assert inp.font.color.rgb.endswith("0000FF"), f"Ô nhập không màu xanh dòng {r}"
        n += 1
    assert n > 80
    bh = [ws.cell(r, 3).value for r in range(7, ws.max_row + 1) if ws.cell(r, 2).value and "BHXH" in str(ws.cell(r, 1).value)]
    assert bh and "XÁC NHẬN" in bh[0]


# ---------------------------------------------------------------- tính lại: mọi kiểm tra = 0
@pytest.mark.parametrize("scenario", ["Base", "Target", "Downside"])
def test_all_checks_zero_for_each_scenario(tmp_path, scenario):
    out = build(tmp_path, "--scenario", scenario, name=f"m_{scenario}.xlsx")
    rows, maxc = check_rows(out)
    assert len(rows) >= 20
    ev = Evaluator(out)
    assert ev.get("Scenarios", "C5") == scenario
    bad = {}
    for r in rows:
        v = ev.get("Checks", f"{maxc}{r}")
        assert isinstance(v, (int, float)), f"Checks!{maxc}{r} = {v!r} (lỗi công thức?)"
        if abs(v) > 0.001:
            bad[r] = v
    assert not bad, f"Kiểm tra ≠ 0 ({scenario}): {bad}"
    assert ev.get("Checks", "D6") == 0


def test_scenarios_move_results_in_expected_direction(tmp_path):
    vals = {}
    for sc in ("Base", "Target", "Downside"):
        out = build(tmp_path, "--scenario", sc, name=f"s_{sc}.xlsx")
        ev = Evaluator(out)
        col = bbm.Model(dict(actual_through=(2026, 9), budget_year=2027)).ycol(2027)
        r = openpyxl.load_workbook(out)["Consolidated"]
        row = next(i for i in range(1, r.max_row + 1) if r.cell(i, 1).value == "EBITDA hợp nhất")
        vals[sc] = ev.get("Consolidated", f"{col}{row}")
    assert vals["Downside"] < vals["Base"] < vals["Target"]


def test_no_excel_errors_after_recalc(tmp_path):
    if not HAS_LO:
        pytest.skip("Cần LibreOffice để quét toàn bộ ô")
    out = build(tmp_path)
    Evaluator(out)
    wb = openpyxl.load_workbook(out, data_only=True)
    errs = [(ws.title, c.coordinate, c.value) for ws in wb.worksheets for row in ws.iter_rows() for c in row
            if isinstance(c.value, str) and (c.value.startswith("#") or c.value.startswith("Err:"))]
    assert not errs, errs[:10]


# ---------------------------------------------------------------- đầu vào CSV thật
def test_csv_inputs_afi_format(tmp_path):
    tdir = tmp_path / "tpl"
    bbm.main(["--write-templates", str(tdir)])
    act = tdir / "actuals_template.csv"
    rows = list(csv.DictReader(act.open(encoding="utf-8")))
    # thêm các dòng mà `afi export-pl` có thể xuất nhưng mô hình phải bỏ qua
    rows.append(dict(company="APL", month="2026-10", line="net_revenue", amount="1", source="x"))  # ngoài kỳ thực tế
    rows.append(dict(company="APL", month="2026-03", line="gross_profit", amount="1", source="x"))  # dòng dẫn xuất
    rows.append(dict(company="XYZ", month="2026-03", line="cogs", amount="1", source="x"))
    with act.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["company", "month", "line", "amount", "source"])
        w.writeheader()
        w.writerows(rows)
    assum = tmp_path / "assumptions.csv"
    assum.write_text("key,period,value,source\napl_vol_ext,2027-01,250,GĐ Plastic 15/11\n"
                     "tax_rate,D,0.2,Kế toán trưởng\n", encoding="utf-8")
    out = build(tmp_path, "--actuals", str(act), "--opening-bs", str(tdir / "opening_bs_template.csv"),
                "--assumptions", str(assum), name="real.xlsx")
    wb = openpyxl.load_workbook(out)
    a = wb["Assumptions"]
    r = next(i for i in range(1, a.max_row + 1) if a.cell(i, 1).value and a.cell(i, 1).value.startswith("Bao bì — sản lượng bán ngoài"))
    assert a.cell(r, 8).value == 250 and a.cell(r, 3).value == "GĐ Plastic 15/11"
    assert "Bỏ qua 3".lower() in str(wb["README"]["A5"].value).lower()
    ai = wb["Actuals_Input"]
    assert ai.max_row - 5 == len(rows) - 3
    rws, maxc = check_rows(out)
    ev = Evaluator(out)
    assert ev.get("Checks", "D6") == 0
    # tổng doanh thu 9T của Plastic trên Forecast = tổng CSV
    exp = sum(float(x["amount"]) for x in rows if x["company"] == "APL" and x["line"] == "net_revenue"
              and x["month"] <= "2026-09") / 1e6
    fc = wb["Forecast_FY2026"]
    rr = [i for i in range(1, fc.max_row + 1) if fc.cell(i, 2).value == "net_revenue"][1]  # khối thứ 2 = Plastic
    got = sum(ev.get("Forecast_FY2026", f"{c}{rr}") for c in "DEFGHIJKL")
    assert got == pytest.approx(exp, abs=0.001)


def test_unknown_assumption_key_rejected(tmp_path):
    bad = tmp_path / "a.csv"
    bad.write_text("key,period,value\nkhong_ton_tai,D,1\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        build(tmp_path, "--assumptions", str(bad))


def test_dump_assumptions_roundtrip(tmp_path):
    dump = tmp_path / "gd.csv"
    bbm.main(["--dump-assumptions", str(dump)])
    rows = list(csv.DictReader(dump.open(encoding="utf-8")))
    assert {"key", "period", "value", "source"} <= set(rows[0])
    a = build(tmp_path, name="a.xlsx")
    b = build(tmp_path, "--assumptions", str(dump), name="b.xlsx")
    wa, wb_ = openpyxl.load_workbook(a)["Assumptions"], openpyxl.load_workbook(b)["Assumptions"]
    for r in range(7, wa.max_row + 1):
        for c in range(4, wa.max_column + 1):
            assert wa.cell(r, c).value == wb_.cell(r, c).value, (r, c)


def test_rolling_forecast_next_quarter(tmp_path):
    """Quý sau: thực tế đến 12/2026 → dự báo/ngân sách 12 tháng 2027, vẫn cân."""
    out = build(tmp_path, "--actual-through", "2026-12", name="q.xlsx")
    wb = openpyxl.load_workbook(out)
    assert "Forecast_FY2027" in wb.sheetnames
    assert wb["FS_Me"]["E5"].value == "T01/2027"
    ev = Evaluator(out)
    assert ev.get("Checks", "D6") == 0
