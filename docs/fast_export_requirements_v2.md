# Báo cáo và cột cần xuất từ FAST — bổ sung đợt 2 (công nợ, TSCĐ, khấu hao, tồn kho)

Ngày: 2026-11-04 · Áp dụng cho: `dashboard/` và `alta-finance-intelligence/`
Tên báo cáo trên FAST là tên thường gặp trong FAST Business; tên menu và mẫu cột có thể khác theo phiên bản. Mọi mục dưới đây là `[ALTA VALIDATION REQUIRED]` cho đến khi có file mẫu thật.

## 1. Hiện trạng: chức năng đã có ≠ dữ liệu đã nạp

**Dữ liệu thật của Alta đã nạp: chưa có file nào.** Mọi số đang hiển thị trên dashboard là dữ liệu mẫu (có nhãn "DỮ LIỆU MẪU"), hoặc file thử tổng hợp do Claude tạo theo khuôn FAST.

| Chức năng | Chức năng đã có trong dashboard? | Báo cáo FAST làm nguồn | Đã nạp dữ liệu thật? | Khi thiếu dữ liệu |
|---|---|---|---|---|
| KQKD, LN gộp, LNTT, LNST | Có | Sổ nhật ký chung (NKC) | Chưa | Ô trống, ghi cần nạp NKC |
| Lãi vay | Có | NKC (dòng TK 635 + diễn giải/đối ứng) | Chưa | "Chưa đủ dữ liệu" nếu tháng chỉ có CĐPS |
| **Khấu hao vào chi phí / EBITDA (sửa ở đợt này)** | Có (sửa) | NKC (TK 214 kèm TK đối ứng) + Bảng tính khấu hao TSCĐ để đối chiếu | Chưa | "Chưa đủ dữ liệu" nếu tháng không có NKC chi tiết |
| Số dư tiền, phải thu, phải trả, tồn kho, nợ vay | Có | Bảng cân đối số phát sinh (CĐPS) | Chưa | "–" và ghi chú thiếu số dư đầu kỳ |
| Dòng tiền trực tiếp | Có | NKC (TK 111/112/113 + đối ứng) | Chưa | Ô trống |
| **Công nợ theo đối tượng (dư đầu, phát sinh, thanh toán, dư cuối)** | Mới (đợt này) | Bảng tổng hợp công nợ phải thu / phải trả | Chưa | Dư đầu/dư cuối: "Chưa đủ dữ liệu"; phát sinh lấy từ NKC nếu có |
| **Công nợ theo hóa đơn, hạn thanh toán, số ngày quá hạn** | Mới | Báo cáo công nợ theo hóa đơn (có Hạn thanh toán) | Chưa | "Chưa đủ dữ liệu", **không** tự tính tuổi nợ |
| **Đối chiếu công nợ với TK 131/331** | Mới | Tổng hợp công nợ + CĐPS | Chưa | Kiểm tra không chạy |
| **TSCĐ: nguyên giá, tăng/giảm, hao mòn, GTCL, khấu hao theo tài sản/bộ phận/tháng** | Mới | Bảng tính và phân bổ khấu hao TSCĐ (hoặc Sổ TSCĐ + Báo cáo tăng giảm TSCĐ) | Chưa | "Chưa đủ dữ liệu" |
| **Phân tích biến động TK 214 (khấu hao, thanh lý, điều chuyển, điều chỉnh)** | Mới | NKC | Chưa | Ô trống |
| **Tồn kho theo mã hàng/kho** | Mới | Báo cáo tổng hợp nhập – xuất – tồn | Chưa | "Chưa đủ dữ liệu" |
| **Hàng chậm luân chuyển** | Mới | Nhập – xuất – tồn **từng tháng** (≥ 3 tháng liên tiếp), hoặc thẻ kho có ngày xuất cuối | Chưa | "Chưa đủ dữ liệu" khi lịch sử < 3 tháng |
| Tuổi nợ FIFO ước tính (bản cũ) | **Đã gỡ bỏ** | — | — | Thay bằng tuổi nợ theo hạn thanh toán từ FAST |

## 2. Báo cáo cần xuất thêm (mỗi công ty, mỗi tháng)

### 2.1 Bảng tổng hợp công nợ phải thu (và phải trả)
- **Kỳ:** 01 → ngày cuối tháng. **Tài khoản:** 131 (phải thu); 331 (phải trả). Nếu FAST cho chọn, xuất **tất cả tiểu khoản** (gồm 13111T).
- **Cột bắt buộc:** Mã khách/Mã NCC (mã đối tượng) · Tên · Dư nợ đầu kỳ · Dư có đầu kỳ · Phát sinh nợ · Phát sinh có · Dư nợ cuối kỳ · Dư có cuối kỳ.
- **Cột nên có:** Tài khoản (khi gộp nhiều tiểu khoản).
- **Tên file:** `Cong no phai thu YYYY-MM - <Công ty>.xlsx`, `Cong no phai tra YYYY-MM - <Công ty>.xlsx`.
- **Dùng cho:** bảng công nợ theo đối tượng; đối chiếu tổng với TK 131/331 trên CĐPS.

