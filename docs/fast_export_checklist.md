# Checklist xuất báo cáo từ FAST (Phase 0)

Người thực hiện: Kế toán tổng hợp · Người kiểm tra: Kế toán trưởng · Hạn: ngày N+4 hằng tháng.
Nguyên tắc: **chỉ xuất, không sửa** dữ liệu trên FAST. Không chỉnh sửa file sau khi xuất (kể cả xóa dòng, đổi tên cột).

## 1. Danh sách file mỗi tháng (mỗi công ty: Alta, Alta Plastic, Alta Media)

| # | Báo cáo trên FAST | Kỳ lọc | Tùy chọn bắt buộc | Tên file |
|---|---|---|---|---|
| 1 | Sổ nhật ký chung (hoặc Sổ chi tiết các tài khoản, tất cả TK) | 01 → ngày cuối tháng | Mẫu có cột **Mã khách/Mã đối tượng** và **Vụ việc**; không lọc theo tài khoản; có dòng Tổng cộng | `NKC YYYY-MM - <Công ty>.xlsx` |
| 2 | Bảng cân đối số phát sinh các tài khoản | 01 → ngày cuối tháng | Chi tiết đến **tài khoản cấp thấp nhất**; có số dư đầu, phát sinh, số dư cuối | `CDPS YYYY-MM - <Công ty>.xlsx` |
| 3 | Bảng kê hóa đơn bán hàng, dịch vụ | 01 → ngày cuối tháng | Giữ mẫu đang dùng cho báo cáo bán hàng 9T/2026 | `Bang ke ban hang YYYY-MM - <Công ty>.xlsx` |
| 4 | Bảng kê mua hàng | 01 → ngày cuối tháng | Như trên | `Bang ke mua hang YYYY-MM - <Công ty>.xlsx` |

`<Công ty>` viết đúng một trong: `Alta`, `Alta Plastic`, `Alta Media`.

**Lần đầu (một lần):** xuất thêm (1) và (2) cho từng tháng từ 01/2025 đến tháng gần nhất, Danh mục tài khoản, Danh mục khách hàng/nhà cung cấp.

## 2. Ghi lại cho mỗi lần xuất (điền vào `FAST_Exports/YYYY-MM/_export_log.xlsx`)
Ngày giờ xuất · người xuất · công ty · tên báo cáo · mẫu báo cáo · kỳ từ–đến · các bộ lọc đã chọn · định dạng (xls/xlsx) · ghi chú (ví dụ: xuất lại do điều chỉnh bút toán).

## 3. Trước khi tải lên thư mục Drive `90_Nguon_BaoCao_2025_KeHoach_2026/FAST_Exports/YYYY-MM/`
- [ ] Mở file, dòng tiêu đề có “Từ ngày … đến ngày …” đúng kỳ.
- [ ] Có dòng “Tổng cộng” ở cuối.
- [ ] Không có sheet ẩn hoặc dòng bị lọc (filter) trong Excel.
- [ ] Tên file đúng quy ước.
- [ ] Nếu là bản xuất lại: **giữ bản cũ**, đặt bản mới cùng tên thêm `(v2)`; hệ thống tự dùng bản mới cho các tháng trùng và lưu bản cũ làm lịch sử.

## 4. Sau khi nạp
- Kiểm tra trang “Dữ liệu & đối chiếu” của dashboard hoặc chạy `afi reconcile`.
- Mọi kiểm tra “Không đạt” phải có giải thích trước khi CFO duyệt kỳ.
