"""Lớp số liệu cho board pack: chỉ đọc warehouse của alta-finance-intelligence (không tự tính lại từ Excel).

- KQKD: `Warehouse.pl()` (= `afi pl`, đọc `mart_pl_monthly`), cộng theo tháng; lãi vay theo quy tắc P3,
  EBITDA theo P4, doanh thu nội bộ theo P5 (chỉ để trình bày, chưa loại trừ trong số hợp nhất).
- Số dư: `fact_tb` (CĐPS, chỉ tài khoản lá), số dư cuối kỳ của bảng có ngày kết thúc = cuối tháng.
- Trạng thái dữ liệu: `run_controls` + `period_status` (giống `afi reconcile`).
- Truy xuất nguồn: `pl_lines_lineage` / `fact_gl_lines` / `fact_tb` → tên file + dòng Excel.
"""
from __future__ import annotations

import calendar
import csv
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import duckdb
from afi.models.warehouse import Warehouse
from afi.parsers.base import load_config
from afi.reconciliations.controls import period_status, run_controls

ORDER = ["ALTA", "APL", "AME"]
SHORT = {"ALTA": "Alta (Mẹ)", "APL": "Alta Plastic", "AME": "Alta Media", None: "Hợp nhất"}

# (key, nhãn, dấu hiển thị: chi phí hiển thị số âm, in đậm)
PL_ROWS = [
    ("net_revenue", "Doanh thu thuần", 1, True),
    ("cogs", "Giá vốn hàng bán", -1, False),
    ("gross_profit", "Lợi nhuận gộp", 1, True),
    ("selling_expenses", "Chi phí bán hàng", -1, False),
    ("admin_expenses", "Chi phí quản lý doanh nghiệp", -1, False),
    ("finance_income", "Doanh thu tài chính", 1, False),
    ("finance_expense", "Chi phí tài chính", -1, False),
    ("interest_expense", "   trong đó: lãi vay", -1, False),
    ("other_income", "Thu nhập khác", 1, False),
    ("other_expense", "Chi phí khác", -1, False),
    ("profit_before_tax", "Lợi nhuận trước thuế", 1, True),
    ("income_tax", "Chi phí thuế TNDN", -1, False),
    ("net_profit", "Lợi nhuận sau thuế", 1, True),
    ("depreciation", "Khấu hao (Có TK 214)", 1, False),
    ("ebitda", "EBITDA", 1, True),
]
LABEL = {k: lbl.strip().replace("trong đó: ", "") for k, lbl, _, _ in PL_ROWS}
LABEL.update(external_revenue="Doanh thu ngoài tập đoàn", ic_revenue="Doanh thu nội bộ")
SIGN = {k: s for k, _, s, _ in PL_ROWS}
SIGN.update(external_revenue=1, ic_revenue=1)
BASE_LINES = ["net_revenue", "cogs", "selling_expenses", "admin_expenses", "finance_income", "finance_expense",
              "other_income", "other_expense", "income_tax", "depreciation", "interest_expense"]
BAL_GROUPS = {  # nhóm số dư: (tiền tố TK, dấu: +1 dư Nợ, −1 dư Có)
    "cash": (["111", "112", "113"], 1),
    "receivables": (["131"], 1),
    "inventory": (["151", "152", "153", "154", "155", "156", "157", "158"], 1),
    "payables": (["331"], -1),
    "debt": (["311", "341"], -1),
}
BAL_LABEL = {"cash": "Tiền và tương đương tiền", "receivables": "Phải thu khách hàng (TK 131)", "inventory": "Hàng tồn kho (TK 15x)",
             "payables": "Phải trả người bán (TK 331)", "debt": "Vay và nợ thuê tài chính (TK 311, 341)"}


def month_end(m: str) -> str:
    y, mo = int(m[:4]), int(m[5:7])
    return f"{m}-{calendar.monthrange(y, mo)[1]:02d}"


def shift(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:7]) + k
    while mo < 1:
        y, mo = y - 1, mo + 12
    while mo > 12:
        y, mo = y + 1, mo - 12
    return f"{y:04d}-{mo:02d}"


