---
name: cash-13-week-treasury
description: Dự báo dòng tiền 13 tuần (direct method), quản trị thanh khoản, hạn mức tín dụng và quan hệ ngân hàng Việt Nam cho Alta Group. Dùng khi hỏi "còn bao nhiêu tiền", "tuần nào thiếu tiền", dự báo thu chi, kế hoạch trả nợ vay, hạn mức/bảo lãnh/L/C, so sánh lãi vay giữa các ngân hàng, kiểm tra covenant, tối ưu vốn lưu động (DSO, DIO, DPO, CCC), hoặc cash pooling giữa 3 công ty.
---

# Dòng tiền 13 tuần & Ngân quỹ

## 1. Mô hình (direct method, theo tuần, theo từng công ty + hợp nhất)
Cấu trúc dòng (mỗi tuần T1…T13, cột Thực tế của tuần trước để đo sai số):

```
Tiền đầu kỳ (khớp sổ phụ ngân hàng)
+ Thu từ khách hàng           ← tuổi nợ phải thu × tỷ lệ thu lịch sử theo nhóm khách
+ Thu khác (cho thuê, hoàn thuế, thanh lý)
- Trả nhà cung cấp            ← lịch thanh toán AP theo hạn, nguyên vật liệu Plastic theo kế hoạch SX
- Lương & BHXH (cố định ngày), thuế (GTGT/TNCN/TNDN theo lịch kê khai)
- Chi phí hoạt động (điện, thuê, marketing, sự kiện Media)
- Capex (theo hợp đồng & tiến độ)
= Dòng tiền hoạt động & đầu tư
+ Giải ngân vay / - Trả gốc / - Trả lãi (theo khế ước từng ngân hàng)
± Chuyển tiền nội bộ (Mẹ ↔ Plastic ↔ Media) — tổng hợp nhất phải = 0
= Tiền cuối kỳ
Tồn quỹ tối thiểu (≥ 2 tuần chi phí cố định + nghĩa vụ nợ đến hạn 4 tuần)
Hạn mức tín dụng chưa sử dụng
= Thanh khoản khả dụng (headroom)
```

## 2. Quy tắc
- Tách **cam kết** (đã có hợp đồng/hóa đơn) và **dự kiến**; dòng thu dự kiến bị chiết khấu xác suất.
- Đo **độ chính xác dự báo** hàng tuần (thực tế vs dự báo tuần trước); sai số > 10% → giải thích (dùng `cm-forecast-accuracy-tracking`).
- Kịch bản: Cơ sở / Thu chậm 30 ngày khách lớn nhất / Doanh thu −20% / Ngân hàng không gia hạn hạn mức.
- Cảnh báo đỏ khi headroom < tồn quỹ tối thiểu ở bất kỳ tuần nào → đề xuất ngay đòn bẩy: đẩy thu (chiết khấu thanh toán sớm, factoring), giãn chi (đàm phán NCC), rút hạn mức, hoãn capex, vay nội bộ.

## 3. Vốn lưu động
- DSO = Phải thu bình quân / Doanh thu × số ngày; DIO = Tồn kho / Giá vốn × ngày; DPO = Phải trả / Giá vốn × ngày; **CCC = DSO + DIO − DPO**. Tính theo từng công ty (Plastic thường DIO cao; Media thường DSO cao do sự kiện/quảng cáo).
- Mỗi 1 ngày CCC giảm = (Doanh thu năm / 365) tiền giải phóng — luôn quy ra VND.
- Bảng tuổi nợ phải thu: 0–30 / 31–60 / 61–90 / 91–180 / >180 ngày; top 10 khách quá hạn kèm người phụ trách thu.

## 4. Vay & ngân hàng VN
- Bảng nợ vay: Ngân hàng | Loại (hạn mức VLĐ / trung dài hạn / bảo lãnh / L/C) | Hạn mức | Dư nợ | Lãi suất (cố định/thả nổi = lãi cơ sở + biên) | Kỳ điều chỉnh | Ngày đáo hạn | Tài sản bảo đảm | Covenant.
- So sánh chi phí vay thực (lãi + phí thu xếp + phí bảo lãnh + yêu cầu ký quỹ/duy trì số dư + bán chéo bảo hiểm) bằng `ps-loan-offer-true-cost-comparator`.
- Covenant (DSCR, Nợ vay/EBITDA, Nợ/VCSH, hệ số thanh toán hiện hành): tính headroom và mức EBITDA giảm tối đa trước khi vi phạm bằng `ps-debt-covenant-dscr-monitor`. Biên an toàn < 15% → báo trước cho ngân hàng.
- Tránh **vay ngắn hạn tài trợ dài hạn** (kiểm tra nguồn vốn của capex).
- Cash pooling nội bộ: cho vay nội bộ cần hợp đồng, lãi suất thị trường, lưu ý trần lãi vay được trừ 30% EBITDA (NĐ132) — xem `vn-finance-compliance`.

## 5. Đầu ra
- Excel 13 tuần (skill `xlsx`): sheet `Inputs`, `AR_Aging`, `AP_Schedule`, `Debt`, `13W_<Cty>`, `13W_Consol`, `Scenarios`, `Accuracy`; công thức liên kết, ô nhập màu xanh.
- Tóm tắt 5 dòng: tiền hiện tại, tuần thấp nhất & số dư, headroom thấp nhất, 3 hành động ưu tiên, quyết định cần CEO.
