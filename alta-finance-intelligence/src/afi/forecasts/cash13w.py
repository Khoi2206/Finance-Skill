"""Dòng tiền 13 tuần (direct method) — spec §8.3, Phase 3.

Model, separate from the ledger:
  Beginning available cash (verified bank snapshot: balance − restricted)
  + receipts (open AR × expected date, other receipts, approved drawdowns)
  − payments (open AP, payroll & social insurance, taxes, CAPEX milestones, interest, principal, other)
  ± intercompany (entity view only; eliminated in the group view)
  = ending available cash;  − CFO floor = headroom;  + undrawn committed facilities = liquidity.

Rules enforced here:
  * every forecast item keeps source (file:row), due date, expected date, amount, owner, confidence;
    anything missing becomes a DATA REQUIRED issue (blocking items are excluded from totals);
  * historical averages only *seed* a missing expected date (collection lag) — the item is marked
    SEED_LAG, confidence is capped and it is never treated as committed;
  * 13 weeks of actuals (GL lines on 111/112/113, classified by config/cash_flow_map.yaml,
    internal transfers excluded) are kept separate from the 13 forecast weeks;
  * Base and Downside are computed from the same items; Downside only delays/reduces receipts and
    brings payments forward, so Downside ≤ Base by construction (parameters are clamped);
  * each run is saved as an immutable forecast version; the next run compares actuals with the
    prior version and rolls the forecast forward.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from ..parsers.base import load_config, norm, text, to_date, to_number

SCHEMA = "afi.cash13w/1"
WEEKS = 13
CONF = ("CAO", "TRUNG_BINH", "THAP")
CONF_LABEL = {"CAO": "Cao", "TRUNG_BINH": "Trung bình", "THAP": "Thấp"}
GROUP = "GROUP"

# (id, nhãn, nhóm) — nhóm: in = thu, out = chi, ic = nội bộ, un = chưa phân loại
LINES = [
    ("AR_COLLECTIONS", "Thu từ khách hàng", "in"),
    ("OTHER_RECEIPTS", "Thu khác", "in"),
    ("DRAWDOWN", "Giải ngân vay (đã duyệt)", "in"),
    ("SUPPLIER_PAYMENTS", "Trả nhà cung cấp", "out"),
    ("PAYROLL", "Lương & BHXH", "out"),
    ("TAXES", "Thuế", "out"),
    ("CAPEX", "Capex theo mốc hợp đồng", "out"),
    ("INTEREST", "Trả lãi vay", "out"),
    ("PRINCIPAL", "Trả gốc vay", "out"),
    ("OTHER_PAYMENTS", "Chi hoạt động & chi khác", "out"),
    ("INTERCOMPANY", "Nội bộ tập đoàn (±)", "ic"),
    ("UNCLASSIFIED", "Chưa phân loại (thực tế)", "un"),
]
LINE_IDS = [x[0] for x in LINES]
LINE_KIND = {x[0]: x[2] for x in LINES}

# GL cash-flow category → 13W line. A tuple means (line if inflow, line if outflow).
ACTUAL_LINE: dict[str, Any] = {
    "CUSTOMER_COLLECTIONS": "AR_COLLECTIONS",
    "DIRECT_SALES": "AR_COLLECTIONS",
    "SUPPLIER_EXPENSE": "SUPPLIER_PAYMENTS",
    "INTEREST_PAID": "INTEREST",
    "PAYROLL": "PAYROLL",
    "SOCIAL_OTHER_PAYABLES": "PAYROLL",
    "TAXES": "TAXES",
    "CAPEX": "CAPEX",
    "BORROWINGS": ("DRAWDOWN", "PRINCIPAL"),
    "INTERCOMPANY": "INTERCOMPANY",
    "UNCLASSIFIED": "UNCLASSIFIED",
}
OTHER_ACTUAL = ("OTHER_RECEIPTS", "OTHER_PAYMENTS")

DEFAULT_PARAMS: dict[str, Any] = {
    "sample": False,
    "max_snapshot_age_days": 3,
    "min_liquidity_floor": {"approved_by": "", "by_company": {}},
    "approval": {"opening_cash_by": "", "floor_by": "", "assumptions_by": ""},
    "variance_threshold_pct": 10,
    "variance_materiality": 50_000_000,
    "collection_lag_days": {"default": 0, "by_customer": {}},
    "scenarios": {
        "base": {"receipt_factor": {"CAO": 1.0, "TRUNG_BINH": 1.0, "THAP": 0.5},
                 "drawdown_factor": {"CAO": 1.0, "TRUNG_BINH": 1.0, "THAP": 0.0}},
        "downside": {"receipt_factor": {"CAO": 1.0, "TRUNG_BINH": 0.8, "THAP": 0.0},
                     "drawdown_factor": {"CAO": 1.0, "TRUNG_BINH": 0.0, "THAP": 0.0},
                     "key_customers_top_n": 3, "key_customers": [], "key_customer_delay_days": 30,
                     "all_receipts_delay_days": 7, "payment_advance_days": 0},
    },
}

# ---- input templates (documented in README) --------------------------------------------------
INPUT_FILES: dict[str, list[str]] = {
    "bank_balances.csv": ["company", "bank", "bank_account", "date", "balance", "restricted", "verified_by", "source"],
    "ar_open.csv": ["company", "customer", "invoice", "invoice_date", "due_date", "outstanding", "expected_date", "confidence", "owner", "counterparty_company"],
    "ap_open.csv": ["company", "supplier", "invoice", "invoice_date", "due_date", "outstanding", "expected_date", "confidence", "owner", "counterparty_company"],
    "debt_schedule.csv": ["company", "lender", "facility", "flow", "due_date", "expected_date", "amount", "confidence", "owner", "approved"],
    "facilities.csv": ["company", "lender", "facility", "limit", "drawn", "expiry_date", "committed"],
    "payroll.csv": ["company", "item", "reference", "due_date", "expected_date", "amount", "confidence", "owner"],
    "taxes.csv": ["company", "item", "reference", "due_date", "expected_date", "amount", "confidence", "owner"],
    "capex.csv": ["company", "item", "reference", "due_date", "expected_date", "amount", "confidence", "owner"],
    "other.csv": ["company", "item", "reference", "direction", "due_date", "expected_date", "amount", "confidence", "owner", "counterparty_company"],
}
REQUIRED_PER_COMPANY = {"ar_open.csv": "công nợ phải thu mở", "ap_open.csv": "công nợ phải trả mở",
                        "payroll.csv": "lịch lương & BHXH", "taxes.csv": "lịch nộp thuế"}
YES = {"y", "yes", "co", "x", "1", "true", "da duyet", "approved"}


def _num(v: Any) -> float | None:
    """Blank → None (missing). Non-numeric → None."""
    if v is None or str(v).strip() == "":
        return None
    return to_number(v)


def _conf(v: Any) -> str | None:
    s = norm(v)
    if s in ("cao", "high", "h"):
        return "CAO"
    if s in ("trung binh", "tb", "medium", "med", "m"):
        return "TRUNG_BINH"
    if s in ("thap", "low", "l"):
        return "THAP"
    return None


def _yes(v: Any) -> bool:
    return norm(v) in YES


def _deep(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _deep(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def monday_of(d: dt.date) -> dt.date:
    return d - dt.timedelta(days=d.weekday())


@dataclass
class Issue:
    severity: str          # LOAI_TRU (excluded from totals) | THIEU_TT (included, info missing) | THONG_TIN
    company: str
    source: str            # file:row or module
    field: str
    message: str
    amount: float | None = None
    reference: str = ""

    def as_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Item:
    id: str
    company: str
    line: str
    counterparty: str
    reference: str
    source: str
    due_date: dt.date | None
    expected_date: dt.date | None
    expected_basis: str    # INPUT | DUE_DATE | SEED_LAG
    amount: float          # signed: + receipt, − payment
    confidence: str
    owner: str
    ic_company: str = ""
    facility: str = ""
    committed: bool = True
    included: bool = True
    placement: dict = field(default_factory=dict)  # scenario → {"date","week","amount"}

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "placement"}
        for k in ("due_date", "expected_date"):
            d[k] = d[k].isoformat() if d[k] else None
        d["placement"] = {s: {"date": p["date"].isoformat() if p["date"] else None, "week": p["week"], "amount": p["amount"]}
                          for s, p in self.placement.items()}
        return d


# ---- loading --------------------------------------------------------------------------------
def read_csv(path: Path) -> list[tuple[int, dict]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [(i + 2, {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}) for i, r in enumerate(rows)
            if any((v or "").strip() for v in r.values())]


def load_params(inputs: Path, params_path: Path | None = None) -> dict:
    p = params_path or inputs / "params.yaml"
    over = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    return _deep(DEFAULT_PARAMS, over or {})


def _sanitize_scenarios(params: dict, issues: list[Issue]) -> None:
    """Clamp Downside so it can never exceed Base (factors ≤ Base, delays ≥ 0)."""
    b, d = params["scenarios"]["base"], params["scenarios"]["downside"]
    for key in ("receipt_factor", "drawdown_factor"):
        for c in CONF:
            bv = min(1.0, max(0.0, float(b[key].get(c, 0))))
            dv = min(1.0, max(0.0, float(d[key].get(c, 0))))
            if dv > bv:
                issues.append(Issue("THONG_TIN", GROUP, "params.yaml", f"downside.{key}.{c}",
                                    f"Hệ số Downside ({dv}) lớn hơn Base ({bv}) — đã hạ về bằng Base"))
                dv = bv
            b[key][c], d[key][c] = bv, dv
    for key in ("key_customer_delay_days", "all_receipts_delay_days", "payment_advance_days"):
        if float(d.get(key, 0) or 0) < 0:
            issues.append(Issue("THONG_TIN", GROUP, "params.yaml", f"downside.{key}", "Số ngày âm — đã đặt về 0"))
            d[key] = 0


class Builder:
    def __init__(self, inputs: Path, start: dt.date, params: dict, entities: dict):
        self.inputs, self.start, self.params = Path(inputs), start, params
        self.entities = entities  # id → {name, tax_code}
        self.issues: list[Issue] = []
        self.items: list[Item] = []
        self.file_hashes: dict[str, str] = {}

    # issue helpers
    def _issue(self, sev, co, src, fld, msg, amount=None, ref=""):
        self.issues.append(Issue(sev, co, src, fld, msg, amount, ref))

    def _rows(self, name: str) -> list[tuple[int, dict]]:
        p = self.inputs / name
        if p.exists():
            self.file_hashes[name] = hashlib.sha256(p.read_bytes()).hexdigest()
        return read_csv(p)

    # ---- opening cash
    def opening(self) -> tuple[dict[str, float], list[dict]]:
        rows = self._rows("bank_balances.csv")
        maxage = int(self.params.get("max_snapshot_age_days", 3))
        out: dict[str, float] = {c: 0.0 for c in self.entities}
        detail = []
        seen: dict[str, int] = {c: 0 for c in self.entities}
        if not rows:
            self._issue("LOAI_TRU", GROUP, "bank_balances.csv", "file", "Thiếu file số dư ngân hàng — tiền đầu kỳ chưa có")
        for rn, r in rows:
            src = f"bank_balances.csv:{rn}"
            co = r.get("company", "").upper()
            bal, res = _num(r.get("balance")), _num(r.get("restricted")) or 0.0
            d = to_date(r.get("date"))
            rec = {"company": co, "bank": r.get("bank", ""), "bank_account": r.get("bank_account", ""), "date": d.isoformat() if d else None,
                   "balance": bal, "restricted": res, "available": None, "verified_by": r.get("verified_by", ""), "source": r.get("source", ""),
                   "row": src, "used": False}
            detail.append(rec)
            if co not in self.entities:
                self._issue("LOAI_TRU", co or "?", src, "company", f"Mã công ty '{co}' không có trong entity_map.yaml"); continue
            if bal is None:
                self._issue("LOAI_TRU", co, src, "balance", "Thiếu số dư", ref=rec["bank_account"]); continue
            if not d:
                self._issue("LOAI_TRU", co, src, "date", "Thiếu ngày số dư", bal, rec["bank_account"]); continue
            if not rec["verified_by"]:
                self._issue("LOAI_TRU", co, src, "verified_by", "Số dư chưa được xác minh với sổ phụ/sao kê — không dùng làm tiền đầu kỳ", bal, rec["bank_account"]); continue
            if d >= self.start:
                self._issue("LOAI_TRU", co, src, "date", f"Ngày số dư {d:%d/%m/%Y} không trước ngày bắt đầu {self.start:%d/%m/%Y}", bal, rec["bank_account"]); continue
            if (self.start - d).days > maxage:
                self._issue("THIEU_TT", co, src, "date", f"Số dư cũ {(self.start - d).days} ngày (> {maxage}) — cần sao kê mới", bal, rec["bank_account"])
            rec["available"] = bal - res
            rec["used"] = True
            out[co] += bal - res
            seen[co] += 1
        for co, n in seen.items():
            if n == 0:
                self._issue("LOAI_TRU", co, "bank_balances.csv", "company", "Không có số dư ngân hàng đã xác minh — tiền đầu kỳ = 0 cho đến khi bổ sung")
        return out, detail

    # ---- forecast items
    def _make(self, fname, rn, r, line, sign, counterparty, reference, amount_key="amount", payment=None) -> Item | None:
        src = f"{fname}:{rn}"
        co = r.get("company", "").upper()
        if co not in self.entities:
            self._issue("LOAI_TRU", co or "?", src, "company", f"Mã công ty '{co}' không có trong entity_map.yaml", ref=reference); return None
        amt = _num(r.get(amount_key))
        if amt is None:
            self._issue("LOAI_TRU", co, src, amount_key, "Thiếu số tiền", ref=reference); return None
        if amt == 0:
            return None
        if amt < 0:
            self._issue("LOAI_TRU", co, src, amount_key, "Số tiền âm — cần kiểm tra (bù trừ/ghi có?)", amt, reference); return None
        ic = (r.get("counterparty_company") or "").upper()
        if ic and (ic not in self.entities or ic == co):
            self._issue("THIEU_TT", co, src, "counterparty_company", f"Công ty đối ứng nội bộ '{ic}' không hợp lệ — xử lý như bên ngoài", amt, reference)
            ic = ""
        if ic:
            line = "INTERCOMPANY"
        is_payment = sign < 0 if payment is None else payment
        due, exp = to_date(r.get("due_date")), to_date(r.get("expected_date"))
        conf = _conf(r.get("confidence"))
        owner = r.get("owner", "")
        basis = "INPUT"
        if r.get("expected_date") and not exp:
            self._issue("THIEU_TT", co, src, "expected_date", f"Ngày dự kiến '{r.get('expected_date')}' không đọc được", amt, reference)
        if r.get("due_date") and not due:
            self._issue("THIEU_TT", co, src, "due_date", f"Ngày đến hạn '{r.get('due_date')}' không đọc được", amt, reference)
        if not due:
            self._issue("THIEU_TT", co, src, "due_date", "Thiếu ngày đến hạn", amt, reference)
        if not exp:
            if not due:
                self._issue("LOAI_TRU", co, src, "expected_date", "Thiếu cả ngày đến hạn và ngày dự kiến — không xếp được vào tuần", amt, reference)
                return None
            if line == "AR_COLLECTIONS":
                lag_cfg = self.params.get("collection_lag_days", {})
                lag = int((lag_cfg.get("by_customer") or {}).get(counterparty, lag_cfg.get("default", 0)) or 0)
                exp, basis = due + dt.timedelta(days=lag), "SEED_LAG"
                self._issue("THIEU_TT", co, src, "expected_date",
                            f"Thiếu ngày dự kiến — tạm ước = hạn + {lag} ngày (độ trễ lịch sử, không phải cam kết)", amt, reference)
            else:
                exp, basis = due, "DUE_DATE"
                if not is_payment:
                    self._issue("THIEU_TT", co, src, "expected_date", "Thiếu ngày dự kiến — tạm dùng ngày đến hạn", amt, reference)
        if not conf:
            self._issue("THIEU_TT", co, src, "confidence", f"Mức tin cậy '{r.get('confidence', '')}' trống/không hợp lệ — tạm xếp Thấp", amt, reference)
            conf = "THAP"
        if basis != "INPUT" and not is_payment and conf == "CAO":
            conf = "TRUNG_BINH"  # seeded/derived dates are never high-confidence commitments
        if not owner:
            self._issue("THIEU_TT", co, src, "owner", "Thiếu người phụ trách", amt, reference)
        it = Item(src, co, line, counterparty, reference, src, due, exp, basis, sign * amt, conf, owner, ic_company=ic,
                  committed=(basis == "INPUT"))
        if exp < self.start:
            if is_payment:
                self._issue("THIEU_TT", co, src, "expected_date",
                            f"Ngày chi dự kiến {exp:%d/%m/%Y} đã qua — đưa vào tuần 1 (thận trọng), cần cập nhật", amt, reference)
            else:
                self._issue("LOAI_TRU", co, src, "expected_date",
                            f"Ngày thu dự kiến {exp:%d/%m/%Y} đã qua — không tính cho đến khi người phụ trách cập nhật", amt, reference)
                it.included = False
        self.items.append(it)
        return it

    def load_items(self) -> None:
        seen_files = {}
        for fname, line, sign, cp_key, ref_key, amt_key in (
            ("ar_open.csv", "AR_COLLECTIONS", 1, "customer", "invoice", "outstanding"),
            ("ap_open.csv", "SUPPLIER_PAYMENTS", -1, "supplier", "invoice", "outstanding"),
            ("payroll.csv", "PAYROLL", -1, "item", "reference", "amount"),
            ("taxes.csv", "TAXES", -1, "item", "reference", "amount"),
            ("capex.csv", "CAPEX", -1, "item", "reference", "amount"),
        ):
            rows = self._rows(fname)
            seen_files[fname] = {r.get("company", "").upper() for _, r in rows}
            for rn, r in rows:
                self._make(fname, rn, r, line, sign, r.get(cp_key, ""), r.get(ref_key, "") or r.get("item", ""), amt_key)
        for rn, r in self._rows("debt_schedule.csv"):
            flow = norm(r.get("flow")).upper().replace(" ", "_")
            ref = f"{r.get('lender', '')} {r.get('facility', '')}".strip()
            if flow in ("PRINCIPAL", "GOC"):
                self._make("debt_schedule.csv", rn, r, "PRINCIPAL", -1, r.get("lender", ""), ref)
            elif flow in ("INTEREST", "LAI"):
                self._make("debt_schedule.csv", rn, r, "INTEREST", -1, r.get("lender", ""), ref)
            elif flow in ("DRAWDOWN", "GIAI_NGAN"):
                if not _yes(r.get("approved")):
                    self._issue("LOAI_TRU", r.get("company", "").upper(), f"debt_schedule.csv:{rn}", "approved",
                                "Giải ngân chưa thuộc hạn mức đã duyệt — không đưa vào dự báo", _num(r.get("amount")), ref)
                    continue
                it = self._make("debt_schedule.csv", rn, r, "DRAWDOWN", 1, r.get("lender", ""), ref)
                if it:
                    it.facility = r.get("facility", "")
            else:
                self._issue("LOAI_TRU", r.get("company", "").upper(), f"debt_schedule.csv:{rn}", "flow",
                            f"Loại dòng '{r.get('flow', '')}' không hợp lệ (PRINCIPAL/INTEREST/DRAWDOWN)", _num(r.get("amount")), ref)
        seen_files["debt_schedule.csv"] = True
        for rn, r in self._rows("other.csv"):
            dirn = norm(r.get("direction"))
            if dirn in ("thu", "in", "receipt"):
                self._make("other.csv", rn, r, "OTHER_RECEIPTS", 1, r.get("item", ""), r.get("reference", "") or r.get("item", ""))
            elif dirn in ("chi", "out", "payment"):
                self._make("other.csv", rn, r, "OTHER_PAYMENTS", -1, r.get("item", ""), r.get("reference", "") or r.get("item", ""))
            else:
                self._issue("LOAI_TRU", r.get("company", "").upper(), f"other.csv:{rn}", "direction",
                            "Cột direction phải là 'thu' hoặc 'chi'", _num(r.get("amount")), r.get("item", ""))
        for fname, label in REQUIRED_PER_COMPANY.items():
            for co in self.entities:
                if co not in seen_files.get(fname, set()):
                    self._issue("LOAI_TRU", co, fname, "file", f"Chưa có {label} cho {co} — dòng này đang bằng 0, không phải 'không có'")
        if not self._rows("debt_schedule.csv"):
            self._issue("THIEU_TT", GROUP, "debt_schedule.csv", "file", "Chưa có lịch vay (gốc, lãi) — xác nhận là không có nợ vay hay còn thiếu")

    def facilities(self) -> list[dict]:
        out = []
        for rn, r in self._rows("facilities.csv"):
            co = r.get("company", "").upper()
            lim, drawn = _num(r.get("limit")), _num(r.get("drawn")) or 0.0
            exp = to_date(r.get("expiry_date"))
            src = f"facilities.csv:{rn}"
            if co not in self.entities or lim is None:
                self._issue("LOAI_TRU", co or "?", src, "limit", "Hạn mức thiếu công ty/hạn mức — không tính vào thanh khoản"); continue
            if not _yes(r.get("committed")):
                self._issue("THONG_TIN", co, src, "committed", "Hạn mức không cam kết — không tính vào thanh khoản", lim - drawn, r.get("facility", ""))
                continue
            if not exp:
                self._issue("THIEU_TT", co, src, "expiry_date", "Thiếu ngày hết hạn hạn mức — giả định hết hạn ngay (không tính)", lim - drawn, r.get("facility", ""))
            out.append({"company": co, "lender": r.get("lender", ""), "facility": r.get("facility", ""), "limit": lim, "drawn": drawn,
                        "expiry_date": exp, "source": src})
        return out

    # ---- scenarios
    def key_customers(self) -> list[str]:
        d = self.params["scenarios"]["downside"]
        if d.get("key_customers"):
            return list(d["key_customers"])
        tot: dict[str, float] = {}
        for it in self.items:
            if it.line == "AR_COLLECTIONS" and it.included:
                tot[it.counterparty] = tot.get(it.counterparty, 0) + it.amount
        n = int(d.get("key_customers_top_n", 0) or 0)
        return [k for k, _ in sorted(tot.items(), key=lambda kv: -kv[1])[:n]]

    def place(self) -> None:
        keys = set(self.key_customers())
        self._keys = sorted(keys)
        for it in self.items:
            for sc in ("base", "downside"):
                p = self.params["scenarios"][sc]
                d, amt = it.expected_date, it.amount
                if not it.included:
                    it.placement[sc] = {"date": None, "week": None, "amount": 0.0}
                    continue
                if it.line != "INTERCOMPANY":
                    if amt > 0 and it.line == "DRAWDOWN":
                        amt = amt * p["drawdown_factor"][it.confidence]
                    elif amt > 0:
                        amt = amt * p["receipt_factor"][it.confidence]
                        if sc == "downside":
                            delay = int(p.get("all_receipts_delay_days", 0) or 0)
                            if it.line == "AR_COLLECTIONS" and it.counterparty in keys:
                                delay += int(p.get("key_customer_delay_days", 0) or 0)
                            d = d + dt.timedelta(days=delay)
                    elif sc == "downside":
                        d = d - dt.timedelta(days=int(p.get("payment_advance_days", 0) or 0))
                if amt < 0 and d < self.start:
                    d = self.start
                wk = (d - self.start).days // 7 + 1
                it.placement[sc] = {"date": d, "week": wk if 1 <= wk <= WEEKS else None, "amount": amt}


# ---- aggregation ----------------------------------------------------------------------------
def _zeros() -> list[float]:
    return [0.0] * WEEKS


def _bridge(opening: float, lines: dict[str, list[float]], floor: float | None, undrawn: list[float], exclude_ic: bool) -> dict:
    op, cl, rec, pay, ic, unc = [], [], [], [], [], []
    cur = opening
    for w in range(WEEKS):
        r = sum(lines[l][w] for l in LINE_IDS if LINE_KIND[l] == "in") + max(0.0, lines["UNCLASSIFIED"][w])
        p = sum(lines[l][w] for l in LINE_IDS if LINE_KIND[l] == "out") + min(0.0, lines["UNCLASSIFIED"][w])
        i = 0.0 if exclude_ic else lines["INTERCOMPANY"][w]
        op.append(cur)
        cur = cur + r + p + i
        rec.append(r); pay.append(p); ic.append(i); cl.append(cur)
    head = [c - floor for c in cl] if floor is not None else [None] * WEEKS
    return {"opening": op, "receipts": rec, "payments": pay, "intercompany": ic, "closing": cl,
            "floor": [floor] * WEEKS if floor is not None else [None] * WEEKS, "headroom": head,
            "undrawn": undrawn, "liquidity": [c + u for c, u in zip(cl, undrawn)],
            "lines": lines, "min_closing": min(cl), "min_closing_week": cl.index(min(cl)) + 1,
            "min_headroom": min(head) if floor is not None else None,
            "breach_weeks": [w + 1 for w, h in enumerate(head) if h is not None and h < 0]}


def _weeks(start: dt.date, offset: int = 0) -> list[dict]:
    out = []
    for i in range(WEEKS):
        s = start + dt.timedelta(days=7 * (i + offset))
        n = i + 1 if offset >= 0 else i + offset
        out.append({"n": n, "start": s.isoformat(), "end": (s + dt.timedelta(days=6)).isoformat(),
                    "label": f"{'T' if n > 0 else 'A'}{abs(n)} · {s:%d/%m}"})
    return out


def _actuals(wh, start: dt.date, entities: dict, cfmap: dict) -> dict:
    """Last 13 weeks of actual cash flows from fact_gl_lines (cash account lines only)."""
    a_start = start - dt.timedelta(days=7 * WEEKS)
    tax = {v["tax_code"]: k for k, v in entities.items() if v.get("tax_code")}
    cats = sorted(((p, c["id"]) for c in cfmap["categories"] for p in c["prefixes"]), key=lambda x: -len(x[0]))
    cash = cfmap.get("cash_accounts", ["111", "112", "113"])
    res: dict[str, Any] = {"by_company": {}, "rows": [], "internal_transfers_excluded": {}, "policy_version": cfmap.get("version")}
    for co in entities:
        res["by_company"][co] = {"lines": {l: _zeros() for l in LINE_IDS}, "has_data": [False] * WEEKS, "count": 0}
        res["internal_transfers_excluded"][co] = 0.0
    if wh is None:
        return res
    cond = " OR ".join(f"starts_with(account_code,'{p}')" for p in cash)
    rows = wh.con.execute(
        f"""SELECT company_id, CAST(posting_date AS VARCHAR), account_code, coalesce(contra_account_code,''), coalesce(debit,0)-coalesce(credit,0),
                   coalesce(counterparty_code,''), coalesce(document_number,''), coalesce(description,''), source_filename, source_row_number
            FROM fact_gl_lines WHERE ({cond}) AND CAST(posting_date AS VARCHAR) >= ? AND CAST(posting_date AS VARCHAR) < ?
            ORDER BY 1, 2, source_row_number""", [a_start.isoformat(), start.isoformat()]).fetchall() if _has_cols(wh) else []
    for co, d, acc, contra, amt, cp, doc, desc, fn, rn in rows:
        if co not in res["by_company"] or not amt:
            continue
        w = (dt.date.fromisoformat(d[:10]) - a_start).days // 7
        cat = next((c for p, c in cats if contra.startswith(p)), "UNCLASSIFIED")
        if cat != "INTERNAL_TRANSFER" and cp in tax and tax[cp] != co:
            cat = "INTERCOMPANY"
        b = res["by_company"][co]
        b["has_data"][w] = True
        if cat == "INTERNAL_TRANSFER":
            res["internal_transfers_excluded"][co] += abs(amt)
            line = None
        else:
            m = ACTUAL_LINE.get(cat, OTHER_ACTUAL)
            line = (m[0] if amt > 0 else m[1]) if isinstance(m, tuple) else m
            b["lines"][line][w] += amt
            b["count"] += 1
        res["rows"].append({"company": co, "date": d[:10], "week": w - WEEKS, "account": acc, "contra": contra, "category": cat,
                            "line": line, "amount": amt, "counterparty": cp, "document": doc, "description": desc,
                            "file": fn, "row": rn})
    return res


def _has_cols(wh) -> bool:
    cols = {r[0] for r in wh.con.execute("DESCRIBE fact_gl_lines").fetchall()}
    return {"counterparty_code", "description"} <= cols


def _actual_view(lines: dict[str, list[float]], exclude_ic: bool) -> dict:
    rec = [sum(lines[l][w] for l in LINE_IDS if LINE_KIND[l] == "in") + max(0.0, lines["UNCLASSIFIED"][w]) for w in range(WEEKS)]
    pay = [sum(lines[l][w] for l in LINE_IDS if LINE_KIND[l] == "out") + min(0.0, lines["UNCLASSIFIED"][w]) for w in range(WEEKS)]
    ic = [0.0 if exclude_ic else lines["INTERCOMPANY"][w] for w in range(WEEKS)]
    return {"lines": lines, "receipts": rec, "payments": pay, "intercompany": ic, "net": [r + p + i for r, p, i in zip(rec, pay, ic)]}


# ---- versions & comparison ------------------------------------------------------------------
def versions_dir(data: Path) -> Path:
    return Path(data) / "forecasts" / "cash13w"


def list_versions(data: Path) -> list[dict]:
    d = versions_dir(data)
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("CF13W-*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
            out.append({"version_id": j["version_id"], "start_date": j["start_date"], "created_at": j["created_at"], "path": str(p)})
        except (ValueError, KeyError):
            continue
    return sorted(out, key=lambda v: (v["start_date"], v["created_at"]))


def prior_version(data: Path, start: dt.date) -> dict | None:
    cands = [v for v in list_versions(data) if v["start_date"] < start.isoformat()]
    if not cands:
        return None
    return json.loads(Path(cands[-1]["path"]).read_text(encoding="utf-8"))


def compare(cur: dict, prior: dict | None, params: dict) -> dict:
    if not prior:
        return {"prior_version_id": None, "message": "Chưa có phiên bản trước để so sánh (lần chạy đầu tiên)."}
    thr, mat = float(params.get("variance_threshold_pct", 10)), float(params.get("variance_materiality", 0))
    a_weeks = {w["start"]: i for i, w in enumerate(cur["actual_weeks"])}
    elapsed = [(j, w) for j, w in enumerate(prior["weeks"]) if w["start"] < cur["start_date"]]
    variance, opening = [], []
    for co in list(cur["views"]):
        pv, cv = prior["views"].get(co), cur["views"][co]
        if not pv:
            continue
        exclude_ic = co == GROUP
        for j, w in elapsed:
            ai = a_weeks.get(w["start"])
            has = ai is not None and (cv["actuals"]["has_data"][ai] if "has_data" in cv["actuals"] else True)
            for l in LINE_IDS:
                if exclude_ic and l == "INTERCOMPANY":
                    continue
                f = pv["scenarios"]["base"]["lines"].get(l, _zeros())[j]
                a = cv["actuals"]["lines"][l][ai] if has else None
                if not f and not a:
                    continue
                var = None if a is None else a - f
                pct = None if var is None or not f else var / abs(f) * 100
                flag = var is not None and abs(var) >= mat and (pct is None or abs(pct) > thr)
                variance.append({"company": co, "week_start": w["start"], "line": l, "forecast": f, "actual": a, "variance": var,
                                 "variance_pct": pct, "needs_explanation": flag,
                                 "status": "OK" if a is not None else "CHUA_CO_THUC_TE"})
        if elapsed:
            j = elapsed[-1][0]
            pc = pv["scenarios"]["base"]["closing"][j]
            opening.append({"company": co, "prior_forecast_closing": pc, "verified_opening": cv["scenarios"]["base"]["opening"][0],
                            "difference": cv["scenarios"]["base"]["opening"][0] - pc})
    roll = {}
    pidx = {w["start"]: j for j, w in enumerate(prior["weeks"])}
    for co, cv in cur["views"].items():
        pv = prior["views"].get(co)
        if not pv:
            continue
        roll[co] = {}
        for sc in ("base", "downside"):
            rows = []
            for i, w in enumerate(cur["weeks"]):
                j = pidx.get(w["start"])
                pc = pv["scenarios"][sc]["closing"][j] if j is not None else None
                cc = cv["scenarios"][sc]["closing"][i]
                rows.append({"week_start": w["start"], "prior_closing": pc, "current_closing": cc,
                             "delta": None if pc is None else cc - pc})
            roll[co][sc] = rows
    return {"prior_version_id": prior["version_id"], "prior_start_date": prior["start_date"],
            "elapsed_weeks": [w["start"] for _, w in elapsed], "opening_check": opening, "week_variance": variance,
            "rollforward": roll, "threshold_pct": thr, "materiality": mat}


# ---- main entry -----------------------------------------------------------------------------
def build(inputs: Path, start: dt.date, data: Path | None = None, params_path: Path | None = None,
          config_dir: Path | None = None, warehouse=None, created_at: dt.datetime | None = None) -> dict:
    inputs = Path(inputs)
    if start.weekday() != 0:
        raise ValueError(f"Ngày bắt đầu {start} không phải thứ Hai (gợi ý: {monday_of(start)})")
    params = load_params(inputs, params_path)
    ent_cfg = load_config("entity_map.yaml", config_dir)["entities"]
    entities = {k: {"name": v["name"], "tax_code": v.get("tax_code")} for k, v in ent_cfg.items()}
    cfmap = load_config("cash_flow_map.yaml", config_dir)
    b = Builder(inputs, start, params, entities)
    _sanitize_scenarios(params, b.issues)
    opening, opening_detail = b.opening()
    b.load_items()
    facs = b.facilities()
    b.place()

    floors_cfg = params.get("min_liquidity_floor", {}) or {}
    by_co = {str(k).upper(): v for k, v in (floors_cfg.get("by_company") or {}).items()}
    floors: dict[str, float | None] = {}
    for co in list(entities) + [GROUP]:
        v = by_co.get(co)
        floors[co] = float(v) if v is not None else None
    if floors[GROUP] is None and all(floors[c] is not None for c in entities):
        floors[GROUP] = sum(floors[c] for c in entities)
    for co, v in floors.items():
        if v is None:
            b._issue("THIEU_TT", co, "params.yaml", "min_liquidity_floor", "Chưa có ngưỡng thanh khoản tối thiểu — headroom chưa tính được")
    if not floors_cfg.get("approved_by"):
        b._issue("THIEU_TT", GROUP, "params.yaml", "min_liquidity_floor.approved_by", "Ngưỡng thanh khoản tối thiểu chưa được CFO duyệt")

    weeks = _weeks(start)
    actual_weeks = _weeks(start - dt.timedelta(days=7 * WEEKS), 0)
    for i, w in enumerate(actual_weeks):
        w["n"] = i - WEEKS
        w["label"] = f"A{WEEKS - i} · {dt.date.fromisoformat(w['start']):%d/%m}"
    if warehouse is None and data is not None:
        from ..models.warehouse import Warehouse
        Path(data).mkdir(parents=True, exist_ok=True)
        warehouse = Warehouse(Path(data), config_dir)
    act = _actuals(warehouse, start, entities, cfmap)

    views: dict[str, Any] = {}
    for co in list(entities) + [GROUP]:
        scen = {}
        for sc in ("base", "downside"):
            lines = {l: _zeros() for l in LINE_IDS}
            for it in b.items:
                if co != GROUP and it.company != co:
                    continue
                if co == GROUP and it.line == "INTERCOMPANY":
                    continue
                p = it.placement[sc]
                if p["week"]:
                    lines[it.line][p["week"] - 1] += p["amount"]
            undrawn = _zeros()
            for f in facs:
                if co != GROUP and f["company"] != co:
                    continue
                for w in range(WEEKS):
                    wend = start + dt.timedelta(days=7 * w + 6)
                    if not f["expiry_date"] or f["expiry_date"] < wend:
                        continue
                    drawn = sum(it.placement[sc]["amount"] for it in b.items if it.line == "DRAWDOWN" and it.company == f["company"]
                                and it.facility == f["facility"] and it.placement[sc]["week"] and it.placement[sc]["week"] <= w + 1)
                    undrawn[w] += max(0.0, f["limit"] - f["drawn"] - drawn)
            op = sum(opening.values()) if co == GROUP else opening[co]
            scen[sc] = _bridge(op, lines, floors[co], undrawn, exclude_ic=(co == GROUP))
        if co == GROUP:
            alines = {l: [sum(act["by_company"][c]["lines"][l][w] for c in entities) for w in range(WEEKS)] for l in LINE_IDS}
            alines["INTERCOMPANY"] = _zeros()
            has = [any(act["by_company"][c]["has_data"][w] for c in entities) for w in range(WEEKS)]
        else:
            alines, has = act["by_company"][co]["lines"], act["by_company"][co]["has_data"]
        av = _actual_view(alines, exclude_ic=(co == GROUP))
        av["has_data"] = has
        views[co] = {"name": "Hợp nhất (loại trừ nội bộ)" if co == GROUP else entities[co]["name"], "scenarios": scen, "actuals": av}

    # intercompany check: forecast IC per week should net to zero across entities
    ic_check = []
    for sc in ("base", "downside"):
        for w in range(WEEKS):
            net = sum(views[c]["scenarios"][sc]["lines"]["INTERCOMPANY"][w] for c in entities)
            if abs(net) > 0.5:
                ic_check.append({"scenario": sc, "week": w + 1, "unmatched": net})
    if any(x["scenario"] == "base" for x in ic_check):
        b._issue("THIEU_TT", GROUP, "intercompany", "counterparty_company",
                 "Dòng nội bộ dự báo chưa khớp giữa hai pháp nhân (tổng ≠ 0) — xem Kiểm tra nội bộ")
    ic_actual = [sum(act["by_company"][c]["lines"]["INTERCOMPANY"][w] for c in entities) for w in range(WEEKS)]

    for co in list(entities) + [GROUP]:
        for sc in ("base", "downside"):
            v = views[co]["scenarios"][sc]
            if v["breach_weeks"]:
                b._issue("THONG_TIN", co, f"model:{sc}", "headroom",
                         f"{'Base' if sc == 'base' else 'Downside'}: tiền dưới ngưỡng tối thiểu ở tuần {', '.join(map(str, v['breach_weeks']))}")

    created = created_at or dt.datetime.now().replace(microsecond=0)
    blocking = [i for i in b.issues if i.severity == "LOAI_TRU"]
    appr = params.get("approval", {}) or {}
    approved = all(appr.get(k) for k in ("opening_cash_by", "floor_by", "assumptions_by")) and not blocking
    fp = hashlib.sha256(json.dumps(b.file_hashes, sort_keys=True).encode()).hexdigest()[:8]
    result = {
        "schema": SCHEMA,
        "version_id": f"CF13W-{start.isoformat()}-{created:%Y%m%dT%H%M%S}-{fp}",
        "created_at": created.isoformat(),
        "start_date": start.isoformat(),
        "sample": bool(params.get("sample")),
        "status": "APPROVED" if approved else "DRAFT",
        "status_label": "Đã duyệt" if approved else "Bản nháp — chờ CFO duyệt tiền đầu kỳ, ngưỡng và giả định",
        "currency": "VND",
        "entities": [{"id": k, "name": v["name"]} for k, v in entities.items()],
        "lines": [{"id": i, "label": l, "kind": k} for i, l, k in LINES],
        "weeks": weeks,
        "actual_weeks": actual_weeks,
        "opening_detail": opening_detail,
        "opening": opening,
        "floors": floors,
        "facilities": [{**f, "expiry_date": f["expiry_date"].isoformat() if f["expiry_date"] else None} for f in facs],
        "views": views,
        "items": [it.as_dict() for it in b.items],
        "data_required": [i.as_dict() for i in b.issues],
        "key_customers_downside": getattr(b, "_keys", []),
        "intercompany_check": {"forecast_unmatched": ic_check, "actual_net_by_week": ic_actual},
        "actual_rows": act["rows"],
        "internal_transfers_excluded": act["internal_transfers_excluded"],
        "params": params,
        "policy": {"cash_flow_map_version": cfmap.get("version"), "cash_flow_map_status": cfmap.get("status")},
        "input_files": b.file_hashes,
    }
    result["comparison"] = compare(result, prior_version(data, start) if data else None, params)
    return result


def save_version(result: dict, data: Path) -> Path:
    d = versions_dir(data)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{result['version_id']}.json"
    if p.exists():
        raise FileExistsError(p)  # versions are immutable
    p.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    return p


def write_json(result: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def write_templates(out: Path) -> list[Path]:
    """Empty CSV templates with headers + a commented params.yaml."""
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, cols in INPUT_FILES.items():
        p = out / name
        with p.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(cols)
        paths.append(p)
    p = out / "params.yaml"
    p.write_text("# [PROPOSED POLICY] Tham số dòng tiền 13 tuần — CFO duyệt trước khi dùng\n" + yaml.safe_dump(DEFAULT_PARAMS, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return paths + [p]
