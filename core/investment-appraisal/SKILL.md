---
name: investment-appraisal
description: Thẩm định dự án đầu tư và business case cho Alta Group — capex máy móc Plastic, màn hình LED/thiết bị Media, bất động sản cho thuê của Mẹ, mảng kinh doanh mới. Dùng khi cần tính NPV, IRR, thời gian hoàn vốn, WACC theo bối cảnh Việt Nam, phân tích độ nhạy/kịch bản, so sánh mua vs thuê, hoặc viết tờ trình đầu tư cho HĐQT.
---

# Thẩm định đầu tư (Capital Allocation)

## 1. Thông tin đầu vào cần có
Mục tiêu dự án · Vốn đầu tư (thiết bị, xây dựng, lắp đặt, vốn lưu động ban đầu) · Tiến độ giải ngân · Sản lượng/công suất & tỷ lệ lấp đầy (LED: tỷ lệ bán slot; cho thuê: occupancy) · Giá bán & lộ trình tăng giá · Chi phí biến đổi & cố định · Thời gian khấu hao (theo khung TT45/2013 và sửa đổi — xác nhận) · Giá trị thanh lý · Nguồn vốn (vốn tự có/vay, lãi suất, ân hạn).

## 2. Phương pháp
1. Dòng tiền tự do dự án (danh nghĩa, VND): EBIT × (1 − thuế TNDN) + khấu hao − capex − Δ vốn lưu động. Không trừ lãi vay vào dòng tiền dự án (đã nằm trong WACC); trình bày thêm **dòng tiền chủ sở hữu** khi có vay dự án.
2. **WACC VN** (ghi rõ từng tham số & nguồn): Rf = lợi suất TPCP 10 năm VN; ERP thị trường VN (tham khảo Damodaran: ERP trưởng thành + country risk premium); beta ngành (Damodaran Emerging Markets, unlevered → relevered theo D/E mục tiêu); phần bù quy mô/khả năng thanh khoản cho công ty chưa niêm yết (2–5%); chi phí nợ = lãi vay thực tế sau thuế. Cho phép Khôi dùng **hurdle rate** HĐQT duyệt thay WACC.
3. Chỉ số: NPV, IRR, MIRR, thời gian hoàn vốn giản đơn & có chiết khấu, PI, ROIC năm ổn định, ảnh hưởng EBITDA/LN hợp nhất năm 1–3, nhu cầu tiền đỉnh (peak funding).
4. **Độ nhạy**: bảng 2 chiều (giá × sản lượng; capex ± 20% × WACC ± 2pt); tornado chart 6 biến; điểm hòa vốn từng biến.
5. **Kịch bản**: Xấu / Cơ sở / Tốt với giả định nhất quán (không chỉ ±% đồng loạt).
6. **Phương án thay thế**: không làm gì; thuê/thuê tài chính; mua cũ; làm theo giai đoạn (real option — giá trị của việc chờ/mở rộng).
7. **Rủi ro định tính**: thị trường, công nghệ (LED lỗi thời nhanh), pháp lý (giấy phép quảng cáo ngoài trời, PCCC, môi trường cho nhựa), đối tác, tỷ giá nếu nhập khẩu thiết bị.

## 3. Tiêu chí quyết định (mặc định, HĐQT có thể thay)
NPV > 0 tại WACC/hurdle; IRR ≥ hurdle + 3pt cho dự án mới, ≥ hurdle cho thay thế/duy trì; hoàn vốn có chiết khấu ≤ 60–70% vòng đời tài sản; không làm Nợ vay/EBITDA hợp nhất vượt ngưỡng covenant.

## 4. Đầu ra
- Excel (skill `xlsx`): `Assumptions` (ô nhập xanh, nguồn), `Capex`, `Revenue`, `Opex`, `FCF`, `WACC`, `Returns`, `Sensitivity`, `Scenarios`, `Checks`.
- **Tờ trình đầu tư** (1–2 trang, skill `docx`): Đề xuất & số tiền xin duyệt → Lý do chiến lược → Kết quả tài chính (bảng) → Độ nhạy & rủi ro → Phương án thay thế đã xem xét → Điều kiện & mốc giải ngân → KPI hậu kiểm (post-investment review sau 12 tháng).
- Liên quan: `cm-business-case-modeling`, `cm-strategic-initiative-modeling`, `ar-business-investment-advisor`, plugin `financial-analysis:dcf`.
