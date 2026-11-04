---
name: budget-model
description: Chạy và cập nhật mô hình Excel Dự báo cả năm & Ngân sách theo driver của Alta Group (Mẹ, Plastic, Media) do script tools/budget-model sinh ra — 3 kịch bản, KQKD/CĐKT/LCTT theo tháng, loại trừ nội bộ, hợp nhất, kiểm tra. Dùng khi lập ngân sách năm sau, cập nhật rolling forecast hằng quý sau khi đóng sổ, chạy kịch bản Base/Target/Downside, hoặc chuẩn bị số ngân sách/dự báo trình CEO, HĐQT.
---

# Mô hình Dự báo & Ngân sách theo driver — Alta Group

Công cụ: `tools/budget-model/build_budget_model.py` (chi tiết đầu vào, sheet, hạn chế: `tools/budget-model/README.md`).
Khung phương pháp: `strategic-plan-budget` (lịch, kiến trúc driver), `group-consolidation-ic` (loại trừ nội bộ), `docs/accounting_policies.md` (P4 EBITDA, P5 hợp nhất, P10 sai số, P11 In 3D).

## 1. Khi nào dùng
| Thời điểm | Việc | Lệnh chính |
|---|---|---|
| Đầu tháng 11 | Bản v1 ngân sách năm sau: 9T thực tế + Q4 dự báo + 12 tháng ngân sách | `--actual-through 2026-09` |
| Tháng 11 | v2: thu giả định BU (công cụ #2), chạy 3 kịch bản, kiểm tra tiền & covenant | `--scenario Downside` |
| Sau đóng sổ mỗi quý | Rolling forecast: thay tháng dự báo bằng thực tế, dự báo phần còn lại | `--actual-through <tháng cuối quý>` |
| Bất kỳ lúc | Hỏi "nếu giá hạt nhựa +8% thì sao" | sửa Assumptions/Scenarios trong Excel |

Không dùng cho: dòng tiền 13 tuần (công cụ #3, theo tuần), định giá dự án capex (`investment-appraisal`), BCTC hợp nhất luật định (cần kiểm toán).

## 2. Chạy
```bash
cd tools/budget-model
python build_budget_model.py --recalc          # dữ liệu mẫu (để xem cấu trúc)
python build_budget_model.py --actuals <actuals.csv> --opening-bs <opening_bs.csv> \
  --assumptions <gia_dinh.csv> --actual-through 2026-09 --budget-year 2027 --recalc --out <file.xlsx>
```
- Số thực tế: `afi export-pl --year 2026 --out actuals.csv` (pipeline `alta-finance-intelligence/`, chỉ dùng tháng đã `RECONCILED`/`APPROVED`).
- Số dư đầu kỳ: từ CĐPS cuối tháng thực tế cuối cùng của từng công ty, theo `templates/opening_bs_template.csv`; số dư nội bộ (`ic_*`) lấy theo đối chiếu công nợ nội bộ đã khớp (P6).
- Giả định: `--dump-assumptions gia_dinh.csv` → gửi BU điền cột `value` và `source` (tên + ngày) → nạp lại bằng `--assumptions`.
- Luôn trả cho người dùng: đường dẫn file, kịch bản, số kiểm tra lỗi (Checks!D6), 3–5 con số chính (doanh thu, EBITDA, LNST, tiền cuối năm, nợ vay thuần/EBITDA), cảnh báo ở Checks mục 5, và những gì vẫn là MẪU.

## 3. Cập nhật rolling forecast hằng quý
1. Đóng sổ & đối chiếu quý trong pipeline (`afi reconcile`); CFO duyệt tháng trong `data/approvals.yaml`.
2. Xuất thực tế (`afi export-pl`) và CĐPS cuối quý → `opening_bs.csv`; đối chiếu công nợ nội bộ cuối quý.
3. Từ file Excel kỳ trước, lưu giả định đã sửa ra CSV (hoặc dùng CSV giả định đã có) — **sửa trực tiếp trong Excel sẽ mất khi sinh lại**; mọi thay đổi giả định phải nằm trong CSV có cột `source`.
4. Rà các giả định quý tới với BU: giá hạt nhựa, sản lượng, backlog Media (lấy từ sổ hợp đồng theo mã vụ việc), lấp đầy mặt bằng, kế hoạch tuyển, capex, giải ngân/trả nợ.
5. Sinh lại với `--actual-through` mới. Forecast_FY tự đổi số tháng thực tế/dự báo; khi `--actual-through` là tháng 12, file chuyển sang Forecast_FY năm ngân sách.
6. So với bản trước: chênh lệch doanh thu/EBITDA cả năm theo công ty, giải thích bằng driver (lượng, giá, giá hạt nhựa, cơ cấu, chi phí), không bằng "điều chỉnh".
7. Lưu phiên bản: `Alta_FC<năm>_NS<năm>_Q<quý>_v<n>.xlsx` + CSV đầu vào cùng thư mục nội bộ.

## 4. Kiểm tra trước khi trình CEO/HĐQT
**Bắt buộc (dừng nếu không đạt):**
- [ ] `Checks!D6 = 0` cho **cả 3 kịch bản** (chạy script với từng `--scenario` hoặc đổi Scenarios!C5 và tính lại).
- [ ] Ô A2 các sheet không còn "DỮ LIỆU MẪU" — hoặc ghi rõ trên slide phần nào còn là mẫu.
- [ ] Số thực tế lấy từ tháng đã đối chiếu/duyệt; README sheet ghi đúng file nguồn; "bỏ qua N dòng" đã được giải thích.
- [ ] Số dư đầu kỳ khớp CĐPS; phải thu/phải trả nội bộ đầu kỳ khớp đối chiếu P6.
- [ ] Tỷ lệ BHXH 21,5% và thuế suất TNDN đã được kế toán xác nhận (cột nguồn không còn "CẦN XÁC NHẬN").

**Chất lượng kế hoạch (theo `strategic-plan-budget` §4):**
- [ ] Mỗi mức tăng trưởng có driver (tấn, giá/kg, job, m², lấp đầy) — không có "+15% cho đẹp".
- [ ] Biên gộp, chi phí/doanh thu, số ngày vốn lưu động so với 9T thực tế: chênh > 3 điểm % phải có sáng kiến cụ thể.
- [ ] Checks mục 5: công ty nào có tháng tiền âm → đã có phương án vốn (hạn mức, giải ngân, giãn capex) và đưa vào Debt.
- [ ] Downside: vẫn trả được nợ gốc & lãi; covenant (Nợ vay/EBITDA, DSCR) còn ≥ 15% dư địa — lấy điều khoản từ hợp đồng vay.
- [ ] In 3D trình bày bằng "đóng góp BU", không phân bổ chi phí chung khi chưa có tiêu thức được duyệt (P11).
- [ ] Giá nội bộ (túi Plastic → Mẹ, thuê mặt bằng, lãi vay Mẹ → Media) có căn cứ giao dịch liên kết.
- [ ] Nêu hạn chế mô hình (không VAT, thuế đơn giản, sở hữu 100%, không có lãi chưa thực hiện) trên phụ lục.

## 5. Đầu ra trình bày
- Bảng 1 trang: Thực hiện 2026 (9T + Q4) vs Ngân sách 2027 theo công ty & hợp nhất (sheet Forecast_FY2026, cột P–R).
- 3 kịch bản: doanh thu, EBITDA, LNST, tiền cuối năm, nợ vay thuần/EBITDA (Scenarios, phần KPI).
- Cầu nối EBITDA 2026 → 2027 theo driver; capex & nguồn vốn; rủi ro & trigger kích hoạt kế hoạch dự phòng.
- Dựng slide bằng `board-management-pack` / skill `pptx`; số trên slide phải trích từ file đã đạt Checks.

## 6. Mở rộng mô hình
Thêm BU/driver/khoản vay: sửa `sample_data.py` (giả định mặc định) và hàm `build_*` tương ứng trong `build_budget_model.py`; mỗi dòng mới phải có nguồn/ghi chú và đi qua ít nhất một kiểm tra. Chạy `python -m pytest -q tests` trước khi commit.
