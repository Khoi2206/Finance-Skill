"""Synthetic FAST-style exports (no real ALTA data). Layout mirrors the observed sales list:
title rows 1-5, header row 6 (TB: merged header rows 6-7), 'Tổng cộng' footer."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl

D = lambda d: dt.datetime(2026, 10, d)  # noqa: E731
TITLE = ["CÔNG TY CỔ PHẦN ALTA PLASTIC", "MST: 0312414944"]
PERIOD = "Từ ngày 01/10/2026 đến ngày 31/10/2026"


def _book(path: Path, title: str, header: list, rows: list, total: list | None = None, sub: list | None = None, period: str = PERIOD,
          company: list | None = None):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for line in (company or TITLE) + [title, period]:
        ws.append([line])
    ws.append([])  # row 5 blank → header at row 6
    ws.append(header)
    if sub:
        ws.append(sub)
    for r in rows:
        ws.append(r)
    if total:
        ws.append(total)
    wb.save(path)
    return path


def journal_lines(scale: float = 1.0):
    """Journal-line layout; voucher HD001 is 1 debit / 2 credits (multi-line)."""
    L = []

    def pair(d, so, dg, dr, cr, amt, kh="", khn="", vv=""):
        amt = round(amt * scale)
        L.append([D(d), so, dg, dr, cr, amt, None, kh, khn, vv])
        L.append([D(d), so, dg, cr, dr, None, amt, kh, khn, vv])

    s = scale
    # multi-line voucher: Dr 131 1,100 / Cr 5111 1,000 / Cr 3331 100 (contra shown as 131 on credit lines)
    L.append([D(3), "HD001", "Bán túi bao bì", "131", "5111", round(1_100_000_000 * s), None, "0311000101", "Cty Vạn Xuân", ""])
    L.append([D(3), "HD001", "Bán túi bao bì", "5111", "131", None, round(1_000_000_000 * s), "0311000101", "Cty Vạn Xuân", ""])
    L.append([D(3), "HD001", "Thuế GTGT", "3331", "131", None, round(100_000_000 * s), "0311000101", "Cty Vạn Xuân", ""])
    pair(5, "HD002", "Bán túi cho Alta", "131", "5111", 200_000_000, "0301420079", "Cty CP Alta")
    pair(10, "PX01", "Giá vốn", "632", "155", 900_000_000)
    pair(12, "BC01", "Thu tiền Vạn Xuân", "1121", "131", 500_000_000, "0311000101", "Cty Vạn Xuân")
    pair(20, "BN01", "Trả lãi vay ngân hàng", "635", "1121", 30_000_000)
    pair(28, "KH01", "Khấu hao", "6424", "2141", 50_000_000)
    pair(28, "PK01", "Lương quản lý", "6421", "334", 120_000_000)
    pair(31, "KC01", "Kết chuyển doanh thu", "5111", "911", 1_200_000_000)
    return L


def gl_line_file(path: Path, scale: float = 1.0, opening_row: bool = True) -> Path:
    rows = journal_lines(scale)
    if opening_row:  # FAST-style banner with amount but no date → must be quarantined, not dropped
        rows.insert(0, [None, None, "Số dư đầu kỳ", None, None, 123, None, None, None, None])
    tot = sum(r[5] or 0 for r in rows if r[0])
    return _book(path, "SỔ NHẬT KÝ CHUNG", ["Ngày ct", "Số ct", "Diễn giải", "Tk", "Tk đ/ư", "Ps nợ", "Ps có", "Mã khách", "Tên khách", "Vụ việc"],
                 rows, [None, None, "Tổng cộng", None, None, tot, tot])


def gl_pair_file(path: Path) -> Path:
    rows = [[D(4), "HD010", "Cho thuê LED", "131", "5113", 400_000_000, "0312000101", "2026LED001"],
            [D(4), "HD010", "Thuế GTGT", "131", "3331", 40_000_000, "0312000101", "2026LED001"],
            [D(15), "BC010", "Thu tiền", "1121", "131", 440_000_000, "0312000101", ""]]
    return _book(path, "BẢNG KÊ CHỨNG TỪ", ["Ngày ct", "Số ct", "Diễn giải", "Tk nợ", "Tk có", "Số tiền", "Mã khách", "Vụ việc"],
                 rows, [None, None, "Tổng cộng", None, None, 880_000_000])


def tb_file(path: Path, tamper: bool = False) -> Path:
    """Merged two-row header. Movements equal the journal fixture (incl. closing entry)."""
    o = {"1121": (5_000_000_000, 0), "131": (2_000_000_000, 0), "155": (3_000_000_000, 0), "2141": (0, 600_000_000),
         "3331": (0, 0), "334": (0, 0), "3411": (0, 8_000_000_000), "4111": (0, 1_400_000_000), "5111": (0, 0),
         "632": (0, 0), "635": (0, 0), "6421": (0, 0), "6424": (0, 0), "911": (0, 0)}
    mv = {}
    for r in journal_lines():
        d, c = mv.get(r[3], (0, 0))
        mv[r[3]] = (d + (r[5] or 0), c + (r[6] or 0))
    rows = []
    for acc in sorted(set(o) | set(mv)):
        od, oc = o.get(acc, (0, 0))
        pd, pc = mv.get(acc, (0, 0))
        net = od - oc + pd - pc
        cd, cc = (net, 0) if net >= 0 else (0, -net)
        if tamper and acc == "131":
            cd += 1_000_000
        rows.append([acc, f"TK {acc}", od, oc, pd, pc, cd, cc])
    rows.insert(0, ["112", "Tiền gửi ngân hàng", *rows[0][2:]])  # parent of 1121 (must not double count)
    leaf = [r for r in rows if r[0] != "112"]
    tot = [None, "Tổng cộng", *[sum(r[i] for r in leaf) for i in range(2, 8)]]
    return _book(path, "BẢNG CÂN ĐỐI SỐ PHÁT SINH CÁC TÀI KHOẢN",
                 ["Tài khoản", "Tên tài khoản", "Số dư đầu kỳ", None, "Phát sinh trong kỳ", None, "Số dư cuối kỳ", None],
                 rows, tot, sub=[None, None, "Nợ", "Có", "Nợ", "Có", "Nợ", "Có"])


def sales_file(path: Path) -> Path:
    rows = [[D(3), "HD1", "HD001", "0311000101", "Cty Vạn Xuân", 1_000_000_000, 100_000_000, 0, 1_100_000_000, "Bán túi bao bì", "131", "NV01", ""],
            [D(5), "HD1", "HD002", "0301420079", "Cty CP Alta", 200_000_000, 20_000_000, 0, 220_000_000, "Bán túi cho Alta", "131", "NV01", ""]]
    return _book(path, "BẢNG KÊ HÓA ĐƠN BÁN HÀNG, DỊCH VỤ",
                 ["Ngày ct", "Mã ct", "Số ct", "Mã khách", "Tên khách", "Tiền", "Thuế", "Chiết khấu", "Phải thu", "Diễn giải", "Tài khoản", "Nv bán hàng", "Vụ việc"],
                 rows, [None, None, None, None, "Tổng cộng", 1_200_000_000, 120_000_000, 0, 1_320_000_000])


# ---------------------------------------------------------------------------
# Multi-entity, multi-month synthetic group (used by tools/board-pack).
# Every name, code and amount below is invented. Customer codes are "KHM-…" and
# supplier codes "NCC-…"; only the three group tax codes are real identifiers.
# ---------------------------------------------------------------------------
import calendar  # noqa: E402
import random  # noqa: E402

GROUP = {
    "ALTA": {"title": ["CÔNG TY CỔ PHẦN ALTA", "MST: 0301420079"], "file": "Alta", "tax": "0301420079"},
    "APL": {"title": ["CÔNG TY CỔ PHẦN ALTA PLASTIC", "MST: 0312414944"], "file": "Alta Plastic", "tax": "0312414944"},
    "AME": {"title": ["CÔNG TY CỔ PHẦN ALTA MEDIA", "MST: 0305904835"], "file": "Alta Media", "tax": "0305904835"},
}
SEASON = [0.86, 0.80, 0.97, 0.98, 1.00, 1.01, 1.00, 1.02, 1.04, 1.07, 1.10, 1.18]
# revenue/month (VND, 2025 base), growth 2026, COGS ratio by period, fixed costs, opening balances
PROFILE = {
    "APL": {"rev": 24e9, "growth": 1.08, "acc": "5111", "ratio": {"2025": 0.80, "2026H1": 0.81, "2026H2": 0.855}, "sell": 0.035,
            "admin": 1.25e9, "dep_prod": 0.90e9, "dep_admin": 0.08e9, "fg": True,
            "customers": [("KHM-P01", "Khách hàng mẫu P01 (FMCG)", 0.30), ("KHM-P02", "Khách hàng mẫu P02 (Thực phẩm)", 0.22),
                          ("KHM-P03", "Khách hàng mẫu P03 (Bán lẻ)", 0.16), ("KHM-P04", "Khách hàng mẫu P04 (Xuất khẩu)", 0.14),
                          ("KHM-P05", "Khách hàng mẫu P05 (Hóa mỹ phẩm)", 0.10), ("0301420079", "Công ty CP Alta (nội bộ)", 0.08)],
            "open": {"1121": 18e9, "131": 34e9, "152": 14e9, "155": 9e9, "2111": 160e9, "2141": -62e9, "331": -16e9, "3411": -60e9, "4111": -80e9}},
    "AME": {"rev": 7.5e9, "growth": 1.22, "acc": "5113", "ratio": {"2025": 0.64, "2026H1": 0.645, "2026H2": 0.65}, "sell": 0.06,
            "admin": 0.72e9, "dep_prod": 0.42e9, "dep_admin": 0.04e9, "fg": False,
            "customers": [("KHM-M01", "Khách hàng mẫu M01 (Sự kiện)", 0.34), ("KHM-M02", "Khách hàng mẫu M02 (Ngân hàng)", 0.22),
                          ("KHM-M03", "Khách hàng mẫu M03 (Quảng cáo)", 0.20), ("KHM-M04", "Khách hàng mẫu M04 (Bán lẻ)", 0.14),
                          ("KHM-M05", "Khách hàng mẫu M05 (Giáo dục)", 0.10)],
            "open": {"1121": 6e9, "131": 14e9, "154": 2e9, "2111": 38e9, "2141": -14e9, "331": -5e9, "3411": -15e9, "4111": -20e9}},
    "ALTA": {"rev": 6.2e9, "growth": 1.04, "acc": "5113", "ratio": {"2025": 0.46, "2026H1": 0.46, "2026H2": 0.47}, "sell": 0.02,
             "admin": 0.95e9, "dep_prod": 0.55e9, "dep_admin": 0.06e9, "fg": False,
             "customers": [("KHM-A01", "Khách thuê mẫu A01", 0.30), ("KHM-A02", "Khách thuê mẫu A02", 0.22), ("KHM-A03", "Khách dự án mẫu A03", 0.20),
                           ("0312414944", "Công ty CP Alta Plastic (nội bộ)", 0.15), ("0305904835", "Công ty CP Alta Media (nội bộ)", 0.13)],
             "open": {"1121": 12e9, "131": 9e9, "154": 1e9, "2111": 120e9, "2141": -40e9, "331": -4e9, "3411": -20e9, "4111": -60e9}},
}
# scripted events so the sample has variances worth explaining (all invented)
EVENTS = {
    ("APL", "2026-10", "KHM-P02"): 0.55,   # P02 order volume down in Oct 2026
    ("AME", "2026-10", "KHM-M01"): 1.85,   # one large event job in Oct 2026
    ("AME", "2026-09", "KHM-M03"): 0.70,
    ("ALTA", "2026-10", "KHM-A03"): 0.40,  # project revenue slips
}


def month_range(a: str, b: str) -> list[str]:
    y, m = int(a[:4]), int(a[5:7])
    out = []
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def group_dataset(root: Path, first: str = "2025-01", last: str = "2026-10", seed: int = 2026,
                  drop_sales_invoice: tuple[str, str] | None = None) -> list[Path]:
    """Write monthly GL (Sổ nhật ký chung), TB (CĐPS) and sales list files for ALTA, APL, AME.

    Double entry is exact, TB movement equals GL movement, the sales list equals GL 511, and every
    P&L account is closed to 911 → 4212 at month end (so the 911 exclusion is exercised).
    drop_sales_invoice=(company, month) removes one invoice from that sales list → REVENUE_BRIDGE fails.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    for cid, prof in PROFILE.items():
        rnd = random.Random(f"{seed}-{cid}")
        bal = {k: round(v) for k, v in prof["open"].items()}
        bal["4211"] = -sum(bal.values())
        prev = {"ar_bill": bal.get("131", 0) * 0.55, "ap": 0.0, "vat": 0.0, "cit": 0.0}
        g = GROUP[cid]
        for month in month_range(first, last):
            y, m = int(month[:4]), int(month[5:7])
            last_day = calendar.monthrange(y, m)[1]
            day = lambda d: dt.datetime(y, m, min(d, last_day))  # noqa: E731
            lines: list[list] = []
            sales: list[list] = []
            n = [0]

            def post(d, dr, cr, amt, desc, kh="", khn="", vv="", prefix="PK"):
                amt = round(amt)
                if amt <= 0:
                    return
                n[0] += 1
                so = f"{prefix}{m:02d}{n[0]:03d}"
                lines.append([day(d), so, desc, dr, cr, amt, None, kh, khn, vv])
                lines.append([day(d), so, desc, cr, dr, None, amt, kh, khn, vv])

            yr = "2025" if y == 2025 else ("2026H1" if m <= 6 else "2026H2")
            growth = 1.0 if y == 2025 else prof["growth"]
            base = prof["rev"] * SEASON[m - 1] * growth
            rev = 0.0
            billed = 0.0
            for i, (kh, khn, w) in enumerate(prof["customers"]):
                amt = round(base * w * rnd.uniform(0.92, 1.08) * EVENTS.get((cid, month, kh), 1.0), -6)
                vat = round(amt * 0.1)
                d = 3 + i * 4
                n[0] += 1
                so = f"HD{m:02d}{n[0]:03d}"
                vv = f"{y}LED{i + 1:03d}" if cid == "AME" else ""
                desc = ("Doanh thu cho thuê/dịch vụ" if prof["acc"] == "5113" else "Doanh thu bán bao bì") + f" {khn}"
                lines.append([day(d), so, desc, "131", prof["acc"], amt + vat, None, kh, khn, vv])
                lines.append([day(d), so, desc, prof["acc"], "131", None, amt, kh, khn, vv])
                lines.append([day(d), so, "Thuế GTGT đầu ra", "33311", "131", None, vat, kh, khn, vv])
                if drop_sales_invoice != (cid, month) or i != 0:
                    sales.append([day(d), "HD1", so, kh, khn, amt, vat, 0, amt + vat, desc, "131", "NV01", vv])
                rev += amt
                billed += amt + vat
            ratio = prof["ratio"][yr] * rnd.uniform(0.985, 1.015)
            cogs = round(rev * ratio)
            dep_p = round(prof["dep_prod"] * (1.0 if y == 2025 else 1.03))
            labor = round(cogs * 0.15)
            mat = cogs - dep_p - labor
            purchase = round(mat * rnd.uniform(0.97, 1.03))
            post(2, "152" if prof["fg"] else "154", "331", purchase, "Mua nguyên vật liệu / dịch vụ đầu vào", "NCC-M01", "Nhà cung cấp mẫu M01", prefix="PN")
            if prof["fg"]:
                post(6, "154", "152", mat, "Xuất NVL sản xuất", prefix="PX")
            post(27, "154", "334", labor, "Lương trực tiếp")
            post(28, "154", "2141", dep_p, "Khấu hao TSCĐ sản xuất/cho thuê", prefix="KH")
            if prof["fg"]:
                post(29, "155", "154", cogs, "Nhập kho thành phẩm", prefix="NK")
                post(30, "632", "155", cogs, "Giá vốn hàng bán", prefix="PX")
            else:
                post(30, "632", "154", cogs, "Giá vốn dịch vụ", prefix="PX")
            sell = rev * prof["sell"] * rnd.uniform(0.9, 1.1)
            post(27, "6411", "334", sell * 0.5, "Lương bán hàng")
            post(20, "6417", "331", sell * 0.5, "Dịch vụ vận chuyển, marketing", "NCC-D01", "Nhà cung cấp mẫu D01")
            adm = prof["admin"] * (1.0 if y == 2025 else 1.06) * rnd.uniform(0.95, 1.05)
            post(27, "6421", "334", adm * 0.6, "Lương quản lý")
            post(22, "6427", "331", adm * 0.4, "Chi phí dịch vụ mua ngoài QLDN", "NCC-D02", "Nhà cung cấp mẫu D02")
            post(28, "6424", "2141", prof["dep_admin"], "Khấu hao TSCĐ văn phòng", prefix="KH")
            post(25, "1121", "515", max(bal.get("1121", 0), 0) * 0.0015, "Lãi tiền gửi ngân hàng", prefix="BC")
            post(25, "635", "1121", -bal.get("3411", 0) * 0.0068, "Trả lãi vay ngân hàng", prefix="BN")
            if m in (3, 9):
                post(18, "811", "1111" if False else "1121", 0.08e9 * rnd.uniform(0.5, 1.5), "Chi phí khác (phạt chậm giao hàng)", prefix="BN")
            if m == 12:
                post(18, "1121", "711", 0.12e9, "Thu thanh lý phế liệu", prefix="BC")
            # cash movements based on opening positions
            post(15, "1121", "131", prev["ar_bill"] * rnd.uniform(0.9, 1.02) + max(bal.get("131", 0) - prev["ar_bill"], 0) * 0.35,
                 "Thu tiền khách hàng", prefix="BC")
            post(16, "331", "1121", max(-bal.get("331", 0), 0) * 0.75, "Trả tiền nhà cung cấp", prefix="BN")
            post(5, "33311", "1121", prev["vat"], "Nộp thuế GTGT tháng trước", prefix="BN")
            post(5, "3334", "1121", prev["cit"], "Tạm nộp thuế TNDN", prefix="BN")
            payroll = labor + sell * 0.5 + adm * 0.6
            post(29, "334", "1121", payroll, "Trả lương", prefix="BN")
            if cid == "APL" and month == "2026-06":
                post(10, "1121", "3411", 15e9, "Giải ngân vay đầu tư dây chuyền", prefix="BC")
            if cid == "APL" and month == "2026-07":
                post(12, "2111", "1121", 12e9, "Thanh toán dây chuyền thổi màng mới", prefix="BN")
            post(26, "3411", "1121", {"APL": 1.0e9, "AME": 0.3e9, "ALTA": 0.5e9}[cid], "Trả nợ gốc vay", prefix="BN")
            # balances before CIT and closing
            tmp = dict(bal)
            for r in lines:
                tmp[r[3]] = tmp.get(r[3], 0) + (r[5] or 0) - (r[6] or 0)
            pbt = -sum(v for a, v in tmp.items() if a[0] in "5678" and a not in bal) - sum(v - bal.get(a, 0) for a, v in tmp.items() if a[0] in "5678" and a in bal)
            cit = round(max(pbt, 0) * 0.2)
            post(31, "8211", "3334", cit, "Chi phí thuế TNDN tạm tính", prefix="PK")
            # closing entries to 911 → 4212
            mv: dict[str, float] = {}
            for r in lines:
                if r[3][0] in "5678":
                    mv[r[3]] = mv.get(r[3], 0) + (r[5] or 0) - (r[6] or 0)
            res = 0.0
            for a, v in sorted(mv.items()):
                if a.startswith("33") or abs(v) < 0.5:
                    continue
                if v < 0:
                    post(31, a, "911", -v, f"Kết chuyển {a}", prefix="KC")
                else:
                    post(31, "911", a, v, f"Kết chuyển {a}", prefix="KC")
                res -= v
            if res > 0:
                post(31, "911", "4212", res, "Kết chuyển lãi", prefix="KC")
            elif res < 0:
                post(31, "4212", "911", -res, "Kết chuyển lỗ", prefix="KC")
            lines.sort(key=lambda r: (r[0], r[1]))
            # files
            per = f"Từ ngày 01/{m:02d}/{y} đến ngày {last_day}/{m:02d}/{y}"
            stem = f"{month} - {g['file']}"
            tot = sum(r[5] or 0 for r in lines)
            out.append(_book(root / f"NKC {stem}.xlsx", "SỔ NHẬT KÝ CHUNG",
                             ["Ngày ct", "Số ct", "Diễn giải", "Tk", "Tk đ/ư", "Ps nợ", "Ps có", "Mã khách", "Tên khách", "Vụ việc"],
                             lines, [None, None, "Tổng cộng", None, None, tot, tot], period=per, company=g["title"]))
            out.append(_book(root / f"Bang ke ban hang {stem}.xlsx", "BẢNG KÊ HÓA ĐƠN BÁN HÀNG, DỊCH VỤ",
                             ["Ngày ct", "Mã ct", "Số ct", "Mã khách", "Tên khách", "Tiền", "Thuế", "Chiết khấu", "Phải thu", "Diễn giải", "Tài khoản", "Nv bán hàng", "Vụ việc"],
                             sales, [None, None, None, None, "Tổng cộng", *[sum(r[i] for r in sales) for i in (5, 6, 7, 8)]], period=per, company=g["title"]))
            mvd: dict[str, list] = {}
            for r in lines:
                x = mvd.setdefault(r[3], [0, 0])
                x[0] += r[5] or 0
                x[1] += r[6] or 0
            rows = []
            new = dict(bal)
            for a in sorted(set(bal) | set(mvd)):
                o = bal.get(a, 0)
                pd_, pc_ = mvd.get(a, [0, 0])
                c = o + pd_ - pc_
                new[a] = c
                rows.append([a, f"TK {a}", max(o, 0), max(-o, 0), pd_, pc_, max(c, 0), max(-c, 0)])
            leaf_tot = [None, "Tổng cộng", *[sum(r[i] for r in rows) for i in range(2, 8)]]
            out.append(_book(root / f"CDPS {stem}.xlsx", "BẢNG CÂN ĐỐI SỐ PHÁT SINH CÁC TÀI KHOẢN",
                             ["Tài khoản", "Tên tài khoản", "Số dư đầu kỳ", None, "Phát sinh trong kỳ", None, "Số dư cuối kỳ", None],
                             rows, leaf_tot, sub=[None, None, "Nợ", "Có", "Nợ", "Có", "Nợ", "Có"], period=per, company=g["title"]))
            prev = {"ar_bill": billed, "vat": max(-(new.get("33311", 0)), 0), "cit": max(-(new.get("3334", 0)), 0)}
            bal = {a: v for a, v in new.items() if abs(v) > 0.5 or a in prof["open"]}
    return out
