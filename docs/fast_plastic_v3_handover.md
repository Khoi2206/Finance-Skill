# Bàn giao dashboard CFO · CEO v3: nạp báo cáo FAST đơn vị PLASTIC

Ngày kiểm thử: 04/11/2026. Bộ nguồn: `FAST_PLASTIC_DataRoom_2026-11-04` (47 file Excel = 45 nội dung khác nhau + 2 bản trùng; 7 file kê khai/tài liệu). Mọi con số dưới đây là kết quả chạy thật của bản v3 trên bộ nguồn này, không có số mẫu.

## 1. File bàn giao

| File | Ghi chú |
|---|---|
| `dashboard/Alta_CFO_CEO_Dashboard_v3.html` | **Bản mới.** Mở trực tiếp bằng Chrome/Edge. Mở lần đầu không có dữ liệu mẫu. Bản online riêng tư: https://claude.ai/artifact/4EMjJY2DcLqgEkAxqbGRMT. Nút tải Excel/CSV chỉ chạy ở bản mở trực tiếp: khung xem online chặn tải file. |
| `dashboard/Alta_CFO_CEO_Dashboard_v2.html` | Bản cũ, giữ nguyên để so sánh (đổi tên từ `Alta_CFO_CEO_Dashboard.html`). |
| `dashboard/src/dashboard.html` / `dashboard/src/dashboard_v2.html` | Mã nguồn v3 / v2. `python3 scripts/build_dashboard.py` tạo lại bản v3. |
| `docs/fast_plastic_v3_handover.md` | Tài liệu này. |

v3 dùng kho IndexedDB riêng (`alta-fast-dash-v3`) nên dữ liệu đã nạp ở v2 và v3 không lẫn nhau.

### Thay đổi chính so với v2

- **Nạp FAST:** chọn nhiều file hoặc cả thư mục (nút “Chọn cả thư mục”, hoặc kéo thả thư mục).
  - Loại báo cáo nhận theo tiêu đề (dòng một ô chữ ở đầu sheet) và tên cột; tên file chỉ là tín hiệu phụ.
  - Không dựa vào vùng khai báo của sheet (FAST khai báo `A1`) và không cố định dòng tiêu đề.
  - Đã hỗ trợ 24 mẫu báo cáo FAST: NKC, CĐPS, sổ chi tiết 1 TK, CĐPS công nợ 131/331, công nợ theo hóa đơn, theo hạn thanh toán, TSCĐ, khấu hao nhiều kỳ, tăng/giảm TSCĐ, CCDC, chi phí CCDC nhiều kỳ, NXT theo kho, phiếu nhập, phiếu xuất, KQKD theo tháng và lũy kế, CĐKT, LCTT trực tiếp, CPSX theo sản phẩm, đơn hàng bán, sổ nhiều TK, bảng kê bán hàng, bảng kê mua hàng.
  - Mẫu chưa hỗ trợ vào **Danh sách chờ xử lý**: không bỏ lặng lẽ, không nạp sai nhóm.
- **Kê khai nguồn:** các file `file_inventory.json` / `download_manifest.json` cho dashboard biết đơn vị, mã kiểm tra, bản trùng và loại yếu tố chi phí.
  - Đơn vị lấy theo thứ tự: kê khai → cột Đơn vị trong dữ liệu → tên file (ghi “cần xác nhận”). Không suy ra pháp nhân từ dòng tên công ty ở đầu báo cáo.
- **Bản trùng:** nhận theo nội dung (SHA-256 của dữ liệu sheet), chỉ dùng một bản.
  - Nạp lại cùng thư mục thì bỏ qua file đã nạp (cùng mã kiểm tra) trước khi đọc.
  - File mới cùng loại, cùng đơn vị, cùng phạm vi (TK, loại yếu tố, kỳ) thay file cũ.
