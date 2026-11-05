# Dashboard v3.1: nhiều đơn vị FAST (ALTA / PLASTIC / MEDIA)

Cập nhật ngày 05/11/2026 theo “Quy ước archive FAST và yêu cầu sửa bộ đọc”. File: `dashboard/Alta_CFO_CEO_Dashboard_v3.html` (cùng đường dẫn và cùng link online với v3; bản v2 vẫn giữ nguyên).

## 1. Đã sửa

| Yêu cầu | Cách làm trong v3.1 |
|---|---|
| Ánh xạ ALTA, PLASTIC, MEDIA | Mã đơn vị dùng thống nhất ở thanh chọn, bảng, đối chiếu, truy nguồn và file xuất (cột “Đơn vị”, tên file `Alta_<ĐƠN VỊ>_…xlsx`). Bỏ nhãn “Tập đoàn”, thay bằng “Các đơn vị”. |
| Đơn vị lấy từ đâu | Căn cứ mạnh: kê khai (`unit`), bộ lọc FAST `ma_dvcs`, cột Đơn vị trong dữ liệu. Căn cứ yếu: tên thư mục, tên file (chỉ mã viết hoa ALTA/ALTA_ME/PLASTIC/MEDIA). Dòng tên công ty ở đầu báo cáo không được dùng. Các căn cứ mâu thuẫn thì file vào **Chờ xác nhận: đơn vị mâu thuẫn**. Chỉ có căn cứ yếu thì file vào **Chờ xác nhận đơn vị**; có nút xác nhận hàng loạt theo thư mục. |
| Schema metadata | Mỗi file có `source_id, unit_code, report_type, period_start, period_end, as_of_date, payment_cutoff, account, cost_factor, asset_direction, kho, data_kind, filters, exported_at, source_file, sheet, raw_file_sha256, cell_content_sha256, unit_basis, validation_status, empty_by_filter`. Đọc được `file_inventory`, `download_manifest`, `report_catalog` (files, catalog), `audit_catalog.exports` (bộ lọc FAST, gắn với file qua mã báo cáo, TK và số bản ghi), các mảng `media_jobs/jobs/files` có `filters`. Trường không suy ra được giữ trống. Sheet “Nguon_file” trong file xuất liệt kê đủ các trường này. |
| `cost_factor` | Ưu tiên bộ lọc `ma_loai`; sau đó `cost_factor` trong kê khai; cuối cùng mới đến ghi chú “Loại yếu tố”. Nguồn của giá trị được ghi lại. |
| Khóa nguồn | Khóa gồm đơn vị, loại báo cáo, phạm vi (TK, loại yếu tố, chiều tăng/giảm, kho, loại dữ liệu), kỳ và ngày chốt. Nhiều snapshot được giữ song song; đơn vị nạp sau không ghi đè đơn vị nạp trước. |
| Bản trùng | Chỉ là bản trùng khi cùng khóa nguồn và cùng nội dung (SHA-256 nội dung ô). Hai file giống hệt nhau nhưng khác đơn vị hoặc bộ lọc được giữ riêng. Tên file không được dùng để gộp. File khác mã kiểm tra trong kê khai vào hàng chờ. |
| Nhiều sheet | Mọi sheet có cấu trúc FAST được nhận làm nguồn riêng (khóa có tên sheet). Vẫn giữ số dòng Excel thật. |
| Ba trạng thái | Bảng “Trạng thái nguồn theo đơn vị” phân biệt: **Chưa xuất / chưa nạp** · **Đã xuất, trống** (file không có dòng dữ liệu, hoặc FAST trả dòng trắng) · **Có dữ liệu** · **Chờ xác nhận**. Ví dụ sổ chi tiết TK 821 PLASTIC là “Đã xuất, trống theo bộ lọc”. |
| Công ty mẹ chưa có | Chọn ALTA thì hiện “ALTA: chưa xuất / chưa nạp dữ liệu”, không hiện số 0. Xem nhiều đơn vị thì có băng cảnh báo “Cộng gộp PLASTIC + MEDIA (chưa phải hợp nhất)” và ghi rõ đơn vị còn thiếu. Nhãn “Hợp nhất” chỉ xuất hiện khi đủ 3 đơn vị **và** kế toán đã tick xác nhận danh sách MST nội bộ, quy tắc loại trừ (Dữ liệu nguồn › Thiết lập). Trước khi xác nhận, ô “Loại trừ nội bộ” bị khóa và số không trừ nội bộ. |
| Trang chi tiết | Công nợ, TSCĐ, Tồn kho, Đơn hàng, Đối chiếu chạy theo từng đơn vị. Ở chế độ nhiều đơn vị có nút chọn đơn vị để xem chi tiết; chi tiết giữa các đơn vị không cộng lẫn. Kiểm tra đối chiếu được chạy riêng cho từng đơn vị (nhóm có tiền tố mã đơn vị). |
| Nạp thư mục gốc | “Chọn cả thư mục” (hoặc kéo thả) có bước **Rà soát trước khi nạp** cho từng bộ dữ liệu: đơn vị và căn cứ, số file Excel, có kê khai không, file không có trong kê khai, file có trong kê khai nhưng thiếu, file khác mã kiểm tra, mâu thuẫn đơn vị giữa thư mục và kê khai. Bấm “Nạp” là xong, không phải gán từng file. |
| KQKD công trình/vụ việc | Đã thêm bộ đọc nhận tiêu đề “kết quả … công trình/vụ việc” với nhóm cột Ps / Lk đn / Lk. Các nhóm được giữ riêng, xem từng nhóm ở cuối trang Bán hàng, không cộng vào KQKD theo sổ. **Chưa kiểm thử với file MEDIA thật** (xem mục 3). |

