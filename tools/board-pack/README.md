# Công cụ #4 — Bộ tạo báo cáo quản trị tháng / báo cáo HĐQT (PPTX)

Từ số liệu đã nạp vào warehouse của `alta-finance-intelligence`, tự dựng deck PowerPoint theo cấu trúc
`core/board-management-pack`. Chạy lại được mỗi tháng/quý.

## Cách dùng
```bash
pip install -e "alta-finance-intelligence[dev]" python-pptx      # một lần
# hằng tháng, sau khi afi ingest + afi reconcile (+ CFO duyệt trong data/approvals.yaml):
afi boardpack --month 2026-10 --plan data/plan_2026.csv            # báo cáo tháng
afi boardpack --month 2026-09 --mode ytd --plan data/plan_2026.csv # lũy kế 9T (báo cáo quý)
# hoặc chạy script trực tiếp:
python tools/board-pack/build_board_pack.py --month 2026-10 --data alta-finance-intelligence/data --plan plan.csv
python tools/board-pack/build_board_pack.py --sample                # deck MẪU từ dữ liệu tổng hợp
```
Tham số: `--threshold-pct 0.10 --threshold-amount 500000000` (ngưỡng giải trình), `--out file.pptx`.
Mặc định ghi vào `tools/board-pack/output/BoardPack_<tháng>[_LK].pptx`.

**File kế hoạch (tùy chọn)** — CSV `company,month,line,amount` (VND, chi phí là số dương):
`company` ∈ ALTA/APL/AME; `line` ∈ `net_revenue, cogs, selling_expenses, admin_expenses, finance_income,
finance_expense, interest_expense, other_income, other_expense, income_tax, depreciation`. Dòng dẫn xuất
(gross_profit, profit_before_tax, net_profit, ebitda) tự tính bằng công thức trong `account_map.yaml`; có thể ghi
thẳng để ghi đè. Ví dụ: `sample/ke_hoach_mau_2026.csv` (mẫu, không phải kế hoạch thật).

## Deck gồm
| Trang | Nội dung |
|---|---|
| Bìa | Kỳ, trạng thái số liệu, nhãn **DỮ LIỆU MẪU** khi `--sample` |
| Tóm tắt điều hành | 3 con số chính (doanh thu, EBITDA, tiền), Xanh/Vàng/Đỏ, bảng theo pháp nhân, quyết định cần HĐQT, 3 rủi ro hàng đầu |
| Dashboard KPI | Thực tế · KH · Cùng kỳ · Δ, xu hướng 6 tháng (sparkline): doanh thu, DT ngoài tập đoàn, LN gộp & biên, EBITDA & biên, LNST, dòng tiền HĐKD, tiền, nợ vay ròng/EBITDA, DSO/DIO/DPO |
| KQKD hợp nhất | Bảng A vs KH vs cùng kỳ + biểu đồ cột |
| Giải trình biến động | Cái gì → Tại sao (từ dữ liệu) → Một lần/lặp lại → Hành động `[CFO điền]` |
| Cầu nối EBITDA | Waterfall native: KH (hoặc cùng kỳ) → doanh thu, giá vốn, CPBH, CPQL, khấu hao, tài chính & khác → thực tế |
| Alta (Mẹ), Alta Plastic, Alta Media | Mỗi pháp nhân 1 trang: KPI, 6 tháng, khách hàng lớn, vấn đề & hành động |
| Tiền & vốn lưu động | Số dư từ CĐPS (cuối kỳ, đầu tháng, đầu năm, cùng kỳ), dòng tiền theo hoạt động, tiền theo pháp nhân |
| Rủi ro | Tín hiệu rủi ro rút từ dữ liệu theo quy tắc cố định; khả năng/tác động/biện pháp để CFO điền |
| Đề xuất nghị quyết | Dự thảo nội dung biểu quyết |
| Phụ lục A1–A4 | KQKD từng pháp nhân · bảng biến động đầy đủ · trạng thái dữ liệu theo tháng · phương pháp |

