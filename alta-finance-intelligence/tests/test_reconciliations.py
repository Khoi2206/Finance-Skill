import fixtures as fx
import yaml

from afi.models.warehouse import Warehouse
from afi.pipeline import Pipeline
from afi.reconciliations.controls import period_status, run_controls, write_report


def _load(files, data, tb=None):
    pl = Pipeline(data)
    for k in ("gl", "sales"):
        pl.ingest(files[k])
    pl.ingest(tb or files["tb"])
    return Warehouse(data)


def test_all_controls_pass_on_consistent_set(files, data):
    wh = _load(files, data)
    res = run_controls(wh)
    fails = [r for r in res if r["status"] == "FAIL"]
    assert not fails, fails
    names = {r["control"] for r in res}
    assert {"FILE_TOTALS", "GL_DR_EQ_CR", "TB_DR_EQ_CR", "TB_ROLLFORWARD", "TB_EQ_GL_MOVEMENT", "REVENUE_BRIDGE"} <= names
    assert period_status(res)["APL|2026-10"] == "RECONCILED"
    assert (write_report(res, period_status(res), data / "dq")).exists()


def test_tampered_tb_fails_and_blocks_status(files, data):
    bad = fx.tb_file(files["dir"] / "CDPS 2026-10 - Alta Plastic.xlsx", tamper=True)
    wh = _load(files, data, tb=bad)
    res = run_controls(wh)
    failing = {r["control"] for r in res if r["status"] == "FAIL"}
    assert {"TB_ROLLFORWARD", "TB_DR_EQ_CR"} & failing
    assert period_status(res)["APL|2026-10"] == "RECONCILIATION_FAILED"


def test_approval_only_applies_to_reconciled_periods(files, data):
    wh = _load(files, data)
    (data / "approvals.yaml").write_text(yaml.safe_dump({"approvals": [{"company_id": "APL", "month": "2026-10", "by": "CFO", "at": "2026-11-05"}]}))
    assert period_status(run_controls(wh), data / "approvals.yaml")["APL|2026-10"] == "APPROVED"


def test_pl_excludes_closing_entries_and_lineage_ties_out(files, data):
    wh = _load(files, data)
    p = wh.pl("APL", "2026-10")
    assert p["net_revenue"] == 1_200_000_000  # the 5111→911 closing line is excluded
    assert p["gross_profit"] == 300_000_000
    assert p["profit_before_tax"] == 1_200_000_000 - 900_000_000 - 30_000_000 - 50_000_000 - 120_000_000
    rows = wh.lineage("net_revenue", "APL", "2026-10")
    assert sum(a for _, _, a in rows) == p["net_revenue"]
    assert all(fn.startswith("NKC 2026-10") and r >= 8 for fn, r, _ in rows)


def test_export_pl_csv_for_budget_model(files, data, tmp_path):
    import csv
    wh = _load(files, data)
    out = tmp_path / "actuals.csv"
    assert wh.export_pl_csv(out, "2026") > 0
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert set(rows[0]) == {"company", "month", "line", "amount"}
    rev = sum(float(r["amount"]) for r in rows if r["company"] == "APL" and r["month"] == "2026-10" and r["line"] == "net_revenue")
    assert rev == 1_200_000_000
