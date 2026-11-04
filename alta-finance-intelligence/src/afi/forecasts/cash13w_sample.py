"""Synthetic sample for the 13-week cash tool. NOT ALTA DATA — every name and number is invented.

write_sample(out, start) creates:
  out/inputs_<start>/        CSV inputs + params.yaml (sample: true) for one Monday
  out/gl/NKC ... - <entity>.xlsx   synthetic FAST-style general journal (cash lines for 14 weeks before start)
Deliberate gaps are included so DATA REQUIRED is exercised (unverified bank account, missing owner,
missing expected date, past expected receipt date, unapproved drawdown).
"""
from __future__ import annotations

import csv
import datetime as dt
import random
from pathlib import Path

import openpyxl
import yaml

from .cash13w import INPUT_FILES

M = 1_000_000
ENT = {
    "ALTA": {"title": "CÔNG TY CỔ PHẦN ALTA (MẪU)", "mst": "0301420079", "file": "Alta"},
    "APL": {"title": "CÔNG TY CỔ PHẦN ALTA PLASTIC (MẪU)", "mst": "0312414944", "file": "Alta Plastic"},
    "AME": {"title": "CÔNG TY CỔ PHẦN ALTA MEDIA (MẪU)", "mst": "0305904835", "file": "Alta Media"},
}
# weekly synthetic levels (VND million): collections, supplier payments, monthly payroll, monthly VAT
LEVEL = {"ALTA": (900, 350, 650, 120), "APL": (4200, 3300, 2600, 450), "AME": (2100, 1350, 1250, 260)}
OWNERS = {"ALTA": "KT Mẹ (mẫu)", "APL": "KT công nợ APL (mẫu)", "AME": "KT công nợ AME (mẫu)"}


def _d(x: dt.date) -> str:
    return x.isoformat()


def _write(path: Path, name: str, rows: list[dict]) -> None:
    cols = INPUT_FILES[name]
    with (path / name).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def _nth(start: dt.date, day: int, months_ahead: int) -> dt.date:
    y, m = start.year, start.month + months_ahead
    while m > 12:
        y, m = y + 1, m - 12
    return dt.date(y, m, min(day, 28))


