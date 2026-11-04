"""Sinh warehouse + file kế hoạch MẪU từ dữ liệu tổng hợp (tests/fixtures.py · group_dataset). Không phải số thật của Alta."""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

from . import REPO
from .facts import BASE_LINES, Facts, shift

AFI_TESTS = REPO / "alta-finance-intelligence" / "tests"
# chỉ tiêu kế hoạch mẫu so với cùng kỳ 2025 (giả định minh họa)
PLAN_GROWTH = {"APL": 1.12, "AME": 1.18, "ALTA": 1.05}


def fixtures():
    if str(AFI_TESTS) not in sys.path:
        sys.path.insert(0, str(AFI_TESTS))
    import fixtures as fx  # noqa: PLC0415
    return fx


def build_warehouse(work: Path, approve: list[tuple[str, str]] = (), **kw):
    """Sinh file FAST tổng hợp → ingest → Warehouse. approve: [(company, month)] ghi vào data/approvals.yaml."""
    from afi.models.warehouse import Warehouse  # noqa: PLC0415
    from afi.pipeline import Pipeline  # noqa: PLC0415

    work = Path(work)
    shutil.rmtree(work, ignore_errors=True)
    files = fixtures().group_dataset(work / "inbox", **kw)
    pl = Pipeline(work / "data")
    for f in files:
        pl.ingest(f, uploader="sample")
    if approve:
        import yaml  # noqa: PLC0415
        (work / "data" / "approvals.yaml").write_text(yaml.safe_dump(
            {"approvals": [{"company_id": c, "month": m, "by": "CFO (mẫu)", "at": "2026-11-05"} for c, m in approve]}, allow_unicode=True), encoding="utf-8")
    return Warehouse(work / "data")


def write_plan(facts: Facts, year: int, out: Path, growth: dict | None = None) -> Path:
    """Kế hoạch mẫu theo tháng: doanh thu = cùng kỳ năm trước × tăng trưởng; giá vốn giữ tỷ lệ năm trước;
    chi phí BH/QL +5%; các dòng khác = năm trước; thuế 20% LNTT kế hoạch."""
    growth = growth or PLAN_GROWTH
    rows = []
    for c in facts.companies:
        for mo in range(1, 13):
            m = f"{year}-{mo:02d}"
            p = facts.pl(c, [shift(m, -12)])
            if not p:
                continue
            g = growth.get(c, 1.0)
            v = {k: p[k] for k in BASE_LINES}
            v["net_revenue"] = p["net_revenue"] * g
            v["cogs"] = p["cogs"] * g
            v["selling_expenses"] = p["selling_expenses"] * g
            v["admin_expenses"] = p["admin_expenses"] * 1.05
            pbt = (v["net_revenue"] + v["finance_income"] + v["other_income"] - v["cogs"] - v["finance_expense"]
                   - v["selling_expenses"] - v["admin_expenses"] - v["other_expense"])
            v["income_tax"] = max(pbt, 0) * 0.2
            rows += [{"company": c, "month": m, "line": k, "amount": round(x, -6)} for k, x in v.items()]
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["company", "month", "line", "amount"])
        w.writeheader()
        w.writerows(rows)
    return out
