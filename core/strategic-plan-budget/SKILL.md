---
name: strategic-plan-budget
description: Lập kế hoạch chiến lược 3 năm, ngân sách năm, OKR/BSC và rolling forecast cho Alta Group, liên kết chiến lược với con số tài chính. Dùng khi chuẩn bị kế hoạch kinh doanh năm sau, ngân sách theo công ty/mảng/phòng ban, giao chỉ tiêu, cập nhật dự báo quý, phân bổ vốn giữa các mảng, hoặc trình ĐHĐCĐ/HĐQT kế hoạch.
---

# Kế hoạch chiến lược & Ngân sách

## 1. Lịch kế hoạch năm (mẫu cho năm N+1)
| Thời gian | Bước | Đầu ra |
|---|---|---|
| Tháng 9 | Rà soát chiến lược: kết quả 9T, môi trường, cập nhật giả định vĩ mô (GDP, CPI, lãi suất, tỷ giá — ghi nguồn) | Strategy review deck |
| Đầu tháng 10 | HĐQT/CEO giao **định hướng top-down**: tăng trưởng doanh thu, EBITDA margin, ngân sách capex, mức nợ tối đa | Thư định hướng kế hoạch |
| Tháng 10 | Các mảng lập **bottom-up**: doanh thu theo khách/sản phẩm/vụ việc, chi phí theo trung tâm chi phí, nhân sự, capex | Template ngân sách mỗi mảng |
| Đầu tháng 11 | Hợp nhất, đối chiếu top-down vs bottom-up, đàm phán khoảng chênh (gap) | Bản kế hoạch v1 |
| Tháng 11 | Kịch bản & dòng tiền, kiểm tra covenant, phê duyệt CEO | v2 + 3 kịch bản |
| Tháng 12 | HĐQT duyệt; giao chỉ tiêu & OKR quý 1 | Kế hoạch chính thức |
| Hàng quý | Rolling forecast 4–6 quý tới; đánh giá OKR | Báo cáo dự báo |

## 2. Kiến trúc mô hình ngân sách
- **Driver-based**: Plastic — sản lượng (tấn) × giá bán, giá hạt nhựa (biến số chính) → biên gộp; Media — số dự án/sự kiện, slot LED × giá × tỷ lệ lấp đầy, hợp đồng khung; Mẹ — diện tích cho thuê × đơn giá × occupancy, phí dịch vụ.
- Nhân sự: headcount theo phòng × lương bình quân × (1 + BHXH ~ 21,5% phần DN — xác nhận) + thưởng (`cm-headcount-and-comp-planning`).
- Ba báo cáo liên kết (KQKD, CĐKT, LCTT) theo tháng cho năm N+1, theo năm cho N+2, N+3.
- Loại trừ nội bộ theo `group-consolidation-ic`.

## 3. Liên kết chiến lược → con số → con người
1. 3–5 **ưu tiên chiến lược** (từ `strategy-dev-director`) → mỗi ưu tiên có sáng kiến, ngân sách, chủ trì.
2. **Balanced Scorecard** 4 góc: Tài chính (doanh thu, EBITDA, ROCE, dòng tiền) · Khách hàng (thị phần, NPS, tỷ lệ giữ chân khách lớn) · Quy trình (OEE nhà máy Plastic, tỷ lệ phế phẩm, thời gian triển khai dự án Media) · Học hỏi & phát triển (nhân sự chủ chốt, đào tạo, chuyển đổi số).
3. **OKR quý**: 1–3 Objective mỗi mảng, 3–4 Key Result đo lường được; tách KPI vận hành (BAU) khỏi OKR (thay đổi).
4. Gắn thưởng: ngưỡng/mục tiêu/vượt (threshold/target/stretch) với tỷ trọng rõ.

## 4. Kiểm tra chất lượng kế hoạch
- Tăng trưởng giả định có giải thích bằng driver (không phải "+15% vì mong muốn").
- So với lịch sử 3 năm: biên lợi nhuận, vòng quay vốn lưu động, tỷ lệ chi phí/doanh thu — chênh > 3pt phải có sáng kiến cụ thể.
- Dòng tiền đủ cho capex + trả nợ + cổ tức ở kịch bản xấu; covenant còn ≥ 15% headroom.
- Có danh sách giả định & rủi ro, và "trigger" để kích hoạt kế hoạch dự phòng.

## 5. Đầu ra
- Excel ngân sách (skill `xlsx`): `Guidance`, `Drivers_<Mảng>`, `Headcount`, `Opex_by_CC`, `Capex`, `PL/BS/CF_<Cty>`, `Consol`, `Scenarios`, `BSC_OKR`, `Checks`.
- Deck trình HĐQT (skill `pptx`, action titles): Kết quả năm nay → Bối cảnh năm sau → Ưu tiên chiến lược → Chỉ tiêu tài chính → Kế hoạch theo mảng → Capex & nguồn vốn → Kịch bản & rủi ro → Đề xuất phê duyệt.
- Kỹ năng liên quan: `cm-budget-creation-management`, `cm-scenario-planning`, `cm-revenue-forecasting`, `w95-strategic-planning`, `ar-strategic-alignment`, `wd-traction-eos`.
