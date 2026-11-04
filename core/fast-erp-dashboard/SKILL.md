---
name: fast-erp-dashboard
description: Vận hành và mở rộng hệ thống "Alta CFO · CEO Dashboard" lấy dữ liệu từ FAST Business ERP (sổ nhật ký chung, bảng cân đối số phát sinh, bảng kê hóa đơn bán hàng) cho Alta Group. Dùng khi Khôi đưa file xuất từ FAST và muốn xem/kiểm tra dashboard CEO–CFO, hỏi một chỉ số được tính thế nào, muốn truy xuất ngược số liệu về chứng từ gốc, file bị nhận sai loại/công ty/kỳ, cần thêm chỉ số hoặc biểu đồ mới, hoặc hỏi quy trình xuất báo cáo từ FAST hằng tháng.
---

# FAST Business → CFO/CEO Dashboard

Hệ thống nằm trong repo `finance-skill`, thư mục `dashboard/`:
- `dashboard/src/dashboard.html` — mã nguồn (một file, chạy trong trình duyệt; ECharts + SheetJS từ cdnjs).
- `dashboard/Alta_CFO_CEO_Dashboard.html` — bản mở trực tiếp, tạo bằng `python3 scripts/build_dashboard.py`.
- `dashboard/README.md` — kiến trúc, danh sách báo cáo FAST cần xuất, quy trình tháng, định nghĩa chỉ số.

## Tài liệu gốc
- Đặc tả: `docs/ALTA_FAST_Data_Architecture_2026-11-04_v1.1.md` (thẻ bằng chứng, vai trò báo cáo, control matrix, state machine).
- Pipeline: `alta-finance-intelligence/` (`afi dictionary | ingest | reconcile | pl`). Với file thật, chạy `afi dictionary` trước, đối chiếu tên cột với `config/report_registry.yaml`, không tự đoán ánh xạ.
- Chính sách chờ duyệt: `docs/accounting_policies.md`; checklist xuất: `docs/fast_export_checklist.md`.

## Báo cáo bổ sung (đợt 2)
Công nợ theo đối tượng/hóa đơn, TSCĐ & khấu hao, Nhập – xuất – tồn: xem `docs/fast_export_requirements_v2.md`. Quy tắc: khấu hao cho EBITDA = Có 214 đối ứng 6xx/154/632; tuổi nợ chỉ theo hạn TT do FAST xuất; hàng chậm luân chuyển cần ≥ 3 tháng NXT liên tiếp; thiếu nguồn → “Chưa đủ dữ liệu”, không tự suy ra.

## Khi Khôi đưa file FAST và hỏi số liệu
1. Nếu chỉ cần xem: hướng dẫn kéo file vào trang **Dữ liệu** của dashboard (bản HTML hoặc artifact).
2. Nếu cần Claude tự phân tích: đọc file bằng pandas, **dùng đúng công thức của dashboard** (bảng `PL`, `BAL`, `CF_CAT` trong `src/dashboard.html`) để số khớp với màn hình:
   - Tìm dòng tiêu đề cột trong 40 dòng đầu; CĐPS có thể có tiêu đề 2 dòng (Số dư đầu kỳ → Nợ/Có).
   - Bỏ dòng "Tổng cộng" nhưng dùng nó để đối chiếu tổng.
   - P&L: loại dòng có Tk hoặc Tk đ/ư bắt đầu bằng 911.
   - Nội bộ: Mã khách (10 số đầu) ∈ {0301420079 Mẹ, 0312414944 Plastic, 0305904835 Media}.
3. Luôn kèm truy xuất: mỗi con số nêu file + số dòng Excel của các dòng đóng góp lớn nhất.
4. Báo mọi kiểm tra không đạt (Nợ ≠ Có, CĐPS ≠ sổ NKC, bảng kê ≠ TK 511, công nợ nội bộ lệch) trước khi kết luận.

## Khi sửa / mở rộng dashboard
- Sửa `src/dashboard.html`, sau đó chạy `python3 scripts/build_dashboard.py`.
- Chỉ số KQKD mới: thêm vào `PL` dạng `[tiền tố TK, 'cn'|'nc', dấu]`; số dư mới: thêm vào `BAL`. Truy xuất ngược tự hoạt động vì drill dùng cùng định nghĩa.
- Kiểm thử: mở bằng Playwright, nạp file mẫu dạng FAST (tiêu đề ở dòng 6, dòng "Tổng cộng" cuối), kiểm tra trang **Dữ liệu → Kiểm tra đối chiếu** đều "Đạt" và console không lỗi.
- Nếu đã publish artifact, cập nhật artifact cùng URL.

## Liên quan
`alta-sales-report` (báo cáo bán hàng chi tiết), `board-management-pack` (dùng số từ dashboard để làm báo cáo HĐQT), `cash-13-week-treasury`, `group-consolidation-ic`.
