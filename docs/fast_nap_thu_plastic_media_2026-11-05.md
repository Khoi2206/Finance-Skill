# Nạp thử dashboard với hai bộ FAST PLASTIC + MEDIA (05/11/2026)

Nguồn: `ALTA_PLASTIC_FAST_9T2026_NAP_CLAUDE.zip` (47 Excel) và `ALTA_MEDIA_FAST_9T2026_NAP_CLAUDE.zip` (49 Excel), giải nén nguyên trạng, không sửa Excel gốc. HTML kiểm tra: `dashboard/Alta_CFO_CEO_Dashboard_v3.html` (bản 3.2) và `dashboard/Alta_CFO_CEO_Dashboard_v3_offline.html`. Mọi số dưới đây là kết quả chạy thật trên Chromium bằng bộ nạp của dashboard: chọn cả hai thư mục, qua bước rà soát, rồi nạp.

## 1. Kết quả tổng

| | PLASTIC | MEDIA | ALTA |
|---|---:|---:|---|
| Excel ghi nhận | 47 | 49 | 0 — chưa xuất / chưa nạp |
| Đang dùng (nguồn chính, đối chiếu hoặc thông tin quản trị) | 44 | 38 | — |
| Đã xuất, trống theo bộ lọc | 1 | 11 | — |
| Bản trùng cùng phạm vi (không cộng) | 2 | 0 | — |
| Chờ xử lý / chưa hỗ trợ / lỗi | 0 | 0 | — |
| Dòng NKC chuẩn hóa | 167.330 | 26.872 | — |
| Doanh thu thuần 9T (NKC, loại 911) | 255.734.182.421 | 65.291.680.758 | không hiện số 0 |
| LNTT 9T (NKC) | 37.120.651.173 | 2.427.885.080 | — |
| Khấu hao 9T (bảng khấu hao nhiều kỳ) | 6.046.267.636 | 11.514.749.892 | — |
| EBITDA 9T | 45.801.117.006 | 15.998.475.652 | — |
| Kiểm tra đối chiếu (đạt / cần xem / không đạt) | 50 / 20 / 6 | 57 / 10 / 4 | 1 cần xem: chưa nạp |

Các tài liệu JSON/Markdown/HTML (17 mục) là metadata/tham khảo, không tính vào 96 Excel.

## 2. Kiểm tra theo điều kiện đạt

| # | Điều kiện | Kết quả |
|---|---|---|
| 1 | Bảng xác nhận từng Excel | Đạt. Bảng ở mục 6 (và trang Dữ liệu nguồn, sheet `Nguon_file` khi xuất). 96/96 file có trạng thái; không file nào bị bỏ qua. |
| 2 | MEDIA đúng công ty; sổ chi tiết, BCTC riêng; hai thứ tự cho cùng kết quả; thêm MEDIA không đổi số PLASTIC | Đạt. MEDIA gán đơn vị theo kê khai + bộ lọc `ma_dvcs`; thư mục `ALTA_MEDIA_…` không bị hiểu là công ty mẹ. Nạp PLASTIC → MEDIA và MEDIA → PLASTIC cho cùng số từng đơn vị (bảng mục 1). Số PLASTIC trước và sau khi thêm MEDIA giống hệt. Sổ chi tiết, KQKD, CĐKT, LCTT FAST giữ theo từng đơn vị; kiểm tra chạy riêng từng đơn vị. |
| 3 | Loại đúng 2 bản PLASTIC trùng; không gộp file trống khác công ty/bộ lọc | Đạt. Chỉ 2 bản trùng (CĐPS `…5f8f9568`, tăng TSCĐ `…204eba51`). TK 821 trống của hai công ty, CPSX MEDIA loại 01 và 02 (cùng nội dung ô) và tài sản giảm MEDIA đều giữ riêng, trạng thái “đã xuất, trống”. |
| 4 | KQKD công trình MEDIA; 3 nguồn bổ sung | Đạt. Đọc 515 dòng vụ việc từ 522 dòng sheet (1 dòng Tổng cộng, 1 dòng trống, 5 dòng tiêu đề). Ps, Lk đn, Lk giữ riêng; tổng từng cột khớp dòng Tổng cộng (D.thu thuần 65.379.370.746). Xem ở cuối trang Bán hàng khi chọn MEDIA. Ba nguồn bổ sung đã có bộ đọc; file MEDIA đều trống nên hiện “Đã xuất, trống theo bộ lọc”. PLASTIC không có file cho ba nguồn này và hiện “Chưa có dữ liệu nguồn phù hợp” theo `supplemental_checks.json`. |
| 5 | Không cộng NKC với sổ chi tiết/tổng hợp; truy nguồn; không sửa số | Đạt. Chỉ tiêu KQKD lấy từ NKC; sổ chi tiết, sổ nhiều TK, KQKD/CĐKT/LCTT FAST chỉ để đối chiếu. Mọi số có truy nguồn tới file › sheet · dòng Excel. Chênh lệch giữ nguyên ở trang Đối chiếu. |
| 6 | Phạm vi đơn vị/kỳ; không gắn nhãn 12T cho 9T; trạng thái đối chiếu kế thừa thành phần | Đạt sau khi sửa. Chọn MEDIA, kỳ T5/2026: file xuất chỉ có dòng MEDIA, chỉ tiêu tháng T1–T5 và lũy kế T1–T5; số dư sổ cái cuối T5. Báo cáo snapshot (công nợ, TSCĐ, tuổi nợ) ghi “Snapshot T9/26 (khác kỳ chọn T5/26)”. Có sheet `Pham_vi`. Thẻ nợ vay ròng ghi “EBITDA 12T: thiếu 3 tháng, mới có 9T”. Chế độ “12 tháng” hiện “Chưa đủ dữ liệu – thiếu dữ liệu một số tháng”. EBITDA trong file xuất có trạng thái gộp từ LNTT, lãi vay, khấu hao (“Có chênh – xem ghi chú”), không còn “Đã đối chiếu” chỉ nhờ khấu hao. |
| 7 | Mở được khi thư viện mạng không tải | Đạt. Kiểm thử với mọi kết nối mạng bị chặn: (a) `…_offline.html` (đã nhúng ECharts 5.5.1 và SheetJS 0.18.5) mở, nạp đủ 49 Excel MEDIA, vẽ biểu đồ; (b) bản thường cạnh thư mục `vendor/` tự dùng thư viện cục bộ, kết quả như (a); (c) bản thường đứng một mình vẫn khởi động, báo rõ thiếu thư viện và hướng dẫn mở bản offline, không dừng toàn bộ ứng dụng. |
| 8 | Báo cáo cuối | Mục 3–5 dưới đây. |

