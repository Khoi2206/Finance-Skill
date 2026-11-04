from afi import dictionary
from afi.pipeline import Pipeline


def test_dictionary_records_layout_and_questions(files, data, tmp_path):
    d = dictionary.build(Pipeline(data), files["gl"])
    assert d["report_id"] == "GL_JOURNAL" and d["header_row"] == 6 and d["data_start_row"] == 7
    assert d["raw_column_names"][:5] == ["Ngày ct", "Số ct", "Diễn giải", "Tk", "Tk đ/ư"]
    assert d["column_mapping"]["contra_account_code"] == "Tk đ/ư"
    assert d["source_file_hash"].startswith("sha256:")
    assert d["status"] == "ALTA_VALIDATION_REQUIRED" and d["approval_status"] == "preliminary"
    assert any("quarantined" in q for q in d["open_questions"])
    assert all("*" in v for v in d["column_examples_redacted"]["Mã khách"])  # party codes masked
    assert dictionary.write(d, tmp_path / "out").exists()
    assert not (data / "manifest.jsonl").exists()  # dictionary does not ingest