- **Không cộng trùng nguồn:** NKC là nguồn chính của KQKD. Sổ chi tiết từng TK, KQKD, CĐKT, LCTT của FAST và sổ nhiều TK chỉ dùng để đối chiếu, không cộng vào chỉ tiêu.
- **Trang mới:** **Dữ liệu nguồn** (kiểm tra đầu vào từng file), **Đối chiếu** và **Đơn hàng**.
- **Trang mở rộng:**
  - **Công nợ:** nhóm tuổi của FAST, dư Nợ/dư Có tách riêng, chênh lệch sổ – hóa đơn riêng.
  - **TSCĐ:** danh sách, khấu hao nhiều kỳ, tăng/giảm, CCDC.
  - **Tồn kho:** tồn theo kho, nhập/xuất theo tháng, chi phí sản xuất theo yếu tố 01/02 để riêng.
- **EBITDA:** khấu hao lấy theo Bảng tính khấu hao nhiều kỳ (tháng có bảng); không dùng biến động ròng TK 214; chi phí CCDC không cộng lại.
  - Kết quả PLASTIC 9T/2026: khấu hao 6.046.267.636 = Có TK 214 đối ứng chi phí trên NKC (khớp từng tháng), EBITDA 45.801.117.006.
- **Xuất Excel/CSV:** chỉ tiêu theo kỳ và danh sách vấn đề dữ liệu.
  - Cột: đơn vị, chỉ tiêu, kỳ, đơn vị tính, giá trị, nguồn, công thức, trạng thái đối chiếu, ghi chú chênh lệch.
  - Có thêm sheet nguồn file.

## 2. Bảng nguồn được hỗ trợ / chưa hỗ trợ

### 2.1 47 file Excel trong bộ nguồn

Kết quả: 45 file **Đang dùng**, 2 file **Bản trùng** (không cộng), 0 file chờ xử lý, 0 lỗi.

