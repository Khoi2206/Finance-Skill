"""Gold layer in DuckDB: effective extractions, facts, P&L mart and lineage queries."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import duckdb

from ..ingestion.store import RawStore
from ..parsers.base import load_config


V, N, B = "NULL::VARCHAR", "NULL::DOUBLE", "NULL::BOOLEAN"
EMPTY = {
    "GL_JOURNAL": f"{V} AS company_id, {V} AS month, {V} AS posting_date, {V} AS document_number, {V} AS account_code, {V} AS contra_account_code, {V} AS description, {V} AS counterparty_code, {V} AS counterparty_name, {V} AS job_code, {N} AS debit, {N} AS credit, {V} AS extraction_id, {V} AS source_filename, NULL::BIGINT AS source_row_number",
    "SALES_LIST": f"{V} AS company_id, {V} AS month, {N} AS amount, {V} AS extraction_id, {V} AS source_filename, NULL::BIGINT AS source_row_number",
    "TB": f"{V} AS company_id, {V} AS report_period_start, {V} AS report_period_end, {V} AS source_filename, {V} AS account_code, {B} AS is_leaf, {N} AS opening_debit, {N} AS opening_credit, {N} AS period_debit, {N} AS period_credit, {N} AS closing_debit, {N} AS closing_credit",
}


def _months(a: str, b: str) -> list[str]:
    y, m = int(a[:4]), int(a[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= b[:7]:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


class Warehouse:
    def __init__(self, data_dir: Path, config_dir: Path | None = None):
        self.data = Path(data_dir)
        self.store = RawStore(self.data)
        self.accounts = load_config("account_map.yaml", config_dir)
        self.con = duckdb.connect(str(self.data / "warehouse.duckdb"))
        self.refresh()

    def refresh(self) -> None:
        con = self.con
        ents = [e for e in self.store.entries() if e.get("status") in ("PARSED", "VALIDATED", "RECONCILED", "APPROVED")]
        # effective extraction per (report, company, month): newest ingested wins
        eff: dict[tuple, dict] = {}
        for e in sorted(ents, key=lambda e: e.get("seq", 0)):
            if e["report_id"] == "TB":
                eff[("TB", e["company_id"], e["report_period_start"] + "~" + e["report_period_end"])] = e
            else:
                for m in _months(e["report_period_start"], e["report_period_end"]):
                    eff[(e["report_id"], e["company_id"], m)] = e
        con.execute("CREATE OR REPLACE TABLE effective (report_id VARCHAR, company_id VARCHAR, period_key VARCHAR, extraction_id VARCHAR)")
        if eff:
            con.executemany("INSERT INTO effective VALUES (?,?,?,?)", [(k[0], k[1], k[2], v["extraction_id"]) for k, v in eff.items()])
        for rid, table in (("GL_JOURNAL", "fact_gl_lines"), ("SALES_LIST", "fact_sales_lines"), ("TB", "fact_tb")):
            files = sorted({str(self.data / "staging" / rid / f"{e['extraction_id']}.parquet") for k, e in eff.items() if k[0] == rid})
            files = [f for f in files if Path(f).exists()]
            if not files:
                con.execute(f"CREATE OR REPLACE VIEW {table} AS SELECT {EMPTY[rid]} WHERE FALSE")
                continue
            src = f"read_parquet({files!r}, union_by_name=true)"
            if rid == "TB":
                con.execute(f"""CREATE OR REPLACE VIEW {table} AS SELECT s.* FROM {src} s JOIN effective e
                    ON e.report_id='TB' AND e.extraction_id=s.extraction_id AND e.company_id=s.company_id
                    AND e.period_key = s.report_period_start || '~' || s.report_period_end""")
            else:
                con.execute(f"""CREATE OR REPLACE VIEW {table} AS SELECT s.*, substr(s.posting_date,1,7) AS month FROM {src} s
                    JOIN effective e ON e.report_id='{rid}' AND e.extraction_id=s.extraction_id AND e.company_id=s.company_id
                    AND e.period_key = substr(s.posting_date,1,7)""")
        self._pl_mart()

    def _pl_mart(self) -> None:
        excl = self.accounts.get("exclude_contra", ["911"])
        ex = " AND ".join(f"NOT starts_with(account_code,'{p}') AND NOT starts_with(coalesce(contra_account_code,''),'{p}')" for p in excl)
        parts = []
        for line, spec in self.accounts["pl_lines"].items():
            cond = " OR ".join(f"starts_with(account_code,'{p}')" for p in spec["prefixes"])
            if spec.get("contra_prefixes"):
                cond = f"({cond}) AND (" + " OR ".join(f"starts_with(coalesce(contra_account_code,''),'{p}')" for p in spec["contra_prefixes"]) + ")"
            val = "credit - debit" if spec["side"] == "cn" else "debit - credit"
            parts.append(f"SELECT company_id, month, '{line}' AS line, {spec['sign']} * ({val}) AS amount, extraction_id, source_filename, source_row_number, "
                         f"account_code, counterparty_code, counterparty_name, description, posting_date "
                         f"FROM fact_gl_lines WHERE ({cond}) AND {ex}")
        self.con.execute("CREATE OR REPLACE VIEW pl_lines_lineage AS " + " UNION ALL ".join(parts))
        self.con.execute("CREATE OR REPLACE VIEW mart_pl_monthly AS SELECT company_id, month, line, sum(amount) AS amount FROM pl_lines_lineage GROUP BY ALL")

    def pl(self, company: str | None = None, month: str | None = None) -> dict[str, float]:
        q = "SELECT line, sum(amount) FROM mart_pl_monthly WHERE 1=1"
        args = []
        if company:
            q += " AND company_id=?"
            args.append(company)
        if month:
            q += " AND month=?"
            args.append(month)
        base = dict(self.con.execute(q + " GROUP BY line", args).fetchall())
        for k in self.accounts["pl_lines"]:
            base.setdefault(k, 0.0)
        for name, expr in self.accounts.get("derived", {}).items():
            base[name] = eval(expr, {"__builtins__": {}}, dict(base))  # expressions come from reviewed config
        return base

    def export_pl_csv(self, out, year: str | None = None) -> int:
        """Write mart_pl_monthly as CSV (company,month,line,amount; amount in VND, base lines only).
        This is the actuals input format of tools/budget-model."""
        import csv
        q = "SELECT company_id, month, line, sum(amount) FROM mart_pl_monthly"
        args = []
        if year:
            q += " WHERE substr(month,1,4)=?"
            args.append(str(year))
        rows = self.con.execute(q + " GROUP BY ALL ORDER BY 1,2,3", args).fetchall()
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["company", "month", "line", "amount"])
            for c, m, line, amt in rows:
                w.writerow([c, m, line, round(amt)])
        return len(rows)

    def lineage(self, line: str, company: str, month: str) -> list[tuple]:
        """Source rows behind one P&L line: (file, Excel row, amount)."""
        return self.con.execute("SELECT source_filename, source_row_number, amount FROM pl_lines_lineage WHERE line=? AND company_id=? AND month=? ORDER BY abs(amount) DESC",
                                [line, company, month]).fetchall()
