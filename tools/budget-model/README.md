# Công cụ #1 — Mô hình Dự báo cả năm & Ngân sách theo driver (Alta Group)

Script Python (openpyxl) sinh **một file Excel có công thức thật** cho 3 pháp nhân Alta (Mẹ 0301420079, Plastic 0312414944, Media 0305904835): driver theo BU → nhân sự, chi phí, capex, vay → KQKD/CĐKT/LCTT theo tháng từng công ty → loại trừ nội bộ → hợp nhất → dự báo cả năm (thực tế + dự báo) → kiểm tra.
Quy trình dùng: skill [`core/budget-model/SKILL.md`](../../core/budget-model/SKILL.md).

> File mẫu `output/Alta_Forecast2026_Budget2027_MAU.xlsx` dùng **DỮ LIỆU MẪU** (số minh họa, không phải số thật của Alta). Mọi sheet có dòng cảnh báo đỏ ở ô A2 cho đến khi thay đủ số thực tế, số dư đầu kỳ và giả định BU.

## Chạy
```bash
pip install openpyxl            # bắt buộc; LibreOffice để tính lại (tùy chọn), pycel cho test khi không có LibreOffice
cd tools/budget-model
python build_budget_model.py --recalc                      # dữ liệu mẫu → output/…_MAU.xlsx (có sẵn giá trị đã tính)
python build_budget_model.py --scenario Downside --out output/downside.xlsx
```
Với số thật (rolling forecast sau khi đóng sổ 9T/2026):
```bash
afi export-pl --year 2026 --out ../../data/actuals_2026.csv        # trong alta-finance-intelligence/
python build_budget_model.py \
  --actuals ../../data/actuals_2026.csv \
  --opening-bs ../../data/opening_bs_2026-09.csv \
  --assumptions ../../data/gia_dinh_2027_v1.csv \
  --actual-through 2026-09 --budget-year 2027 --recalc \
  --out output/Alta_FC2026_NS2027_v1.xlsx
```
Không commit file có số thật lên repo công khai; để trong thư mục dữ liệu nội bộ.

## Đầu vào (CSV UTF-8, có dòng tiêu đề) — mẫu trong `templates/`
| File | Cột | Ghi chú |
|---|---|---|
| `actuals` | `company,month,line,amount[,source]` | Đúng output `afi export-pl`. `company` = `ALTA`/`APL`/`AME`; `month` = `YYYY-MM`; `amount` **đồng**. `line` ∈ `net_revenue, cogs, selling_expenses, admin_expenses, finance_income, finance_expense, other_income, other_expense, income_tax, depreciation` (+ tùy chọn `ic_revenue`, `ic_interest` để hợp nhất số thực tế theo P5). Dòng ngoài kỳ thực tế, dòng dẫn xuất (`gross_profit`…) hoặc công ty lạ bị bỏ qua và báo số dòng. |
| `opening_bs` | `company,line,amount` | Số dư cuối tháng thực tế cuối cùng (đồng). `line` ∈ `cash, ar, inv, invest_sub, oth_asset, fa, ap, tax_pay, loan_bank, oth_liab, capital, re` và số dư nội bộ `ic_bag` (Plastic phải thu Mẹ), `ic_rent_apl`, `ic_rent_ame` (Mẹ phải thu), `ic_loan` (Mẹ cho Media vay). Phải tự cân — Checks báo nếu lệch. |
| `assumptions` | `key,period,value[,source]` | `period` = `YYYY-MM` hoặc `D` (giá trị cố định). Khóa nào không có dùng giá trị MẪU. Ghi `source` = người cung cấp + ngày; còn chữ "MẪU" thì vẫn bị tính là mẫu. Xuất toàn bộ khóa hiện hành: `--dump-assumptions file.csv`. |