| # | File | Loại nhận diện (theo tiêu đề + cột) | Phạm vi / kỳ | Dòng dữ liệu | Trạng thái trong v3 |
|---:|---|---|---|---:|---|
| 1 | Báo cáo chi tiết CCDC - PLASTIC - 9T2026.xlsx | Danh sách CCDC | 2026-09 → 2026-09 · chốt 2026-09-30 | 30 | Đang dùng |
| 2 | Báo cáo chi tiết TSCĐ - PLASTIC - 9T2026.xlsx | Danh sách TSCĐ | 2026-09 → 2026-09 · chốt 2026-09-30 | 167 | Đang dùng |
| 3 | Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026 - 204eba51.xlsx | Tăng/giảm TSCĐ | 2026-01 → 2026-09 · chốt 2026-09-30 | 23 | Bản trùng của “Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026.xlsx” (không cộng) |
| 4 | Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026 - 6d585ea2.xlsx | Tăng/giảm TSCĐ | 2026-01 → 2026-09 · chốt 2026-09-30 | 2 | Đang dùng |
| 5 | Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026.xlsx | Tăng/giảm TSCĐ | 2026-01 → 2026-09 · chốt 2026-09-30 | 23 | Đang dùng |
| 6 | Báo cáo kết quả hoạt động sản xuất kinh doanh cho nhiều kỳ - PLASTIC - 9T2026.xlsx | KQKD theo tháng | 2026-01 → 2026-09 | 58 | Đang dùng |
| 7 | Báo cáo kết quả sản xuất kinh doanh - PLASTIC - 9T2026.xlsx | KQKD lũy kế | 2026-01 → 2026-09 · chốt 2026-09-30 | 58 | Đang dùng |
| 8 | Báo cáo lưu chuyển tiền tệ theo phương pháp trực tiếp - PLASTIC - 9T2026.xlsx | LCTT trực tiếp | 2026-01 → 2026-09 · chốt 2026-09-30 | 36 | Đang dùng |
| 9 | Báo cáo tổng hợp chi phí sản xuất theo sản phẩm - PLASTIC - 9T2026 - f586feaa.xlsx | CPSX theo sản phẩm · Loại yếu tố 02 | 2026-01 → 2026-09 · chốt 2026-09-30 | 1.811 | Đang dùng |
| 10 | Báo cáo tổng hợp chi phí sản xuất theo sản phẩm - PLASTIC - 9T2026.xlsx | CPSX theo sản phẩm · Loại yếu tố 01 | 2026-01 → 2026-09 · chốt 2026-09-30 | 1.887 | Đang dùng |
| 11 | Bảng cân đối kế toán - PLASTIC - 9T2026.xlsx | CĐKT | 2026-09 → 2026-09 · chốt 2026-09-30 | 240 | Đang dùng |
| 12 | Bảng cân đối phát sinh các tài khoản - PLASTIC - 9T2026 - 5f8f9568.xlsx | CĐPS tài khoản | 2026-01 → 2026-09 · chốt 2026-09-30 | 254 | Bản trùng của “Bảng cân đối phát sinh các tài khoản - PLASTIC - 9T2026.xlsx” (không cộng) |
| 13 | Bảng cân đối phát sinh các tài khoản - PLASTIC - 9T2026.xlsx | CĐPS tài khoản | 2026-01 → 2026-09 · chốt 2026-09-30 | 254 | Đang dùng |
| 14 | Bảng cân đối phát sinh công nợ của một tài khoản - PLASTIC - 9T2026 - d6a99c49.xlsx | CĐPS công nợ 131 TK131 | 2026-01 → 2026-09 · chốt 2026-09-30 | 433 | Đang dùng |
| 15 | Bảng cân đối phát sinh công nợ của một tài khoản - PLASTIC - 9T2026.xlsx | CĐPS công nợ 331 TK331 | 2026-01 → 2026-09 · chốt 2026-09-30 | 540 | Đang dùng |
| 16 | Bảng kê công nợ của các hóa đơn theo hạn thanh toán - PLASTIC - 9T2026 - 4e3103dc.xlsx | Tuổi nợ phải thu theo hạn TK131 | 2026-09 → 2026-09 · chốt 2026-09-30 | 694 | Đang dùng |
| 17 | Bảng kê công nợ của các hóa đơn theo hạn thanh toán - PLASTIC - 9T2026.xlsx | Tuổi nợ phải trả theo hạn TK331 | 2026-09 → 2026-09 · chốt 2026-09-30 | 758 | Đang dùng |
| 18 | Bảng kê công nợ phải trả theo hóa đơn - PLASTIC - 9T2026.xlsx | Công nợ phải trả theo hóa đơn TK331 | 2000-01 → 2026-09 · chốt 2026-09-30 | 4.530 | Đang dùng |
| 19 | Bảng kê công nợ theo hóa đơn - PLASTIC - 9T2026.xlsx | Công nợ phải thu theo hóa đơn TK131 | 2000-01 → 2026-09 · chốt 2026-09-30 | 8.162 | Đang dùng |
| 20 | Bảng kê hóa đơn bán hàng, dịch vụ - Alta Plastic - PLASTIC - 9T2026.xlsx | Bảng kê hóa đơn bán hàng | 2026-01 → 2026-09 · chốt 2026-09-30 | 6.591 | Đang dùng |
| 21 | Bảng kê mua hàng - Alta Plastic - PLASTIC - 9T2026.xlsx | Bảng kê mua hàng | 2026-01 → 2026-09 · chốt 2026-09-30 | 6.107 | Đang dùng |
| 22 | Bảng kê phiếu nhập - PLASTIC - 9T2026.xlsx | Bảng kê phiếu nhập | 2026-01 → 2026-09 · chốt 2026-09-30 | 6.105 | Đang dùng |
| 23 | Bảng kê phiếu xuất - PLASTIC - 9T2026.xlsx | Bảng kê phiếu xuất | 2026-01 → 2026-09 · chốt 2026-09-30 | 61.825 | Đang dùng |
| 24 | Bảng kê đơn hàng bán - PLASTIC - 9T2026.xlsx | Đơn hàng bán | 2026-03 → 2026-09 | 34.826 | Đang dùng |
| 25 | Bảng tính chi phí CCDC nhiều kỳ - PLASTIC - 9T2026.xlsx | Chi phí CCDC nhiều kỳ | 2026-01 → 2026-09 · chốt 2026-09-30 | 30 | Đang dùng |
| 26 | Bảng tính khấu hao TSCĐ nhiều kỳ - PLASTIC - 9T2026.xlsx | Khấu hao nhiều kỳ | 2026-01 → 2026-09 · chốt 2026-09-30 | 101 | Đang dùng |
| 27 | Sổ chi tiết của một tài khoản - TK131 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK131 | 2026-01 → 2026-09 · chốt 2026-09-30 | 26.668 | Đang dùng |
| 28 | Sổ chi tiết của một tài khoản - TK154 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK154 | 2026-01 → 2026-09 · chốt 2026-09-30 | 7.120 | Đang dùng |
| 29 | Sổ chi tiết của một tài khoản - TK211 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK211 | 2026-01 → 2026-09 · chốt 2026-09-30 | 77 | Đang dùng |
| 30 | Sổ chi tiết của một tài khoản - TK214 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK214 | 2026-01 → 2026-09 · chốt 2026-09-30 | 201 | Đang dùng |
| 31 | Sổ chi tiết của một tài khoản - TK241 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK241 | 2026-01 → 2026-09 · chốt 2026-09-30 | 1 | Đang dùng |
| 32 | Sổ chi tiết của một tài khoản - TK242 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK242 | 2026-01 → 2026-09 · chốt 2026-09-30 | 64 | Đang dùng |
| 33 | Sổ chi tiết của một tài khoản - TK331 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK331 | 2026-01 → 2026-09 · chốt 2026-09-30 | 11.273 | Đang dùng |
| 34 | Sổ chi tiết của một tài khoản - TK341 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK341 | 2026-01 → 2026-09 · chốt 2026-09-30 | 138 | Đang dùng |
| 35 | Sổ chi tiết của một tài khoản - TK511 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK511 | 2026-01 → 2026-09 · chốt 2026-09-30 | 17.299 | Đang dùng |
| 36 | Sổ chi tiết của một tài khoản - TK521 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK521 | 2026-01 → 2026-09 · chốt 2026-09-30 | 137 | Đang dùng |
| 37 | Sổ chi tiết của một tài khoản - TK621 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK621 | 2026-01 → 2026-09 · chốt 2026-09-30 | 13.839 | Đang dùng |
| 38 | Sổ chi tiết của một tài khoản - TK622 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK622 | 2026-01 → 2026-09 · chốt 2026-09-30 | 351 | Đang dùng |
| 39 | Sổ chi tiết của một tài khoản - TK627 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK627 | 2026-01 → 2026-09 · chốt 2026-09-30 | 3.009 | Đang dùng |
| 40 | Sổ chi tiết của một tài khoản - TK632 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK632 | 2026-01 → 2026-09 · chốt 2026-09-30 | 20.821 | Đang dùng |
| 41 | Sổ chi tiết của một tài khoản - TK635 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK635 | 2026-01 → 2026-09 · chốt 2026-09-30 | 353 | Đang dùng |
| 42 | Sổ chi tiết của một tài khoản - TK641 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK641 | 2026-01 → 2026-09 · chốt 2026-09-30 | 2.531 | Đang dùng |
| 43 | Sổ chi tiết của một tài khoản - TK642 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK642 | 2026-01 → 2026-09 · chốt 2026-09-30 | 678 | Đang dùng |
| 44 | Sổ chi tiết của một tài khoản - TK821 - PLASTIC - 9T2026.xlsx | Sổ chi tiết TK TK821 | 2026-01 → 2026-09 · chốt 2026-09-30 | 0 | Đang dùng |
| 45 | Sổ chi tiết lên cho nhiều tài khoản - PLASTIC - 9T2026.xlsx | DS số dư nhiều TK | 2026-01 → 2026-09 · chốt 2026-09-30 | 254 | Đang dùng |
| 46 | Sổ nhật ký chung - PLASTIC - 9T2026.xlsx | Sổ nhật ký chung | 2026-01 → 2026-09 · chốt 2026-09-30 | 167.330 | Đang dùng |
| 47 | Tổng hợp nhập xuất tồn theo kho - PLASTIC - 9T2026.xlsx | NXT theo kho | 2026-01 → 2026-09 · chốt 2026-09-30 | 6.663 | Đang dùng |