### 2.2 Báo cáo công nợ theo hóa đơn (phải thu, phải trả)
Chỉ có khi Alta bật **theo dõi công nợ theo hóa đơn / thanh toán theo hóa đơn** trên FAST. Cần kế toán xác nhận (câu hỏi mở #6 trong đặc tả).
- **Ngày lấy số:** ngày cuối tháng.
- **Cột bắt buộc:** Mã đối tượng · Tên · Số hóa đơn · Ngày hóa đơn · **Hạn thanh toán (ngày đến hạn)** · Số tiền hóa đơn (hoặc phát sinh) · Đã thanh toán · Còn lại (dư cuối).
- **Cột nên có:** Dư đầu kỳ của hóa đơn · Thanh toán trong kỳ · Số ngày quá hạn (nếu FAST tính sẵn) · Tài khoản.
- **Tên file:** `Cong no theo hoa don phai thu YYYY-MM - <Công ty>.xlsx` (tương tự cho phải trả).
- **Quy tắc trên dashboard:**
  - Số ngày quá hạn lấy từ cột của FAST, nếu không có thì tính = ngày lấy số − Hạn thanh toán **do FAST xuất**.
  - Hóa đơn không có hạn thanh toán được xếp nhóm "Không có hạn TT", không tự gán kỳ hạn.

### 2.3 Bảng tính và phân bổ khấu hao TSCĐ (kèm tăng/giảm)
- **Kỳ:** từng tháng (để có khấu hao theo tháng). Có thể thay bằng Sổ TSCĐ + Báo cáo tăng giảm TSCĐ nếu FAST tách riêng.
- **Cột bắt buộc:** Mã tài sản · Tên tài sản · Nguyên giá (đầu kỳ, tăng, giảm, cuối kỳ) · Khấu hao trong kỳ · Hao mòn lũy kế (đầu kỳ, giảm, cuối kỳ) · Giá trị còn lại cuối kỳ.
- **Cột nên có:** Nhóm/loại tài sản · **Bộ phận sử dụng** · Ngày bắt đầu tính khấu hao · Số tháng khấu hao · TK chi phí khấu hao · TK nguyên giá (211/213).
- Nếu chỉ có nguyên giá cuối kỳ và hao mòn cuối kỳ, các cột tăng/giảm hiển thị "Chưa đủ dữ liệu".
- **Tên file:** `TSCD YYYY-MM - <Công ty>.xlsx`.
- **Dùng cho:** trang TSCĐ; đối chiếu nguyên giá với TK 211/212/213 và hao mòn với TK 214; đối chiếu khấu hao trong kỳ với phát sinh Có TK 214 đối ứng chi phí trên NKC.

### 2.4 Báo cáo tổng hợp nhập – xuất – tồn
- **Kỳ:** từng tháng, **liên tục ít nhất 3 tháng gần nhất**; nên có 6–12 tháng để xếp hàng chậm luân chuyển ≥ 6 tháng.
- **Cột bắt buộc:** Mã kho (hoặc dòng nhóm "Kho: …") · Mã vật tư/hàng · Tên · ĐVT · Tồn đầu (SL, GT) · Nhập (SL, GT) · Xuất (SL, GT) · Tồn cuối (SL, GT).
- **Cột nên có:** TK vật tư (152/153/155/156) để đối chiếu theo từng TK; Nhóm vật tư.
- **Tùy chọn thay thế:** Sổ chi tiết vật tư / thẻ kho (Ngày, Mã kho, Mã vật tư, Nhập SL/GT, Xuất SL/GT) để có ngày xuất gần nhất. Chưa xây parser (Phase sau).
- **Tên file:** `NXT YYYY-MM - <Công ty>.xlsx`.
- **Dùng cho:** tồn kho theo mã/kho; số tháng liên tiếp không xuất; đối chiếu tổng giá trị tồn với TK 152, 153, 155, 156, 157.

### 2.5 Sổ nhật ký chung (đã có trong danh sách cũ): yêu cầu thêm
- Bắt buộc có cột **TK đối ứng** trên mọi dòng. Không có cột này thì không tách được khấu hao khỏi thanh lý/điều chuyển, và EBITDA sẽ hiển thị "Chưa đủ dữ liệu".
- Giữ cột **Mã đối tượng** để đối chiếu phát sinh công nợ theo khách/NCC.

## 3. Quy tắc tính mới (bổ sung vào `docs/accounting_policies.md`)
| Mã | Quy tắc |
|---|---|
| P4 (sửa) | **Khấu hao cho EBITDA = phát sinh Có TK 214 có TK đối ứng là chi phí/giá thành (6xx, 154, 632)**. Không dùng biến động ròng TK 214. |
| P12 | Biến động TK 214 tách 4 nhóm theo TK đối ứng: Khấu hao vào chi phí (6xx, 154, 632) · Thanh lý/nhượng bán (211, 212, 213, 217, 811) · Điều chuyển (214, 136, 336, 1388, 3388, 411) · Điều chỉnh khác (còn lại). |
| P13 | Tuổi nợ chỉ tính theo **hạn thanh toán do FAST xuất**. Nhóm: Chưa đến hạn, 1–30, 31–60, 61–90, 91–180, > 180 ngày, Không có hạn TT. |
| P14 | Hàng chậm luân chuyển = mã còn tồn cuối > 0 và **không có lượng xuất** trong N tháng liên tiếp gần nhất đã nạp (mặc định 3 và 6 tháng). Lịch sử đã nạp < 3 tháng: "Chưa đủ dữ liệu". |
