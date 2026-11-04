"""afi — ALTA FAST read-only pipeline CLI.

  afi ingest FILE...         store raw copy (idempotent), classify, parse to staging
  afi dictionary FILE...     write physical data dictionary YAML (does not ingest)
  afi reconcile              run control matrix, write data/dq/dq_report.md
  afi status                 list extractions in the manifest
  afi pl --company APL --month 2026-10 [--lineage net_revenue]
  afi export-pl --out actuals.csv [--year 2026]   CSV company,month,line,amount (VND) for tools/budget-model
  afi boardpack --month 2026-10 [--mode month|ytd] [--plan plan.csv]   board pack PPTX (tools/board-pack)
  afi cash13w --inputs DIR [--start 2026-11-09] [--out DIR] [--no-save]
                             13-week direct cash forecast (Base/Downside), saved as a version
  afi cash13w --templates DIR      write empty CSV templates + params.yaml
  afi cash13w --write-sample DIR   write a synthetic sample (inputs for 2 Mondays + FAST-style GL)
"""
from __future__ import annotations

import argparse
import datetime as dt
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
    p = sub.add_parser("boardpack", help="board pack PPTX (tools/board-pack)")
    p.add_argument("--month", required=True); p.add_argument("--mode", choices=["month", "ytd"], default="month")
    p.add_argument("--plan", type=Path); p.add_argument("--out", type=Path)
    p.add_argument("--threshold-pct", type=float, default=0.10); p.add_argument("--threshold-amount", type=float, default=500e6)
    p = sub.add_parser("cash13w", help="13-week cash forecast")
    p.add_argument("--inputs", type=Path, help="folder with bank_balances.csv, ar_open.csv, ... params.yaml")
    p.add_argument("--start", help="Monday of forecast week 1 (default: Monday of this week)")
    p.add_argument("--params", type=Path, help="params.yaml (default: <inputs>/params.yaml)")
    p.add_argument("--out", type=Path, help="output folder for .xlsx and .json (default: <data>/forecasts/cash13w/out)")
    p.add_argument("--no-save", action="store_true", help="do not store this run as a forecast version")
    p.add_argument("--templates", type=Path, help="write empty input templates to this folder and exit")
    p.add_argument("--write-sample", type=Path, help="write a synthetic sample to this folder and exit")
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
    elif a.cmd == "boardpack":
        tool = ROOT.parent / "tools" / "board-pack"
        if not tool.exists():
            print(f"Không tìm thấy công cụ board pack tại {tool}", file=sys.stderr)
            return 2
        sys.path.insert(0, str(tool))
        from boardpack.cli import main as boardpack_main  # noqa: PLC0415
        args = ["--month", a.month, "--mode", a.mode, "--data", str(a.data),
                "--threshold-pct", str(a.threshold_pct), "--threshold-amount", str(a.threshold_amount)]
        args += ["--plan", str(a.plan)] if a.plan else []
        args += ["--out", str(a.out)] if a.out else []
        return boardpack_main(args)
    elif a.cmd == "cash13w":
        return _cash13w(a)
    return 0


def _cash13w(a) -> int:
    from .forecasts import cash13w as cf
    from .forecasts.cash13w_excel import write_excel

    start = dt.date.fromisoformat(a.start) if a.start else cf.monday_of(dt.date.today())
    if a.templates:
        for p in cf.write_templates(a.templates):
            print(p)
        return 0
    if a.write_sample:
        from .forecasts.cash13w_sample import write_sample
        s = write_sample(a.write_sample, start)
        print(f"DỮ LIỆU MẪU (tổng hợp) → {a.write_sample}")
        print(f"  inputs tuần trước: {s['inputs_prior']}\n  inputs tuần này:   {s['inputs']}")
        for g in s["gl"]:
            print(f"  GL: {g}")
        return 0
    if not a.inputs:
        print("cần --inputs DIR (hoặc --templates / --write-sample)", file=sys.stderr)
        return 2
    res = cf.build(a.inputs, start, data=a.data, params_path=a.params)
    out = a.out or cf.versions_dir(a.data) / "out"
    stem = res["version_id"]
    x = write_excel(res, out / f"{stem}.xlsx")
    j = cf.write_json(res, out / f"{stem}.json")
    if not a.no_save:
        print(f"version saved: {cf.save_version(res, a.data)}")
    print(f"{'[MẪU] ' if res['sample'] else ''}{res['version_id']} · {res['status_label']}")
    print(f"Excel: {x}\nJSON:  {j}")
    for co, v in res["views"].items():
        for sc in ("base", "downside"):
            s = v["scenarios"][sc]
            mh = "n/a" if s["min_headroom"] is None else f"{s['min_headroom']:,.0f}"
            br = ",".join(map(str, s["breach_weeks"])) or "-"
            print(f"  {co:<6} {sc:<8} đầu kỳ {s['opening'][0]:>18,.0f} · thấp nhất {s['min_closing']:>18,.0f} (T{s['min_closing_week']}) · headroom min {mh:>16} · dưới ngưỡng: {br}")
    blocking = sum(1 for i in res["data_required"] if i["severity"] == "LOAI_TRU")
    print(f"DATA REQUIRED: {len(res['data_required'])} ({blocking} loại khỏi dự báo)")
    c = res["comparison"]
    print(f"So sánh: {c.get('prior_version_id') or c.get('message')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
