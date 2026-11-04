"""Physical data dictionary (data contract, spec §3) generated from a genuine sample file."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .ingestion.store import sha256
from .parsers.base import company_from, period_from_title, text


def _redact(v) -> str:
    s = text(v)
    if re.fullmatch(r"\d{10}(-\d{3})?", s):
        return s[:3] + "*******" + s[10:]  # tax codes / party codes
    if re.fullmatch(r"-?[\d.,]+", s):
        return "<number>"
    return s[:40]


def build(pipeline, path: Path) -> dict:
    sh, layout, rid, why, res = pipeline.analyse(path)
    reg = pipeline.registry
    spec = reg["reports"][rid]
    inv = {v: k for k, v in layout.columns.items()}
    rows = sh.rows[layout.data_start_row - 1: layout.data_start_row + 4]
    examples = {h: [_redact(r[j]) for r in rows if j < len(r) and r[j] not in (None, "")][:3] for j, h in enumerate(layout.raw_headers) if h}
    types = {}
    for j, h in enumerate(layout.raw_headers):
        vals = [r[j] for r in sh.rows[layout.data_start_row - 1:] if r and j < len(r) and r[j] not in (None, "")][:200]
        types[h or f"col{j+1}"] = sorted({type(v).__name__ for v in vals}) or ["empty"]
    per = period_from_title(layout.title_lines)
    cid, cwhy = company_from(path.name, layout.title_lines, pipeline.entities)
    questions = []
    if not per:
        questions.append("Period not found in title rows: confirm export filter dates.")
    if not cid:
        questions.append("Company not identified from filename/title: rename file to end with the company name.")
    unmapped = [h for j, h in enumerate(layout.raw_headers) if h and j not in inv]
    if unmapped:
        questions.append(f"Unmapped columns {unmapped}: confirm meaning or add aliases in report_registry.yaml.")
    if res and res.control_totals:
        diff = {k: round(res.parsed_totals.get(k, 0) - v, 2) for k, v in res.control_totals.items()}
        if any(abs(x) > 0.5 for x in diff.values()):
            questions.append(f"Parsed totals differ from 'Tổng cộng': {diff}")
    elif res:
        questions.append("No 'Tổng cộng' row found: confirm the export includes totals.")
    if res and res.quarantine:
        questions.append(f"{len(res.quarantine)} rows quarantined: review reasons below.")
    return {
        "report_id": rid,
        "fast_display_name": spec["fast_display_name"],
        "status": spec["status"],
        "classification": why,
        "sample_file": path.name,
        "source_file_hash": "sha256:" + sha256(path),
        "file_format": path.suffix.lower().lstrip("."),
        "sheet_names": [sh.name],
        "title_rows": layout.title_lines,
        "header_row": layout.header_row,
        "header_rows_merged": layout.merged_header,
        "data_start_row": layout.data_start_row,
        "period_from": per[0].isoformat() if per else None,
        "period_to": per[1].isoformat() if per else None,
        "company_detected": cid,
        "company_reason": cwhy,
        "raw_column_names": layout.raw_headers,
        "column_mapping": {k: layout.raw_headers[v] for k, v in layout.columns.items()},
        "unmapped_columns": unmapped,
        "column_types": types,
        "column_examples_redacted": examples,
        "grain_definition": spec.get("grain"),
        "parser": spec.get("parser"),
        "parser_notes": res.notes if res else [],
        "rows_parsed": len(res.records) if res else None,
        "control_totals": res.control_totals if res else None,
        "parsed_totals": res.parsed_totals if res else None,
        "quarantined_rows": [{"row": q["source_row_number"], "reason": q["reason"]} for q in (res.quarantine if res else [])][:50],
        "open_questions": questions,
        "owner": "Finance",
        "approval_status": "preliminary",
    }


def write(d: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{d['report_id']}__{Path(d['sample_file']).stem}.yaml"
    p.write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p