def write_inputs(out: Path, start: dt.date, seed: int = 7, adjust: dict | None = None) -> Path:
    rnd = random.Random(f"{seed}-{start}")
    p = out / f"inputs_{start.isoformat()}"
    p.mkdir(parents=True, exist_ok=True)
    snap = start - dt.timedelta(days=3)
    bank = [
        {"company": "ALTA", "bank": "Ngân hàng mẫu A", "bank_account": "A-0001", "balance": 6_400 * M, "restricted": 0},
        {"company": "ALTA", "bank": "Quỹ tiền mặt", "bank_account": "TM-ALTA", "balance": 85 * M, "restricted": 0},
        {"company": "APL", "bank": "Ngân hàng mẫu B", "bank_account": "B-0101", "balance": 11_900 * M, "restricted": 1_500 * M},
        {"company": "APL", "bank": "Ngân hàng mẫu A", "bank_account": "A-0102", "balance": 2_350 * M, "restricted": 0},
        {"company": "AME", "bank": "Ngân hàng mẫu C", "bank_account": "C-0201", "balance": 5_150 * M, "restricted": 400 * M},
        {"company": "AME", "bank": "Ngân hàng mẫu A", "bank_account": "A-0202", "balance": 610 * M, "restricted": 0, "unverified": True},
    ]
    for b in bank:
        if adjust and b["bank_account"] in adjust:  # keep sample consistent: prior balance + actual week flows
            b["balance"] = adjust[b["bank_account"]]
        else:
            b["balance"] = round(b["balance"] * (1 + rnd.uniform(-0.04, 0.04)), -6)
        b.update(date=_d(snap), verified_by="" if b.pop("unverified", False) else "KT trưởng (mẫu)",
                 source=f"Sao kê {snap:%d/%m/%Y} (mẫu)")
    _write(p, "bank_balances.csv", bank)

    ar, ap = [], []
    for co, (col, sup, _, _) in LEVEL.items():
        n = 14 if co != "ALTA" else 8
        for i in range(n):
            exp = start + dt.timedelta(days=rnd.randint(0, 48))
            due = exp - dt.timedelta(days=rnd.randint(0, 20))
            inv_d = due - dt.timedelta(days=rnd.choice([30, 45, 60]))
            amt = round(col * rnd.uniform(0.3, 0.75) * M, -6)
            ar.append({"company": co, "customer": f"Khách mẫu {co}-{i % 6 + 1:02d}", "invoice": f"{co}-HD{1000 + i}", "invoice_date": _d(inv_d),
                       "due_date": _d(due), "outstanding": amt, "expected_date": _d(exp),
                       "confidence": rnd.choice(["Cao", "Cao", "Trung bình", "Thấp"]), "owner": OWNERS[co]})
        for i in range(10):
            due = start + dt.timedelta(days=rnd.randint(0, 45))
            ap.append({"company": co, "supplier": f"NCC mẫu {co}-{i % 5 + 1:02d}", "invoice": f"{co}-MH{500 + i}",
                       "invoice_date": _d(due - dt.timedelta(days=30)), "due_date": _d(due), "outstanding": round(sup * rnd.uniform(0.3, 0.6) * M, -6),
                       "expected_date": _d(due), "confidence": "Cao", "owner": OWNERS[co]})
    # deliberate gaps (DATA REQUIRED)
    ar[2]["owner"] = ""
    ar[16]["expected_date"] = ""
    ar[17]["expected_date"] = _d(start - dt.timedelta(days=9))
    # intercompany: Plastic pays rent to Mẹ (both sides recorded, same date)
    ic_date = _nth(start, 5, 1)
    ar.append({"company": "ALTA", "customer": "Alta Plastic (nội bộ)", "invoice": "ALTA-IC-THUE", "invoice_date": _d(start), "due_date": _d(ic_date),
               "outstanding": 520 * M, "expected_date": _d(ic_date), "confidence": "Cao", "owner": OWNERS["ALTA"], "counterparty_company": "APL"})
    ap.append({"company": "APL", "supplier": "Alta (Mẹ) — thuê nhà xưởng (nội bộ)", "invoice": "ALTA-IC-THUE", "invoice_date": _d(start), "due_date": _d(ic_date),
               "outstanding": 520 * M, "expected_date": _d(ic_date), "confidence": "Cao", "owner": OWNERS["APL"], "counterparty_company": "ALTA"})
    _write(p, "ar_open.csv", ar)
    _write(p, "ap_open.csv", ap)

    pay, tax, other = [], [], []
    for co, (col, sup, payroll, vat) in LEVEL.items():
        for k in range(4):
            d10, d25, d20 = _nth(start, 10, k), _nth(start, 25, k), _nth(start, 20, k)
            if d10 >= start:
                pay.append({"company": co, "item": "Lương tháng", "reference": f"Bảng lương {d10:%m/%Y}", "due_date": _d(d10), "expected_date": _d(d10),
                            "amount": payroll * M, "confidence": "Cao", "owner": "HCNS (mẫu)"})
            if d25 >= start:
                pay.append({"company": co, "item": "BHXH, BHYT, BHTN", "reference": f"BHXH {d25:%m/%Y}", "due_date": _d(d25), "expected_date": _d(d25),
                            "amount": round(payroll * 0.32) * M, "confidence": "Cao", "owner": "HCNS (mẫu)"})
            if d20 >= start:
                tax.append({"company": co, "item": "Thuế GTGT", "reference": f"Tờ khai {(d20 - dt.timedelta(days=25)):%m/%Y}", "due_date": _d(d20),
                            "expected_date": _d(d20), "amount": vat * M, "confidence": "Trung bình", "owner": "KT thuế (mẫu)"})
                tax.append({"company": co, "item": "Thuế TNCN", "reference": f"TNCN {(d20 - dt.timedelta(days=25)):%m/%Y}", "due_date": _d(d20),
                            "expected_date": _d(d20), "amount": round(payroll * 0.06) * M, "confidence": "Cao", "owner": "KT thuế (mẫu)"})
        q = dt.date(2027, 1, 30)
        if start <= q < start + dt.timedelta(days=91):
            tax.append({"company": co, "item": "Tạm nộp TNDN quý 4", "reference": "TNDN Q4/2026", "due_date": _d(q), "expected_date": _d(q),
                        "amount": round(vat * 1.4) * M, "confidence": "Thấp", "owner": "KT thuế (mẫu)"})
        # contracted / ordered but not yet invoiced (pipeline) — never "history averaged"
        for wk in range(5, 13):
            other.append({"company": co, "item": "Thu theo hợp đồng/đơn hàng đã ký, chưa xuất HĐ", "reference": f"HĐ mẫu {co}-{wk:02d}", "direction": "thu",
                          "due_date": _d(start + dt.timedelta(days=7 * wk + 2)), "expected_date": _d(start + dt.timedelta(days=7 * wk + 4)),
                          "amount": round(col * 1.0 * rnd.uniform(0.9, 1.1)) * M, "confidence": "Trung bình" if wk < 10 else "Thấp", "owner": OWNERS[co]})
            other.append({"company": co, "item": "Chi mua theo PO đã đặt / chi phí hoạt động", "reference": f"PO mẫu {co}-{wk:02d}", "direction": "chi",
                          "due_date": _d(start + dt.timedelta(days=7 * wk + 3)), "expected_date": _d(start + dt.timedelta(days=7 * wk + 3)),
                          "amount": round(sup * 0.75 * rnd.uniform(0.9, 1.1)) * M, "confidence": "Trung bình", "owner": OWNERS[co]})
    other.append({"company": "AME", "item": "Chi phí sự kiện cuối năm (mẫu)", "reference": "SK-12", "direction": "chi", "due_date": _d(start + dt.timedelta(days=40)),
                  "expected_date": _d(start + dt.timedelta(days=40)), "amount": 900 * M, "confidence": "Cao", "owner": ""})
    _write(p, "payroll.csv", pay)
    _write(p, "taxes.csv", tax)
    _write(p, "other.csv", other)
    _write(p, "capex.csv", [
        {"company": "APL", "item": "Máy thổi màng (mẫu) — mốc 2", "reference": "HĐ thiết bị mẫu / mốc nghiệm thu", "due_date": _d(start + dt.timedelta(days=38)),
         "expected_date": _d(start + dt.timedelta(days=38)), "amount": 3_200 * M, "confidence": "Cao", "owner": "BQL dự án (mẫu)"},
        {"company": "APL", "item": "Máy thổi màng (mẫu) — mốc 3", "reference": "HĐ thiết bị mẫu / mốc vận hành", "due_date": _d(start + dt.timedelta(days=73)),
         "expected_date": _d(start + dt.timedelta(days=73)), "amount": 2_100 * M, "confidence": "Trung bình", "owner": "BQL dự án (mẫu)"},
        {"company": "AME", "item": "Màn hình LED (mẫu)", "reference": "HĐ mua LED mẫu", "due_date": _d(start + dt.timedelta(days=24)),
         "expected_date": _d(start + dt.timedelta(days=24)), "amount": 1_400 * M, "confidence": "Cao", "owner": "BU LED (mẫu)"},
    ])
    debt = []
    for k in range(4):
        d = _nth(start, 25, k)
        if start <= d < start + dt.timedelta(days=91):
            debt.append({"company": "APL", "lender": "Ngân hàng mẫu B", "facility": "VLĐ-B", "flow": "INTEREST", "due_date": _d(d), "expected_date": _d(d),
                         "amount": 95 * M, "confidence": "Cao", "owner": "KT ngân hàng (mẫu)"})
            debt.append({"company": "AME", "lender": "Ngân hàng mẫu C", "facility": "VLĐ-C", "flow": "INTEREST", "due_date": _d(d), "expected_date": _d(d),
                         "amount": 28 * M, "confidence": "Cao", "owner": "KT ngân hàng (mẫu)"})
    debt += [
        {"company": "APL", "lender": "Ngân hàng mẫu B", "facility": "TDH-B", "flow": "PRINCIPAL", "due_date": _d(start + dt.timedelta(days=43)),
         "expected_date": _d(start + dt.timedelta(days=43)), "amount": 1_250 * M, "confidence": "Cao", "owner": "KT ngân hàng (mẫu)"},
        {"company": "APL", "lender": "Ngân hàng mẫu B", "facility": "VLĐ-B", "flow": "DRAWDOWN", "due_date": _d(start + dt.timedelta(days=36)),
         "expected_date": _d(start + dt.timedelta(days=36)), "amount": 2_500 * M, "confidence": "Trung bình", "owner": "CFO (mẫu)", "approved": "Y"},
        {"company": "AME", "lender": "Ngân hàng mẫu C", "facility": "Mới-C", "flow": "DRAWDOWN", "due_date": _d(start + dt.timedelta(days=50)),
         "expected_date": _d(start + dt.timedelta(days=50)), "amount": 1_500 * M, "confidence": "Thấp", "owner": "CFO (mẫu)", "approved": ""},
    ]
    _write(p, "debt_schedule.csv", debt)
    _write(p, "facilities.csv", [
        {"company": "APL", "lender": "Ngân hàng mẫu B", "facility": "VLĐ-B", "limit": 15_000 * M, "drawn": 9_200 * M, "expiry_date": "2027-06-30", "committed": "Y"},
        {"company": "AME", "lender": "Ngân hàng mẫu C", "facility": "VLĐ-C", "limit": 5_000 * M, "drawn": 2_300 * M, "expiry_date": "2026-12-31", "committed": "Y"},
    ])
    params = {
        "sample": True,
        "min_liquidity_floor": {"approved_by": "", "by_company": {"ALTA": 1_500 * M, "APL": 4_000 * M, "AME": 2_000 * M}},
        "approval": {"opening_cash_by": "", "floor_by": "", "assumptions_by": ""},
        "collection_lag_days": {"default": 12, "by_customer": {}},
        "scenarios": {"downside": {"receipt_factor": {"CAO": 1.0, "TRUNG_BINH": 0.85, "THAP": 0.0}, "key_customers_top_n": 2,
                                   "key_customer_delay_days": 30, "all_receipts_delay_days": 7}},
    }
    (p / "params.yaml").write_text("# DỮ LIỆU MẪU — tham số [PROPOSED POLICY], chưa được CFO duyệt\n" + yaml.safe_dump(params, allow_unicode=True, sort_keys=False),
                                   encoding="utf-8")
    return p


