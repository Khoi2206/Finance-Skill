"""Bình luận biến động tự sinh theo quy tắc của core/board-management-pack §2.

Chỉ giải trình khi |Δ| > ngưỡng % **và** > ngưỡng tuyệt đối (mặc định 10% và 500 triệu).
Cấu trúc: Cái gì (số, %) → Tại sao (chỉ từ dữ liệu: tách thành phần, khách hàng/tài khoản đóng góp lớn nhất,
dòng Excel gốc) → Một lần hay lặp lại (so tháng trước) → Hành động (ô trống cho CFO). Không tự đoán nguyên nhân.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .facts import LABEL, SHORT, Facts, SourceRow, shift
from .fmt import bn, change, month_label, pct, pts, signed_bn

COMMENT_LINES = ["net_revenue", "cogs", "gross_profit", "selling_expenses", "admin_expenses", "finance_expense", "ebitda", "net_profit"]
COST = {"cogs", "selling_expenses", "admin_expenses", "finance_expense", "other_expense", "income_tax", "interest_expense"}
ACTION = "[CFO điền: hành động · người phụ trách · thời hạn · tác động dự báo cả năm]"
# thành phần của các dòng dẫn xuất: (dòng, dấu đóng góp)
COMPONENTS = {
    "gross_profit": [("net_revenue", 1), ("cogs", -1)],
    "ebitda": [("net_revenue", 1), ("cogs", -1), ("selling_expenses", -1), ("admin_expenses", -1), ("depreciation", 1), ("fin_other_ex_interest", 1)],
    "net_profit": [("net_revenue", 1), ("cogs", -1), ("selling_expenses", -1), ("admin_expenses", -1), ("finance_income", 1),
                   ("finance_expense", -1), ("other_income", 1), ("other_expense", -1), ("income_tax", -1)],
}
LABEL_X = {**LABEL, "fin_other_ex_interest": "Tài chính & khác (trừ lãi vay)", "depreciation": "Khấu hao cộng lại"}


def fin_other(p: dict) -> float:
    return p["finance_income"] - (p["finance_expense"] - p["interest_expense"]) + p["other_income"] - p["other_expense"]


def value(p: dict, line: str) -> float:
    return fin_other(p) if line == "fin_other_ex_interest" else p[line]


@dataclass
class Variance:
    cid: str | None
    line: str
    base: str                 # "KH" | "CK"
    actual: float
    compare: float
    delta: float              # A − B (giá trị gốc)
    pct: float | None
    favourable: bool
    what: str
    why: list[str] = field(default_factory=list)
    recurring: str = ""
    action: str = ACTION
    sources: list[SourceRow] = field(default_factory=list)


@dataclass
class Rules:
    pct: float = 0.10
    amount: float = 500e6

    def hit(self, a: float, b: float) -> bool:
        d = a - b
        return abs(d) > self.amount and (b == 0 or abs(d) > self.pct * abs(b))

    def text(self) -> str:
        return f"|Δ| > {self.pct * 100:.0f}% và > {self.amount / 1e6:,.0f} triệu đồng".replace(",", ".")


def bridge(a: dict, b: dict) -> list[tuple[str, float]]:
    """Cầu nối EBITDA B → A theo dòng KQKD (tổng các bước = ΔEBITDA)."""
    return [(LABEL_X[k], s * (value(a, k) - value(b, k))) for k, s in COMPONENTS["ebitda"]]


def variances(f: Facts, cid: str | None, months: list[str], mode: str, rules: Rules, lines=COMMENT_LINES) -> list[Variance]:
    a = f.pl(cid, months)
    if not a:
        return []
    py_m = [shift(m, -12) for m in months]
    out = []
    for base, b in (("KH", f.plan_pl(cid, months)), ("CK", f.pl(cid, py_m))):
        if not b:
            continue
        for line in lines:
            if b.get(line) is None or not rules.hit(a[line], b[line]):
                continue
            out.append(_explain(f, cid, months, py_m, mode, rules, line, base, a, b))
    out.sort(key=lambda v: -abs(v.delta))
    return out


def _explain(f, cid, months, py_m, mode, rules, line, base, a, b) -> Variance:
    d = a[line] - b[line]
    fav = (d < 0) if line in COST else (d > 0)
    who = SHORT[cid]
    per = f"tháng {month_label(months[0])}" if mode == "month" else f"{len(months)}T/{months[-1][:4]}"
    ref = "kế hoạch" if base == "KH" else "cùng kỳ"
    ch = change(a[line], b[line])
    what = (f"{LABEL[line]} {who} {per}: {bn(a[line])} tỷ, {'cao' if d > 0 else 'thấp'} hơn {ref} {bn(abs(d))} tỷ"
            + (f" ({pct(abs(ch), signed=False)})" if ch is not None else "") + f" — {'thuận lợi' if fav else 'bất lợi'}.")
    why: list[str] = []
    if line in COMPONENTS:
        parts = sorted(((LABEL_X[k], s * (value(a, k) - value(b, k))) for k, s in COMPONENTS[line]), key=lambda x: -abs(x[1]))
        why.append("Tách theo dòng KQKD (tác động lên chỉ tiêu): " + "; ".join(f"{k} {signed_bn(v)} tỷ" for k, v in parts[:3]) + ".")
        if line == "gross_profit" and a["net_revenue"] and b["net_revenue"]:
            gd = a["gross_margin"] - b["gross_margin"]
            why.append(f"Biên gộp {pct(a['gross_margin'], signed=False)} so với {pct(b['gross_margin'], signed=False)}, "
                       f"{'tăng' if gd >= 0 else 'giảm'} {pts(abs(gd)).lstrip('+')}.")
    if line == "cogs" and a["net_revenue"] and b["net_revenue"]:
        ra, rb = a["cogs"] / a["net_revenue"], b["cogs"] / b["net_revenue"]
        why.append(f"Tách: do doanh thu thay đổi {signed_bn((a['net_revenue'] - b['net_revenue']) * rb)} tỷ; do tỷ lệ giá vốn/doanh thu "
                   f"{pct(ra, signed=False)} so với {pct(rb, signed=False)} {signed_bn((ra - rb) * a['net_revenue'])} tỷ "
                   "(chưa có sản lượng để tách giá/lượng).")
    if line not in COMPONENTS:
        has_py = f.pl(cid, py_m) is not None
        if base == "CK" or has_py:
            by = "counterparty_name" if line == "net_revenue" else "account_code"
            con = f.contributors(line, cid, months, py_m, by=by)
            if con:
                lab = "khách hàng" if by == "counterparty_name" else "tài khoản"
                pre = "So với cùng kỳ, " if base == "KH" else ""
                why.append(pre + f"chênh lệch lớn nhất theo {lab}: " +
                           "; ".join(f"{('TK ' if by == 'account_code' else '') + str(k)} {bn(x)} so với {bn(y)}, Δ {signed_bn(dd)}" for k, x, y, dd in con) + ".")
    if line not in COMPONENTS and base == "KH":
        why.append("Kế hoạch lập ở cấp dòng nên không tách được theo khách hàng/tài khoản so với KH.")
    src, n = f.source_rows(line if line not in COMPONENTS else "net_revenue", cid, months, 2)
    if line not in COMPONENTS and src:
        why.append("Dòng gốc lớn nhất: " + "; ".join(f"{s.text()} = {bn(s.amount, 2)} tỷ" for s in src) + f" (trong {n} dòng).")
    rec = "–"
    if mode == "month":
        pm = [shift(months[0], -1)]
        pa = f.pl(cid, pm)
        pb = f.plan_pl(cid, pm) if base == "KH" else f.pl(cid, [shift(pm[0], -12)])
        if pa and pb and pb.get(line) is not None:
            pd_ = pa[line] - pb[line]
            same = (pd_ > 0) == (d > 0)
            if rules.hit(pa[line], pb[line]) and same:
                rec = f"Tháng {month_label(pm[0])} cũng lệch cùng chiều: Δ {signed_bn(pd_)} tỷ, vượt ngưỡng → có dấu hiệu lặp lại; [CFO xác nhận]."
            else:
                rec = f"Tháng {month_label(pm[0])}: Δ {signed_bn(pd_)} tỷ, {'cùng' if same else 'ngược'} chiều, {'vượt' if rules.hit(pa[line], pb[line]) else 'không vượt'} ngưỡng → có thể là một lần; [CFO xác nhận]."
        else:
            rec = "Không có số tháng trước để so sánh; [CFO xác nhận]."
    return Variance(cid, line, base, a[line], b[line], d, change(a[line], b[line]), fav, what, why, rec, ACTION, src)
