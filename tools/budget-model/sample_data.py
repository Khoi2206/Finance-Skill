"""DỮ LIỆU MẪU cho mô hình Dự báo & Ngân sách Alta Group.

TOÀN BỘ số trong file này là ước lượng minh họa để mô hình chạy được —
KHÔNG phải số liệu thật của Alta. Đơn vị tiền: triệu đồng (trừ khi ghi khác).
Thay bằng: (1) CSV thực tế từ `afi export-pl`, (2) CSV số dư đầu kỳ,
(3) CSV giả định BU (`--assumptions`) — xem README.md.
"""
from __future__ import annotations

import random

SEASON = {1: 0.95, 2: 0.70, 3: 1.00, 4: 1.00, 5: 1.02, 6: 1.00,
          7: 0.98, 8: 1.00, 9: 1.02, 10: 1.05, 11: 1.08, 12: 1.15}

OWN = {
    "gen": "Kế toán trưởng / CFO",
    "apl": "GĐ Alta Plastic",
    "ame": "GĐ Alta Media",
    "me": "Phụ trách cho thuê & dự án — Alta (Mẹ)",
    "hr": "Phòng Nhân sự",
    "fin": "Kế toán / CFO (hợp đồng vay)",
}

MEDIA_TYPES = [
    # code, tên, job/tháng, giá trị bq (tr/job), biên gộp, % ghi nhận trong tháng ký, % backlog ghi nhận/tháng, backlog 30/9
    ("LED", "Cho thuê màn hình LED", 6, 300, 0.35, 0.50, 0.50, 1800),
    ("BA", "Thiết bị, giải pháp", 3, 800, 0.20, 0.20, 0.30, 6000),
    ("TTB", "Cho thuê hệ thống đa phương tiện", 8, 120, 0.30, 0.60, 0.60, 600),
    ("DVK", "Dịch vụ, chia doanh thu", 4, 150, 0.40, 0.40, 0.40, 900),
    ("TKL", "Phần mềm, thiết kế", 5, 80, 0.55, 0.30, 0.35, 1200),
]

HEADCOUNT = [
    # key, công ty, tên nhóm, phân loại (641/642), BU, số người, lương bq (tr/người/tháng)
    ("hc_alta_sales", "ALTA", "Alta (Mẹ) — Kinh doanh", "641", "", 4, 18.0),
    ("hc_alta_admin", "ALTA", "Alta (Mẹ) — Quản lý & văn phòng", "642", "", 12, 22.0),
    ("hc_apl_sales", "APL", "Plastic — Kinh doanh", "641", "", 10, 16.0),
    ("hc_apl_admin", "APL", "Plastic — Quản lý & văn phòng", "642", "", 12, 18.0),
    ("hc_apl_3d", "APL", "Plastic — BU In 3D (trực tiếp)", "642", "3D", 6, 15.0),
    ("hc_ame_sales", "AME", "Media — Kinh doanh", "641", "", 8, 20.0),
    ("hc_ame_admin", "AME", "Media — Quản lý & văn phòng", "642", "", 10, 20.0),
]

OPEX = [
    # key, công ty, diễn giải, phân loại, kiểu (fixed: tr/tháng | pct: % doanh thu ngoài), giá trị, BU
    ("alta_ox_mkt", "ALTA", "Marketing, môi giới cho thuê", "641", "fixed", 60, ""),
    ("alta_ox_util", "ALTA", "Điện, nước, văn phòng", "642", "fixed", 120, ""),
    ("alta_ox_service", "ALTA", "Dịch vụ thuê ngoài (kiểm toán, pháp lý, tư vấn)", "642", "fixed", 90, ""),
    ("alta_ox_other", "ALTA", "Chi phí QLDN khác", "642", "fixed", 80, ""),
    ("apl_ox_freight", "APL", "Vận chuyển, giao hàng", "641", "pct", 0.025, ""),
    ("apl_ox_mkt", "APL", "Marketing, hoa hồng bán hàng", "641", "fixed", 70, ""),
    ("apl_ox_admin", "APL", "Điện, nước, văn phòng, phí ngân hàng", "642", "fixed", 150, ""),
    ("apl_ox_3d", "APL", "BU In 3D — chi phí trực tiếp (vật tư phụ, phần mềm, marketing)", "642", "fixed", 60, "3D"),
    ("apl_ox_other", "APL", "Chi phí QLDN khác", "642", "fixed", 90, ""),
    ("ame_ox_mkt", "AME", "Marketing, sự kiện", "641", "fixed", 80, ""),
    ("ame_ox_comm", "AME", "Hoa hồng môi giới dự án", "641", "pct", 0.015, ""),
    ("ame_ox_admin", "AME", "Điện, nước, văn phòng", "642", "fixed", 90, ""),
    ("ame_ox_other", "AME", "Chi phí QLDN khác", "642", "fixed", 70, ""),
]


