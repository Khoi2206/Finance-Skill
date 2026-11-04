"""SALES_LIST parser — Bảng kê hóa đơn bán hàng, dịch vụ ([ALTA OBSERVED] layout)."""
from __future__ import annotations

from .base import Layout, ParseResult, Sheet, is_total_row, text, to_date, to_number

VERSION = "0.1.0"
NUM = ["amount", "vat", "discount", "receivable"]


def parse(sheet: Sheet, layout: Layout, registry: dict) -> ParseResult:
    c = layout.columns
    res = ParseResult("SALES_LIST", VERSION, layout)
    labels = registry.get("total_row_labels", [])
    g = lambda row, k: row[c[k]] if k in c and c[k] < len(row) else None  # noqa: E731
    for i in range(layout.data_start_row - 1, len(sheet.rows)):
        row = sheet.rows[i] or []
        if not any(v not in (None, "") for v in row):
            continue
        if is_total_row(row, labels):
            res.control_totals = {k: to_number(g(row, k)) or 0.0 for k in NUM if k in c}
            continue
        d = to_date(g(row, "posting_date"))
        vals = {k: to_number(g(row, k)) for k in NUM}
        if d is None:
            if any(v for v in vals.values()):
                res.quarantine.append({"source_row_number": i + 1, "reason": "amount without readable date", "raw": [text(v) for v in row]})
            continue
        bad = [k for k, v in vals.items() if v is None]
        if bad:
            res.quarantine.append({"source_row_number": i + 1, "reason": f"non-numeric {bad}", "raw": [text(v) for v in row]})
            continue
        res.records.append({
            "posting_date": d, "document_type": text(g(row, "document_type")), "document_number": text(g(row, "document_number")),
            "invoice_number": text(g(row, "invoice_number")), "counterparty_code": text(g(row, "counterparty_code")),
            "counterparty_name": text(g(row, "counterparty_name")), "description": text(g(row, "description")),
            "account_code": text(g(row, "account_code")), "salesperson": text(g(row, "salesperson")), "job_code": text(g(row, "job_code")),
            **{k: (v or 0.0) for k, v in vals.items()}, "source_row_number": i + 1,
        })
    res.parsed_totals = {k: sum(r[k] for r in res.records) for k in NUM if k in c}
    return res