def months_for(month: str, mode: str) -> list[str]:
    return [month] if mode == "month" else [f"{month[:4]}-{i:02d}" for i in range(1, int(month[5:7]) + 1)]


def prior_year(months: list[str]) -> list[str]:
    return [shift(m, -12) for m in months]


@dataclass
class SourceRow:
    file: str
    row: int
    amount: float
    account: str = ""
    party: str = ""

    def text(self) -> str:
        extra = " · ".join(x for x in (f"TK {self.account}" if self.account else "", self.party) if x)
        return f"{self.file} · dòng {self.row}" + (f" ({extra})" if extra else "")


@dataclass
class Status:
    label: str                      # APPROVED | RECONCILED | SƠ BỘ
    detail: dict = field(default_factory=dict)  # "CID|YYYY-MM" → trạng thái gốc

    @property
    def final(self) -> bool:
        return self.label in ("APPROVED", "RECONCILED")


def _arrow(res):
    """pyarrow.Table từ kết quả DuckDB (tên hàm khác nhau giữa các phiên bản duckdb)."""
    for name in ("to_arrow_table", "fetch_arrow_table", "arrow"):
        if hasattr(res, name):
            t = getattr(res, name)()
            return t.read_all() if hasattr(t, "read_all") else t
    raise RuntimeError("duckdb không hỗ trợ xuất Arrow")


def load_plan(path: Path | None) -> dict[tuple[str, str, str], float]:
    """CSV kế hoạch: company, month, line, amount (VND). line ∈ dòng cơ sở của account_map + interest_expense;
    có thể ghi thẳng dòng dẫn xuất (gross_profit, ebitda, …) để ghi đè giá trị tính."""
    if not path:
        return {}
    out: dict[tuple[str, str, str], float] = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            k = (r["company"].strip(), r["month"].strip()[:7], r["line"].strip())
            out[k] = out.get(k, 0.0) + float(str(r["amount"]).replace(",", "").strip() or 0)
    return out


