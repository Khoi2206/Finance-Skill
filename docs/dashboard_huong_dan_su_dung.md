# Hướng dẫn sử dụng dashboard CFO · CEO

Cho người dùng dashboard: nạp báo cáo FAST, đọc số, kiểm tra chênh lệch, xuất và chia sẻ. Áp dụng bản v3.3 (05/11/2026). Người sửa mã xem [`dashboard_cau_truc_ky_thuat.md`](dashboard_cau_truc_ky_thuat.md).

## 1. Mở dashboard

| Bạn muốn | Mở file |
|---|---|
| Dùng hằng ngày, máy có mạng | `dashboard/Alta_CFO_CEO_Dashboard_v3.html` (để thư mục `vendor/` cạnh file thì vẫn chạy khi mất mạng) |
| Máy không có mạng, hoặc để tạo bản chia sẻ đọc được không cần mạng | `dashboard/Alta_CFO_CEO_Dashboard_v3_offline.html` |
| Xem trên claude.ai | https://claude.ai/artifact/4EMjJY2DcLqgEkAxqbGRMT (riêng tư; người khác chỉ mở được khi bạn chia sẻ) |

- Dùng Chrome hoặc Edge, nhấp đúp file để mở.
- Dữ liệu chỉ xử lý trong trình duyệt của bạn, không gửi lên máy chủ.
- Dữ liệu đã nạp được giữ lại trong trình duyệt đó: lần sau mở lại không cần nạp lại. Sang máy hoặc trình duyệt khác thì phải nạp lại, hoặc gửi bản chia sẻ (mục 8).

## 2. Chuẩn bị dữ liệu từ FAST

Mỗi đơn vị (ALTA, PLASTIC, MEDIA) xuất vào **một thư mục riêng**, ví dụ:

```
FAST/
  ALTA_PLASTIC_FAST_9T2026_NAP_CLAUDE/
     01_File_FAST_goc/   ← các file Excel xuất nguyên từ FAST, không sửa
     download_manifest.json, file_inventory.json, … ← file kê khai (nếu có)
  ALTA_MEDIA_FAST_9T2026_NAP_CLAUDE/
     …
```

- Giữ nguyên file Excel gốc: không xóa dòng tổng, đổi cột hay sửa số.
- Có file kê khai (manifest) thì dashboard tự biết đơn vị, bộ lọc, loại yếu tố và bản trùng. Không có kê khai vẫn nạp được, nhưng phải xác nhận đơn vị (mục 3).
- Danh sách báo cáo cần xuất: [`fast_export_checklist.md`](fast_export_checklist.md). Tối thiểu cần **Sổ nhật ký chung** và **Bảng cân đối phát sinh** của kỳ.

## 3. Nạp dữ liệu

1. Vào trang **Dữ liệu nguồn**.
2. Bấm **Chọn cả thư mục** và chọn thư mục `FAST` (chứa nhiều đơn vị) hoặc thư mục của một đơn vị. Cũng có thể kéo thả cả thư mục vào khung nạp.
3. Bảng **Rà soát thư mục trước khi nạp** hiện ra. Mỗi bộ dữ liệu một dòng, gồm:
   - đơn vị và căn cứ (kê khai, tên thư mục);
   - số file Excel;
   - có kê khai hay không;
   - file thiếu hoặc thừa so với kê khai;
   - file khác mã kiểm tra;
   - đơn vị mâu thuẫn.
4. Bấm **Nạp … file**. Bộ khoảng 100 file mất 1–2 phút; dòng tiến độ ở đầu trang cho biết đang đọc file nào.

Nạp lại sau khi xuất lại từ FAST: chọn lại cả thư mục.
- File giống hệt được bỏ qua.
- File mới cùng loại, cùng đơn vị, cùng phạm vi (TK, kỳ, bộ lọc) sẽ thay file cũ.
- File trùng nội dung trong cùng phạm vi chỉ dùng một bản.

