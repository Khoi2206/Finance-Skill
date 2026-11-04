import json

import fixtures as fx

from afi.models.warehouse import Warehouse
from afi.pipeline import Pipeline


def test_reingest_same_file_is_idempotent(files, data):
    pl = Pipeline(data)
    first = pl.ingest(files["gl"])
    second = pl.ingest(files["gl"])
    assert first["status"] == "PARSED" and second.get("duplicate")
    assert len(pl.store.entries()) == 1
    assert len(list((data / "staging" / "GL_JOURNAL").glob("*.parquet"))) == 1
    assert len(list((data / "raw").iterdir())) == 1


def test_provenance_and_company_period_detection(files, data):
    r = Pipeline(data).ingest(files["gl"])
    assert r["company_id"] == "APL" and r["report_period_start"] == "2026-10-01" and r["report_period_end"] == "2026-10-31"
    wh = Warehouse(data)
    cols = {c[0] for c in wh.con.execute("SELECT * FROM fact_gl_lines LIMIT 0").description}
    assert {"extraction_id", "source_filename", "source_sheet", "source_row_number", "report_id", "company_id",
            "report_period_start", "report_period_end", "parser_version", "ingested_at", "dq_status"} <= cols


def test_corrected_export_supersedes_but_keeps_history(files, data):
    pl = Pipeline(data)
    pl.ingest(files["gl"])
    corrected = fx.gl_line_file(files["dir"] / "NKC 2026-10 - Alta Plastic (v2).xlsx", scale=1.1)
    pl.ingest(corrected)
    assert len(pl.store.entries()) == 2  # both extractions preserved
    wh = Warehouse(data)
    files_used = {f for (f,) in wh.con.execute("SELECT DISTINCT source_filename FROM fact_gl_lines").fetchall()}
    assert files_used == {corrected.name}
    assert round(wh.pl("APL", "2026-10")["net_revenue"]) == round(1_200_000_000 * 1.1)


def test_company_from_title_when_filename_has_none(tmp_path, data):
    r = Pipeline(data).ingest(fx.sales_file(tmp_path / "bang ke.xlsx"))
    assert r["company_id"] == "APL" and r["status"] == "PARSED"  # title holds the company name and MST


def test_unknown_company_is_quarantined_not_dropped(tmp_path, data, monkeypatch):
    monkeypatch.setattr(fx, "TITLE", ["CÔNG TY KHÔNG RÕ", ""])
    r = Pipeline(data).ingest(fx.sales_file(tmp_path / "bang ke.xlsx"))
    assert r["status"] == "QUARANTINED" and "company unknown" in r["error"]
    manifest = [json.loads(x) for x in (data / "manifest.jsonl").read_text().splitlines()]
    assert manifest[-1]["status"] == "QUARANTINED"
    assert any((data / "raw").iterdir())  # raw bytes kept