Ngoài 47 file Excel, v3 đọc 7 file khác:

- **Kê khai** (đọc làm cấu hình, không nạp số): `file_inventory.json`, `download_manifest.json`.
- **Ghi chép báo cáo đã thử:** `supplemental_checks.json`.
- **Tài liệu tham khảo** (không nạp số): `report_catalog.json`, `audit_catalog.json`, `00_Muc_luc_FAST_PLASTIC.html`, `02_Huong_dan_nap_va_review.md`.

Danh mục menu FAST có 413 mục. Đây **không** phải 413 báo cáo đã tải: dashboard chỉ hiển thị các báo cáo có file.

### 2.2 Chưa có dữ liệu nguồn phù hợp (FAST trả dòng trắng)

| Báo cáo FAST | Bộ lọc đã thử | Hiển thị trong dashboard |
|---|---|---|
| Bảng kê đơn hàng mua (13.60.12) | PLASTIC 01/01–30/09/2026, mọi loại/trạng thái | “Chưa có dữ liệu nguồn phù hợp” (trang Đơn hàng) |
| Chi phí theo vụ việc / công trình TK 154 (rpt_covvth3) | PLASTIC 9T/2026, TK 154 | “Chưa có dữ liệu nguồn phù hợp” (trang Tồn kho) |
| So sánh NVL thực tế – định mức (16.80.37) | PLASTIC kỳ 1–9/2026 | “Chưa có dữ liệu nguồn phù hợp” (trang Tồn kho) |