### Đọc bảng “Kiểm tra đầu vào từng file”

| Trạng thái | Nghĩa | Cần làm |
|---|---|---|
| **Đang dùng** | Nguồn đã vào số (nguồn chính, đối chiếu hoặc thông tin quản trị: xem cột “Vai trò”) | — |
| **Đã xuất, trống theo bộ lọc** | FAST trả về không có dòng nào (ví dụ TK 821 không phát sinh). Đây không phải là thiếu báo cáo. | — |
| **Bản trùng của “…” (không cộng)** | Cùng phạm vi, cùng nội dung với file khác | — |
| **Bị thay bởi file mới hơn cùng phạm vi** | Đã có file nạp sau thay thế | Xóa file cũ nếu muốn gọn |
| **Chờ xác nhận đơn vị PLASTIC** | Chỉ biết đơn vị qua tên thư mục/tên file | Bấm nút **Xác nhận … cho N file** ở bảng Trạng thái nguồn |
| **Chờ xác nhận: đơn vị mâu thuẫn** | Kê khai, bộ lọc, cột dữ liệu hoặc tên file nói khác nhau | Kiểm tra file; chọn đơn vị trong cột “Đơn vị” nếu chắc chắn |
| **Chờ xác nhận: khác kê khai** | Mã kiểm tra hoặc TK khác bản đã kê khai | Xuất lại từ FAST hoặc sửa kê khai |
| **Chờ chọn loại yếu tố 01/02** | File chi phí sản xuất chưa biết loại yếu tố | Chọn ở cột “Loại báo cáo” |
| **Chờ xử lý: chưa hỗ trợ** | Mẫu báo cáo dashboard chưa đọc được | Gửi mẫu cho người sửa mã |

- Cột **Dòng dữ liệu**: số dòng chi tiết thật, đã loại dòng tiêu đề, dòng tổng, dòng nhóm và dòng trống. Rê chuột để xem cách đếm.
- Bảng **Trạng thái nguồn theo đơn vị** (đầu trang) ghi rõ từng loại báo cáo của mỗi đơn vị là “Có dữ liệu”, “Đã xuất, trống”, “Chờ xác nhận” hay “Chưa xuất / chưa nạp”.

## 4. Chọn phạm vi xem

Thanh trên cùng:

| Ô | Ý nghĩa |
|---|---|
| **Các đơn vị / ALTA / PLASTIC / MEDIA** | Xem từng đơn vị hoặc cộng các đơn vị đã nạp |
| **Đến T…/26** | Tháng cuối của kỳ xem |
| **Tháng / Lũy kế năm / 12 tháng** | Chỉ tháng đó; từ tháng 1 đến tháng chọn; 12 tháng gần nhất |
| **Loại trừ nội bộ** | Chỉ bật được khi kế toán đã xác nhận danh sách MST nội bộ (mục 9) |
| **Lưu bản chia sẻ** | Mục 8 |

Lưu ý:
- **Các đơn vị** hiện “Cộng gộp PLASTIC + MEDIA (chưa phải hợp nhất)”. Số hợp nhất chỉ có khi đủ ALTA, PLASTIC, MEDIA và loại trừ nội bộ đã được xác nhận.
- Đơn vị chưa có dữ liệu (hiện tại là ALTA) hiện “chưa xuất / chưa nạp”, **không phải số 0**.
- Chế độ **12 tháng** cần đủ 12 tháng liên tiếp. Thiếu tháng thì chỉ tiêu hiện “Chưa đủ dữ liệu”, không tự coi tháng thiếu bằng 0. Tương tự, “EBITDA 12T: thiếu 3 tháng” nghĩa là mới có 9 tháng.
- Trang chi tiết (Công nợ, TSCĐ, Tồn kho, Đơn hàng, Đối chiếu): khi chọn “Các đơn vị” có nút chọn đơn vị để xem chi tiết; chi tiết không cộng lẫn giữa các đơn vị.

