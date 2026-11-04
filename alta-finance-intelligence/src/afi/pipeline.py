"""Orchestration: raw → classify → parse → staging (Parquet) + quarantine, with manifest status."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .ingestion.store import RawStore
from .parsers import PARSERS
from .parsers.base import UnsupportedFile, classify, company_from, detect_layout, load_config, period_from_title, read_workbook


class Pipeline:
    def __init__(self, data_dir: Path, config_dir: Path | None = None):
        self.data = Path(data_dir)
        self.store = RawStore(self.data)
        self.staging = self.data / "staging"
        self.registry = load_config("report_registry.yaml", config_dir)
        self.entities = load_config("entity_map.yaml", config_dir)

    def analyse(self, path: Path):
        """Read + classify + parse a file without storing anything (used by dictionary too)."""
        sheets = read_workbook(path)
        tried = []
        for sh in sheets:
            layout = detect_layout(sh.rows, self.registry["aliases"])
            if not layout:
                tried.append(f"{sh.name}: no header row")
                continue
            rid, why = classify(layout, self.registry)
            if not rid:
                tried.append(f"{sh.name}: {why}")
                continue
            spec = self.registry["reports"][rid]
            if not spec.get("parser"):
                return sh, layout, rid, why, None
            result = PARSERS[spec["parser"]](sh, layout, self.registry)
            return sh, layout, rid, why, result
        raise UnsupportedFile("; ".join(tried) or "empty workbook")

    def ingest(self, path: Path, uploader: str | None = None, company: str | None = None) -> dict:
        path = Path(path)
        entry, is_new = self.store.put(path, uploader)
        if not is_new:
            return {**entry, "duplicate": True}
        upd = {"extraction_id": entry["extraction_id"]}
        try:
            sh, layout, rid, why, res = self.analyse(path)
        except UnsupportedFile as e:
            upd.update(status="QUARANTINED", error=str(e))
            self.store.append(upd)
            return {**entry, **upd}
        cid, cwhy = (company, "given by user") if company else company_from(path.name, layout.title_lines, self.entities)
        per = period_from_title(layout.title_lines)
        recs = res.records if res else []
        if not per and recs and "posting_date" in recs[0]:
            ds = [r["posting_date"] for r in recs if r.get("posting_date")]
            per = (min(ds), max(ds)) if ds else None
        upd.update(report_id=rid, classification=why, source_sheet=sh.name, header_row=layout.header_row,
                   company_id=cid, company_reason=cwhy,
                   report_period_start=per[0].isoformat() if per else None, report_period_end=per[1].isoformat() if per else None,
                   parser_version=res.parser_version if res else None,
                   rows_parsed=len(recs), rows_quarantined=len(res.quarantine) if res else 0,
                   control_totals=res.control_totals if res else {}, parsed_totals=res.parsed_totals if res else {})
        problems = []
        if not cid:
            problems.append("company unknown")
        if not per:
            problems.append("period unknown")
        if res is None:
            problems.append(f"no parser yet for {rid}")
        if problems:
            upd.update(status="QUARANTINED", error="; ".join(problems))
        else:
            self._write_staging(rid, entry, upd, res)
            upd["status"] = "PARSED"
        self.store.append(upd)
        return {**entry, **upd}

    def _write_staging(self, rid: str, entry: dict, upd: dict, res) -> None:
        prov = {"extraction_id": entry["extraction_id"], "source_filename": entry["source_filename"], "source_sheet": upd["source_sheet"],
                "report_id": rid, "company_id": upd["company_id"], "report_period_start": upd["report_period_start"],
                "report_period_end": upd["report_period_end"], "parser_version": upd["parser_version"],
                "ingested_at": entry["ingested_at"], "dq_status": "PARSED"}
        out = self.staging / rid
        out.mkdir(parents=True, exist_ok=True)
        rows = [{**r, **prov, **({"posting_date": r["posting_date"].isoformat()} if isinstance(r.get("posting_date"), dt.date) else {})} for r in res.records]
        if rows:
            pq.write_table(pa.Table.from_pylist(rows), out / f"{entry['extraction_id']}.parquet")
        if res.quarantine:
            q = self.data / "quarantine"
            q.mkdir(exist_ok=True)
            (q / f"{entry['extraction_id']}.json").write_text(json.dumps({"source_filename": entry["source_filename"], "rows": res.quarantine}, ensure_ascii=False, indent=1), encoding="utf-8")