Không có số 0 nào được điền thay cho các mục này.

### 2.3 Chỉ tiêu cần nguồn chưa đủ

- **Vòng quay hàng tồn kho, DIO:** để “Chưa đủ dữ liệu” vì NXT không khớp sổ (mục 3).
- **Giao hàng thực tế theo đơn:** để “Chưa đủ dữ liệu”. Phiếu xuất không có số đơn hàng, và 54.194 dòng có tiền = 0.
- **Chi phí thuế TNDN / LNST:** TK 821 không có phát sinh nên LNST gắn nhãn “Thuế TNDN chưa xác nhận”, không kết luận thuế bằng 0.
- **Hàng chậm luân chuyển:** tính trên NXT 9 tháng. Cần đọc cùng cảnh báo tồn âm.

## 3. Chênh lệch còn lại và thiếu dữ liệu (kết quả chạy thật)

Trang **Đối chiếu**: 76 kiểm tra, gồm 50 đạt, 20 cần xem, 6 không đạt. Dashboard không điều chỉnh số để khớp. Những chênh lệch đã tìm được bằng chứng có ghi rõ phần giải thích được và phần còn lại.

### 3.1 Không đạt: chưa có bằng chứng giải thích, cần kế toán xử lý

1. **Bảng kê bán hàng vs TK 511:** bảng kê 260.999.810.468, TK 511 (loại 911 và bút toán chuyển 521→511) 257.128.936.602, chênh **3.870.873.866**. Đối chiếu theo từng số chứng từ cho thấy toàn bộ chênh nằm ở:
   - 6.684 chứng từ ghi TK 511 trên NKC nhưng không có trên bảng kê, ảnh hưởng 3.689.573.300, chủ yếu chứng từ loại HD điều chỉnh (DC…);
   - 8 chứng từ chỉ có trên bảng kê, 100.168.625;
   - 8 chứng từ có ở cả hai nhưng khác số, 81.131.941;
   - còn lại 0.

   Theo TK công nợ, phần lớn ở 13111T:
   - Bảng kê 13111T là 3.698.762.510.
   - Trên NKC, Có 511 đối ứng 13111T là 84.305.280.126, sau đó ghi âm −84.294.148.356.

   Đã xác định được chứng từ gây chênh, nhưng chưa có bằng chứng về lý do nghiệp vụ, nên vẫn để “Không đạt”. Cảnh báo không bị xóa.
