from afi.pipeline import Pipeline


def test_gl_journal_line_layout_with_multiline_voucher(files, data):
    sh, layout, rid, why, res = Pipeline(data).analyse(files["gl"])
    assert rid == "GL_JOURNAL" and "title" in why
    assert layout.header_row == 6 and not layout.merged_header
    hd001 = [r for r in res.records if r["document_number"] == "HD001"]
    assert len(hd001) == 3  # kept as journal lines, never re-paired
    assert sum(r["debit"] for r in hd001) == sum(r["credit"] for r in hd001)
    assert res.parsed_totals == res.control_totals
    assert len(res.quarantine) == 1 and res.quarantine[0]["source_row_number"] == 7  # 'Số dư đầu kỳ' banner
    assert all(r["source_row_number"] >= 8 for r in res.records)


def test_gl_pair_layout_split_into_lines(files, data):
    _, _, rid, _, res = Pipeline(data).analyse(files["pair"])
    assert rid == "GL_JOURNAL"
    assert len(res.records) == 6
    assert sum(r["debit"] for r in res.records) == sum(r["credit"] for r in res.records) == 880_000_000
    assert res.control_totals == {"debit": 880_000_000, "credit": 880_000_000}


def test_trial_balance_merged_header_and_leaf_only(files, data):
    _, layout, rid, _, res = Pipeline(data).analyse(files["tb"])
    assert rid == "TB" and layout.merged_header and layout.header_row == 7
    assert "opening_debit" in layout.columns and "closing_credit" in layout.columns
    parent = next(r for r in res.records if r["account_code"] == "112")
    assert parent["is_leaf"] is False
    assert res.parsed_totals == res.control_totals  # parent row not double counted


def test_sales_list_observed_layout(files, data):
    _, layout, rid, _, res = Pipeline(data).analyse(files["sales"])
    assert rid == "SALES_LIST" and layout.header_row == 6
    assert len(res.records) == 2
    assert res.records[0]["counterparty_code"] == "0311000101"  # code kept as text
    assert res.parsed_totals["amount"] == res.control_totals["amount"] == 1_200_000_000