## 2. Kiểm thử

Chạy trên Chromium với bộ PLASTIC thật cùng hai bộ kiểm thử dựng lại từ PLASTIC: đổi mã đơn vị thành MEDIA ở tên file và kê khai. Các bộ dựng lại chỉ nằm trong thư mục tạm của phiên làm việc, không vào dashboard.

| Kịch bản | Kết quả |
|---|---|
| Chỉ PLASTIC (nạp như v3) | Số không đổi: doanh thu thuần 255.734.182.421, LNTT 37.120.651.173, EBITDA 45.801.117.006; 44 file dùng + 1 file “đã xuất, trống” (TK 821) + 2 bản trùng |
| PLASTIC rồi MEDIA; MEDIA rồi PLASTIC | Số từng đơn vị giống nhau ở cả hai thứ tự. Bản trùng chỉ nhận trong cùng đơn vị (2 + 2). Nội dung giống hệt nhưng khác đơn vị không bị gộp |
| Nạp lại cùng thư mục | Không thêm file |
| Bộ có cột Đơn vị = PLASTIC nhưng kê khai = MEDIA | File đơn hàng vào “Chờ xác nhận: đơn vị mâu thuẫn”, không vào số |
| Kê khai ghi PLASTIC, thư mục/tên file ghi MEDIA | Rà soát báo mâu thuẫn; cả 47 file chờ xác nhận, không vào số của đơn vị nào |
| Chỉ thư mục Excel, không có kê khai | File chờ xác nhận đơn vị. Một nút “Xác nhận PLASTIC cho … file” là nạp đủ. Hai file chi phí sản xuất vẫn chờ chọn loại yếu tố (không còn bộ lọc hay ghi chú) |
| Chọn ALTA | “ALTA: chưa xuất / chưa nạp dữ liệu”; trong file xuất có dòng ALTA “Chưa xuất / chưa nạp”, không có số |
| Nhiều đơn vị | Hiện “Cộng gộp PLASTIC + MEDIA (chưa phải hợp nhất)”, không trừ nội bộ khi chưa xác nhận |
| File xuất theo phạm vi | Chọn PLASTIC: chỉ có dòng PLASTIC. Chọn “Các đơn vị”: ALTA (chưa nạp) + PLASTIC + MEDIA |
| Lỗi số liệu FAST | Vẫn báo như v3 (bán hàng vs TK 511, NXT âm, CĐKT không cân…), không điều chỉnh để đạt |
| Trình duyệt | 0 lỗi console |

## 3. Cần thêm để hoàn tất

- **Bộ MEDIA thật (49 Excel, `FAST_MEDIA_DataRoom_2026-11-04`)** chưa có trong phiên làm việc này. Thiếu nó thì chưa chạy được tiêu chí “đủ 96 Excel”, chưa kiểm được bộ đọc KQKD công trình/vụ việc (515 dòng) và cách đọc `media_jobs/filters` thật.
- **Ba cấu trúc còn thiếu khác** (tổng cộng bốn, tính cả KQKD công trình/vụ việc) chưa có file mẫu nên chưa viết bộ đọc. Hiện chúng vào danh sách chờ, không bị nạp sai nhóm.
- **`Dashboard_v3_Kiem_tra/01_Loi_can_sua_gap_v3.md`** (8 lỗi và bằng chứng) chưa được tải lên. Có file này mới đối chiếu được từng lỗi.