2. **Tồn kho NXT vs TK 152, 153, 155, 156, 157:** NXT −1.028.689.955.883, CĐPS 59.004.136.018.
   - Kho PL.01T có tồn cuối −1.226,4 tỷ (xuất 1.220,9 tỷ, nhập −5,5 tỷ).
   - 2.007 mã hàng tồn cuối âm.
   - Bảng kê phiếu xuất có 54.194 dòng tiền = 0.

   Cần kế toán chạy lại tính giá xuất kho, kiểm tra kho PL.01T và TK tồn kho cấu hình (đổi ở Dữ liệu nguồn › Thiết lập).
3. **Nguyên giá danh sách TSCĐ vs TK 211–213:** 65.240.393.027 vs 67.267.837.993, chênh **−2.027.444.966**. Chưa giải thích; có thể liên quan các bút toán ghi tăng chưa có trên báo cáo tăng (mục 3.2.6), cần kế toán xác nhận.
4. **Hao mòn lũy kế danh sách TSCĐ vs TK 214:** 32.663.825.576 vs 32.489.502.318, chênh **174.323.258**. Chưa giải thích.
5. **CĐKT FAST không cân:** tổng cộng tài sản (mã 280) 162.409.534.780 vs tổng cộng nguồn vốn (mã 440) 160.095.005.053, chênh 2.314.529.727. Báo cáo theo mẫu TT99; chỉ dùng đối chiếu (tiền mã 110 khớp CĐPS).
6. **LCTT FAST mã 70 vs tiền cuối kỳ:** 3.362.590.665 vs 4.248.297.762, chênh −885.707.097. Mã 60 (tiền đầu kỳ) khớp.

### 3.2 Cần xem: đã tìm được bằng chứng hoặc là thông tin quản trị

1. **TK 13111G lệch khoảng 13 triệu** (cảnh báo ở bản trước): NKC có 1 dòng ghi mã **“13111g”** (chữ thường), Nợ 13.000.000. CĐPS của FAST gộp vào 13111G. v3 chuẩn hóa chữ hoa (có cảnh báo, xem được dòng chứng từ), nên phát sinh từng TK NKC = CĐPS khớp toàn bộ 148 TK chi tiết. Nên sửa mã trên chứng từ.
2. **Bảng kê vs TK 511 đối ứng 13111G:** chênh 8.030.500 (22.367.164.282 vs 22.359.133.782). Xem chứng từ ở kiểm tra bán hàng, nhóm theo số chứng từ.
3. **KQKD FAST dòng 10 vs NKC:** chênh −1.398.427.241, giải thích đủ từ nguồn:
   - dòng 01 đã sau bút toán chuyển 521→511 (1.396.659.181) nhưng dòng 02 vẫn trừ 1.396.659.181, tức giảm trừ bị trừ hai lần trên mẫu KQKD;
   - cộng số dư TK 511/521 chưa kết chuyển 911 (−1.768.060);
   - còn lại 0.

   Doanh thu thuần trên dashboard = 255.734.182.421 (theo NKC).
4. **KQKD FAST dòng 50 vs LNTT theo NKC:** 35.413.647.855 vs 37.120.651.173, giải thích đủ:
   - giảm trừ bị trừ hai lần: −1.396.659.181;
   - số dư TK loại 5–8 chưa kết chuyển 911 cuối kỳ: −310.344.137 (chủ yếu 63218 −316.966.000, 6427P 8.846.571, 6421 3.477.744, 6428 −3.806.320);
   - còn lại 0.
5. **KQKD nhiều kỳ dòng 01, tháng 4:** lệch 136.940, bằng số dư TK 51121B chưa kết chuyển.
6. **Tăng TSCĐ: báo cáo 14.734.748.844 vs PS Nợ 211 là 17.721.808.166.** Chênh 2.987.059.322 tách đủ theo nguồn ghi tăng:
   - 2.165.549.859 là 7 dòng Nợ 211 / Có 1541MM ngày 21/09/2026 (M01–M06/09), không có trên báo cáo tăng;
   - 821.509.463 là Nợ 211 / Có 4211 (Q01/01, 02/01/2026);
   - phần mua mới khớp 14.035.832.574.

   Chứng từ M06/09 có 2 dòng giống hệt (58.752.888 × 2), cần kiểm tra ghi trùng.
