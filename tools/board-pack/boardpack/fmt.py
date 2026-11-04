"""Định dạng số theo chuẩn board pack: tỷ đồng 1 chữ số thập phân, số âm trong ngoặc, dấu phẩy thập phân."""
from __future__ import annotations

BN = 1e9


def _vn(x: float, dec: int) -> str:
    s = f"{abs(x):,.{dec}f}"  # 1,234.5
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def bn(v: float | None, dec: int = 1, dash: str = "–") -> str:
    """VND → 'tỷ' string: 25300000000 → '25,3'; −1.2e9 → '(1,2)'."""
    if v is None:
        return dash
    x = v / BN
    if round(abs(x), dec) == 0:
        return _vn(0, dec)
    return f"({_vn(x, dec)})" if x < 0 else _vn(x, dec)


def signed_bn(v: float | None, dec: int = 1) -> str:
    """Chênh lệch: '+2,1' hoặc '(2,1)'."""
    if v is None:
        return "–"
    s = bn(v, dec)
    return s if s.startswith("(") or s in ("0,0", "0") else "+" + s


def pct(v: float | None, dec: int = 1, signed: bool = True) -> str:
    """Tỷ lệ (0.139 → '+13,9%'; −0.05 → '(5,0%)')."""
    if v is None:
        return "–"
    x = v * 100
    body = _vn(x, dec) + "%"
    if round(x, dec) == 0:
        return _vn(0, dec) + "%"
    if x < 0:
        return f"({body})"
    return ("+" if signed else "") + body


def pts(v: float | None, dec: int = 1) -> str:
    """Điểm phần trăm: 0.021 → '+2,1 điểm'."""
    if v is None:
        return "–"
    x = v * 100
    return (f"({_vn(x, dec)} điểm)" if x < 0 else f"+{_vn(x, dec)} điểm") if round(x, dec) else "0,0 điểm"


def vnd(v: float) -> str:
    """Số đồng đầy đủ cho ghi chú nguồn: 1.234.567.890 hoặc (1.234.567.890)."""
    s = _vn(v, 0)
    return f"({s})" if v < 0 else s


def ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def change(a: float | None, b: float | None) -> float | None:
    """Δ% = (A − B) / |B|."""
    if a is None or b is None or b == 0:
        return None
    return (a - b) / abs(b)


def month_label(m: str) -> str:
    return f"{m[5:7]}/{m[:4]}"


def period_label(month: str, mode: str) -> str:
    return f"tháng {month_label(month)}" if mode == "month" else f"{int(month[5:7])}T/{month[:4]}"


def vs(a: float | None, b: float | None, ref: str) -> str:
    """Cụm so sánh cho action title: 'thấp hơn kế hoạch 2,2%' (không lồng ngoặc)."""
    d = change(a, b)
    if d is None:
        return f"chưa có số {ref}"
    if round(d * 100, 1) == 0:
        return f"bằng {ref}"
    return f"{'cao' if d > 0 else 'thấp'} hơn {ref} {_vn(d * 100, 1)}%"


def vs_amt(d: float, ref: str) -> str:
    """'cao hơn kế hoạch 4,1 tỷ' từ chênh lệch tuyệt đối."""
    return f"{'cao' if d > 0 else 'thấp'} hơn {ref} {bn(abs(d))} tỷ"


def vs_pts(d: float | None, ref: str) -> str:
    if d is None:
        return f"chưa có số {ref}"
    return f"{'tăng' if d > 0 else 'giảm'} {_vn(abs(d) * 100, 1)} điểm so với {ref}"


def cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def lower1(s: str) -> str:
    """Hạ chữ đầu trừ khi là viết tắt (EBITDA, DSO…)."""
    return s if len(s) > 1 and s[1].isupper() else s[:1].lower() + s[1:]
