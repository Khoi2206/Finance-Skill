"""Shared parsing utilities: workbook reading, normalisation, header detection, classification.

Nothing here modifies source files. Every value keeps its Excel row number for lineage.
"""
from __future__ import annotations

import csv
import datetime as dt
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[3] / "config"


def load_config(name: str, config_dir: Path | None = None) -> dict:
    return yaml.safe_load(((config_dir or CONFIG_DIR) / name).read_text(encoding="utf-8"))


def norm(value: Any) -> str:
    """Lowercase, strip Vietnamese diacritics, đ→d, punctuation→single space."""
    s = unicodedata.normalize("NFD", "" if value is None else str(value))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").replace("đ", "d").replace("Đ", "D").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def to_number(value: Any) -> float | None:
    """Parse VN/EN number formats. Returns None when the cell is not numeric (caller decides)."""
    if value is None or value == "":
        return 0.0
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "").replace(" ", "")
    if not s:
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1]
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+(,\d+)?", s):
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    elif re.fullmatch(r"-?\d+,\d+", s):
        s = s.replace(",", ".")
    try:
        x = float(s)
    except ValueError:
        return None
    return -x if neg else x


def to_date(value: Any) -> dt.date | None:
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, (int, float)) and 20000 < value < 80000:  # Excel serial
        return dt.date(1899, 12, 30) + dt.timedelta(days=int(value))
    s = str(value).strip()
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", s)
    if m:
        return dt.date(int(m[3]), int(m[2]), int(m[1]))
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        return dt.date(int(m[1]), int(m[2]), int(m[3]))
    return None


