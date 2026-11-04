"""Control matrix → DQ status per company × month. Parsing success is not accounting approval."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from ..models.warehouse import Warehouse, _months

TOL_EXACT = 0.5
TOL_ROUND = 1000.0


def run_controls(wh: Warehouse) -> list[dict]:
    con, out = wh.con, []

    def add(control, company, period, ok, detail, expected=None, actual=None, severity="FAIL"):
        out.append({"control": control, "company_id": company, "period": period, "status": "PASS" if ok else severity,
                    "expected": expected, "actual": actual, "difference": None if expected is None or actual is None else round(actual - expected, 2), "detail": detail})

    # 1. file totals vs Tổng cộng
    for e in wh.store.entries():
        if e.get("status") != "PARSED":
            continue
        ct, pt = e.get("control_totals") or {}, e.get("parsed_totals") or {}
        per = (e.get("report_period_start") or "")[:7] + "→" + (e.get("report_period_end") or "")[:7]
        if not ct:
            add("FILE_TOTALS", e["company_id"], per, False, f"{e['source_filename']}: no 'Tổng cộng' row found", severity="WARN")
            continue
        for k, v in ct.items():
            add("FILE_TOTALS", e["company_id"], per, abs(pt.get(k, 0) - v) <= TOL_EXACT, f"{e['source_filename']} · {k}", v, pt.get(k, 0))
    # 2. GL balance per company × month
    for cid, month, d, c in con.execute("SELECT company_id, month, sum(debit), sum(credit) FROM fact_gl_lines GROUP BY ALL ORDER BY ALL").fetchall():
        add("GL_DR_EQ_CR", cid, month, abs(d - c) <= TOL_EXACT, "Σ debit = Σ credit", d, c)
    # 2b. voucher balance (warning: voucher id reliability not yet confirmed)
    for cid, month, n in con.execute("""SELECT company_id, month, count(*) FROM (SELECT company_id, month, posting_date, document_number, sum(debit)-sum(credit) diff
            FROM fact_gl_lines GROUP BY ALL HAVING abs(diff) > 0.5) GROUP BY ALL""").fetchall():
        add("GL_VOUCHER_BALANCE", cid, month, False, f"{n} vouchers (date + number) not balanced; confirm voucher key with Finance", severity="WARN")
    # 3. TB integrity + 4. TB vs GL
    tb = con.execute("SELECT DISTINCT company_id, report_period_start, report_period_end, source_filename FROM fact_tb").fetchall()
    for cid, p0, p1, fn in tb:
        per = p0[:7] + "→" + p1[:7]
        s = con.execute("""SELECT sum(opening_debit), sum(opening_credit), sum(period_debit), sum(period_credit), sum(closing_debit), sum(closing_credit)
            FROM fact_tb WHERE is_leaf AND company_id=? AND report_period_start=?""", [cid, p0]).fetchone()
        for name, a, b in (("opening", s[0], s[1]), ("movement", s[2], s[3]), ("closing", s[4], s[5])):
            add("TB_DR_EQ_CR", cid, per, abs(a - b) <= TOL_EXACT, f"{fn} · {name}", a, b)
        bad = con.execute("""SELECT account_code FROM fact_tb WHERE company_id=? AND report_period_start=?
            AND abs((opening_debit-opening_credit)+(period_debit-period_credit)-(closing_debit-closing_credit)) > 0.5""", [cid, p0]).fetchall()
        add("TB_ROLLFORWARD", cid, per, not bad, f"opening + movement = closing per account; failing: {[b[0] for b in bad][:10]}")
        months = _months(p0, p1)
        have = {m for (m,) in con.execute("SELECT DISTINCT month FROM fact_gl_lines WHERE company_id=?", [cid]).fetchall()}
        if set(months) <= have:
            diffs = con.execute(f"""WITH g AS (SELECT account_code, sum(debit) d, sum(credit) c FROM fact_gl_lines WHERE company_id=? AND month IN ({','.join('?'*len(months))}) GROUP BY 1),
                t AS (SELECT account_code, period_debit d, period_credit c FROM fact_tb WHERE is_leaf AND company_id=? AND report_period_start=?)
                SELECT coalesce(t.account_code, g.account_code), coalesce(g.d,0)-coalesce(t.d,0), coalesce(g.c,0)-coalesce(t.c,0)
                FROM t FULL JOIN g USING (account_code) WHERE abs(coalesce(g.d,0)-coalesce(t.d,0))>0.5 OR abs(coalesce(g.c,0)-coalesce(t.c,0))>0.5""",
                                [cid, *months, cid, p0]).fetchall()
            add("TB_EQ_GL_MOVEMENT", cid, per, not diffs, "leaf movement = GL movement" + (f"; differences: {[(a, round(b), round(c)) for a, b, c in diffs][:8]}" if diffs else ""))
    # 5. revenue bridge
    for cid, month, gl, sl in con.execute("""WITH g AS (SELECT company_id, month, sum(amount) gl FROM pl_lines_lineage WHERE line='net_revenue' GROUP BY ALL),
            s AS (SELECT company_id, month, sum(amount) sl FROM fact_sales_lines GROUP BY ALL)
            SELECT company_id, month, coalesce(gl,0), coalesce(sl,0) FROM g FULL JOIN s USING (company_id, month) ORDER BY ALL""").fetchall():
        add("REVENUE_BRIDGE", cid, month, abs(gl - sl) <= TOL_ROUND, "GL 511/521 net (excl. 911) vs sales list 'Tiền'; differences need listed reconciling items", sl, gl)
    return out


def period_status(results: list[dict], approvals_path: Path | None = None) -> dict[str, str]:
    approved = set()
    if approvals_path and approvals_path.exists():
        for a in (yaml.safe_load(approvals_path.read_text(encoding="utf-8")) or {}).get("approvals", []):
            approved.add((a["company_id"], a["month"]))
    status: dict[str, str] = {}
    for r in results:
        months = _months(r["period"][:7], r["period"][-7:]) if "→" in r["period"] else [r["period"]]
        for m in months:
            k = f"{r['company_id']}|{m}"
            cur = status.get(k, "RECONCILED")
            if r["status"] == "FAIL":
                cur = "RECONCILIATION_FAILED"
            status[k] = cur
    for k, v in status.items():
        cid, m = k.split("|")
        if v == "RECONCILED" and (cid, m) in approved:
            status[k] = "APPROVED"
    return status


def write_report(results: list[dict], status: dict[str, str], out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "dq_results.json").write_text(json.dumps({"results": results, "status": status}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    lines = ["# Data quality report", "", "## Status by company × month", "", "| Company | Month | Status |", "|---|---|---|"]
    lines += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {v} |" for k, v in sorted(status.items())]
    lines += ["", "## Controls", "", "| Control | Company | Period | Result | Expected | Actual | Difference | Detail |", "|---|---|---|---|---|---|---|---|"]
    f = lambda v: "" if v is None else f"{v:,.0f}"  # noqa: E731
    lines += [f"| {r['control']} | {r['company_id']} | {r['period']} | {r['status']} | {f(r['expected'])} | {f(r['actual'])} | {f(r['difference'])} | {r['detail']} |" for r in results]
    p = out_dir / "dq_report.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p
