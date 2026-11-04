"""GL_JOURNAL parser — journal-line layout (Tk / Tk đ/ư / Ps nợ / Ps có) or Dr/Cr pair layout.

Pair rows are split into one debit line and one credit line. Multi-line vouchers are never
re-paired by joining debits to credits.
"""
from __future__ import annotations

import re

from .base import Layout, ParseResult, Sheet, is_total_row, text, to_date, to_number

VERSION = "0.1.0"


def parse(sheet: Sheet, layout: Layout, registry: dict) -> ParseResult:
    c = layout.columns
    res = ParseResult("GL_JOURNAL", VERSION, layout)
    pair = "account_code" not in c and {"debit_account", "credit_account", "amount"} <= c.keys()
    res.notes.append("layout: Dr/Cr pair (split into 2 lines)" if pair else "layout: journal line")
    labels = registry.get("total_row_labels", [])
    g = lambda row, k: row[c[k]] if k in c and c[k] < len(row) else None  # noqa: E731
    deb = cred = 0.0
    for i in range(layout.data_start_row - 1, len(sheet.rows)):
        row = sheet.rows[i] or []
        excel_row = i + 1
        if not any(v not in (None, "") for v in row):
            continue
        if is_total_row(row, labels):
            if pair:
                t = to_number(g(row, "amount")) or 0.0
                res.control_totals = {"debit": t, "credit": t}
            else:
                res.control_totals = {"debit": to_number(g(row, "debit")) or 0.0, "credit": to_number(g(row, "credit")) or 0.0}
            continue
        d = to_date(g(row, "posting_date"))
        base = {
            "posting_date": d,
            "document_number": text(g(row, "document_number")),
            "document_type": text(g(row, "document_type")),
            "description": text(g(row, "description")),
            "counterparty_code": text(g(row, "counterparty_code")),
            "counterparty_name": text(g(row, "counterparty_name")),
            "job_code": text(g(row, "job_code")),
            "source_row_number": excel_row,
        }
        if pair:
            dr, cr, amt = text(g(row, "debit_account")).replace(" ", ""), text(g(row, "credit_account")).replace(" ", ""), to_number(g(row, "amount"))
            if d is None and not dr and not cr:
                continue  # descriptive / repeated header row with no posting content
            problem = _problem(d, [dr, cr], amt)
            if problem:
                res.quarantine.append({"source_row_number": excel_row, "reason": problem, "raw": [text(v) for v in row]})
                continue
            res.records.append({**base, "account_code": dr, "contra_account_code": cr, "debit": amt, "credit": 0.0, "line_side": "Dr"})
            res.records.append({**base, "account_code": cr, "contra_account_code": dr, "debit": 0.0, "credit": amt, "line_side": "Cr"})
            deb += amt
            cred += amt
        else:
            acc = text(g(row, "account_code")).replace(" ", "")
            dv, cv = to_number(g(row, "debit")), to_number(g(row, "credit"))
            if d is None and not acc and not dv and not cv:
                continue  # opening-balance banner or blank-ish row
            if d is None and not acc and (dv or cv):
                res.quarantine.append({"source_row_number": excel_row, "reason": "amount without date/account (subtotal or opening balance?)", "raw": [text(v) for v in row]})
                continue
            problem = _problem(d, [acc], dv if dv is not None else None) or (None if cv is not None else "credit not numeric")
            if problem:
                res.quarantine.append({"source_row_number": excel_row, "reason": problem, "raw": [text(v) for v in row]})
                continue
            if not dv and not cv:
                continue
            res.records.append({**base, "account_code": acc, "contra_account_code": text(g(row, "contra_account_code")).replace(" ", ""),
                                "debit": dv, "credit": cv, "line_side": "Dr" if dv else "Cr"})
            deb += dv
            cred += cv
    res.parsed_totals = {"debit": deb, "credit": cred}
    return res


def _problem(d, accounts, amount) -> str | None:
    if d is None:
        return "missing or unreadable posting date"
    if any(not re.match(r"^\d{3}", a or "") for a in accounts):
        return f"account code not recognised: {accounts}"
    if amount is None:
        return "amount not numeric"
    return None
