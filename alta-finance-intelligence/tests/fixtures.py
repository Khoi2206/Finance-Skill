"""Synthetic FAST-style exports (no real ALTA data). Layout mirrors the observed sales list:
title rows 1-5, header row 6 (TB: merged header rows 6-7), 'Tổng cộng' footer."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl

D = lambda d: dt.datetime(2026, 10, d)  # noqa: E731
TITLE = ["CÔNG TY CỔ PHẦN ALTA PLASTIC", "MST: 0312414944"]
PERIOD = "Từ ngày 01/10/2026 đến ngày 31/10/2026"


def _book(path: Path, title: str, header: list, rows: list, total: list | None = None, sub: list | None = None, period: str = PERIOD):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for line in TITLE + [title, period]:
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
