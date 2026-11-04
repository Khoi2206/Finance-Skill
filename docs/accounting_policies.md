# Chính sách tính chỉ số quản trị — bản nháp chờ duyệt

**Trạng thái:** `[PROPOSED POLICY]` · Phiên bản `2026-11-04.1` · Áp dụng cho: dashboard (`dashboard/`) và pipeline (`alta-finance-intelligence/config/*.yaml`).
Mỗi chính sách chỉ có hiệu lực khi có chữ ký ở cột “Duyệt”. Khi sửa, tăng phiên bản trong file YAML tương ứng.

| # | Chính sách | Quy tắc đề xuất | Cấu hình | Duyệt (tên, ngày) |
|---|---|---|---|---|
| P1 | Bút toán kết chuyển | Loại khỏi số liệu KQKD mọi dòng có TK hoặc TK đối ứng bắt đầu bằng 911 | `account_map.yaml: exclude_contra` | |
| P2 | Doanh thu thuần | Có − Nợ TK 511 và 521 | `pl_lines.net_revenue` | |
| P3 | Lãi vay | Dòng TK 635 có diễn giải “lãi vay / lãi tiền vay” hoặc đối ứng 335, 341, 3388, 311. Cần xác nhận tiểu khoản 635x của Alta | `interest_expense_rule` | |
| P4 | EBITDA | LNTT + lãi vay + **khấu hao vào chi phí = phát sinh Có − Nợ TK 214 có TK đối ứng 6xx, 154, 632**. Không dùng biến động ròng TK 214. Tháng không có sổ NKC chi tiết → “Chưa đủ dữ liệu”. Áp dụng như nhau cho 3 công ty | `pl_lines.depreciation.contra_prefixes` (v2026-11-04.2) | |
| P5 | Hợp nhất quản trị | Cộng 3 pháp nhân; loại doanh thu nội bộ (dòng 511 có mã đối tượng là MST công ty trong tập đoàn) khỏi doanh thu và giá vốn; loại lãi vay nội bộ khỏi 515 và 635. Chưa loại lãi chưa thực hiện trong tồn kho | dashboard `PL.e` | |
| P6 | Đối chiếu công nợ nội bộ | Số dư Nợ − Có trên TK 131, 331, 136, 336, 138, 338, 341, 128 của dòng có đối tượng là công ty khác trong tập đoàn phải triệt tiêu theo cặp; chênh lệch > 1.000 đ vào danh sách ngoại lệ | dashboard `icTable` | |
| P7 | Phân loại dòng tiền | Theo TK đối ứng của dòng TK 111/112/113 (bảng trong `cash_flow_map.yaml`); không khớp → `UNCLASSIFIED`; chuyển giữa các TK tiền bị loại | `cash_flow_map.yaml` | |
| P8 | Số ngày vốn lưu động | DSO = Phải thu ÷ (doanh thu 3 tháng × 1,1) × 91 · DIO = Tồn kho ÷ giá vốn 3 tháng × 91 · DPO = Phải trả ÷ (giá vốn 3 tháng × 1,1) × 91 | dashboard | |
| P9 | Tuổi nợ khi FAST không có công nợ theo hóa đơn | FIFO theo mã khách; phần số dư đầu kỳ không có chi tiết ghi “Chưa rõ tuổi”; nhãn `DERIVED – FIFO` | dashboard `aging()` | |
| P10 | Ngưỡng sai số | 0 đ cho tổng file và cân đối CĐPS; ≤ 1.000 đ cho các đối chiếu khác | `controls.py` | |
| P11 | Phân bổ chi phí chung cho BU (đặc biệt In 3D) | **Không phân bổ** cho đến khi có tiêu thức được duyệt | `entity_map.yaml` | |
| P12 | Phân tích biến động TK 214 | Tách theo TK đối ứng: khấu hao vào chi phí (6xx, 154, 632) · thanh lý/nhượng bán (211–213, 217, 811) · điều chuyển (214, 136, 336, 1388, 3388, 411) · điều chỉnh khác | dashboard `daCat()` | |
| P13 | Tuổi nợ | Chỉ theo hạn thanh toán / số ngày quá hạn do FAST xuất (báo cáo công nợ theo hóa đơn). Không có → “Chưa đủ dữ liệu”; hóa đơn thiếu hạn TT xếp nhóm riêng. Bỏ tuổi nợ FIFO ước tính | dashboard `debtData()` | |
| P14 | Hàng chậm luân chuyển | Còn tồn và không xuất trong ≥ 3 / ≥ 6 tháng liên tiếp của các file NXT đã nạp; lịch sử < 3 tháng → “Chưa đủ dữ liệu” | dashboard `stockData()` | |