## Các sheet
README · **Scenarios** (ô C5 chọn Base/Target/Downside; KPI hợp nhất) · **Checks** (ô D6 = số kiểm tra lỗi, phải = 0; mục 5 là cảnh báo tiền âm/lỗ) · Assumptions · Drivers_Plastic · Drivers_Media · Drivers_Me · Headcount · Opex · Capex · Debt · FS_Me · FS_Plastic · FS_Media · IC_Elims · Consolidated · Forecast_FY2026 · Actuals_Input.

Driver chính:
- **Plastic**: tấn × giá bán/kg; giá vốn = (giá hạt nhựa/kg × định mức + chi phí chuyển đổi/kg) × tấn; thương mại hạt nhựa = giá mua × (1 + biên cộng); phế liệu = tỷ lệ × sản lượng; **In 3D tách riêng** (đơn × giá trị × biên; đóng góp BU = lãi gộp − chi phí trực tiếp; không phân bổ chi phí chung — P11).
- **Media** (LED/BA/TTB/DVK/TKL): job ký mới × giá trị bq → backlog; doanh thu = backlog đầu kỳ × % ghi nhận/tháng + ký mới × % ghi nhận ngay; giá vốn = doanh thu × (1 − biên).
- **Mẹ**: (diện tích − diện tích nội bộ) × lấp đầy × đơn giá; cho Plastic/Media thuê theo giá nội bộ; dự án công nghệ × biên; bán lại túi mua từ Plastic.
- **Nhân sự**: người × lương × (1 + 21,5% BHXH phần DN *[cần xác nhận]* + thưởng/12); tăng lương từ T1 năm ngân sách.
- Nội bộ: Plastic bán túi cho Mẹ · Mẹ cho Plastic/Media thuê · Mẹ cho Media vay (lãi) · đầu tư vào công ty con vs vốn góp con.

## Kiểm tra (tất cả = 0, sai số ≤ 1.000 đ)
CĐKT cân (3 công ty + hợp nhất, cả số dư đầu kỳ) · tiền CĐKT = tiền cuối LCTT · từng cặp nội bộ bên bán = bên mua · tổng loại trừ thu = chi · phải thu = phải trả nội bộ · cho vay = đi vay nội bộ · dòng tiền vay nội bộ triệt tiêu · LNST hợp nhất = tổng LNST · doanh thu mảng = doanh thu hợp nhất · Forecast khớp BCTC từng tháng dự báo · tổng CSV thực tế = tổng đã ánh xạ · ô kịch bản hợp lệ.

## Test
```bash
cd tools/budget-model && python -m pytest -q tests
BUDGET_MODEL_EVALUATOR=pycel python -m pytest -q tests   # ép dùng pycel thay LibreOffice
```
Test sinh file, kiểm tra mọi ô tính toán là công thức, ô nhập màu xanh có nguồn, tính lại bằng LibreOffice headless (hoặc pycel) và mọi ô Checks = 0 cho cả 3 kịch bản; kiểm tra nhập CSV định dạng `afi`, xuất/nạp lại giả định, và cuộn sang quý sau (`--actual-through 2026-12`).

## Hạn chế (đọc trước khi trình)
- Không tính VAT trong công nợ; vốn lưu động theo số ngày × doanh thu/giá vốn tháng ÷ 30.
- Thuế TNDN = thuế suất × LNTT từng tháng, nộp T1/T4/T7/T10; chưa có ưu đãi, chuyển lỗ, chi phí không được trừ.
- Lãi vay trên dư nợ đầu tháng; không có hạn mức tự động khi thiếu tiền — xem cảnh báo "tiền âm" ở Checks mục 5.
- Mẹ bán hết túi trong tháng → không có lãi chưa thực hiện trong tồn kho (khớp P5 hiện hành). Hợp nhất giả định sở hữu 100%; chưa có NCI, lợi thế thương mại, cổ tức con → Mẹ.
- Tháng dự báo trong Forecast dồn toàn bộ khấu hao vào giá vốn để so được với dòng `cogs` của `afi`.
- Số thực tế 9T chỉ có KQKD (theo `afi`); CĐKT/LCTT thực tế 9T chưa đưa vào — số dư đầu kỳ nhập riêng.