def text(value: Any) -> str:
    """Codes stay text (leading zeros, suffixes like 13111T)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


@dataclass
class Sheet:
    name: str
    rows: list[list[Any]]  # rows[i] is Excel row i+1


def read_workbook(path: Path) -> list[Sheet]:
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xlsm"):
        import openpyxl

        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        return [Sheet(ws.title, [list(r) for r in ws.iter_rows(values_only=True)]) for ws in wb.worksheets]
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            return [Sheet("csv", [list(r) for r in csv.reader(f)])]
    if ext == ".xls":
        try:
            import xlrd  # type: ignore
        except ImportError as e:  # pragma: no cover - depends on environment
            raise UnsupportedFile("Định dạng .xls cần thư viện xlrd; hãy cài xlrd hoặc xuất lại dạng .xlsx") from e
        book = xlrd.open_workbook(str(path))
        out = []
        for sh in book.sheets():
            rows = []
            for r in range(sh.nrows):
                row = []
                for c in range(sh.ncols):
                    cell = sh.cell(r, c)
                    if cell.ctype == xlrd.XL_CELL_DATE:
                        row.append(xlrd.xldate.xldate_as_datetime(cell.value, book.datemode))
                    else:
                        row.append(cell.value if cell.value != "" else None)
                rows.append(row)
            out.append(Sheet(sh.name, rows))
        return out
    raise UnsupportedFile(f"Không hỗ trợ định dạng {ext}")


class UnsupportedFile(Exception):
    pass


@dataclass
class Layout:
    header_row: int  # 1-based Excel row of the (last) header row
    data_start_row: int  # 1-based
    raw_headers: list[str]
    merged_header: bool
    title_lines: list[str]
    columns: dict[str, int]  # canonical → 0-based column index


def _alias_index(aliases: dict[str, list[str]]) -> dict[str, str]:
    idx = {}
    for canon, al in aliases.items():
        for a in al:
            idx.setdefault(norm(a), canon)
    return idx


def map_columns(headers: list[str], aliases: dict[str, list[str]]) -> dict[str, int]:
    """Exact alias match first, then containment for long aliases. Each raw column used once."""
    H = [norm(h) for h in headers]
    cols: dict[str, int] = {}
    used: set[int] = set()
    for canon, al in aliases.items():
        for a in al:
            a = norm(a)
            for j, h in enumerate(H):
                if j not in used and h == a:
                    cols[canon] = j
                    used.add(j)
                    break
            if canon in cols:
                break
    for canon, al in aliases.items():
        if canon in cols:
            continue
        for a in al:
            a = norm(a)
            if len(a) < 5:
                continue
            j = next((j for j, h in enumerate(H) if j not in used and a in h), None)
            if j is not None:
                cols[canon] = j
                used.add(j)
                break
    return cols


def detect_layout(rows: list[list[Any]], aliases: dict[str, list[str]], scan: int = 40) -> Layout | None:
    known = set(_alias_index(aliases))
    best, best_score = -1, 0.0
    for i, r in enumerate(rows[:scan]):
        score = 0.0
        for c in r or []:
            n = norm(c)
            if n in ("no", "co"):
                score += 0.3
            elif n in known or re.search(r"dau ky|cuoi ky|ten tai khoan|phat sinh", n):
                score += 1
        if score > best_score:
            best, best_score = i, score
    if best < 0 or best_score < 3:
        return None
    headers = [text(x) for x in rows[best]]
    nxt = [norm(x) for x in (rows[best + 1] if best + 1 < len(rows) else [])]
    merged = sum(1 for x in nxt if x in ("no", "co")) >= 2
    data_start = best + 2
    if merged:
        parent, combined = "", []
        sub = rows[best + 1]
        for j in range(max(len(headers), len(sub))):
            h = headers[j] if j < len(headers) else ""
            if h:
                parent = h
            s = text(sub[j]) if j < len(sub) else ""
            combined.append(f"{h or parent} {s}".strip() if s else h)
        headers = combined
        data_start = best + 3
    title = [" ".join(text(c) for c in r if c not in (None, "")) for r in rows[:best]]
    return Layout(
        header_row=best + (2 if merged else 1),
        data_start_row=data_start,
        raw_headers=headers,
        merged_header=merged,
        title_lines=[t for t in title if t],
        columns=map_columns(headers, aliases),
    )


def classify(layout: Layout, registry: dict) -> tuple[str | None, str]:
    """Return (report_id, reason). Title wins; header fingerprint confirms or decides."""
    title = norm(" ".join(layout.title_lines))
    for rid, spec in registry["reports"].items():
        if any(p in title for p in spec.get("title_patterns", [])):
            if any(all(c in layout.columns for c in fp) for fp in spec.get("fingerprints", [])):
                return rid, f"title '{next(p for p in spec['title_patterns'] if p in title)}' + header fingerprint"
    for rid, spec in registry["reports"].items():
        if any(all(c in layout.columns for c in fp) for fp in spec.get("fingerprints", [])):
            return rid, "header fingerprint only (title not recognised)"
    return None, "no title pattern or header fingerprint matched"


def period_from_title(lines: list[str]) -> tuple[dt.date, dt.date] | None:
    t = " ".join(lines)
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})\D+(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        return dt.date(int(m[3]), int(m[2]), int(m[1])), dt.date(int(m[6]), int(m[5]), int(m[4]))
    n = norm(t)
    m = re.search(r"thang (\d{1,2}) nam (\d{4})", n)
    if m:
        y, mo = int(m[2]), int(m[1])
        return dt.date(y, mo, 1), _month_end(y, mo)
    m = re.search(r"quy (\d) nam (\d{4})", n)
    if m:
        y, q = int(m[2]), int(m[1])
        return dt.date(y, 3 * q - 2, 1), _month_end(y, 3 * q)
    return None


def _month_end(y: int, m: int) -> dt.date:
    return (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))


def company_from(filename: str, title_lines: list[str], entity_map: dict) -> tuple[str | None, str]:
    stem = norm(Path(filename).stem)
    # most specific pattern first (longest)
    pats = sorted(((p, cid) for cid, e in entity_map["entities"].items() for p in e.get("filename_patterns", [])),
                  key=lambda x: -len(x[0]))
    for p, cid in pats:
        if re.search(norm(p.rstrip("$")) + ("$" if p.endswith("$") else ""), stem):
            return cid, f"filename matches '{p}'"
    title = norm(" ".join(title_lines))
    for cid, e in entity_map["entities"].items():
        if e["tax_code"] in " ".join(title_lines):
            return cid, "tax code in title"
    for p, cid in pats:
        if norm(p.rstrip("$")) in title:
            return cid, f"title contains '{p.rstrip('$')}'"
    return None, "company not found in filename or title"


def is_total_row(row: list[Any], labels: list[str]) -> bool:
    return any(norm(c) in labels for c in row if isinstance(c, str))


@dataclass
class ParseResult:
    report_id: str
    parser_version: str
    layout: Layout
    records: list[dict] = field(default_factory=list)
    quarantine: list[dict] = field(default_factory=list)
    control_totals: dict[str, float] = field(default_factory=dict)
    parsed_totals: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
