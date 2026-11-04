---
name: cash-13-week-treasury
description: Dự báo dòng tiền 13 tuần (direct method), quản trị thanh khoản, hạn mức tín dụng và quan hệ ngân hàng Việt Nam cho Alta Group. Dùng khi hỏi "còn bao nhiêu tiền", "tuần nào thiếu tiền", dự báo thu chi, kế hoạch trả nợ vay, hạn mức/bảo lãnh/L/C, so sánh lãi vay giữa các ngân hàng, kiểm tra covenant, tối ưu vốn lưu động (DSO, DIO, DPO, CCC), hoặc cash pooling giữa 3 công ty.
---

# Dòng tiền 13 tuần & Ngân quỹ

## 0. Công cụ có sẵn — dùng trước khi tự dựng mô hình
Repo có công cụ #3: `afi cash13w` (pipeline `alta-finance-intelligence/`, đặc tả FAST §8.3) + trang xem `tools/cash-13w/cash13w.html` (bản online, riêng tư: https://claude.ai/artifact/PL9kJr4Wx3SCPUqBjoPn72).

**Quy trình mỗi thứ Hai** (tuần 1 bắt đầu từ thứ Hai này):
1. `afi ingest` sổ nhật ký chung 3 công ty tới hết Chủ nhật vừa qua → có 13 tuần thực tế.
2. Lấy sao kê ngân hàng thứ Sáu (hoặc cuối tuần) → `bank_balances.csv`, ghi người xác minh và tiền bị hạn chế (ký quỹ L/C, bảo lãnh). Không xác minh = không dùng làm tiền đầu kỳ.
3. Kế toán công nợ cập nhật `ar_open.csv`/`ap_open.csv` theo hóa đơn: ngày đến hạn, **ngày dự kiến**, mức tin cậy, người phụ trách. Cập nhật lịch vay, lương & BHXH, thuế, capex theo mốc hợp đồng, khoản khác (mẫu cột: `alta-finance-intelligence/README.md`; tạo file trống: `afi cash13w --templates DIR`).
4. `afi cash13w --inputs DIR --start YYYY-MM-DD` → Excel (cầu nối tuần bằng công thức) + JSON + lưu phiên bản; tự so với phiên bản tuần trước.
5. Mở JSON trong `cash13w.html`: xem tuần thấp nhất, headroom, tuần dưới ngưỡng (Base/Downside, từng pháp nhân và hợp nhất), thực tế vs dự báo tuần trước, danh sách **DATA REQUIRED** → giao việc bổ sung cho người phụ trách.
6. Viết tóm tắt 5 dòng (mục 5) từ file kết quả. Chênh lệch > 10% và ≥ 50 triệu phải có lời giải thích.

Khi trả lời: chỉ dùng số trong JSON/Excel đã chạy; không lấp chỗ trống bằng bình quân lịch sử (lịch sử chỉ để ước **ngày** thu, có đánh dấu); luôn nêu số mục DATA REQUIRED và trạng thái duyệt (Bản nháp cho tới khi CFO duyệt tiền đầu kỳ, ngưỡng, giả định trong `params.yaml`).

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
- Excel 13 tuần do `afi cash13w` sinh: `Tom_tat`, `Tien_dau_ky`, `Chi_tiet` (ô nhập xanh), `Base_<Cty>`/`Down_<Cty>`/`*_HopNhat` (SUMIFS từ `Chi_tiet`, có dòng kiểm tra = 0), `Thuc_te_13T`, `Thuc_te_dong`, `So_sanh`, `DATA_REQUIRED`, `Tham_so`. Chỉ dựng Excel thủ công (skill `xlsx`) cho phân tích ngoài phạm vi công cụ.
- Tóm tắt 5 dòng: tiền hiện tại, tuần thấp nhất & số dư, headroom thấp nhất, 3 hành động ưu tiên, quyết định cần CEO.