def write_gl(out: Path, start: dt.date, weeks: int = 14, seed: int = 11) -> list[Path]:
    """Synthetic journal (journal-line layout) with cash lines for `weeks` weeks before `start`."""
    rnd = random.Random(seed)
    g0 = start - dt.timedelta(days=7 * weeks)
    end = start - dt.timedelta(days=1)
    (out / "gl").mkdir(parents=True, exist_ok=True)
    paths = []
    for co, e in ENT.items():
        col, sup, payroll, vat = LEVEL[co]
        L = []
        n = [0]

        def post(d, dr, cr, amt, desc, cp="", cpn=""):
            n[0] += 1
            so = f"CT{n[0]:05d}"
            a = round(amt * M, -5)
            L.append([d, so, desc, dr, cr, a, None, cp, cpn])
            L.append([d, so, desc, cr, dr, None, a, cp, cpn])

        for w in range(weeks):
            ws = g0 + dt.timedelta(days=7 * w)
            for k in range(3):
                post(ws + dt.timedelta(days=rnd.randint(0, 4)), "1121", "131", col / 3 * rnd.uniform(0.7, 1.3), "Thu tiền khách hàng (mẫu)", f"KM{co}{k}", f"Khách mẫu {co}-{k + 1:02d}")
            for k in range(2):
                post(ws + dt.timedelta(days=rnd.randint(0, 4)), "331", "1121", sup / 2 * rnd.uniform(0.7, 1.3), "Trả nhà cung cấp (mẫu)", f"NM{co}{k}", f"NCC mẫu {co}-{k + 1:02d}")
            post(ws + dt.timedelta(days=2), "6427", "1111", 25 * rnd.uniform(0.5, 1.5), "Chi phí văn phòng (mẫu)")
            for day in range(7):
                d = ws + dt.timedelta(days=day)
                if d.day == 10:
                    post(d, "334", "1121", payroll * rnd.uniform(0.97, 1.03), "Trả lương (mẫu)")
                if d.day == 25:
                    post(d, "3383", "1121", payroll * 0.32, "Nộp BHXH (mẫu)")
                    if co == "APL":
                        post(d, "635", "1121", 95, "Trả lãi vay (mẫu)")
                    if co == "AME":
                        post(d, "635", "1121", 28, "Trả lãi vay (mẫu)")
                if d.day == 20:
                    post(d, "33311", "1121", vat * rnd.uniform(0.85, 1.15), "Nộp thuế GTGT (mẫu)")
                if d.day == 5:
                    post(d, "1111", "1121", 120, "Rút tiền gửi về quỹ (mẫu)")  # internal transfer
                    if co == "APL":
                        post(d, "331", "1121", 520, "Trả tiền thuê nhà xưởng cho Alta (nội bộ, mẫu)", ENT["ALTA"]["mst"], "Alta (Mẹ)")
                    if co == "ALTA":
                        post(d, "1121", "131", 520, "Thu tiền thuê nhà xưởng từ Alta Plastic (nội bộ, mẫu)", ENT["APL"]["mst"], "Alta Plastic")
                if d.day == 15 and co == "APL" and d.month % 3 == 0:
                    post(d, "3411", "1121", 1250, "Trả gốc vay trung hạn (mẫu)")
        L.sort(key=lambda r: (r[0], r[1]))
        wb = openpyxl.Workbook()
        sh = wb.active
        for line in [e["title"], f"MST: {e['mst']}", "SỔ NHẬT KÝ CHUNG", f"Từ ngày {g0:%d/%m/%Y} đến ngày {end:%d/%m/%Y}", None]:
            sh.append([line])
        sh.append(["Ngày ct", "Số ct", "Diễn giải", "Tk", "Tk đ/ư", "Ps nợ", "Ps có", "Mã khách", "Tên khách"])
        for r in L:
            sh.append([dt.datetime.combine(r[0], dt.time())] + r[1:])
        tot = sum(r[5] or 0 for r in L)
        sh.append([None, None, "Tổng cộng", None, None, tot, tot])
        path = out / "gl" / f"NKC MAU {g0:%Y%m%d}-{end:%Y%m%d} - {e['file']}.xlsx"
        wb.save(path)
        paths.append(path)
    return paths