7. **Giảm TSCĐ:** 2 thẻ (06.08.37, 07.01.05), nguyên giá = hao mòn = 138.104.893, GTCL 0. Khớp Nợ TK 214 đối ứng 211/811 trên NKC.
8. **Tuổi nợ phải thu:** báo cáo theo hạn (chốt 30/09/2026) 16.523.101.687, trong khi bảng kê theo hóa đơn 38.553.263.836.
   - Đối chiếu từng hóa đơn: **453 hóa đơn còn dư (22.030.162.149) không có trong báo cáo theo hạn**; còn lại 0.
   - Chưa rõ nguyên nhân (bộ lọc khi xuất?). Nhóm tuổi trên trang Công nợ chỉ phủ 42,9% số dư.
9. **Tuổi nợ phải trả:** báo cáo theo hạn 28.410.018.625 vs bảng kê theo hóa đơn 36.535.631.411.
   - 276 hóa đơn còn dư (7.298.866.664) không có trong báo cáo theo hạn.
   - 53 hóa đơn có ở cả hai báo cáo nhưng khác số còn lại (−826.746.122).
   - Còn lại 0.
   - 304 hóa đơn phải trả còn dư không có hạn thanh toán (18.554.608.106): không xếp tuổi, không coi là trong hạn.
10. **Hóa đơn so với sổ:**
    - Phải thu: theo hóa đơn 38.553.263.836, theo sổ 38.024.307.807. FAST tự in cột “Chênh lệch” cho 29 khách, tổng 512.786.220.
    - Phải trả: theo hóa đơn 36.535.631.411, theo sổ ròng 23.909.868.334.
11. **Dư Nợ / dư Có:** báo cáo theo đối tượng và CĐPS chênh hai chiều bằng nhau, do CĐPS bù trừ theo tiểu khoản. v3 giữ số theo từng đối tượng, không bù trừ giữa các đối tượng.
    - Phải thu: Nợ 38.045.911.854 / Có 21.604.047.
    - Phải trả: Có 28.194.038.669 / Nợ 4.284.170.335.
12. **Dòng tiền NKC chưa phân loại:** −2.000.002.874, giữ riêng, không gán vào HĐKD.
13. **TK 821:** 0 dòng phát sinh. Thuế TNDN chưa xác nhận.

### 3.3 Đã khớp (trích)

- NKC: Nợ = Có = 2.626.869.891.851 = dòng Tổng cộng. 39.735/39.735 chứng từ tách được cặp Nợ/Có, nên TK đối ứng không bị gán tùy tiện.
- Phát sinh và số dư 148 TK chi tiết: NKC = CĐPS.
- 18 sổ chi tiết TK (131, 154, 211, 214, 241, 242, 331, 341, 511, 521, 621, 622, 627, 632, 635, 641, 642, 821) khớp NKC cả phát sinh lẫn số dư đầu/cuối.
- CĐPS công nợ 131 và 331 khớp số dư ròng TK 131/331.
- Khấu hao bảng nhiều kỳ = NKC Có 214 đối ứng chi phí = CĐPS Có 214 = 6.046.267.636.
- Chi phí CCDC nhiều kỳ = Có TK 242 = 689.238.228.
- CĐKT mã 110 = tiền theo CĐPS = 4.248.297.762.
- Sổ nhiều TK = CĐPS.

## 4. Hướng dẫn ngắn: chọn cả thư mục FAST và nạp lại