def _A(key, label, unit, sec, kind="m", base=0.0, growth=0.0, season=False, events=None,
       note="", rnd=None):
    return dict(key=key, label=label, unit=unit, sec=sec, kind=kind, base=base, growth=growth,
                season=season, events=events or {}, note=note, rnd=rnd)


def assumption_specs(budget_year: int) -> list[dict]:
    """Danh sách giả định (thứ tự = thứ tự trên sheet Assumptions)."""
    B = budget_year
    S = []
    # ---- Chung
    S += [
        _A("budget_year", "Năm ngân sách", "năm", "gen", "D", B, note="Cấu trúc mô hình"),
        _A("unit_vnd", "Quy đổi: số đồng trong 1 đơn vị mô hình", "đồng", "gen", "D", 1_000_000,
           note="Mô hình tính bằng triệu đồng; CSV thực tế tính bằng đồng"),
        _A("tax_rate", "Thuế suất TNDN", "%", "gen", "D", 0.20,
           note="20% phổ thông — xác nhận ưu đãi/chuyển lỗ từng công ty"),
        _A("bhxh_rate", "BHXH + BHYT + BHTN phần doanh nghiệp", "%", "gen", "D", 0.215,
           note="21,5% = 17,5% + 3% + 1% — CẦN XÁC NHẬN với kế toán (chưa gồm KPCĐ 2%, trần lương đóng)"),
        _A("raise_rate", "Tăng lương bình quân năm ngân sách", "%", "hr", "D", 0.06),
        _A("bonus_months", "Thưởng (số tháng lương / năm, trích đều)", "tháng", "hr", "D", 1.0),
        _A("deposit_rate", "Lãi suất tiền gửi không kỳ hạn/ngắn hạn", "%/năm", "fin", "D", 0.03),
        _A("ic_days", "Số ngày thanh toán công nợ nội bộ", "ngày", "gen", "D", 30),
    ]
    # ---- Plastic
    S += [
        _A("apl_vol_ext", "Bao bì — sản lượng bán ngoài tập đoàn", "tấn/tháng", "apl", base=180, growth=0.08, season=True),
        _A("apl_vol_ic", "Bao bì — sản lượng bán cho Alta (Mẹ)", "tấn/tháng", "apl", base=20, growth=0.05, season=True),
        _A("apl_price_ext", "Bao bì — giá bán bình quân (ngoài)", "đồng/kg", "apl", base=46_000, growth=0.02),
        _A("apl_price_ic", "Bao bì — giá bán nội bộ cho Mẹ", "đồng/kg", "apl", base=42_000, growth=0.02,
           note="Cần chính sách giá chuyển nhượng (giao dịch liên kết)"),
        _A("resin_price", "Giá hạt nhựa mua vào bình quân", "đồng/kg", "apl", base=30_000, growth=0.02),
        _A("apl_resin_norm", "Định mức hạt nhựa / kg thành phẩm", "kg/kg", "apl", "D", 1.04),
        _A("apl_conv_cost", "Chi phí chuyển đổi (điện, NC trực tiếp, phụ liệu; chưa gồm khấu hao)", "đồng/kg", "apl",
           base=5_000, growth=0.04),
        _A("apl_scrap_rate", "Tỷ lệ phế liệu thu hồi / sản lượng", "%", "apl", "D", 0.03),
        _A("apl_scrap_price", "Giá bán phế liệu", "đồng/kg", "apl", base=8_000),
        _A("apl_resin_vol", "Thương mại hạt nhựa — sản lượng bán", "tấn/tháng", "apl", base=60, growth=0.05, season=True),
        _A("apl_resin_markup", "Thương mại hạt nhựa — biên cộng trên giá mua", "%", "apl", "D", 0.04),
        _A("p3d_orders", "In 3D — số đơn hàng", "đơn/tháng", "apl", base=40, growth=0.15, season=True, rnd=0),
        _A("p3d_value", "In 3D — giá trị bình quân/đơn", "triệu/đơn", "apl", base=25, growth=0.03),
        _A("p3d_gm", "In 3D — biên lợi nhuận gộp", "%", "apl", "D", 0.45),
        _A("apl_dso", "Plastic — số ngày phải thu", "ngày", "apl", "D", 45),
        _A("apl_dio", "Plastic — số ngày tồn kho", "ngày", "apl", "D", 40),
        _A("apl_dpo", "Plastic — số ngày phải trả", "ngày", "apl", "D", 35),
    ]
    # ---- Media
    for code, name, jobs, val, gm, inm, burn, bl in MEDIA_TYPES:
        c = code.lower()
        S += [
            _A(f"ame_{c}_jobs", f"{code} — số job ký mới ({name})", "job/tháng", "ame", base=jobs, growth=0.10,
               season=True),
            _A(f"ame_{c}_value", f"{code} — giá trị bình quân/job", "triệu/job", "ame", base=val, growth=0.03),
            _A(f"ame_{c}_gm", f"{code} — biên lợi nhuận gộp", "%", "ame", "D", gm),
            _A(f"ame_{c}_inm", f"{code} — % giá trị ghi nhận ngay trong tháng ký", "%", "ame", "D", inm),
            _A(f"ame_{c}_burn", f"{code} — % backlog đầu kỳ ghi nhận mỗi tháng", "%", "ame", "D", burn),
            _A(f"ame_{c}_bl0", f"{code} — backlog chưa ghi nhận tại ngày đầu kỳ", "triệu", "ame", "D", bl,
               note="Lấy từ sổ theo dõi hợp đồng/mã vụ việc"),
        ]
    S += [
        _A("ame_dso", "Media — số ngày phải thu", "ngày", "ame", "D", 60),
        _A("ame_dio", "Media — số ngày tồn kho/chi phí dở dang", "ngày", "ame", "D", 5),
        _A("ame_dpo", "Media — số ngày phải trả", "ngày", "ame", "D", 45),
    ]
    # ---- Mẹ
    S += [
        _A("me_area_total", "Tổng diện tích cho thuê được", "m²", "me", base=12_000),
        _A("me_area_apl", "Diện tích cho Alta Plastic thuê (nội bộ)", "m²", "me", base=3_000),
        _A("me_area_ame", "Diện tích cho Alta Media thuê (nội bộ)", "m²", "me", base=500),
        _A("me_occ", "Tỷ lệ lấp đầy phần diện tích cho bên ngoài", "%", "me", base=0.85, growth=0.0235),
        _A("me_rent_ext", "Đơn giá thuê bình quân (bên ngoài)", "đồng/m²/tháng", "me", base=180_000, growth=0.05),
        _A("me_rent_ic", "Đơn giá thuê nội bộ", "đồng/m²/tháng", "me", base=150_000, growth=0.05,
           note="Cần chính sách giá chuyển nhượng"),
        _A("me_opcost", "Chi phí vận hành mặt bằng / m² tổng", "đồng/m²/tháng", "me", base=25_000, growth=0.04),
        _A("me_tech_rev", "Thiết bị & dự án công nghệ — doanh thu", "triệu/tháng", "me", base=1_500, growth=0.05,
           season=True),
        _A("me_tech_gm", "Thiết bị & dự án công nghệ — biên gộp", "%", "me", "D", 0.18),
        _A("me_bag_price", "Bán lại túi bao bì — giá bán bình quân", "đồng/kg", "me", base=47_000, growth=0.02),
        _A("alta_dso", "Mẹ — số ngày phải thu", "ngày", "me", "D", 30),
        _A("alta_dio", "Mẹ — số ngày tồn kho", "ngày", "me", "D", 10),
        _A("alta_dpo", "Mẹ — số ngày phải trả", "ngày", "me", "D", 30),
    ]
    # ---- Nhân sự
    for key, co, name, cls, bu, n, sal in HEADCOUNT:
        ev = {(B, m): n + 2 for m in range(3, 13)} if key == "hc_apl_sales" else {}
        if key == "hc_ame_sales":
            ev = {(B, m): n + 1 for m in range(4, 13)}
        S += [
            _A(f"{key}_n", f"{name} — số người", "người", "hr", base=n, events=ev, rnd=0),
            _A(f"{key}_sal", f"{name} — lương bình quân hiện tại", "triệu/người/tháng", "hr", "D", sal),
        ]
    # ---- Chi phí hoạt động
    for key, co, name, cls, kind, val, bu in OPEX:
        if kind == "pct":
            S.append(_A(key, f"{name} ({co})", "% doanh thu ngoài", "opex", "D", val))
        else:
            S.append(_A(key, f"{name} ({co})", "triệu/tháng", "opex", base=val, growth=0.04))
    # ---- Capex & khấu hao
    S += [
        _A("capex_alta", "Capex Alta (Mẹ) — cải tạo mặt bằng", "triệu", "fin", base=200),
        _A("capex_apl", "Capex Plastic — bảo trì + máy mới", "triệu", "fin", base=300, events={(B, 4): 6_300},
           note="MẪU: máy thổi màng mới 6.000tr tháng 4"),
        _A("capex_ame", "Capex Media — màn hình LED, thiết bị", "triệu", "fin", base=150, events={(B, 3): 1_650}),
        _A("life_alta", "Thời gian khấu hao tài sản mới — Mẹ", "năm", "fin", "D", 10),
        _A("life_apl", "Thời gian khấu hao tài sản mới — Plastic", "năm", "fin", "D", 8),
        _A("life_ame", "Thời gian khấu hao tài sản mới — Media", "năm", "fin", "D", 5),
        _A("dep_exist_alta", "Khấu hao tài sản hiện có — Mẹ", "triệu/tháng", "fin", base=400,
           note="Theo bảng tính khấu hao TSCĐ (FAST)"),
        _A("dep_exist_apl", "Khấu hao tài sản hiện có — Plastic", "triệu/tháng", "fin", base=550),
        _A("dep_exist_ame", "Khấu hao tài sản hiện có — Media", "triệu/tháng", "fin", base=350),
    ]
    # ---- Vay
    S += [
        _A("draw_alta", "Giải ngân vay ngân hàng — Mẹ", "triệu", "fin", base=0),
        _A("repay_alta", "Trả gốc vay ngân hàng — Mẹ", "triệu", "fin", base=500),
        _A("rate_alta", "Lãi suất vay bình quân — Mẹ", "%/năm", "fin", base=0.09),
        _A("draw_apl", "Giải ngân vay ngân hàng — Plastic", "triệu", "fin", base=0, events={(B, 4): 6_000},
           note="MẪU: vay trung hạn tài trợ máy mới"),
        _A("repay_apl", "Trả gốc vay ngân hàng — Plastic", "triệu", "fin", base=300),
        _A("rate_apl", "Lãi suất vay bình quân — Plastic", "%/năm", "fin", base=0.085),
        _A("draw_ame", "Giải ngân vay ngân hàng — Media", "triệu", "fin", base=0),
        _A("repay_ame", "Trả gốc vay ngân hàng — Media", "triệu", "fin", base=150),
        _A("rate_ame", "Lãi suất vay bình quân — Media", "%/năm", "fin", base=0.095),
        _A("icl_draw", "Mẹ cho Media vay thêm (nội bộ)", "triệu", "fin", base=0, events={(B, 3): 2_000}),
        _A("icl_repay", "Media trả gốc vay nội bộ cho Mẹ", "triệu", "fin", base=0),
        _A("icl_rate", "Lãi suất vay nội bộ Mẹ → Media", "%/năm", "fin", base=0.07,
           note="Cần hợp đồng vay & chính sách lãi suất giao dịch liên kết"),
    ]
    # ---- Khác
    for co, nm in (("alta", "Mẹ"), ("apl", "Plastic"), ("ame", "Media")):
        S += [
            _A(f"oth_inc_{co}", f"Thu nhập khác — {nm}", "triệu", "gen", base=0),
            _A(f"oth_exp_{co}", f"Chi phí khác — {nm}", "triệu", "gen", base=0),
        ]
    S.append(_A("div_alta", "Cổ tức Mẹ trả cổ đông (tiền)", "triệu", "fin", base=0,
                note="Cổ tức con → Mẹ chưa mô hình (cần loại trừ nội bộ nếu có)"))
    return S


