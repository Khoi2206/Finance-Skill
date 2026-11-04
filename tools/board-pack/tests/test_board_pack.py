import csv
import re

import pytest
from afi import cli as afi_cli
from afi.models.warehouse import Warehouse
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from boardpack.commentary import Rules, variances
from boardpack.deck import build_deck
from boardpack.facts import Facts, load_plan
from boardpack.fmt import bn, pct, signed_bn
from boardpack.sample import build_warehouse

REQUIRED = ["COVER", "EXEC", "KPI", "PL", "VAR-HN", "BRIDGE", "ENT-ALTA", "ENT-APL", "ENT-AME", "CASH", "RISK", "RESOLUTION",
            "APP-ENT", "APP-VAR", "APP-DQ", "APP-METHOD"]


def slide_text(slide) -> str:
    out = []
    for sh in slide.shapes:
        if sh.has_text_frame:
            out.append(sh.text_frame.text)
        if sh.has_table:
            out += [c.text for r in sh.table.rows for c in r.cells]
    return "\n".join(out)


def table_rows(slide, first_header: str):
    for sh in slide.shapes:
        if sh.has_table and sh.table.cell(0, 0).text == first_header:
            return {r.cells[0].text.strip(): [c.text for c in r.cells] for r in sh.table.rows}
    raise AssertionError(f"no table with header {first_header}")


@pytest.fixture(scope="module")
def deck(group, tmp_path_factory):
    f = Facts(group["wh"], group["plan"])
    out = tmp_path_factory.mktemp("deck") / "bp.pptx"
    path, d = build_deck(f, "2026-10", "month", out, sample=True)
    return {"path": path, "deck": d, "prs": Presentation(str(path)), "facts": f}


def by_code(dk, code):
    return [dk["prs"].slides[i] for i, (c, _) in enumerate(dk["deck"].index) if c == code]


# ---------- deck mở được, đủ trang ----------
def test_deck_opens_and_has_all_sections(deck):
    prs = deck["prs"]
    codes = [c for c, _ in deck["deck"].index]
    assert len(prs.slides) == len(codes)
    for c in REQUIRED:
        assert c in codes, c
    for i, (c, title) in enumerate(deck["deck"].index):
        assert title.split(" ")[0] in slide_text(prs.slides[i])


def test_cover_marks_sample_and_every_slide_shows_data_status(deck):
    prs = deck["prs"]
    assert "DỮ LIỆU MẪU" in slide_text(prs.slides[0])
    for s in prs.slides:
        t = slide_text(s)
        assert re.search(r"Số liệu: (APPROVED|RECONCILED|SƠ BỘ)", t) or "Phụ lục A4" in t


def test_status_follows_reconcile_and_approvals(deck):
    t = lambda code: slide_text(by_code(deck, code)[0])  # noqa: E731
    assert "Số liệu: APPROVED" in t("ENT-APL")          # đã duyệt trong approvals.yaml
    assert "Số liệu: RECONCILED" in t("ENT-AME")        # qua kiểm soát, chưa duyệt
    assert "Số liệu: RECONCILED" in t("PL")             # hợp nhất = mức yếu nhất


# ---------- số trên slide khớp afi pl ----------
def test_consolidated_pl_matches_afi_pl(deck, group):
    wh = Warehouse(group["data"])
    p = wh.pl(None, "2026-10")
    rows = table_rows(by_code(deck, "PL")[0], "Chỉ tiêu")
    assert rows["Doanh thu thuần"][1] == bn(p["net_revenue"])
    assert rows["Giá vốn hàng bán"][1] == bn(-p["cogs"])
    assert rows["Lợi nhuận gộp"][1] == bn(p["gross_profit"])
    assert rows["Lợi nhuận trước thuế"][1] == bn(p["profit_before_tax"])
    assert rows["Lợi nhuận sau thuế"][1] == bn(p["net_profit"])
    py = wh.pl(None, "2025-10")
    assert rows["Doanh thu thuần"][5] == bn(py["net_revenue"])


def test_entity_numbers_match_afi_pl_cli(deck, group, capsys):
    rows = table_rows(by_code(deck, "APP-ENT")[0], "Chỉ tiêu")
    header = rows["Chỉ tiêu"]
    for cid, name in (("ALTA", "Alta (Mẹ)"), ("APL", "Alta Plastic"), ("AME", "Alta Media")):
        afi_cli.main(["--data", str(group["data"]), "pl", "--company", cid, "--month", "2026-10"])
        out = dict((ln.split()[0], float(ln.split()[1].replace(",", ""))) for ln in capsys.readouterr().out.strip().splitlines())
        j = header.index(name)
        assert rows["Doanh thu thuần"][j] == bn(out["net_revenue"])
        assert rows["Lợi nhuận sau thuế"][j] == bn(out["net_profit"])
        assert rows["Chi phí quản lý doanh nghiệp"][j] == bn(-out["admin_expenses"])
        ent = table_rows(by_code(deck, f"ENT-{cid}")[0], "Chỉ tiêu")
        assert ent["Doanh thu thuần"][1] == bn(out["net_revenue"])


def test_ebitda_follows_policy_p4(deck, group):
    wh = Warehouse(group["data"])
    p = wh.pl(None, "2026-10")
    interest = wh.con.execute("""SELECT sum(debit-credit) FROM fact_gl_lines WHERE month='2026-10' AND starts_with(account_code,'635')
                                 AND lower(strip_accents(description)) LIKE '%lai vay%'""").fetchone()[0]
    rows = table_rows(by_code(deck, "PL")[0], "Chỉ tiêu")
    assert rows["EBITDA"][1] == bn(p["profit_before_tax"] + interest + p["depreciation"])


