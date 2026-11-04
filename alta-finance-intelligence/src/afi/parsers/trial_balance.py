"""TB parser — Bảng cân đối số phát sinh. Supports merged two-row headers (Nợ/Có under each group)."""
from __future__ import annotations

import re

from .base import Layout, ParseResult, Sheet, is_total_row, text, to_number

VERSION = "0.1.0"
AMOUNTS = ["opening_debit", "opening_credit", "period_debit", "period_credit", "closing_debit", "closing_credit"]


def parse(sheet: Sheet, layout: Layout, registry: dict) -> ParseResult:
    c = layout.columns
    res = ParseResult("TB", VERSION, layout)
    missing = [k for k in AMOUNTS + ["account_code"] if k not in c]
    if missing:
        res.notes.append(f"missing columns: {missing}")
    labels = registry.get("total_row_labels", [])
    g = lambda row, k: row[c[k]] if k in c and c[k] < len(row) else None  # noqa: E731
    for i in range(layout.data_start_row - 1, len(sheet.rows)):
        row = sheet.rows[i] or []
        if not any(v not in (None, "") for v in row):
            continue
        if is_total_row(row, labels):
            res.control_totals = {k: to_number(g(row, k)) or 0.0 for k in AMOUNTS}
            continue
        acc = text(g(row, "account_code")).replace(" ", "")
        if not re.match(r"^\d{3}[0-9A-Za-z]*$", acc):
            if any(isinstance(v, (int, float)) and v for v in row):
                res.quarantine.append({"source_row_number": i + 1, "reason": "numeric row without account code", "raw": [text(v) for v in row]})
            continue
        vals = {k: to_number(g(row, k)) for k in AMOUNTS}
        bad = [k for k, v in vals.items() if v is None]
        if bad:
            res.quarantine.append({"source_row_number": i + 1, "reason": f"non-numeric {bad}", "raw": [text(v) for v in row]})
            continue
        res.records.append({"account_code": acc, "account_name": text(g(row, "account_name")), **vals, "source_row_number": i + 1})
    codes = [r["account_code"] for r in res.records]
    for r in res.records:
        r["is_leaf"] = not any(o != r["account_code"] and o.startswith(r["account_code"]) for o in codes)
    leaves = [r for r in res.records if r["is_leaf"]]
    res.parsed_totals = {k: sum(r[k] for r in leaves) for k in AMOUNTS}
    return res
