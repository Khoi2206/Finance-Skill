"""13-week cash forecast (spec §8.3). Synthetic inputs only."""
import csv
import datetime as dt
import json

import openpyxl
import pytest
import yaml

from afi.cli import main
from afi.forecasts import cash13w as cf
from afi.forecasts.cash13w_excel import write_excel
from afi.models.warehouse import Warehouse
from afi.pipeline import Pipeline

S1 = dt.date(2026, 10, 26)  # Monday
S2 = dt.date(2026, 11, 2)
M = 1_000_000
D = lambda d, n: (d + dt.timedelta(days=n)).isoformat()  # noqa: E731


def _csv(folder, name, rows):
    cols = cf.INPUT_FILES[name]
    with (folder / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def make_inputs(folder, start, ar=None, ap=None, bank=None, payroll=True, taxes=True, params=None, other=None):
    folder.mkdir(parents=True, exist_ok=True)
    snap = D(start, -3)
    _csv(folder, "bank_balances.csv", bank if bank is not None else [
        {"company": c, "bank": "NH mẫu", "bank_account": f"{c}-1", "date": snap, "balance": b, "restricted": r, "verified_by": "KTT"}
        for c, b, r in (("ALTA", 3000 * M, 0), ("APL", 5000 * M, 500 * M), ("AME", 2000 * M, 0))])
    base_ar = [{"company": c, "customer": f"KH {c}", "invoice": f"{c}-1", "due_date": D(start, 1), "outstanding": 100 * M,
                "expected_date": D(start, 1), "confidence": "Cao", "owner": "A"} for c in ("ALTA", "AME")]
    _csv(folder, "ar_open.csv", base_ar + (ar or []))
    base_ap = [{"company": c, "supplier": "NCC", "invoice": f"{c}-P1", "due_date": D(start, 3), "outstanding": 50 * M,
                "expected_date": D(start, 3), "confidence": "Cao", "owner": "B"} for c in ("ALTA", "AME")]
    _csv(folder, "ap_open.csv", base_ap + (ap or []))
    if payroll:
        _csv(folder, "payroll.csv", [{"company": c, "item": "Lương", "due_date": D(start, 9), "expected_date": D(start, 9), "amount": 80 * M,
                                      "confidence": "Cao", "owner": "HC"} for c in ("ALTA", "APL", "AME")])
    if taxes:
        _csv(folder, "taxes.csv", [{"company": c, "item": "GTGT", "due_date": D(start, 18), "expected_date": D(start, 18), "amount": 30 * M,
                                    "confidence": "Trung bình", "owner": "T"} for c in ("ALTA", "APL", "AME")])
    if other:
        _csv(folder, "other.csv", other)
    (folder / "params.yaml").write_text(yaml.safe_dump(params or {"min_liquidity_floor": {"approved_by": "CFO", "by_company": {
        "ALTA": 500 * M, "APL": 1000 * M, "AME": 500 * M}}}), encoding="utf-8")
    return folder


APL_AR = [{"company": "APL", "customer": "KH lớn", "invoice": "APL-1", "due_date": D(S1, 1), "outstanding": 600 * M, "expected_date": D(S1, 1),
           "confidence": "Cao", "owner": "C"},
          {"company": "APL", "customer": "KH nhỏ", "invoice": "APL-2", "due_date": D(S1, 20), "outstanding": 200 * M, "expected_date": D(S1, 20),
           "confidence": "Thấp", "owner": "C"}]
APL_AP = [{"company": "APL", "supplier": "NCC hạt", "invoice": "APL-P1", "due_date": D(S1, 2), "outstanding": 250 * M, "expected_date": D(S1, 2),
           "confidence": "Cao", "owner": "D"}]
IC_AR = {"company": "ALTA", "customer": "Alta Plastic", "invoice": "IC-1", "due_date": D(S1, 4), "outstanding": 70 * M, "expected_date": D(S1, 4),
         "confidence": "Cao", "owner": "A", "counterparty_company": "APL"}
IC_AP = {"company": "APL", "supplier": "Alta Mẹ", "invoice": "IC-1", "due_date": D(S1, 4), "outstanding": 70 * M, "expected_date": D(S1, 4),
         "confidence": "Cao", "owner": "D", "counterparty_company": "ALTA"}


def gl_file(path, title, mst, start, lines):
    wb = openpyxl.Workbook()
    ws = wb.active
    end = start + dt.timedelta(days=6)
    for x in [title, f"MST: {mst}", "SỔ NHẬT KÝ CHUNG", f"Từ ngày {start:%d/%m/%Y} đến ngày {end:%d/%m/%Y}", None]:
        ws.append([x])
    ws.append(["Ngày ct", "Số ct", "Diễn giải", "Tk", "Tk đ/ư", "Ps nợ", "Ps có", "Mã khách", "Tên khách"])
    tot = 0
    for i, (day, dr, cr, amt, cp) in enumerate(lines):
        d = dt.datetime.combine(start + dt.timedelta(days=day), dt.time())
        ws.append([d, f"CT{i}", "mẫu", dr, cr, amt, None, cp, ""])
        ws.append([d, f"CT{i}", "mẫu", cr, dr, None, amt, cp, ""])
        tot += amt
    ws.append([None, None, "Tổng cộng", None, None, tot, tot])
    wb.save(path)
    return path


@pytest.fixture
def gl_week(tmp_path):
    """Actuals for week S1: APL collects 500, pays 200, moves 100 bank→cash, pays IC 50 to ALTA; ALTA receives IC 50."""
    d = tmp_path / "gl"
    d.mkdir()
    apl = gl_file(d / "NKC 2026-10-26 - Alta Plastic.xlsx", "CÔNG TY CP ALTA PLASTIC", "0312414944", S1, [
        (1, "1121", "131", 500 * M, "KH01"), (2, "331", "1121", 200 * M, "NCC01"), (3, "1111", "1121", 100 * M, ""),
        (4, "331", "1121", 50 * M, "0301420079")])
    alta = gl_file(d / "NKC 2026-10-26 - Alta.xlsx", "CÔNG TY CP ALTA", "0301420079", S1, [(4, "1121", "131", 50 * M, "0312414944")])
    return [apl, alta]


def _assert_bridge(res):
    for co, v in res["views"].items():
        for sc, s in v["scenarios"].items():
            for w in range(cf.WEEKS):
                assert s["opening"][w] + s["receipts"][w] + s["payments"][w] + s["intercompany"][w] == pytest.approx(s["closing"][w]), (co, sc, w)
                if w:
                    assert s["opening"][w] == pytest.approx(s["closing"][w - 1])
                lines_sum = sum(s["lines"][l][w] for l in cf.LINE_IDS if not (co == cf.GROUP and l == "INTERCOMPANY"))
                assert lines_sum == pytest.approx(s["receipts"][w] + s["payments"][w] + s["intercompany"][w])


def test_weekly_bridge_ties_and_opening_is_verified_available_cash(tmp_path):
    inp = make_inputs(tmp_path / "in", S1, ar=APL_AR + [IC_AR], ap=APL_AP + [IC_AP])
    res = cf.build(inp, S1, data=tmp_path / "data")
    _assert_bridge(res)
    assert res["opening"] == {"ALTA": 3000 * M, "APL": 4500 * M, "AME": 2000 * M}  # balance − restricted
    apl = res["views"]["APL"]["scenarios"]["base"]
    assert apl["lines"]["AR_COLLECTIONS"][0] == 600 * M
    assert apl["lines"]["AR_COLLECTIONS"][2] == 100 * M  # Thấp × 0.5 in Base
    assert apl["headroom"][0] == pytest.approx(apl["closing"][0] - 1000 * M)
    assert res["views"]["GROUP"]["scenarios"]["base"]["opening"][0] == 9500 * M


def test_downside_never_exceeds_base_even_with_bad_params(tmp_path):
    params = {"min_liquidity_floor": {"approved_by": "CFO", "by_company": {"APL": 1}},
              "scenarios": {"downside": {"receipt_factor": {"CAO": 1.0, "TRUNG_BINH": 1.5, "THAP": 0.9}, "all_receipts_delay_days": -5,
                                         "key_customer_delay_days": 30, "key_customers_top_n": 1, "payment_advance_days": 3}}}
    inp = make_inputs(tmp_path / "in", S1, ar=APL_AR, ap=APL_AP, params=params)
    res = cf.build(inp, S1, data=tmp_path / "data")
    for co, v in res["views"].items():
        b, d = v["scenarios"]["base"], v["scenarios"]["downside"]
        assert all(x <= y + 1e-6 for x, y in zip(d["closing"], b["closing"])), co
        assert all(x <= y + 1e-6 for x, y in zip(d["liquidity"], b["liquidity"])), co
    assert res["key_customers_downside"] == ["KH lớn"]
    d = res["views"]["APL"]["scenarios"]["downside"]["lines"]["AR_COLLECTIONS"]
    assert d[0] == 0 and d[4] == 600 * M  # largest customer delayed 30 days (week 5)
    assert any(i["field"].startswith("downside.") for i in res["data_required"])  # clamped and reported
    _assert_bridge(res)


def test_versions_compare_actual_with_prior_forecast(tmp_path, gl_week):
    data = tmp_path / "data"
    pl = Pipeline(data)
    for f in gl_week:
        assert pl.ingest(f)["status"] == "PARSED"
    prior = cf.build(make_inputs(tmp_path / "in1", S1, ar=APL_AR + [IC_AR], ap=APL_AP + [IC_AP]), S1, data=data)
    p = cf.save_version(prior, data)
    assert p.exists()
    with pytest.raises(FileExistsError):
        cf.save_version(prior, data)  # versions are immutable
    cur = cf.build(make_inputs(tmp_path / "in2", S2), S2, data=data)
    c = cur["comparison"]
    assert c["prior_version_id"] == prior["version_id"] and c["elapsed_weeks"] == [S1.isoformat()]
    var = {(x["company"], x["line"]): x for x in c["week_variance"]}
    assert var[("APL", "AR_COLLECTIONS")]["forecast"] == 600 * M
    assert var[("APL", "AR_COLLECTIONS")]["actual"] == 500 * M
    assert var[("APL", "AR_COLLECTIONS")]["variance"] == -100 * M
    assert var[("APL", "SUPPLIER_PAYMENTS")]["variance"] == 50 * M  # paid 200 vs 250 forecast
    assert var[("APL", "AR_COLLECTIONS")]["needs_explanation"]  # −16.7 % and ≥ materiality
    assert var[("APL", "INTERCOMPANY")]["actual"] == -50 * M and var[("APL", "INTERCOMPANY")]["forecast"] == -70 * M
    assert ("GROUP", "INTERCOMPANY") not in var
    op = {o["company"]: o for o in c["opening_check"]}
    pc = prior["views"]["APL"]["scenarios"]["base"]["closing"][0]
    assert op["APL"]["prior_forecast_closing"] == pc and op["APL"]["difference"] == 4500 * M - pc
    rf = c["rollforward"]["APL"]["base"]
    assert rf[0]["week_start"] == S2.isoformat() and rf[0]["prior_closing"] == prior["views"]["APL"]["scenarios"]["base"]["closing"][1]
    assert rf[-1]["prior_closing"] is None  # week 13 of the new forecast was beyond the old horizon
    # a re-run of the same Monday still compares with the previous Monday, not with itself
    cf.save_version(cur, data)
    again = cf.build(make_inputs(tmp_path / "in3", S2), S2, data=data, created_at=dt.datetime(2026, 11, 3, 9))
    assert again["comparison"]["prior_version_id"] == prior["version_id"]


def test_internal_transfers_and_intercompany_are_eliminated_from_group(tmp_path, gl_week):
    data = tmp_path / "data"
    pl = Pipeline(data)
    for f in gl_week:
        pl.ingest(f)
    res = cf.build(make_inputs(tmp_path / "in", S2, ar=[{**IC_AR, "due_date": D(S2, 4), "expected_date": D(S2, 4)}],
                               ap=[{**IC_AP, "due_date": D(S2, 4), "expected_date": D(S2, 4)}] + [{**APL_AP[0], "due_date": D(S2, 2), "expected_date": D(S2, 2)}]),
                   S2, data=data)
    # actuals (last 13 weeks; S1 is the last one)
    a = res["views"]["APL"]["actuals"]
    assert a["lines"]["AR_COLLECTIONS"][-1] == 500 * M and a["lines"]["SUPPLIER_PAYMENTS"][-1] == -200 * M
    assert a["lines"]["INTERCOMPANY"][-1] == -50 * M
    assert a["net"][-1] == 250 * M  # the 100 bank→cash transfer is not a cash flow
    assert res["internal_transfers_excluded"]["APL"] == 200 * M  # both legs, gross
    g = res["views"]["GROUP"]["actuals"]
    assert g["lines"]["INTERCOMPANY"][-1] == 0 and g["net"][-1] == 300 * M
    assert res["intercompany_check"]["actual_net_by_week"][-1] == 0
    # forecast: IC kept per entity, eliminated in group; matched pair → group = sum of entities
    for sc in ("base", "downside"):
        assert res["views"]["ALTA"]["scenarios"][sc]["lines"]["INTERCOMPANY"][0] == 70 * M
        assert res["views"]["APL"]["scenarios"][sc]["lines"]["INTERCOMPANY"][0] == -70 * M
        grp = res["views"]["GROUP"]["scenarios"][sc]
        assert grp["intercompany"] == [0.0] * cf.WEEKS
        tot = [sum(res["views"][c]["scenarios"][sc]["closing"][w] for c in ("ALTA", "APL", "AME")) for w in range(cf.WEEKS)]
        assert grp["closing"] == pytest.approx(tot)
    assert res["intercompany_check"]["forecast_unmatched"] == []
    # unmatched IC is flagged
    res2 = cf.build(make_inputs(tmp_path / "in2", S2, ar=[{**IC_AR, "due_date": D(S2, 4), "expected_date": D(S2, 4)}]), S2, data=data)
    assert res2["intercompany_check"]["forecast_unmatched"]
    assert any(i["source"] == "intercompany" for i in res2["data_required"])


def test_missing_data_goes_to_data_required(tmp_path):
    bank = [{"company": "ALTA", "bank": "NH", "bank_account": "A1", "date": D(S1, -3), "balance": 1000 * M, "verified_by": "KTT"},
            {"company": "ALTA", "bank": "NH", "bank_account": "A2", "date": D(S1, -3), "balance": 999 * M, "verified_by": ""},
            {"company": "APL", "bank": "NH", "bank_account": "P1", "date": D(S1, -3), "balance": "", "verified_by": "KTT"}]
    ar = [{"company": "APL", "customer": "KH", "invoice": "NOAMT", "due_date": D(S1, 3), "outstanding": "", "expected_date": D(S1, 3), "confidence": "Cao", "owner": "x"},
          {"company": "APL", "customer": "KH", "invoice": "NOOWNER", "due_date": D(S1, 3), "outstanding": 10 * M, "expected_date": D(S1, 3), "confidence": "Cao"},
          {"company": "APL", "customer": "KH", "invoice": "NODATES", "outstanding": 20 * M, "confidence": "Cao", "owner": "x"},
          {"company": "APL", "customer": "KH", "invoice": "PAST", "due_date": D(S1, -20), "outstanding": 30 * M, "expected_date": D(S1, -2),
           "confidence": "Cao", "owner": "x"},
          {"company": "APL", "customer": "KH", "invoice": "SEED", "due_date": D(S1, 1), "outstanding": 40 * M, "confidence": "Cao", "owner": "x"},
          {"company": "APL", "customer": "KH", "invoice": "NOCONF", "due_date": D(S1, 1), "outstanding": 50 * M, "expected_date": D(S1, 1), "owner": "x"},
          {"company": "XYZ", "customer": "KH", "invoice": "BADCO", "due_date": D(S1, 1), "outstanding": 60 * M, "expected_date": D(S1, 1), "owner": "x"}]
    params = {"collection_lag_days": {"default": 14}}
    inp = make_inputs(tmp_path / "in", S1, ar=ar, bank=bank, payroll=False, params=params)
    _csv(inp, "debt_schedule.csv", [{"company": "APL", "lender": "NH", "facility": "F", "flow": "DRAWDOWN", "due_date": D(S1, 5), "amount": 900 * M,
                                     "confidence": "Cao", "owner": "CFO", "approved": ""}])
    res = cf.build(inp, S1, data=tmp_path / "data")
    dr = res["data_required"]
    by = lambda ref: {(i["severity"], i["field"]) for i in dr if i["reference"] == ref}  # noqa: E731
    assert ("LOAI_TRU", "outstanding") in by("NOAMT")
    assert ("THIEU_TT", "owner") in by("NOOWNER")
    assert ("LOAI_TRU", "expected_date") in by("NODATES")
    assert ("LOAI_TRU", "expected_date") in by("PAST")
    assert ("THIEU_TT", "expected_date") in by("SEED")
    assert ("THIEU_TT", "confidence") in by("NOCONF")
    assert any(i["company"] == "XYZ" and i["severity"] == "LOAI_TRU" for i in dr)
    assert any(i["field"] == "verified_by" and i["reference"] == "A2" for i in dr)
    assert any(i["field"] == "approved" and i["source"].startswith("debt_schedule") for i in dr)
    assert {i["company"] for i in dr if i["source"] == "payroll.csv" and i["severity"] == "LOAI_TRU"} == {"ALTA", "APL", "AME"}
    assert any(i["field"] == "min_liquidity_floor" and i["company"] == "APL" for i in dr)
    # opening uses verified rows only; APL has no usable balance
    assert res["opening"]["ALTA"] == 1000 * M and res["opening"]["APL"] == 0
    # amounts: only placeable items count; seeded date = due + 14 and never high confidence / committed
    items = {i["reference"]: i for i in res["items"]}
    assert "NOAMT" not in items and "NODATES" not in items and "BADCO" not in items
    assert items["PAST"]["included"] is False and items["PAST"]["placement"]["base"]["amount"] == 0
    assert items["SEED"]["expected_basis"] == "SEED_LAG" and items["SEED"]["expected_date"] == D(S1, 15)
    assert items["SEED"]["confidence"] == "TRUNG_BINH" and items["SEED"]["committed"] is False
    assert items["NOCONF"]["confidence"] == "THAP"
    apl = res["views"]["APL"]["scenarios"]["base"]["lines"]
    assert apl["AR_COLLECTIONS"][0] == 10 * M + 25 * M  # NOOWNER + NOCONF (Thấp × 0.5)
    assert apl["AR_COLLECTIONS"][2] == 40 * M
    assert apl["DRAWDOWN"] == [0.0] * cf.WEEKS
    assert res["status"] == "DRAFT"
    _assert_bridge(res)


def test_excel_bridge_uses_formulas_and_json_roundtrip(tmp_path):
    res = cf.build(make_inputs(tmp_path / "in", S1, ar=APL_AR + [IC_AR], ap=APL_AP + [IC_AP]), S1, data=tmp_path / "data")
    x = write_excel(res, tmp_path / "out" / "f.xlsx")
    wb = openpyxl.load_workbook(x)
    assert {"Tom_tat", "Chi_tiet", "Tien_dau_ky", "Base_APL", "Down_HopNhat", "Thuc_te_13T", "So_sanh", "DATA_REQUIRED"} <= set(wb.sheetnames)
    ws = wb["Base_APL"]
    labels = {ws.cell(r, 1).value.strip(): r for r in range(6, ws.max_row + 1) if ws.cell(r, 1).value}
    assert str(ws.cell(labels["Tiền khả dụng đầu kỳ"], 3).value).startswith("=SUMIFS(Tien_dau_ky!")
    assert ws.cell(labels["Tiền khả dụng đầu kỳ"], 4).value == f"=C{labels['Tiền khả dụng cuối kỳ']}"
    assert str(ws.cell(labels["Thu từ khách hàng"], 3).value).startswith("=SUMIFS(Chi_tiet!")
    g = wb["Base_HopNhat"]
    assert not any((g.cell(r, 2).value or "") == "INTERCOMPANY" for r in range(1, g.max_row + 1))
    j = json.loads(cf.write_json(res, tmp_path / "out" / "f.json").read_text(encoding="utf-8"))
    assert j["schema"] == cf.SCHEMA and len(j["weeks"]) == 13 and len(j["actual_weeks"]) == 13
    assert j["actual_weeks"][-1]["end"] == D(S1, -1)


def test_cli_sample_end_to_end(tmp_path):
    out, data = tmp_path / "sample", tmp_path / "data"
    assert main(["cash13w", "--start", S2.isoformat(), "--write-sample", str(out)]) == 0
    assert main(["--data", str(data), "ingest", *map(str, sorted((out / "gl").glob("*.xlsx")))]) == 0
    assert main(["--data", str(data), "cash13w", "--start", S1.isoformat(), "--inputs", str(out / f"inputs_{S1}"), "--out", str(tmp_path / "o")]) == 0
    assert main(["--data", str(data), "cash13w", "--start", S2.isoformat(), "--inputs", str(out / f"inputs_{S2}"), "--out", str(tmp_path / "o")]) == 0
    vs = cf.list_versions(data)
    assert [v["start_date"] for v in vs] == [S1.isoformat(), S2.isoformat()]
    j = json.loads(sorted((tmp_path / "o").glob(f"CF13W-{S2}*.json"))[0].read_text(encoding="utf-8"))
    assert j["sample"] is True and j["comparison"]["prior_version_id"] == vs[0]["version_id"]
    assert any(j["views"]["APL"]["actuals"]["has_data"])
    # sample bank balance = prior balance + actual flows of the elapsed week → opening check ties for the main account
    _assert_bridge(j)
    with pytest.raises(ValueError):
        cf.build(out / f"inputs_{S2}", dt.date(2026, 11, 4), data=data)  # not a Monday


def test_templates_have_documented_headers(tmp_path):
    paths = cf.write_templates(tmp_path / "t")
    for name, cols in cf.INPUT_FILES.items():
        assert (tmp_path / "t" / name).read_text(encoding="utf-8").strip() == ",".join(cols)
    assert yaml.safe_load((tmp_path / "t" / "params.yaml").read_text(encoding="utf-8"))["scenarios"]["downside"]["key_customer_delay_days"] == 30
    assert len(paths) == len(cf.INPUT_FILES) + 1
    Warehouse(tmp_path / "empty")  # empty warehouse still builds (no GL → actuals flagged, not invented)
    res = cf.build(make_inputs(tmp_path / "in", S1), S1, data=tmp_path / "empty")
    assert not any(res["views"]["APL"]["actuals"]["has_data"])
