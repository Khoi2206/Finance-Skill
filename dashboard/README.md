# Alta CFO · CEO Dashboard (FAST Business)

Hệ thống biến báo cáo xuất từ **FAST Business** thành bảng điều hành CEO/CFO. Chỉ cần một file HTML, xử lý ngay trong trình duyệt: không cần máy chủ, không cài đặt, dữ liệu không rời máy.

- **Bản hiện hành (v3):** `Alta_CFO_CEO_Dashboard_v3.html`.
  - Nạp cả thư mục FAST, kiểm tra đầu vào từng file, có trang Đối chiếu và Đơn hàng.
  - Thêm công nợ theo nhóm tuổi của FAST, TSCĐ/CCDC, kho và chi phí sản xuất theo yếu tố.
  - Không có dữ liệu mẫu.
  - Bàn giao và kết quả kiểm thử với bộ PLASTIC 9T/2026: [`docs/fast_plastic_v3_handover.md`](../docs/fast_plastic_v3_handover.md).
- **Bản cũ (v2), giữ để so sánh:** `Alta_CFO_CEO_Dashboard_v2.html` (mã nguồn `src/dashboard_v2.html`).
  - Bản online v2: https://claude.ai/artifact/6HGw5XDTkaSe2NpRi235E6.
  - v2 có dữ liệu mẫu khi chưa nạp file.
- **Mã nguồn v3:** `src/dashboard.html`. Sửa xong chạy `python3 scripts/build_dashboard.py` để tạo lại `Alta_CFO_CEO_Dashboard_v3.html`.
- Phần dưới mô tả kiến trúc chung (từ v1/v2). Phần nạp FAST theo thư mục, bản trùng, nguồn chính/nguồn đối chiếu của v3 xem tài liệu bàn giao.

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
| 6 | Bảng tổng hợp công nợ phải thu / phải trả | Tháng | Nên có | Trang Công nợ: dư đầu, phát sinh, thanh toán, dư cuối theo đối tượng; đối chiếu TK 131/331 |
| 7 | Công nợ theo hóa đơn (có Hạn thanh toán) | Cuối tháng | Nên có | Hóa đơn còn dư, số ngày quá hạn, tuổi nợ |
| 8 | Bảng tính và phân bổ khấu hao TSCĐ | Tháng | Nên có | Trang TSCĐ; đối chiếu TK 211–213/214; khấu hao theo tài sản/bộ phận/tháng |
| 9 | Nhập – xuất – tồn theo kho/mã hàng | Tháng, ≥ 3 tháng liên tiếp | Nên có | Trang Tồn kho; hàng chậm luân chuyển; đối chiếu TK 15x |
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

## 6. Bổ sung 2026-11-04 (đợt 2)
- Trang mới: **Công nợ** (phải thu/phải trả theo đối tượng và hóa đơn, tuổi nợ theo hạn thanh toán FAST, đối chiếu TK 131/331), **TSCĐ** (cộng dồn nguyên giá/hao mòn, biến động TK 214 tách khấu hao/thanh lý/điều chuyển/điều chỉnh, khấu hao theo tháng/bộ phận/tài sản), **Tồn kho** (theo mã/kho, hàng chậm luân chuyển, đối chiếu TK 15x).
- EBITDA chỉ cộng lại khấu hao vào chi phí (Có 214 đối ứng 6xx/154/632); thiếu sổ NKC chi tiết → “Chưa đủ dữ liệu”.
- Bỏ tuổi nợ FIFO ước tính. Chỉ tiêu thiếu nguồn hiển thị “Chưa đủ dữ liệu”.
- Trang Dữ liệu có bảng **Chức năng × dữ liệu nguồn** cho biết chức năng nào đã có dữ liệu thật/mẫu, và cột “Thiếu cột” cho từng file.
- Danh sách báo cáo/cột: `docs/fast_export_requirements_v2.md`.

## 7. Sản xuất Alta Plastics (file HTML)
- Kéo thả file **“Tổng quan sản xuất – Alta Plastics” (.html)** vào trang Dữ liệu. Dashboard đọc khối số liệu `window.BASELINE` nhúng trong file (sổ sản lượng tháng, kế hoạch thổi, kế hoạch cắt + lịch máy + tồn kho, theo dõi máy ngưng, in 3D), **không chạy mã của file**.
- Chỉ số tính bằng đúng mô hình `AltaModel` của file đó (nhúng nguyên văn), nên số khớp với dashboard sản xuất: thổi/cắt so định mức, phế vượt định mức, cuộn chờ cắt, giờ máy ngưng và nguyên nhân, máy cắt không người, đơn thổi còn lại, tồn thành phẩm theo nhóm, mã sắp hết hàng, in 3D, cảnh báo.
- Nối với FAST: doanh thu, giá vốn Alta Plastic theo tháng ÷ kg cắt.
- Truy xuất: file HTML không lưu số dòng Excel, nên nguồn ghi tên file Excel gốc, sheet và khóa (ngày / PO / máy / mã hàng).