def write_sample(out: Path, start: dt.date) -> dict:
    """Prior-week inputs, GL, then this week's inputs whose main bank balance = prior balance + GL net of the week."""
    import csv as _csv

    out = Path(out)
    prev = start - dt.timedelta(days=7)
    pin = write_inputs(out, prev)
    gl = write_gl(out, start)
    net = _week_net(gl, prev, start)
    main = {"ALTA": "A-0001", "APL": "B-0101", "AME": "C-0201"}
    with (pin / "bank_balances.csv").open(encoding="utf-8") as f:
        prior = {r["bank_account"]: float(r["balance"]) for r in _csv.DictReader(f)}
    adjust = {acc: round(prior[acc] + net.get(co, 0.0), -5) for co, acc in main.items()}
    adjust["TM-ALTA"] = prior["TM-ALTA"]
    return {"inputs_prior": pin, "inputs": write_inputs(out, start, adjust=adjust), "gl": gl}


def _week_net(gl_files: list[Path], a: dt.date, b: dt.date) -> dict[str, float]:
    """Net cash movement (111/112) per entity between a (incl.) and b (excl.) in the synthetic GL."""
    out: dict[str, float] = {}
    for p in gl_files:
        co = next(k for k, e in ENT.items() if p.stem.endswith(e["file"]))
        ws = openpyxl.load_workbook(p, read_only=True).active
        for r in ws.iter_rows(min_row=7, values_only=True):
            if isinstance(r[0], dt.datetime) and a <= r[0].date() < b and str(r[3]).startswith(("111", "112")):
                out[co] = out.get(co, 0.0) + (r[5] or 0) - (r[6] or 0)
    return out