## 3. Nguồn đã đủ / chưa hỗ trợ

- **Đã có bộ đọc và đã kiểm thử trên file thật (28 mẫu FAST):** NKC; CĐPS; sổ chi tiết 1 TK; sổ nhiều TK; CĐPS công nợ 131/331; công nợ theo hóa đơn 131/331 (lịch sử 01/01/2000–30/09/2026); tuổi nợ theo hạn 131/331; danh sách TSCĐ; khấu hao nhiều kỳ; tăng/giảm TSCĐ; danh sách CCDC; chi phí CCDC nhiều kỳ; NXT theo kho; phiếu nhập; phiếu xuất; bảng kê bán hàng; bảng kê mua hàng; đơn hàng bán; KQKD theo tháng và lũy kế; CĐKT; LCTT trực tiếp; CPSX theo sản phẩm (yếu tố 01/02); KQKD công trình/vụ việc. Ba mẫu đơn hàng mua, chi phí công trình TK 154, NVL thực tế – định mức mới kiểm thử với file trống (đúng cột tiêu đề, 0 dòng).
- **Chưa hỗ trợ trong bộ nguồn này:** không có. Mẫu FAST lạ sẽ vào “Danh sách chờ xử lý”.
- **Nguồn trống theo bộ lọc FAST (đã xuất, không phải chưa lấy):**
  - MEDIA: đơn hàng bán, đơn hàng mua, chi phí công trình TK 154, CPSX loại 01 và 02, NVL thực tế–định mức, sổ chi tiết TK 241/521/621/821, tài sản giảm.
  - PLASTIC: sổ chi tiết TK 821.

## 4. Lỗi phần mềm

**Đã sửa trong bản này, kiểm lại trên 96 Excel:**

