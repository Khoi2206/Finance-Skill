"""afi — ALTA FAST read-only pipeline CLI.

  afi ingest FILE...         store raw copy (idempotent), classify, parse to staging
  afi dictionary FILE...     write physical data dictionary YAML (does not ingest)
  afi reconcile              run control matrix, write data/dq/dq_report.md
  afi status                 list extractions in the manifest
  afi pl --company APL --month 2026-10 [--lineage net_revenue]
  afi export-pl --out actuals.csv [--year 2026]   CSV company,month,line,amount (VND) for tools/budget-model
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import dictionary
from .models.warehouse import Warehouse
from .pipeline import Pipeline
from .reconciliations.controls import period_status, run_controls, write_report

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="afi", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "data", help="data directory (default: ./data)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest"); p.add_argument("files", nargs="+", type=Path); p.add_argument("--company"); p.add_argument("--uploader")
    p = sub.add_parser("dictionary"); p.add_argument("files", nargs="+", type=Path); p.add_argument("--out", type=Path, default=ROOT / "docs" / "data_contracts")
    sub.add_parser("reconcile")
    sub.add_parser("status")
    p = sub.add_parser("pl"); p.add_argument("--company"); p.add_argument("--month"); p.add_argument("--lineage")
    p = sub.add_parser("export-pl"); p.add_argument("--out", type=Path, required=True); p.add_argument("--year")
    a = ap.parse_args(argv)

    if a.cmd == "ingest":
        pl = Pipeline(a.data)
        for f in a.files:
            r = pl.ingest(f, a.uploader, a.company)
            tag = "DUPLICATE (already ingested)" if r.get("duplicate") else r["status"]
            print(f"{f.name}: {tag} · {r.get('report_id')} · {r.get('company_id')} · {r.get('report_period_start')}→{r.get('report_period_end')} · "
                  f"rows {r.get('rows_parsed')} · quarantined {r.get('rows_quarantined')}" + (f" · {r['error']}" if r.get("error") else ""))
    elif a.cmd == "dictionary":
        pl = Pipeline(a.data)
        for f in a.files:
            d = dictionary.build(pl, f)
            print(f"{f.name} → {dictionary.write(d, a.out)}")
            for q in d["open_questions"]:
                print("   ? " + q)
    elif a.cmd == "reconcile":
        wh = Warehouse(a.data)
        res = run_controls(wh)
        st = period_status(res, a.data / "approvals.yaml")
        p = write_report(res, st, a.data / "dq")
        fails = [r for r in res if r["status"] == "FAIL"]
        print(f"{len(res)} controls · {len(fails)} FAIL · report: {p}")
        for k, v in sorted(st.items()):
            print(f"  {k}: {v}")
        return 1 if fails else 0
    elif a.cmd == "status":
        for e in Pipeline(a.data).store.entries():
            print(f"{e['ingested_at']} {e['extraction_id'][:12]} {e.get('status'):<12} {e.get('report_id')} {e.get('company_id')} "
                  f"{e.get('report_period_start')}→{e.get('report_period_end')} {e['source_filename']}")
    elif a.cmd == "pl":
        wh = Warehouse(a.data)
        for k, v in wh.pl(a.company, a.month).items():
            print(f"{k:<20} {v:>20,.0f}")
        if a.lineage:
            print(f"\nLineage: {a.lineage}")
            for fn, row, amt in wh.lineage(a.lineage, a.company, a.month):
                print(f"  {fn} · row {row}: {amt:,.0f}")
    elif a.cmd == "export-pl":
        n = Warehouse(a.data).export_pl_csv(a.out, a.year)
        print(f"{n} rows → {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