def default_value(spec: dict, year: int, month: int, budget_year: int):
    if spec["kind"] == "D":
        return spec["base"]
    if (year, month) in spec["events"]:
        return spec["events"][(year, month)]
    v = spec["base"] * (1 + spec["growth"] if year == budget_year else 1)
    if spec["season"]:
        v *= SEASON[month]
    if spec["rnd"] is not None:
        return round(v, spec["rnd"])
    return round(v, 4) if abs(v) < 10 else round(v)


# ---------------------------------------------------------------- số dư đầu kỳ (triệu đồng)
OPENING_BS = {
    # company: {line: amount}; re (LNST chưa phân phối) tính cân bằng
    "ALTA": dict(cash=8_000, ar=3_700, inv=800, invest_sub=40_000, oth_asset=2_000, fa=60_000,
                 ap=1_500, tax_pay=300, loan_bank=30_000, oth_liab=1_500, capital=80_000),
    "APL": dict(cash=5_000, ar=15_700, inv=13_000, oth_asset=1_500, fa=40_000,
                ap=11_400, tax_pay=400, loan_bank=25_000, oth_liab=1_000, capital=30_000),
    "AME": dict(cash=3_000, ar=12_300, inv=700, oth_asset=1_000, fa=12_000,
                ap=6_300, tax_pay=200, loan_bank=8_000, oth_liab=800, capital=10_000),
}
OPENING_IC = dict(ic_bag=840, ic_rent_apl=450, ic_rent_ame=105, ic_loan=5_000)