## 5. Các trang

| Trang | Nội dung | Nguồn chính |
|---|---|---|
| **CEO** | Doanh thu thuần, lợi nhuận gộp, EBITDA, LNST, tiền, nợ vay ròng; doanh thu và biên theo tháng; KQKD; cơ cấu doanh thu; khách hàng lớn | NKC, CĐPS, bảng kê bán hàng |
| **CFO** | Tiền, dòng tiền HĐKD, phải thu (DSO), tồn kho (DIO), phải trả; dòng tiền trực tiếp theo nhóm; công nợ quá hạn; công nợ nội bộ | NKC (TK tiền theo TK đối ứng), CĐPS |
| **Bán hàng** | Doanh thu theo bảng kê, theo mảng, theo khách. Với MEDIA có thêm **KQKD theo công trình/vụ việc**: chọn nhóm Ps / Lk đn / Lk, ba nhóm không cộng với nhau | Bảng kê hóa đơn, KQKD công trình |
| **Đơn hàng** | Đơn hàng bán theo trạng thái, khách, sản phẩm, tháng giao. Trạng thái là tại ngày xuất file, không phải tồn đơn cuối kỳ. Giá trị đơn khác doanh thu. | Bảng kê đơn hàng bán |
| **Công nợ** | Phải thu / phải trả: dư Nợ và dư Có tách riêng; tuổi nợ theo nhóm của FAST tại ngày chốt báo cáo; đối tượng quá hạn; chênh lệch sổ – hóa đơn | CĐPS công nợ, công nợ theo hóa đơn, theo hạn thanh toán |
| **TSCĐ** | Nguyên giá, hao mòn, giá trị còn lại; khấu hao theo tháng; tăng/giảm tài sản; CCDC. Ô “EBITDA dùng khấu hao nào?” giải thích công thức. | Báo cáo TSCĐ, bảng khấu hao nhiều kỳ |
| **Tồn kho** | Tồn theo kho, mã hàng (số lượng chỉ cộng cùng ĐVT); nhập/xuất theo tháng; chi phí sản xuất theo sản phẩm (yếu tố 01 và 02 riêng) | NXT theo kho, phiếu nhập/xuất, CPSX |
| **Sản xuất** | Chỉ số sản xuất Alta Plastics | File HTML “Tổng quan sản xuất” |
| **Dữ liệu nguồn** | Nạp file, kiểm tra từng file, trạng thái theo đơn vị, báo cáo FAST đã thử nhưng trống, ma trận chỉ tiêu × nguồn, xuất, thiết lập | — |
| **Đối chiếu** | Kiểm tra giữa các báo cáo FAST theo đơn vị: Đạt / Cần xem / Không đạt | — |
| **Quy trình** | Quy trình hằng tháng và định nghĩa chỉ số | — |

Một số nhãn trên thẻ:

| Nhãn | Nghĩa |
|---|---|
| **KH theo bảng khấu hao** | EBITDA dùng khấu hao từ bảng khấu hao nhiều kỳ, không dùng biến động TK 214 |
| **Thuế TNDN chưa xác nhận** | TK 821 không phát sinh; không kết luận thuế bằng 0 |
| **Snapshot T9/26 (khác kỳ chọn …)** | Trong file xuất: số chốt tại ngày báo cáo FAST, không theo tháng đang chọn |

## 6. Truy xuất về chứng từ

Bấm vào **bất kỳ số nào**: thẻ, ô bảng KQKD, cột biểu đồ, dòng công nợ, dòng kiểm tra có nhãn “xem chứng từ”. Hộp **Truy xuất nguồn** mở ra với:

- **Số đang xem, công thức, và dòng “Tổng các dòng”**: dấu ✓ nghĩa là các dòng chứng từ cộng lại đúng bằng số hiển thị.
- **Bảng theo tài khoản / nhóm**: bấm một dòng để lọc.
- **Các dòng chứng từ**, mỗi dòng có **Nguồn** = tên file › sheet · số dòng trong Excel, để mở file FAST gốc đúng dòng đó.
- Ô tìm kiếm và sắp xếp.
- Nút **Sao chép bảng** (dán vào Excel) và nút **Tải Excel** (toàn bộ dòng, kèm file, sheet, dòng Excel).

Đóng bằng nút **Đóng** hoặc phím Esc.

## 7. Xuất dữ liệu

| Bạn cần | Làm |
|---|---|
| Dữ liệu một biểu đồ | Bấm **CSV**, **Excel** hoặc **PNG** ngay trên biểu đồ. CSV/Excel gồm số từng chuỗi theo tháng hoặc nhóm và sheet `Pham_vi` (đơn vị, kỳ, chế độ kỳ). Ô trống là không có dữ liệu, không phải 0. |
| Bảng chứng từ sau một con số | Mở truy xuất (mục 6) → **Tải Excel** |
| Bảng chỉ tiêu theo kỳ và danh sách vấn đề | Trang Dữ liệu nguồn hoặc Đối chiếu → **Tải Excel (4 sheet)**, **Tải CSV chỉ tiêu**, **Tải CSV vấn đề dữ liệu** |

File Excel chỉ tiêu có các sheet:
- `Pham_vi`: đơn vị, kỳ, có phải hợp nhất không, thời điểm xuất.
- `Chi_tieu`: đơn vị, chỉ tiêu, kỳ, giá trị, nguồn, công thức, trạng thái đối chiếu, ghi chú chênh lệch.
- `Van_de_du_lieu`
- `Nguon_file`: từng file với đầy đủ metadata.

Phạm vi file xuất theo đúng đơn vị và tháng đang chọn. Ví dụ chọn MEDIA, T5/26: chỉ có số MEDIA, tháng T1–T5 và lũy kế đến T5.

Trên link claude.ai, mỗi lần lưu trình duyệt sẽ hỏi xác nhận. Mở file HTML trực tiếp thì file tải về thư mục Tải xuống như bình thường.

## 8. Gửi dashboard cho người khác đọc

1. Chọn phạm vi muốn gửi:
   - **Các đơn vị**: gửi tất cả đơn vị.
   - Một đơn vị, ví dụ **MEDIA**: file chỉ chứa số MEDIA.
2. Bấm **Lưu bản chia sẻ** (thanh trên cùng). Sau vài giây có file `Alta_Dashboard_<đơn vị>_den_<tháng>_ban_chia_se.html`: khoảng 17 MB cho hai đơn vị, 5 MB cho một đơn vị.
3. Gửi file qua email, Drive, Teams…

Người nhận:
- Nhấp đúp file để mở; không cần nạp gì.
- Thấy băng **Bản chia sẻ chỉ đọc** kèm thời điểm đóng gói.
- Xem được mọi trang, đổi đơn vị/kỳ, truy xuất chứng từ, xuất biểu đồ và Excel.
- Không nạp, xóa hay sửa nguồn được. Bản chia sẻ không ghi gì vào dữ liệu trình duyệt của họ.

Lưu ý:
- Lưu từ **bản offline** thì người nhận mở được không cần mạng. Lưu từ bản thường hoặc link claude.ai thì người nhận cần mạng để tải thư viện biểu đồ và Excel.
- Số trong bản chia sẻ cố định tại lúc lưu. Muốn cập nhật thì nạp lại dữ liệu FAST mới và lưu bản mới.
- File chứa số liệu chi tiết đến từng chứng từ: chỉ gửi cho người được phép xem.

## 9. Thiết lập (trang Dữ liệu nguồn, cuối trang)