def test_plan_column_equals_plan_csv(deck, group):
    with open(group["plan"], encoding="utf-8") as fh:
        rev = sum(float(r["amount"]) for r in csv.DictReader(fh) if r["month"] == "2026-10" and r["line"] == "net_revenue")
    rows = table_rows(by_code(deck, "PL")[0], "Chỉ tiêu")
    assert rows["Doanh thu thuần"][2] == bn(rev)
    assert load_plan(group["plan"])[("APL", "2026-10", "net_revenue")] > 0


def test_ytd_mode_sums_months(group, tmp_path):
    f = Facts(group["wh"], group["plan"])
    _, d = build_deck(f, "2026-10", "ytd", tmp_path / "ytd.pptx")
    wh = Warehouse(group["data"])
    total = sum(wh.pl(None, f"2026-{m:02d}")["net_revenue"] for m in range(1, 11))
    prs = Presentation(str(tmp_path / "ytd.pptx"))
    pl = prs.slides[[c for c, _ in d.index].index("PL")]
    assert table_rows(pl, "Chỉ tiêu")["Doanh thu thuần"][1] == bn(total)
    assert "10T/2026" in slide_text(pl)


# ---------- biểu đồ native, ghi chú nguồn ----------
def test_charts_are_native_and_no_pictures(deck):
    n_charts = 0
    for s in deck["prs"].slides:
        for sh in s.shapes:
            assert sh.shape_type != MSO_SHAPE_TYPE.PICTURE
            n_charts += bool(getattr(sh, "has_chart", False) and sh.has_chart)
    assert n_charts >= 15  # waterfall, cột, đường, sparkline
    bridge = by_code(deck, "BRIDGE")[0]
    ch = next(sh.chart for sh in bridge.shapes if getattr(sh, "has_chart", False) and sh.has_chart)
    assert len(ch.plots[0].categories) == 8  # KH + 6 bước + thực tế


def test_waterfall_steps_add_up(deck):
    d = deck["deck"]
    from boardpack.commentary import bridge
    a, b = d.A[None], d.KH[None]
    assert abs(sum(v for _, v in bridge(a, b)) - (a["ebitda"] - b["ebitda"])) < 1


def test_speaker_notes_cite_excel_file_and_row(deck):
    for code in ("EXEC", "KPI", "PL", "BRIDGE", "ENT-APL", "CASH", "APP-ENT"):
        notes = by_code(deck, code)[0].notes_slide.notes_text_frame.text
        assert re.search(r"(NKC|CDPS) 2026-1?\d - Alta.*\.xlsx · dòng \d+", notes), code
    pl_notes = by_code(deck, "PL")[0].notes_slide.notes_text_frame.text
    assert "afi pl --month 2026-10 --lineage net_revenue" in pl_notes


# ---------- bình luận biến động ----------
def test_commentary_respects_threshold_and_has_structure(deck):
    f, d = deck["facts"], deck["deck"]
    allv = [v for vs in d.VAR.values() for v in vs]
    assert allv
    for v in allv:
        assert abs(v.delta) > 500e6 and abs(v.delta) > 0.10 * abs(v.compare)
        assert v.what and v.why and "[CFO điền" in v.action
    # tăng ngưỡng → ít bình luận hơn; ngưỡng rất cao → không có
    assert len(variances(f, "APL", ["2026-10"], "month", Rules(0.10, 2e9))) < len(d.VAR["APL"])
    assert variances(f, None, ["2026-10"], "month", Rules(0.10, 1e12)) == []


def test_revenue_commentary_uses_customer_lineage(deck):
    v = next(v for v in deck["deck"].VAR["AME"] if v.line == "net_revenue" and v.base == "CK")
    joined = " ".join(v.why)
    assert "Khách hàng mẫu M01" in joined          # sự kiện lớn có thật trong dữ liệu tổng hợp
    assert ".xlsx · dòng" in joined


def test_rules_unit():
    r = Rules()
    assert r.hit(1.7e9, 1.0e9)          # +700tr, +70%
    assert not r.hit(10.4e9, 10.0e9)    # +400tr
    assert not r.hit(110.6e9, 110.0e9)  # +600tr nhưng < 10%


def test_number_format():
    assert bn(25_340_000_000) == "25,3"
    assert bn(-1_260_000_000) == "(1,3)"
    assert bn(1_234_560_000_000) == "1.234,6"
    assert signed_bn(2.1e9) == "+2,1" and signed_bn(-2.1e9) == "(2,1)"
    assert pct(-0.05) == "(5,0%)"


# ---------- dữ liệu chưa đối chiếu → SƠ BỘ; thiếu KH/cùng kỳ vẫn chạy ----------
def test_failed_reconciliation_marks_preliminary_and_no_plan(tmp_path):
    wh = build_warehouse(tmp_path / "w", first="2026-09", last="2026-10", drop_sales_invoice=("AME", "2026-10"))
    f = Facts(wh)
    _, d = build_deck(f, "2026-10", "month", tmp_path / "bp.pptx")
    assert d.ST["AME"].label == "SƠ BỘ" and d.ST[None].label == "SƠ BỘ"
    assert d.ST["APL"].label == "RECONCILED"
    prs = Presentation(str(tmp_path / "bp.pptx"))
    codes = [c for c, _ in d.index]
    assert "Số liệu: SƠ BỘ" in slide_text(prs.slides[codes.index("ENT-AME")])
    assert any("chưa đối chiếu" in r for r, _ in d.risk_flags())
    assert table_rows(prs.slides[codes.index("PL")], "Chỉ tiêu")["Doanh thu thuần"][2] == "–"  # không có KH
