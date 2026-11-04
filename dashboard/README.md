# Alta CFO · CEO Dashboard (FAST Business)

Hệ thống biến báo cáo xuất từ **FAST Business** thành bảng điều hành CEO/CFO. Chỉ cần một file HTML, xử lý ngay trong trình duyệt: không cần máy chủ, không cài đặt, dữ liệu không rời máy.

- **Mở dùng:** `Alta_CFO_CEO_Dashboard.html` (nhấp đúp mở bằng Chrome/Edge), hoặc bản online (riêng tư) trên Claude: https://claude.ai/artifact/6HGw5XDTkaSe2NpRi235E6.
- **Mã nguồn:** `src/dashboard.html`. Sửa xong chạy `python3 scripts/build_dashboard.py` để tạo lại bản mở trực tiếp.
- Lần đầu mở sẽ thấy **dữ liệu mẫu** (đánh dấu rõ). Nạp file thật thì dữ liệu mẫu biến mất.

## 1. Kiến trúc

```
FAST Business ──(Kết xuất Excel)──► 3 loại báo cáo × 3 công ty
        │
        ▼
 Trang "Dữ liệu" (kéo thả)
   ├─ Nhận diện: loại báo cáo (theo tiêu đề + tên cột), công ty (theo tên file), kỳ ("Từ ngày … đến ngày …")
   ├─ Chuẩn hóa thành 3 bảng: Sổ cái (từng dòng Nợ/Có) · CĐPS (số dư) · Bảng kê bán hàng
   ├─ Đối chiếu: dòng "Tổng cộng" · Nợ = Có · CĐPS = sổ NKC · Doanh thu bảng kê = TK 511
   └─ Lưu IndexedDB trong trình duyệt (nạp lại tháng mới, file mới thay file cũ cùng tháng)
        │
        ▼
 Lớp chỉ số (công thức theo TK VAS — TT200/TT99)
   ├─ KQKD: doanh thu, giá vốn, LN gộp, CP BH/QLDN, tài chính, LNTT, LNST, EBITDA (loại bút toán kết chuyển 911)
   ├─ Số dư: tiền, phải thu, tồn kho, phải trả, nợ vay, thuế (CĐPS hoặc số dư đầu + phát sinh)
   ├─ Dòng tiền trực tiếp (TK 111/112/113 theo TK đối ứng), tuổi nợ FIFO, DSO/DIO/DPO/CCC
   └─ Hợp nhất: loại trừ doanh thu/lãi nội bộ theo MST 3 công ty
        │
        ▼
 Trang CEO · CFO · Bán hàng  ──(bấm bất kỳ số nào)──► Truy xuất ngược: dòng chứng từ gốc + tên file + số dòng Excel
```

## 2. Báo cáo cần xuất từ FAST (mỗi công ty)

| # | Báo cáo trên FAST | Kỳ | Bắt buộc | Dùng cho |
|---|---|---|---|---|
| 1 | **Sổ nhật ký chung** (hoặc Sổ chi tiết các tài khoản, có cột *Tk* và *Tk đ/ư*) — chọn mẫu có cột **Mã khách / Mã đối tượng** và **Vụ việc** | Tháng (01 → cuối tháng) | Có | Mọi chỉ số KQKD, dòng tiền, tuổi nợ, nội bộ, truy xuất |
| 2 | **Bảng cân đối số phát sinh các tài khoản** (chi tiết cấp thấp nhất) | Tháng | Có | Số dư cuối tháng, đối chiếu với sổ NKC |
| 3 | **Bảng kê hóa đơn bán hàng, dịch vụ** | Tháng | Nên có | Mảng doanh thu, khách hàng, điểm kiểm soát hóa đơn |
| 4 | Bảng kê mua hàng | Tháng | Tùy chọn | (dự phòng mở rộng) |
| 5 | File kế hoạch (mẫu 4 cột: Công ty, Chỉ tiêu, Tháng, Kế hoạch) | Năm | Tùy chọn | So sánh % kế hoạch |

Lần đầu: xuất thêm sổ NKC + CĐPS **từ tháng 1 năm trước** để có số cùng kỳ và số dư đầu kỳ.
Tên menu trên FAST có thể khác theo phiên bản; quan trọng là đúng tên báo cáo và có đủ cột.

**Đặt tên file** (kết thúc bằng tên công ty):
`NKC 2026-10 - Alta Plastic.xlsx` · `CDPS 2026-10 - Alta Media.xlsx` · `Bang ke ban hang 2026-10 - Alta.xlsx`

## 3. Quy trình hằng tháng (≈ 20 phút)

| Ngày | Việc | Người |
|---|---|---|
| N+3 | Khóa sổ: trích trước, khấu hao, phân bổ, giá vốn; đối chiếu ngân hàng & công nợ nội bộ | Kế toán tổng hợp |
| N+4 | Xuất 3 báo cáo × 3 công ty, đặt tên theo quy ước, để vào thư mục chung `FAST/2026-10/` | Kế toán tổng hợp |
| N+4 | Kéo 9 file vào trang **Dữ liệu**; xử lý mọi dòng đỏ ở “Đối chiếu trong file” và “Kiểm tra đối chiếu” | Kế toán trưởng |
| N+5 | Đọc trang **CFO** (tiền, vốn lưu động, tuổi nợ, nội bộ) → gửi danh sách việc cần xử lý (dùng “Sao chép bảng”) | CFO |
| N+5 | Đọc trang **CEO**, chuẩn bị báo cáo HĐQT (skill `board-management-pack`) | CFO → CEO |

## 4. Chỉ số & quy tắc tính

Xem trang **Quy trình** trong dashboard (bảng “Định nghĩa chỉ số”). Tóm tắt:
- P&L tính từ phát sinh sổ NKC, **loại mọi dòng có TK hoặc TK đối ứng 911** → không phụ thuộc đã kết chuyển hay chưa.
- Lãi vay = dòng TK 635 có diễn giải “lãi vay” hoặc đối ứng 335/341/3388. EBITDA = LNTT + lãi vay + phát sinh Có TK 214.
- Số dư = CĐPS cùng tháng; nếu không có, = số dư đầu của CĐPS gần nhất + phát sinh sổ NKC.
- Nội bộ: dòng có Mã khách là MST 0301420079 / 0312414944 / 0305904835 (sửa ở trang Dữ liệu → Thiết lập).
- Hạn chế đã biết: chưa loại lãi chưa thực hiện trong tồn kho nội bộ; tài sản/nợ ngắn hạn là ước tính theo đầu TK; tuổi nợ của số dư đầu kỳ ghi “Chưa rõ tuổi”.

## 5. Mở rộng
- Thêm chỉ số: sửa bảng `PL` / `BAL` / `CF_CAT` trong `src/dashboard.html`.
- Thêm quy tắc phân mảng doanh thu: hàm `segOf()` (đồng bộ với skill `alta-sales-report`).
- Nhờ Claude: dùng skill `fast-erp-dashboard`.