class Facts:
    def __init__(self, wh: Warehouse, plan_path: Path | None = None, approvals: Path | None = None):
        self.wh = wh
        # Bản sao trong bộ nhớ của các bảng gold (đọc Parquet một lần). KQKD vẫn tính bằng chính Warehouse.pl
        # trên bản sao này, nên số trên slide = `afi pl`.
        self.con = duckdb.connect()
        for t in ("fact_gl_lines", "fact_tb", "pl_lines_lineage", "mart_pl_monthly"):
            self.con.register("_src", _arrow(wh.con.sql(f"SELECT * FROM {t}")))
            self.con.execute(f"CREATE TABLE {t} AS SELECT * FROM _src")
            self.con.unregister("_src")
        self._shim = SimpleNamespace(con=self.con, accounts=wh.accounts)
        ents = load_config("entity_map.yaml")["entities"]
        self.tax = {cid: e["tax_code"] for cid, e in ents.items()}
        self.names = {cid: e["name"] for cid, e in ents.items()}
        acc = wh.accounts
        self.excl = acc.get("exclude_contra", ["911"])
        self.derived = acc.get("derived", {})
        self.irule = acc.get("interest_expense_rule", {})
        self.cash_map = load_config("cash_flow_map.yaml")
        self.plan = load_plan(plan_path)
        self.plan_path = plan_path
        self.controls = run_controls(wh)
        self.status_map = period_status(self.controls, approvals or (wh.data / "approvals.yaml"))
        have = self.con.execute("SELECT DISTINCT company_id, month FROM fact_gl_lines").fetchall()
        self.gl_months = {(c, m) for c, m in have}
        self.companies = [c for c in ORDER if any(x == c for x, _ in self.gl_months)]
        self._pl: dict = {}

    # ---------- helpers ----------
    def scope(self, cid: str | None) -> list[str]:
        return self.companies if cid is None else [cid]

    def has_data(self, cid: str | None, months: list[str]) -> bool:
        return all((c, m) in self.gl_months for c in self.scope(cid) for m in months)

    @staticmethod
    def _in(col: str, vals: list[str]) -> tuple[str, list]:
        return f"{col} IN ({','.join('?' * len(vals))})", list(vals)

    def _where(self, cid, months, alias=""):
        a = f"{alias}." if alias else ""
        c1, p1 = self._in(a + "company_id", self.scope(cid))
        c2, p2 = self._in(a + "month", months)
        return f"{c1} AND {c2}", p1 + p2

    def _excl_sql(self) -> str:
        return " AND ".join(f"NOT starts_with(account_code,'{p}') AND NOT starts_with(coalesce(contra_account_code,''),'{p}')" for p in self.excl)

    def _interest_sql(self) -> str:
        kw = "|".join(self.irule.get("description_keywords", ["lai vay"]))
        contra = " OR ".join(f"starts_with(coalesce(contra_account_code,''),'{p}')" for p in self.irule.get("contra_prefixes", []))
        return (f"starts_with(account_code,'{self.irule.get('account_prefix', '635')}') AND {self._excl_sql()} AND "
                f"(regexp_matches(lower(strip_accents(coalesce(description,''))), '{kw}')" + (f" OR {contra})" if contra else ")"))

    # ---------- P&L ----------
    def pl(self, cid: str | None, months: list[str]) -> dict[str, float] | None:
        """KQKD (giá trị gốc: chi phí là số dương) — cộng `afi pl` theo tháng. None nếu thiếu dữ liệu."""
        key = (cid, tuple(months))
        if key in self._pl:
            return self._pl[key]
        if not self.has_data(cid, months):
            self._pl[key] = None
            return None
        tot: dict[str, float] = {}
        for m in months:
            for k, v in Warehouse.pl(self._shim, cid, m).items():
                tot[k] = tot.get(k, 0.0) + v
        w, p = self._where(cid, months)
        tot["interest_expense"] = self.con.execute(f"SELECT coalesce(sum(debit-credit),0) FROM fact_gl_lines WHERE {w} AND {self._interest_sql()}", p).fetchone()[0]
        tot["ic_revenue"] = self._ic_revenue(cid, months)
        self._finish(tot)
        self._pl[key] = tot
        return tot

    @staticmethod
    def _finish(t: dict) -> None:
        t["ebitda"] = t["profit_before_tax"] + t["interest_expense"] + t["depreciation"]
        t["external_revenue"] = t["net_revenue"] - t.get("ic_revenue", 0.0)
        t["gross_margin"] = t["gross_profit"] / t["net_revenue"] if t["net_revenue"] else None
        t["ebitda_margin"] = t["ebitda"] / t["net_revenue"] if t["net_revenue"] else None

    def _ic_revenue(self, cid, months) -> float:
        tot = 0.0
        for c in self.scope(cid):
            others = [t for k, t in self.tax.items() if k != c]
            w, p = self._where(c, months)
            q, p2 = self._in("counterparty_code", others)
            tot += self.con.execute(f"SELECT coalesce(sum(amount),0) FROM pl_lines_lineage WHERE line='net_revenue' AND {w} AND {q}", p + p2).fetchone()[0]
        return tot

    def plan_pl(self, cid: str | None, months: list[str]) -> dict[str, float] | None:
        if not self.plan:
            return None
        if not all(any(k[0] == c and k[1] == m for k in self.plan) for c in self.scope(cid) for m in months):
            return None
        t = {k: 0.0 for k in BASE_LINES}
        explicit: dict[str, float] = {}
        for (c, m, line), v in self.plan.items():
            if c in self.scope(cid) and m in months:
                (t if line in t else explicit)[line] = (t if line in t else explicit).get(line, 0.0) + v
        for name, expr in self.derived.items():
            t[name] = eval(expr, {"__builtins__": {}}, dict(t))  # cùng công thức đã duyệt trong account_map.yaml
        t["ic_revenue"] = 0.0
        self._finish(t)
        for k, v in explicit.items():
            t[k] = v
        if "ebitda" in explicit or "net_revenue" in explicit:
            t["ebitda_margin"] = t["ebitda"] / t["net_revenue"] if t["net_revenue"] else None
        t["external_revenue"] = explicit.get("external_revenue")  # KH thường không tách nội bộ
        return t

    def plan_lines_missing(self) -> list[str]:
        have = {k[2] for k in self.plan}
        return [x for x in BASE_LINES if x not in have] if self.plan else []

    def ltm_ebitda(self, cid, month) -> float | None:
        p = self.pl(cid, [shift(month, -i) for i in range(12)])
        return p["ebitda"] if p else None

    # ---------- trạng thái ----------
    def status(self, cid: str | None, months: list[str]) -> Status:
        det = {f"{c}|{m}": self.status_map.get(f"{c}|{m}", "CHƯA CÓ DỮ LIỆU") for c in self.scope(cid) for m in months}
        vals = set(det.values())
        if vals == {"APPROVED"}:
            lab = "APPROVED"
        elif vals <= {"APPROVED", "RECONCILED"}:
            lab = "RECONCILED"
        else:
            lab = "SƠ BỘ"
        return Status(lab, det)

    # ---------- số dư ----------
    def balances(self, cid: str | None, month: str) -> dict[str, float] | None:
        key = ("bal", cid, month)
        if key not in self._pl:
            self._pl[key] = self._balances(cid, month)
        return self._pl[key]

    def _balances(self, cid, month):
        end = month_end(month)
        out = {k: 0.0 for k in BAL_GROUPS}
        for c in self.scope(cid):
            r = self.con.execute("SELECT max(report_period_start) FROM fact_tb WHERE company_id=? AND report_period_end=?", [c, end]).fetchone()[0]
            if r is None:
                return None
            for g, (prefixes, sign) in BAL_GROUPS.items():
                cond = " OR ".join(f"starts_with(account_code,'{p}')" for p in prefixes)
                out[g] += sign * self.con.execute(f"""SELECT coalesce(sum(closing_debit - closing_credit),0) FROM fact_tb
                    WHERE is_leaf AND company_id=? AND report_period_start=? AND report_period_end=? AND ({cond})""", [c, r, end]).fetchone()[0]
        out["net_debt"] = out["debt"] - out["cash"]
        return out

    def balance_rows(self, cid: str | None, month: str, group: str, n: int = 3) -> list[SourceRow]:
        prefixes, sign = BAL_GROUPS[group]
        cond = " OR ".join(f"starts_with(t.account_code,'{p}')" for p in prefixes)
        c1, p1 = self._in("t.company_id", self.scope(cid))
        rows = self.con.execute(f"""SELECT t.source_filename, t.source_row_number, {sign}*(t.closing_debit-t.closing_credit) v, t.account_code, t.company_id
            FROM fact_tb t JOIN (SELECT company_id, max(report_period_start) s FROM fact_tb WHERE report_period_end=? GROUP BY 1) x
              ON x.company_id=t.company_id AND x.s=t.report_period_start
            WHERE t.is_leaf AND t.report_period_end=? AND {c1} AND ({cond}) ORDER BY abs(v) DESC LIMIT {n}""", [month_end(month), month_end(month), *p1]).fetchall()
        return [SourceRow(f, int(r), v, a, c) for f, r, v, a, c in rows]

    def working_capital_days(self, cid, month) -> dict[str, float | None]:
        """P8: DSO = PT ÷ (DT 3 tháng × 1,1) × 91; DIO = HTK ÷ GV 3 tháng × 91; DPO = PTr ÷ (GV 3 tháng × 1,1) × 91."""
        b = self.balances(cid, month)
        p = self.pl(cid, [shift(month, -i) for i in range(3)])
        if not b or not p:
            return {"dso": None, "dio": None, "dpo": None}
        f = lambda num, den: num / den * 91 if den else None  # noqa: E731
        return {"dso": f(b["receivables"], p["net_revenue"] * 1.1), "dio": f(b["inventory"], p["cogs"]), "dpo": f(b["payables"], p["cogs"] * 1.1)}

    # ---------- dòng tiền ----------
    def cash_flows(self, cid: str | None, months: list[str]) -> dict[str, float] | None:
        key = ("cf", cid, tuple(months))
        if key not in self._pl:
            self._pl[key] = self._cash_flows(cid, months)
        return self._pl[key]

    def _cash_flows(self, cid, months):
        if not self.has_data(cid, months):
            return None
        cats = sorted(((p, c["activity"]) for c in self.cash_map["categories"] for p in c["prefixes"]), key=lambda x: -len(x[0]))
        cash = " OR ".join(f"starts_with(account_code,'{p}')" for p in self.cash_map["cash_accounts"])
        w, p = self._where(cid, months)
        out = {"operating": 0.0, "investing": 0.0, "financing": 0.0, "intercompany": 0.0, "unclassified": 0.0}
        for contra, amt in self.con.execute(f"SELECT coalesce(contra_account_code,''), sum(debit-credit) FROM fact_gl_lines WHERE {w} AND ({cash}) GROUP BY 1", p).fetchall():
            act = next((a for pre, a in cats if contra.startswith(pre)), "unclassified")
            if act != "none":
                out[act] = out.get(act, 0.0) + amt
        return out

    # ---------- truy xuất & phân tích ----------
    def source_rows(self, line: str, cid: str | None, months: list[str], n: int = 3) -> tuple[list[SourceRow], int]:
        """Các dòng Excel đóng góp lớn nhất cho một chỉ tiêu cơ sở; trả về (top n, tổng số dòng)."""
        w, p = self._where(cid, months)
        if line == "interest_expense":
            base = f"SELECT source_filename f, source_row_number r, debit-credit a, account_code ac, counterparty_name cp FROM fact_gl_lines WHERE {w} AND {self._interest_sql()}"
        elif line == "ic_revenue":
            q, p2 = self._in("counterparty_code", list(self.tax.values()))
            base = f"SELECT source_filename f, source_row_number r, amount a, account_code ac, counterparty_name cp FROM pl_lines_lineage WHERE line='net_revenue' AND {w} AND {q}"
            p = p + p2
        else:
            base = f"SELECT source_filename f, source_row_number r, amount a, account_code ac, counterparty_name cp FROM pl_lines_lineage WHERE line=? AND {w}"
            p = [line] + p
        rows = self.con.execute(f"SELECT * FROM ({base}) ORDER BY abs(a) DESC", p).fetchall()
        return [SourceRow(f, int(r), a, ac or "", cp or "") for f, r, a, ac, cp in rows[:n]], len(rows)

    def contributors(self, line: str, cid: str | None, months_a: list[str], months_b: list[str], by: str = "counterparty_name", n: int = 3):
        """Chênh lệch theo khách hàng/tài khoản giữa hai kỳ (chỉ dòng cơ sở): [(khóa, A, B, Δ)] sắp theo |Δ|."""
        wa, pa = self._where(cid, months_a)
        wb, pb = self._where(cid, months_b)
        col = "coalesce(nullif(counterparty_name,''), '(không có đối tượng)')" if by == "counterparty_name" else by
        q = f"""WITH a AS (SELECT {col} k, sum(amount) v FROM pl_lines_lineage WHERE line=? AND {wa} GROUP BY 1),
                     b AS (SELECT {col} k, sum(amount) v FROM pl_lines_lineage WHERE line=? AND {wb} GROUP BY 1)
                SELECT coalesce(a.k,b.k), coalesce(a.v,0), coalesce(b.v,0), coalesce(a.v,0)-coalesce(b.v,0) d
                FROM a FULL JOIN b ON a.k=b.k ORDER BY abs(d) DESC LIMIT {n}"""
        return self.con.execute(q, [line, *pa, line, *pb]).fetchall()

    def top_customers(self, cid: str | None, months: list[str], n: int = 5):
        w, p = self._where(cid, months)
        return self.con.execute(f"""SELECT coalesce(nullif(counterparty_name,''),'(không có)'), sum(amount) v FROM pl_lines_lineage
            WHERE line='net_revenue' AND {w} GROUP BY 1 ORDER BY v DESC LIMIT {n}""", p).fetchall()

    def trend(self, cid: str | None, month: str, n: int = 6) -> list[tuple[str, dict | None]]:
        return [(m, self.pl(cid, [m])) for m in (shift(month, -i) for i in range(n - 1, -1, -1))]