1. Mở `Alta_CFO_CEO_Dashboard_v3.html` bằng Chrome hoặc Edge (cần mạng lần đầu để tải thư viện đọc Excel và vẽ biểu đồ).
2. Vào **Dữ liệu nguồn** → **Chọn cả thư mục** → chọn thư mục DataRoom (gồm `01_File_FAST_goc` và các file `.json`), hoặc kéo thả cả thư mục vào khung nạp. Bộ 54 file mất khoảng 1–2 phút; sổ NKC lớn nhất.
3. Xem bảng **Kiểm tra đầu vào từng file**: loại báo cáo, đơn vị (và cơ sở xác định), kỳ / ngày chốt, dòng dữ liệu thật (rê chuột để xem cách đếm), cảnh báo, vai trò. Xử lý **Danh sách chờ**:
   - file chi phí sản xuất chưa có loại yếu tố thì chọn 01/02;
   - file chưa nhận được đơn vị thì chọn đơn vị.
4. Vào **Đối chiếu** đọc các mục “Không đạt” / “Cần xem”; bấm dòng có nhãn “xem chứng từ” để truy về file, sheet, dòng Excel. Bấm **Tải Excel chỉ tiêu & vấn đề** để gửi kế toán.
5. **Nạp lại** sau khi xuất lại từ FAST: chọn lại cả thư mục.
   - File giống hệt được bỏ qua.
   - File mới cùng loại, đơn vị, phạm vi thay file cũ; file cũ hiện “Bị thay bởi file mới hơn cùng phạm vi”.
   - File trùng nội dung chỉ dùng một bản.
   - Có thể tắt/bật hoặc xóa từng file.
   - Muốn làm lại từ đầu: **Xóa toàn bộ dữ liệu đã nạp**.
6. Dashboard tự chọn phạm vi **Plastic** khi chỉ có dữ liệu một công ty. Chọn “Tập đoàn” chỉ có ý nghĩa khi đã nạp đủ cả 3 công ty.

## 5. Kiểm thử đã chạy (Chromium, bộ nguồn thật)

| Kịch bản | Kết quả |
|---|---|
| Nạp cả 54 file một lần | 45 đang dùng, 2 bản trùng, 7 tham khảo/kê khai; 167.330 dòng NKC; 0 lỗi trình duyệt |
| Nạp theo thứ tự ngược | Cùng kết quả (doanh thu thuần 255.734.182.421, LNTT 37.120.651.173, EBITDA 45.801.117.006) |
| Nạp Excel trước, kê khai sau | Trước kê khai: bản trùng vẫn nhận theo nội dung; 2 file CPSX chờ chọn loại yếu tố; đơn vị theo tên file “cần xác nhận”. Sau kê khai: hết chờ, cùng kết quả |
| Nạp lại cùng thư mục | Không thêm file (54), khoảng 5 giây |
| Tải lại trang | Dữ liệu giữ trong IndexedDB, chỉ tiêu không đổi |
| Báo cáo cùng tên khác TK (18 sổ chi tiết, CĐPS công nợ 131 và 331, tuổi nợ phải thu/phải trả) | Mỗi file một phạm vi riêng, không thay nhau |
| Chọn tay loại yếu tố trùng phạm vi | File sau thay file trước; đổi lại thì cả 01 và 02 cùng được dùng, không cộng lẫn |
| Tắt NKC | KQKD theo NKC chuyển “Chưa đủ dữ liệu”; bật lại trở về số cũ |
| Xóa bản chính của cặp trùng | Bản còn lại tự thành bản dùng |
| Hóa đơn trước 2026 | 1.512/8.162 hóa đơn phải thu trước 2026 được giữ (còn dư 2.250.894.477) |
| Dòng tổng | Khớp dòng Tổng cộng của NKC, bảng kê, CĐPS, TSCĐ; không cộng dòng tổng / dòng nhóm / dòng tổng chứng từ |
| Truy xuất | Mọi thẻ, ô bảng, cột biểu đồ, kiểm tra có “xem chứng từ” mở danh sách dòng gốc kèm file › sheet · dòng Excel; tổng dòng = số hiển thị |
| Chức năng cũ | CEO, CFO, Bán hàng, Sản xuất (nạp file HTML “Tổng quan sản xuất”) chạy bình thường |
| Màn hình 390 px | Không cuộn ngang trang |