def opening_bs() -> tuple[dict, dict]:
    bs = {k: dict(v) for k, v in OPENING_BS.items()}
    ic = dict(OPENING_IC)
    ar_ic = {"ALTA": ic["ic_rent_apl"] + ic["ic_rent_ame"], "APL": ic["ic_bag"], "AME": 0}
    ap_ic = {"ALTA": ic["ic_bag"], "APL": ic["ic_rent_apl"], "AME": ic["ic_rent_ame"]}
    loan_a = {"ALTA": ic["ic_loan"], "APL": 0, "AME": 0}
    loan_l = {"ALTA": 0, "APL": 0, "AME": ic["ic_loan"]}
    for co, d in bs.items():
        assets = d["cash"] + d["ar"] + ar_ic[co] + d["inv"] + loan_a[co] + d.get("invest_sub", 0) + d["fa"] + d["oth_asset"]
        liab = d["ap"] + ap_ic[co] + d["tax_pay"] + d["loan_bank"] + loan_l[co] + d["oth_liab"]
        d["re"] = assets - liab - d["capital"]
    return bs, ic


# ---------------------------------------------------------------- thực tế mẫu 9T (đồng)
LEVELS = {  # triệu đồng/tháng, mức bình quân minh họa
    "ALTA": dict(net_revenue=4_200, cogs=2_750, selling_expenses=160, admin_expenses=640, finance_income=45,
                 finance_expense=230, other_income=10, other_expense=5, depreciation=400, ic_revenue=500,
                 ic_interest=29),
    "APL": dict(net_revenue=11_300, cogs=9_800, selling_expenses=600, admin_expenses=1_150, finance_income=10,
                finance_expense=180, other_income=15, other_expense=10, depreciation=550, ic_revenue=780),
    "AME": dict(net_revenue=5_900, cogs=4_150, selling_expenses=420, admin_expenses=550, finance_income=5,
                finance_expense=95, other_income=0, other_expense=0, depreciation=350),
}


def sample_actuals(year: int, through_month: int) -> list[dict]:
    rnd = random.Random(20260930)
    rows = []
    for co, lv in LEVELS.items():
        for m in range(1, through_month + 1):
            s = SEASON[m] * 0.93  # năm hiện tại thấp hơn mức Q4 dự báo một chút
            noise = {k: rnd.uniform(0.94, 1.06) for k in lv}
            vals = {}
            for line, v in lv.items():
                seasonal = line in ("net_revenue", "cogs", "selling_expenses", "ic_revenue")
                vals[line] = v * (s if seasonal else 1.0) * noise[line]
            pbt = (vals["net_revenue"] - vals["cogs"] - vals["selling_expenses"] - vals["admin_expenses"]
                   + vals["finance_income"] - vals["finance_expense"] + vals["other_income"] - vals["other_expense"])
            vals["income_tax"] = max(0.0, pbt) * 0.20
            for line, v in vals.items():
                rows.append(dict(company=co, month=f"{year}-{m:02d}", line=line, amount=round(v * 1_000_000),
                                 source="DỮ LIỆU MẪU"))
    return rows