## Quy tắc đã cài
- **Số**: tỷ đồng, 1 chữ số thập phân, số âm trong ngoặc, dấu phẩy thập phân; chi phí hiển thị âm trong bảng KQKD; Δ dương = thuận lợi.
- **Action title**: tiêu đề mỗi trang là câu kết luận sinh từ số (ví dụ "EBITDA tháng 10/2026 8,9 tỷ, thấp hơn kế hoạch 1,4 tỷ; yếu tố lớn nhất: doanh thu thuần (giảm 1,0 tỷ)").
- **Trạng thái dữ liệu** mỗi trang = kết quả `afi reconcile` (`run_controls` + `period_status` + `data/approvals.yaml`) cho các pháp nhân × tháng của trang: APPROVED / RECONCILED / **SƠ BỘ** (có kiểm soát FAIL hoặc thiếu dữ liệu). Hợp nhất lấy mức yếu nhất.
- **Bình luận biến động**: chỉ khi |Δ| > 10% **và** > 500 triệu. "Tại sao" chỉ gồm dữ kiện: tách theo dòng KQKD, tách giá vốn theo doanh thu và tỷ lệ giá vốn, khách hàng/tài khoản đóng góp lớn nhất (qua lineage), dòng Excel gốc lớn nhất. Không suy đoán nguyên nhân; hành động để trống cho CFO.
- **Xanh/Vàng/Đỏ**: EBITDA ≥ 95% KH (hoặc cùng kỳ nếu chưa có KH) → Xanh; 85–95% → Vàng; < 85% hoặc LNST âm → Đỏ.
- **Biểu đồ native** PowerPoint (sửa số qua *Edit Data*), không dùng ảnh.
- **Speaker notes** mỗi trang: từng số → bảng nguồn, file Excel + dòng chính (lineage), lệnh `afi pl … --lineage …` để kiểm tra.

## Nguồn số liệu
`Warehouse.pl()` (= `afi pl`, `mart_pl_monthly`) cộng theo tháng · lãi vay theo P3 và EBITDA theo P4 · doanh thu nội bộ theo MST (P5) ·
số dư `fact_tb` (TK lá, CĐPS kết thúc cuối tháng) · dòng tiền `fact_gl_lines` TK 111/112/113 theo `cash_flow_map.yaml` (P7) · DSO/DIO/DPO theo P8.
Các chính sách đều đang `[PROPOSED POLICY]` (`docs/accounting_policies.md`).

## Test
```bash
cd tools/board-pack && python -m pytest -q          # 16 test: mở deck, đủ trang, số khớp afi pl, ytd, notes, ngưỡng, SƠ BỘ
cd alta-finance-intelligence && python -m pytest -q # test pipeline cũ
```
Dữ liệu test: `alta-finance-intelligence/tests/fixtures.py · group_dataset()` — 3 pháp nhân × 22 tháng (GL, CĐPS, bảng kê bán hàng) tổng hợp, mọi kiểm soát PASS.

## Hạn chế
- Số hợp nhất là **cộng gộp**, chưa loại trừ nội bộ (P5 chưa có trong pipeline); trang KQKD ghi rõ doanh thu nội bộ.
- Chưa có sản lượng → cầu nối EBITDA theo dòng KQKD, chưa tách giá/lượng/cơ cấu/giá hạt nhựa (cần Phase 4, công cụ #15).
- Dòng tiền 13 tuần (công cụ #3), covenant (#5), sáng kiến chiến lược & capex, dự báo cả năm: chưa có nguồn → để ô `[CFO điền]` hoặc ghi chú.
- Khách hàng lấy theo "Tên khách" trên sổ cái (chưa có danh mục đối tượng — Phase 1).
- Kế hoạch chỉ ở cấp dòng × tháng, nên biến động so với KH không tách được theo khách hàng (bình luận ghi rõ, và dẫn số so với cùng kỳ).
- Chưa chạy trên file FAST thật của Alta.