| Lỗi trong `05_Loi_v3_can_kiem_tra_lai.md` | Kết quả chạy lại |
|---|---|
| P0 Không khởi động khi CDN lỗi | Đã sửa: dự phòng `vendor/`, bản offline, thông báo rõ khi thiếu thư viện |
| P0 MEDIA không vào công ty | Đã sửa: 49 file MEDIA gán MEDIA; NKC 26.872 dòng |
| P0 Ghi đè sổ chi tiết/BCTC, trộn kiểm tra | Đã sửa: dữ liệu FAST tách theo đơn vị; kiểm tra MEDIA 71 mục riêng |
| P1 Trùng giữa công ty/bộ lọc | Đã sửa: chỉ 2 bản PLASTIC trùng |
| P1 KQKD công trình và 3 nguồn bổ sung | Đã sửa (mục 2 #4) |
| P1 EBITDA 12T khi có 9T | Đã sửa |
| P1 Xuất cố định PLASTIC | Đã sửa |
| P1 Nhãn “Đã đối chiếu” EBITDA | Đã sửa |
| Thêm, phát hiện khi chạy lại | (a) Nút Tháng / Lũy kế / 12 tháng không có tác dụng từ v2: mọi trang luôn tính lũy kế năm. Đã sửa. (b) Thư mục `ALTA_MEDIA_…`/`ALTA_PLASTIC_…` có thể bị hiểu là công ty mẹ. Đã sửa: ALTA đứng trước mã đơn vị là tiền tố tập đoàn. (c) Banner tồn kho và ghi chú file xuất của MEDIA lấy kiểm tra của PLASTIC. Đã sửa. (d) Đơn hàng bán MEDIA trống hiện “cần nạp”. Đã sửa thành “đã xuất, trống”. |

**Sửa thêm trong bản 3.3 (05/11, sau lần nạp thử):**

| Lỗi còn lại | Cách sửa | Kiểm tra trên 96 Excel |
|---|---|---|
| Đọc Excel chạy trên luồng giao diện | Đọc Excel và tính mã kiểm tra nội dung trong luồng nền (Web Worker). Nếu luồng nền không chạy được thì tự quay về cách cũ. | 96/96 file đọc bằng luồng nền, ở cả bản thường và bản offline. Thời gian nạp khoảng 85 giây. Giao diện đứng lâu nhất khoảng 1,5 giây (trước: cả lượt đọc từng file lớn). Số liệu không đổi. |
| Dữ liệu chỉ nằm trong trình duyệt đang mở; không gửi được cho người khác | Nút **Lưu bản chia sẻ** ở thanh trên tạo một file HTML có sẵn dữ liệu đã nạp (nén gzip). Phạm vi theo đơn vị đang chọn. Người nhận mở là đọc được ở chế độ chỉ đọc: không nạp, xóa hay sửa nguồn, không ghi vào dữ liệu riêng của trình duyệt họ. Mọi trang, truy xuất chứng từ và nút xuất vẫn dùng được. | Bản chia sẻ hai đơn vị 16,6 MB, chỉ MEDIA 4,7 MB, đóng gói khoảng 3–4 giây. Mở trong trình duyệt sạch, chặn mạng: số khớp bản gốc (EBITDA PLASTIC 45.801.117.006, MEDIA 15.998.475.652); bản MEDIA không chứa số PLASTIC; 0 lỗi. |
| Không xuất được dữ liệu biểu đồ | Mỗi biểu đồ có nút **CSV / Excel / PNG**. CSV và Excel gồm dữ liệu từng chuỗi và sheet `Pham_vi` (đơn vị, kỳ, chế độ kỳ); ô trống là không có dữ liệu, không phải 0. Cửa sổ truy xuất có thêm nút **Tải Excel** (toàn bộ dòng chứng từ kèm file, sheet, dòng Excel). | Đã thử cả ba định dạng; nút có ở mọi biểu đồ của CEO, CFO, Bán hàng, Công nợ, TSCĐ, Tồn kho. Tải Excel truy xuất EBITDA MEDIA: 4.216 dòng. |
| Dòng tiền NKC còn phần đối ứng chưa phân loại | Đối ứng là TK 811 (chi phí khác): PLASTIC phiếu chi PLT13818 ngày 30/09 số tiền 2.000.000.000; MEDIA BN086.M01/26 số tiền 20.000.000 và vài khoản phí nhỏ. Theo mẫu LCTT trực tiếp TT200/TT99 (mã 07 “Tiền chi khác cho hoạt động kinh doanh”), xếp vào nhóm riêng “Chi phí khác (TK 811)” thuộc HĐKD. | Phần chưa phân loại còn 0 ở cả hai đơn vị. |
| Nút lưu/xuất trên link online claude.ai | Dùng quyền tải file của Artifact (người xem bấm xác nhận khi lưu); mở file HTML trực tiếp thì tải bình thường. | — |

**Lưu ý khi chia sẻ:** bản chia sẻ lưu từ `Alta_CFO_CEO_Dashboard_v3_offline.html` đã nhúng thư viện nên người nhận mở được không cần mạng. Lưu từ bản thường hoặc link online thì người nhận cần mạng để tải thư viện biểu đồ và Excel.

## 5. Chênh lệch từ nguồn FAST (không phải lỗi phần mềm, không tự điều chỉnh)

**PLASTIC** (6 không đạt, giống lần kiểm tra trước; chi tiết và chứng từ ở trang Đối chiếu):
- **Bảng kê bán hàng vs TK 511:** chênh 3.870.873.866.
- **NXT vs TK tồn kho:** chênh −1.087.694.091.901; kho PL.01T tồn âm.
- **Danh sách TSCĐ vs sổ:**
  - nguyên giá lệch TK 211–213: −2.027.444.966;
  - hao mòn lệch TK 214: 174.323.258.
- **CĐKT FAST không cân:** 2.314.529.727.
- **LCTT FAST mã 70 vs tiền cuối kỳ:** −885.707.097.

**MEDIA** (4 không đạt):
- **Bảng kê bán hàng vs TK 511:** 65.740.825.647 so với 65.291.680.758, chênh 449.144.889. Theo số chứng từ:
  - 3 chứng từ chỉ có trên bảng kê: 445.144.889;
  - 1 chứng từ PKT chỉ có trên NKC: 4.000.000;
  - còn lại 0.
- **NXT vs TK 152–157:** 10.896.209.042 so với 1.866.039.554, chênh 9.030.169.488; 1 mã tồn âm. Danh sách TK tồn kho đối chiếu (Thiết lập) có thể cần chỉnh cho MEDIA, cần kế toán xác nhận.
- **Nguyên giá danh sách TSCĐ vs TK 211–213:** chênh 566.658.
- **CĐKT FAST không cân:** 76.449.039.875 so với 75.800.603.932, chênh 648.435.943.

**MEDIA, cần xem:**
- **Tuổi nợ phải thu:** báo cáo theo hạn thiếu 65 hóa đơn còn dư (2.765.370.198); nhóm tuổi phủ 77,9% số dư.
- **Tuổi nợ phải trả:** báo cáo theo hạn thiếu 125 hóa đơn (1.408.424.210).
- **Hóa đơn chưa có hạn thanh toán:** 6 hóa đơn phải thu (1.891.543.115), 32 hóa đơn phải trả (608.413.920).
- **Chênh sổ – hóa đơn:** phải thu −275.942.134 (FAST in “Chênh lệch” cho 4 khách, tổng 275.683.620); phải trả 1.648.228.710.
- **Doanh thu thuần KQKD công trình vs NKC:** 65.379.370.746 so với 65.291.680.758, chênh 87.689.988.
- **TK 821:** không phát sinh, thuế TNDN chưa xác nhận.

## 6. Dữ liệu còn thiếu cho CEO/CFO Actual

- **ALTA (công ty mẹ):** chưa có bộ xuất. Không thể có số hợp nhất. Dashboard ghi “Cộng gộp PLASTIC + MEDIA (chưa phải hợp nhất)” và không trừ nội bộ khi chưa xác nhận.
- **Kỳ 10–12/2025** (hoặc 12 tháng liên tiếp) cho các chỉ tiêu TTM: EBITDA 12T, nợ vay/EBITDA, EBITDA/lãi vay. Số dư đầu năm đã có qua CĐPS.
- **Danh sách MST nội bộ và quy tắc loại trừ** được kế toán xác nhận (trang Dữ liệu nguồn › Thiết lập).
- **Xác nhận của kế toán cho các chênh lệch mục 5:** NXT âm, CĐKT không cân, chứng từ bán hàng, các hóa đơn ngoài báo cáo tuổi nợ, thuế TNDN, và TK tồn kho đối chiếu cho MEDIA.
- **Đơn hàng bán MEDIA và đơn hàng mua:** FAST trả trống. Nếu MEDIA có đơn hàng ngoài FAST, cần nguồn khác.
- **Planning/Forecast:** là module khác. Dashboard chỉ nhận bộ số kế hoạch để so sánh (mẫu 4 cột ở trang Quy trình).

## 7. Bảng xác nhận 96 Excel

“Dòng hợp lệ” là dòng chi tiết thật, đã loại dòng tiêu đề, dòng tổng, dòng nhóm và dòng trống. “Dòng sheet” là số dòng trong sheet Excel.

| # | Đơn vị | File | Nhận dạng | Kỳ / ngày chốt | Dòng hợp lệ | Dòng sheet | Trạng thái · vai trò |
|---:|---|---|---|---|---:|---:|---|
| 1 | MEDIA | Bang_ke_ban_hang_dich_vu - MEDIA - 9T2026 - 6655e7f0.xlsx | Bảng kê hóa đơn bán hàng | 2026-01→2026-09 · chốt 2026-09-30 | 748 | 755 | Đang dùng · nguồn chính |
| 2 | MEDIA | Bang_ke_don_hang_ban - MEDIA - 9T2026 - bfe09bbc.xlsx | Bảng kê đơn hàng bán | — | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 3 | MEDIA | Bang_ke_don_hang_mua - MEDIA - 9T2026 - 63d24731.xlsx | Bảng kê đơn hàng mua | — | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 4 | MEDIA | Bang_ke_mua_hang - MEDIA - 9T2026 - 29a68e2a.xlsx | Bảng kê mua hàng | 2026-01→2026-09 · chốt 2026-09-30 | 635 | 640 | Đang dùng · Phân tích mua hàng (không phải chi phí kỳ) |
| 5 | MEDIA | Bang_ke_phieu_nhap_thuc_te - MEDIA - 9T2026 - 1085103b.xlsx | Bảng kê phiếu nhập | 2026-01→2026-09 · chốt 2026-09-30 | 635 | 640 | Đang dùng · nguồn chính |
| 6 | MEDIA | Bang_ke_phieu_xuat_thuc_te - MEDIA - 9T2026 - f26de105.xlsx | Bảng kê phiếu xuất | 2026-01→2026-09 · chốt 2026-09-30 | 467 | 472 | Đang dùng · nguồn chính |
| 7 | MEDIA | Can_doi_cong_no_131 - MEDIA - 9T2026 - d628f605.xlsx | CĐPS công nợ phải thu (TK131) | 2026-01→2026-09 · chốt 2026-09-30 | 232 | 239 | Đang dùng · nguồn chính |
| 8 | MEDIA | Can_doi_cong_no_331 - MEDIA - 9T2026 - 4204584f.xlsx | CĐPS công nợ phải trả (TK331) | 2026-01→2026-09 · chốt 2026-09-30 | 541 | 548 | Đang dùng · nguồn chính |
| 9 | MEDIA | Can_doi_ke_toan_30092026_TT99 - MEDIA - 9T2026 - b42e358a.xlsx | Cân đối kế toán (FAST) | 2026-09→2026-09 · chốt 2026-09-30 | 240 | 245 | Đang dùng · đối chiếu |
| 10 | MEDIA | Can_doi_phat_sinh - MEDIA - 9T2026 - 6df1066e.xlsx | Cân đối phát sinh tài khoản | 2026-01→2026-09 · chốt 2026-09-30 | 207 | 215 | Đang dùng · nguồn chính |
| 11 | MEDIA | CCDC_chi_tiet_cuoi_T9 - MEDIA - 9T2026 - 7ae33513.xlsx | Danh sách CCDC cuối kỳ | 2026-09→2026-09 · chốt 2026-09-30 | 270 | 277 | Đang dùng · nguồn chính |
| 12 | MEDIA | CCDC_phan_bo_T1_T9 - MEDIA - 9T2026 - f5adf337.xlsx | Chi phí CCDC nhiều kỳ | 2026-01→2026-09 · chốt 2026-09-30 | 270 | 277 | Đang dùng · nguồn chính |
| 13 | MEDIA | Chi_phi_cong_trinh_vu_viec_TK154 - MEDIA - 9T2026 - e2d9f0c9.xlsx | Chi phí SX theo công trình, vụ việc (TK 154) | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 14 | MEDIA | Chi_phi_san_xuat_loai01 - MEDIA - 9T2026 - 7d8e1223.xlsx | Chi phí SX theo sản phẩm (yt01) · yếu tố 01 | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 15 | MEDIA | Chi_phi_san_xuat_loai02 - MEDIA - 9T2026 - 22888f83.xlsx | Chi phí SX theo sản phẩm (yt02) · yếu tố 02 | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 16 | MEDIA | Cong_no_hoa_don_131 - MEDIA - 9T2026 - 76925ddd.xlsx | Công nợ phải thu theo hóa đơn (TK131) | 2000-01→2026-09 · chốt 2026-09-30 | 986 | 1217 | Đang dùng · nguồn chính |
| 17 | MEDIA | Cong_no_hoa_don_331 - MEDIA - 9T2026 - ed70733d.xlsx | Công nợ phải trả theo hóa đơn (TK331) | 2000-01→2026-09 · chốt 2026-09-30 | 2.960 | 2965 | Đang dùng · nguồn chính |
| 18 | MEDIA | Khau_hao_T1_T9 - MEDIA - 9T2026 - 4fb7a5b7.xlsx | Khấu hao TSCĐ nhiều kỳ | 2026-01→2026-09 · chốt 2026-09-30 | 54 | 61 | Đang dùng · nguồn chính |
| 19 | MEDIA | KQKD_luy_ke_9T_TT99 - MEDIA - 9T2026 - 92e4a07e.xlsx | KQKD lũy kế (FAST) | 2026-01→2026-09 · chốt 2026-09-30 | 58 | 63 | Đang dùng · đối chiếu |
| 20 | MEDIA | KQKD_theo_cong_trinh_vu_viec - MEDIA - 9T2026 - 0fd5146f.xlsx | KQKD theo công trình / vụ việc | 2026-01→2026-09 · chốt 2026-09-30 | 515 | 522 | Đang dùng · thông tin quản trị |
| 21 | MEDIA | KQKD_theo_thang_9T_TT99 - MEDIA - 9T2026 - b9ec451f.xlsx | KQKD theo tháng (FAST) | 2026-01→2026-09 | 58 | 63 | Đang dùng · đối chiếu |
| 22 | MEDIA | Luu_chuyen_tien_te_truc_tiep_9T_TT99 - MEDIA - 9T2026 - d0ca8bc2.xlsx | Lưu chuyển tiền tệ trực tiếp (FAST) | 2026-01→2026-09 · chốt 2026-09-30 | 36 | 41 | Đang dùng · đối chiếu |
| 23 | MEDIA | Nhat_ky_chung - MEDIA - 9T2026 - f50ad8eb.xlsx | Sổ nhật ký chung | 2026-01→2026-09 · chốt 2026-09-30 | 26.872 | 33532 | Đang dùng · nguồn chính |
| 24 | MEDIA | NVL_thuc_te_so_dinh_muc - MEDIA - 9T2026 - 3a062b53.xlsx | NVL thực tế so với định mức | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 25 | MEDIA | NXT_theo_kho_thuc_te_9T - MEDIA - 9T2026 - 46084394.xlsx | Nhập – xuất – tồn theo kho | 2026-01→2026-09 · chốt 2026-09-30 | 587 | 603 | Đang dùng · nguồn chính |
| 26 | MEDIA | So_chi_tiet_nhieu_TK - MEDIA - 9T2026 - 16754436.xlsx | Danh sách TK (sổ chi tiết nhiều TK) | 2026-01→2026-09 · chốt 2026-09-30 | 207 | 212 | Đang dùng · đối chiếu |
| 27 | MEDIA | So_chi_tiet_TK131 - MEDIA - 9T2026 - f639bb0c.xlsx | Sổ chi tiết tài khoản (TK131) | 2026-01→2026-09 · chốt 2026-09-30 | 2.515 | 2524 | Đang dùng · đối chiếu |
| 28 | MEDIA | So_chi_tiet_TK154 - MEDIA - 9T2026 - 8974a1d2.xlsx | Sổ chi tiết tài khoản (TK154) | 2026-01→2026-09 · chốt 2026-09-30 | 79 | 88 | Đang dùng · đối chiếu |
| 29 | MEDIA | So_chi_tiet_TK211 - MEDIA - 9T2026 - 3a4a8584.xlsx | Sổ chi tiết tài khoản (TK211) | 2026-01→2026-09 · chốt 2026-09-30 | 11 | 20 | Đang dùng · đối chiếu |
| 30 | MEDIA | So_chi_tiet_TK214 - MEDIA - 9T2026 - 95722e36.xlsx | Sổ chi tiết tài khoản (TK214) | 2026-01→2026-09 · chốt 2026-09-30 | 52 | 61 | Đang dùng · đối chiếu |
| 31 | MEDIA | So_chi_tiet_TK241 - MEDIA - 9T2026 - 00e61a8f.xlsx | Sổ chi tiết tài khoản (TK241) | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 9 | Đã xuất, trống theo bộ lọc |
| 32 | MEDIA | So_chi_tiet_TK242 - MEDIA - 9T2026 - 6679f68e.xlsx | Sổ chi tiết tài khoản (TK242) | 2026-01→2026-09 · chốt 2026-09-30 | 302 | 311 | Đang dùng · đối chiếu |
| 33 | MEDIA | So_chi_tiet_TK331 - MEDIA - 9T2026 - d45aae34.xlsx | Sổ chi tiết tài khoản (TK331) | 2026-01→2026-09 · chốt 2026-09-30 | 8.939 | 8948 | Đang dùng · đối chiếu |
| 34 | MEDIA | So_chi_tiet_TK341 - MEDIA - 9T2026 - 935274b2.xlsx | Sổ chi tiết tài khoản (TK341) | 2026-01→2026-09 · chốt 2026-09-30 | 189 | 198 | Đang dùng · đối chiếu |
| 35 | MEDIA | So_chi_tiet_TK511 - MEDIA - 9T2026 - 7e53ac26.xlsx | Sổ chi tiết tài khoản (TK511) | 2026-01→2026-09 · chốt 2026-09-30 | 888 | 897 | Đang dùng · đối chiếu |
| 36 | MEDIA | So_chi_tiet_TK521 - MEDIA - 9T2026 - 949178e9.xlsx | Sổ chi tiết tài khoản (TK521) | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 9 | Đã xuất, trống theo bộ lọc |
| 37 | MEDIA | So_chi_tiet_TK621 - MEDIA - 9T2026 - 3ba45cb9.xlsx | Sổ chi tiết tài khoản (TK621) | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 9 | Đã xuất, trống theo bộ lọc |
| 38 | MEDIA | So_chi_tiet_TK622 - MEDIA - 9T2026 - 583f512a.xlsx | Sổ chi tiết tài khoản (TK622) | 2026-01→2026-09 · chốt 2026-09-30 | 63 | 72 | Đang dùng · đối chiếu |
| 39 | MEDIA | So_chi_tiet_TK627 - MEDIA - 9T2026 - a8d1f056.xlsx | Sổ chi tiết tài khoản (TK627) | 2026-01→2026-09 · chốt 2026-09-30 | 2.186 | 2195 | Đang dùng · đối chiếu |
| 40 | MEDIA | So_chi_tiet_TK632 - MEDIA - 9T2026 - 8f0baa1e.xlsx | Sổ chi tiết tài khoản (TK632) | 2026-01→2026-09 · chốt 2026-09-30 | 207 | 216 | Đang dùng · đối chiếu |
| 41 | MEDIA | So_chi_tiet_TK635 - MEDIA - 9T2026 - 5eb6f9e6.xlsx | Sổ chi tiết tài khoản (TK635) | 2026-01→2026-09 · chốt 2026-09-30 | 365 | 374 | Đang dùng · đối chiếu |
| 42 | MEDIA | So_chi_tiet_TK641 - MEDIA - 9T2026 - d44790ab.xlsx | Sổ chi tiết tài khoản (TK641) | 2026-01→2026-09 · chốt 2026-09-30 | 126 | 135 | Đang dùng · đối chiếu |
| 43 | MEDIA | So_chi_tiet_TK642 - MEDIA - 9T2026 - 1d106dfd.xlsx | Sổ chi tiết tài khoản (TK642) | 2026-01→2026-09 · chốt 2026-09-30 | 2.468 | 2477 | Đang dùng · đối chiếu |
| 44 | MEDIA | So_chi_tiet_TK821 - MEDIA - 9T2026 - 33eea106.xlsx | Sổ chi tiết tài khoản (TK821) | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 9 | Đã xuất, trống theo bộ lọc |
| 45 | MEDIA | Tai_san_chi_tiet_cuoi_T9 - MEDIA - 9T2026 - 93fe7103.xlsx | Danh sách TSCĐ cuối kỳ | 2026-09→2026-09 · chốt 2026-09-30 | 147 | 154 | Đang dùng · nguồn chính |
| 46 | MEDIA | Tai_san_giam_9T - MEDIA - 9T2026 - 658e4e08.xlsx | Tăng/giảm TSCĐ · giảm | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 6 | Đã xuất, trống theo bộ lọc |
| 47 | MEDIA | Tai_san_tang_9T - MEDIA - 9T2026 - 46e553b4.xlsx | Tăng/giảm TSCĐ · tăng | 2026-01→2026-09 · chốt 2026-09-30 | 5 | 12 | Đang dùng · nguồn chính |
| 48 | MEDIA | Tuoi_no_131_30092026 - MEDIA - 9T2026 - 9385b822.xlsx | Tuổi nợ phải thu theo hạn (TK131) | 2026-09→2026-09 · chốt 2026-09-30 | 136 | 141 | Đang dùng · nguồn chính |
| 49 | MEDIA | Tuoi_no_331_30092026 - MEDIA - 9T2026 - a29f65ba.xlsx | Tuổi nợ phải trả theo hạn (TK331) | 2026-09→2026-09 · chốt 2026-09-30 | 285 | 290 | Đang dùng · nguồn chính |
| 50 | PLASTIC | Bảng cân đối kế toán - PLASTIC - 9T2026.xlsx | Cân đối kế toán (FAST) | 2026-09→2026-09 · chốt 2026-09-30 | 240 | 245 | Đang dùng · đối chiếu |
| 51 | PLASTIC | Bảng cân đối phát sinh các tài khoản - PLASTIC - 9T2026 - 5f8f9568.xlsx | Cân đối phát sinh tài khoản | 2026-01→2026-09 · chốt 2026-09-30 | 254 | 262 | Bản trùng của “Bảng cân đối phát sinh các tài khoản - PLASTIC - 9T2026.xlsx” (không cộng) |
| 52 | PLASTIC | Bảng cân đối phát sinh các tài khoản - PLASTIC - 9T2026.xlsx | Cân đối phát sinh tài khoản | 2026-01→2026-09 · chốt 2026-09-30 | 254 | 262 | Đang dùng · nguồn chính |
| 53 | PLASTIC | Bảng cân đối phát sinh công nợ của một tài khoản - PLASTIC - 9T2026 - d6a99c49.xlsx | CĐPS công nợ phải thu (TK131) | 2026-01→2026-09 · chốt 2026-09-30 | 433 | 440 | Đang dùng · nguồn chính |
| 54 | PLASTIC | Bảng cân đối phát sinh công nợ của một tài khoản - PLASTIC - 9T2026.xlsx | CĐPS công nợ phải trả (TK331) | 2026-01→2026-09 · chốt 2026-09-30 | 540 | 547 | Đang dùng · nguồn chính |
| 55 | PLASTIC | Bảng kê công nợ của các hóa đơn theo hạn thanh toán - PLASTIC - 9T2026 - 4e3103dc.xlsx | Tuổi nợ phải thu theo hạn (TK131) | 2026-09→2026-09 · chốt 2026-09-30 | 694 | 699 | Đang dùng · nguồn chính |
| 56 | PLASTIC | Bảng kê công nợ của các hóa đơn theo hạn thanh toán - PLASTIC - 9T2026.xlsx | Tuổi nợ phải trả theo hạn (TK331) | 2026-09→2026-09 · chốt 2026-09-30 | 758 | 763 | Đang dùng · nguồn chính |
| 57 | PLASTIC | Bảng kê công nợ phải trả theo hóa đơn - PLASTIC - 9T2026.xlsx | Công nợ phải trả theo hóa đơn (TK331) | 2000-01→2026-09 · chốt 2026-09-30 | 4.530 | 4535 | Đang dùng · nguồn chính |
| 58 | PLASTIC | Bảng kê công nợ theo hóa đơn - PLASTIC - 9T2026.xlsx | Công nợ phải thu theo hóa đơn (TK131) | 2000-01→2026-09 · chốt 2026-09-30 | 8.162 | 8601 | Đang dùng · nguồn chính |
| 59 | PLASTIC | Bảng kê đơn hàng bán - PLASTIC - 9T2026.xlsx | Bảng kê đơn hàng bán | 2026-03→2026-09 | 34.826 | 34831 | Đang dùng · nguồn chính |
| 60 | PLASTIC | Bảng kê hóa đơn bán hàng, dịch vụ - Alta Plastic - PLASTIC - 9T2026.xlsx | Bảng kê hóa đơn bán hàng | 2026-01→2026-09 · chốt 2026-09-30 | 6.591 | 6598 | Đang dùng · nguồn chính |
| 61 | PLASTIC | Bảng kê mua hàng - Alta Plastic - PLASTIC - 9T2026.xlsx | Bảng kê mua hàng | 2026-01→2026-09 · chốt 2026-09-30 | 6.107 | 6112 | Đang dùng · Phân tích mua hàng (không phải chi phí kỳ) |
| 62 | PLASTIC | Bảng kê phiếu nhập - PLASTIC - 9T2026.xlsx | Bảng kê phiếu nhập | 2026-01→2026-09 · chốt 2026-09-30 | 6.105 | 6110 | Đang dùng · nguồn chính |
| 63 | PLASTIC | Bảng kê phiếu xuất - PLASTIC - 9T2026.xlsx | Bảng kê phiếu xuất | 2026-01→2026-09 · chốt 2026-09-30 | 61.825 | 61830 | Đang dùng · nguồn chính |
| 64 | PLASTIC | Bảng tính chi phí CCDC nhiều kỳ - PLASTIC - 9T2026.xlsx | Chi phí CCDC nhiều kỳ | 2026-01→2026-09 · chốt 2026-09-30 | 30 | 37 | Đang dùng · nguồn chính |
| 65 | PLASTIC | Bảng tính khấu hao TSCĐ nhiều kỳ - PLASTIC - 9T2026.xlsx | Khấu hao TSCĐ nhiều kỳ | 2026-01→2026-09 · chốt 2026-09-30 | 101 | 108 | Đang dùng · nguồn chính |
| 66 | PLASTIC | Báo cáo chi tiết CCDC - PLASTIC - 9T2026.xlsx | Danh sách CCDC cuối kỳ | 2026-09→2026-09 · chốt 2026-09-30 | 30 | 37 | Đang dùng · nguồn chính |
| 67 | PLASTIC | Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026 - 204eba51.xlsx | Tăng/giảm TSCĐ · tăng | 2026-01→2026-09 · chốt 2026-09-30 | 23 | 30 | Bản trùng của “Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026.xlsx” (không cộng) |
| 68 | PLASTIC | Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026 - 6d585ea2.xlsx | Tăng/giảm TSCĐ · giảm | 2026-01→2026-09 · chốt 2026-09-30 | 2 | 9 | Đang dùng · nguồn chính |
| 69 | PLASTIC | Báo cáo chi tiết tăng_giảm TSCĐ - PLASTIC - 9T2026.xlsx | Tăng/giảm TSCĐ · tăng | 2026-01→2026-09 · chốt 2026-09-30 | 23 | 30 | Đang dùng · nguồn chính |
| 70 | PLASTIC | Báo cáo chi tiết TSCĐ - PLASTIC - 9T2026.xlsx | Danh sách TSCĐ cuối kỳ | 2026-09→2026-09 · chốt 2026-09-30 | 167 | 174 | Đang dùng · nguồn chính |
| 71 | PLASTIC | Báo cáo kết quả hoạt động sản xuất kinh doanh cho nhiều kỳ - PLASTIC - 9T2026.xlsx | KQKD theo tháng (FAST) | 2026-01→2026-09 | 58 | 63 | Đang dùng · đối chiếu |
| 72 | PLASTIC | Báo cáo kết quả sản xuất kinh doanh - PLASTIC - 9T2026.xlsx | KQKD lũy kế (FAST) | 2026-01→2026-09 · chốt 2026-09-30 | 58 | 63 | Đang dùng · đối chiếu |
| 73 | PLASTIC | Báo cáo lưu chuyển tiền tệ theo phương pháp trực tiếp - PLASTIC - 9T2026.xlsx | Lưu chuyển tiền tệ trực tiếp (FAST) | 2026-01→2026-09 · chốt 2026-09-30 | 36 | 41 | Đang dùng · đối chiếu |
| 74 | PLASTIC | Báo cáo tổng hợp chi phí sản xuất theo sản phẩm - PLASTIC - 9T2026 - f586feaa.xlsx | Chi phí SX theo sản phẩm (yt02) · yếu tố 02 | 2026-01→2026-09 · chốt 2026-09-30 | 1.811 | 1816 | Đang dùng · nguồn chính |
| 75 | PLASTIC | Báo cáo tổng hợp chi phí sản xuất theo sản phẩm - PLASTIC - 9T2026.xlsx | Chi phí SX theo sản phẩm (yt01) · yếu tố 01 | 2026-01→2026-09 · chốt 2026-09-30 | 1.887 | 1892 | Đang dùng · nguồn chính |
| 76 | PLASTIC | Sổ chi tiết của một tài khoản - TK131 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK131) | 2026-01→2026-09 · chốt 2026-09-30 | 26.668 | 26677 | Đang dùng · đối chiếu |
| 77 | PLASTIC | Sổ chi tiết của một tài khoản - TK154 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK154) | 2026-01→2026-09 · chốt 2026-09-30 | 7.120 | 7129 | Đang dùng · đối chiếu |
| 78 | PLASTIC | Sổ chi tiết của một tài khoản - TK211 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK211) | 2026-01→2026-09 · chốt 2026-09-30 | 77 | 86 | Đang dùng · đối chiếu |
| 79 | PLASTIC | Sổ chi tiết của một tài khoản - TK214 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK214) | 2026-01→2026-09 · chốt 2026-09-30 | 201 | 210 | Đang dùng · đối chiếu |
| 80 | PLASTIC | Sổ chi tiết của một tài khoản - TK241 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK241) | 2026-01→2026-09 · chốt 2026-09-30 | 1 | 10 | Đang dùng · đối chiếu |
| 81 | PLASTIC | Sổ chi tiết của một tài khoản - TK242 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK242) | 2026-01→2026-09 · chốt 2026-09-30 | 64 | 73 | Đang dùng · đối chiếu |
| 82 | PLASTIC | Sổ chi tiết của một tài khoản - TK331 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK331) | 2026-01→2026-09 · chốt 2026-09-30 | 11.273 | 11282 | Đang dùng · đối chiếu |
| 83 | PLASTIC | Sổ chi tiết của một tài khoản - TK341 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK341) | 2026-01→2026-09 · chốt 2026-09-30 | 138 | 147 | Đang dùng · đối chiếu |
| 84 | PLASTIC | Sổ chi tiết của một tài khoản - TK511 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK511) | 2026-01→2026-09 · chốt 2026-09-30 | 17.299 | 17308 | Đang dùng · đối chiếu |
| 85 | PLASTIC | Sổ chi tiết của một tài khoản - TK521 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK521) | 2026-01→2026-09 · chốt 2026-09-30 | 137 | 146 | Đang dùng · đối chiếu |
| 86 | PLASTIC | Sổ chi tiết của một tài khoản - TK621 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK621) | 2026-01→2026-09 · chốt 2026-09-30 | 13.839 | 13848 | Đang dùng · đối chiếu |
| 87 | PLASTIC | Sổ chi tiết của một tài khoản - TK622 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK622) | 2026-01→2026-09 · chốt 2026-09-30 | 351 | 360 | Đang dùng · đối chiếu |
| 88 | PLASTIC | Sổ chi tiết của một tài khoản - TK627 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK627) | 2026-01→2026-09 · chốt 2026-09-30 | 3.009 | 3018 | Đang dùng · đối chiếu |
| 89 | PLASTIC | Sổ chi tiết của một tài khoản - TK632 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK632) | 2026-01→2026-09 · chốt 2026-09-30 | 20.821 | 20830 | Đang dùng · đối chiếu |
| 90 | PLASTIC | Sổ chi tiết của một tài khoản - TK635 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK635) | 2026-01→2026-09 · chốt 2026-09-30 | 353 | 362 | Đang dùng · đối chiếu |
| 91 | PLASTIC | Sổ chi tiết của một tài khoản - TK641 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK641) | 2026-01→2026-09 · chốt 2026-09-30 | 2.531 | 2540 | Đang dùng · đối chiếu |
| 92 | PLASTIC | Sổ chi tiết của một tài khoản - TK642 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK642) | 2026-01→2026-09 · chốt 2026-09-30 | 678 | 687 | Đang dùng · đối chiếu |
| 93 | PLASTIC | Sổ chi tiết của một tài khoản - TK821 - PLASTIC - 9T2026.xlsx | Sổ chi tiết tài khoản (TK821) | 2026-01→2026-09 · chốt 2026-09-30 | 0 | 9 | Đã xuất, trống theo bộ lọc |
| 94 | PLASTIC | Sổ chi tiết lên cho nhiều tài khoản - PLASTIC - 9T2026.xlsx | Danh sách TK (sổ chi tiết nhiều TK) | 2026-01→2026-09 · chốt 2026-09-30 | 254 | 259 | Đang dùng · đối chiếu |
| 95 | PLASTIC | Sổ nhật ký chung - PLASTIC - 9T2026.xlsx | Sổ nhật ký chung | 2026-01→2026-09 · chốt 2026-09-30 | 167.330 | 207072 | Đang dùng · nguồn chính |
| 96 | PLASTIC | Tổng hợp nhập xuất tồn theo kho - PLASTIC - 9T2026.xlsx | Nhập – xuất – tồn theo kho | 2026-01→2026-09 · chốt 2026-09-30 | 6.663 | 6689 | Đang dùng · nguồn chính |