| Mục | Dùng khi |
|---|---|
| **TK hàng tồn kho dùng để đối chiếu với NXT** | Mặc định 152, 153, 155, 156, 157. Đổi nếu đơn vị dùng TK khác. |
| **MST công ty mẹ / PLASTIC / MEDIA** | Dòng có mã khách hoặc NCC là các MST này được coi là giao dịch nội bộ |
| **Kế toán đã xác nhận danh sách MST nội bộ và quy tắc loại trừ** | Chỉ tick khi kế toán đã duyệt. Sau đó ô “Loại trừ nội bộ” mới dùng được, và khi đủ 3 đơn vị mới được gọi là “Hợp nhất”. |

Mỗi file trong bảng có nút **Tắt / Bật** (bỏ tạm khỏi số liệu) và **Xóa**. **Xóa toàn bộ dữ liệu đã nạp** xóa dữ liệu trong trình duyệt này, không xóa file Excel trên máy.

## 10. Đọc trang Đối chiếu

| Kết quả | Nghĩa |
|---|---|
| **Đạt** | Hai báo cáo FAST khớp nhau |
| **Cần xem** | Có chênh nhưng đã tìm được nguồn gốc từ dữ liệu, hoặc là thông tin cần kế toán xác nhận (ví dụ thuế TNDN chưa phát sinh) |
| **Không đạt** | Có chênh chưa giải thích được bằng chứng từ |

Dashboard **không bao giờ điều chỉnh số để khớp**. Chênh lệch nằm trong số liệu FAST thì kế toán xử lý trên FAST rồi xuất lại. Ví dụ hiện tại:
- tồn kho âm trên NXT;
- cân đối kế toán FAST không cân;
- bảng kê bán hàng lệch TK 511;
- báo cáo tuổi nợ thiếu hóa đơn.

Danh sách hiện tại: [`fast_nap_thu_plastic_media_2026-11-05.md`](fast_nap_thu_plastic_media_2026-11-05.md).

Kiểm tra có nhãn **xem chứng từ**: bấm để xem đúng các chứng từ gây chênh. Một số kiểm tra có **Bảng chi tiết** (bấm để mở).

## 11. Quy trình hằng tháng gợi ý

1. Kế toán khóa sổ trên FAST (khấu hao, phân bổ, giá vốn, kết chuyển).
2. Xuất bộ báo cáo cho từng đơn vị vào thư mục riêng, kèm kê khai.
3. Mở dashboard → Dữ liệu nguồn → Chọn cả thư mục → rà soát → Nạp.
4. Kiểm tra bảng trạng thái: không còn file “Chờ”.
5. Đọc trang Đối chiếu; gửi Excel vấn đề dữ liệu cho kế toán.
6. Đọc CEO, CFO, Công nợ; xuất biểu đồ cần đưa vào báo cáo.
7. Lưu bản chia sẻ (từ bản offline) gửi CEO/HĐQT.

## 12. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| Băng “Không tải được thư viện …” | Mở bản `…_offline.html`, hoặc để thư mục `vendor/` cạnh file HTML |
| Trang trống “Chưa có dữ liệu cho phạm vi và kỳ đã chọn” | Kiểm tra đơn vị và tháng đang chọn; đơn vị đó đã nạp chưa (bảng Trạng thái nguồn) |
| Số không đổi sau khi xuất lại từ FAST | Kiểm tra file mới có trạng thái “Đang dùng” và file cũ “Bị thay”. Nếu file mới giống hệt file cũ thì đã bị bỏ qua là đúng. |
| Nhiều file “Chờ xác nhận đơn vị” | Thư mục thiếu file kê khai: dùng nút xác nhận theo thư mục |
| Nạp chậm | Bình thường với khoảng 100 file (1–2 phút); không đóng tab khi đang nạp |
| Bấm lưu/xuất không thấy file | Trên link claude.ai: bấm đồng ý ở hộp xác nhận. Mở file trực tiếp: xem thư mục Tải xuống. |
| Muốn làm lại từ đầu | Dữ liệu nguồn → Xóa toàn bộ dữ liệu đã nạp → nạp lại thư mục |
