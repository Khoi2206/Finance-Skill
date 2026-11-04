# Công cụ #2 — Thu thập giả định Ngân sách 2027 từ BU

Trang web dùng chung: mỗi trưởng BU điền giả định ngân sách, CFO theo dõi ai đã nộp, so với định hướng top-down và xuất số sang mô hình Excel (công cụ #1). Dùng lại được cho mọi mùa ngân sách.

- **Link trang:** https://claude.ai/artifact/7a2nEGm5X6UvcsTJUxzkqG (riêng tư, chỉ Khôi mở được cho tới khi chia sẻ)
- **Mã nguồn:** `tools/bu-assumptions/bu-assumptions.html`
- **Dữ liệu:** lưu trong kho dữ liệu của chính artifact trên claude.ai (không nằm trong repo). Đơn vị tiền: **triệu đồng**.

## BU và mã

| Pháp nhân | Mã | BU |
|---|---|---|
| Alta (Mẹ) `ALTA` | `ALTA-RENT` | Cho thuê mặt bằng |
| | `ALTA-TECH` | Thiết bị & dự án công nghệ |
| | `ALTA-BAG` | Thương mại túi bao bì |
| Alta Plastic `APL` | `APL-PACK` | Bao bì nhựa |
| | `APL-RESIN` | Thương mại hạt nhựa |
| | `APL-3D` | In 3D |
| Alta Media `AME` | `AME-LED` | LED |
| | `AME-BA` | Thiết bị, giải pháp |
| | `AME-TTB` | Cho thuê hệ thống đa phương tiện |
| | `AME-DVK` | Dịch vụ, chia doanh thu |
| | `AME-TKL` | Phần mềm, thiết kế |

Mã khớp `alta-finance-intelligence/config/entity_map.yaml` (riêng `ALTA-BAG` mới thêm ở trang này, chưa có trong entity map).

## Quy trình mùa ngân sách

1. **CFO gửi định hướng** — tab *Tổng hợp CFO*, mục cuối: nhập cho từng pháp nhân ước thực hiện doanh thu 2026, tăng trưởng mục tiêu %, biên gộp mục tiêu %, trần capex; hạn nộp và thông điệp. Bấm *Lưu & gửi định hướng*. Trưởng BU thấy ngay ở đầu biểu mẫu.
2. **Chia sẻ link** cho trưởng BU (xem mục dưới).
3. **BU điền** — tab *Trang BU*, chọn BU, chọn nhập theo quý hoặc tháng:
   - Doanh thu theo khách hàng lớn / nhóm sản phẩm: sản lượng mỗi kỳ, đơn giá, biên gộp %.
   - Nhân sự: số người cuối kỳ theo bộ phận, lương bình quân (chi phí tính × 1,215 gồm phần BHXH DN ~21,5% — cần xác nhận tỷ lệ).
   - Chi phí chính, capex (hạng mục, số tiền, tháng thanh toán), rủi ro & cơ hội (không cộng vào kế hoạch), mức độ tự tin 1–5.
   - *Lưu nháp* bất cứ lúc nào; *Nộp cho CFO* khi xong (trang kiểm tra: có doanh thu, capex đủ tên/số tiền, đã chọn mức tự tin). Đã nộp thì khóa; muốn sửa bấm *Rút lại để sửa*.
4. **CFO rà soát** — bảng trạng thái (Chưa bắt đầu / Nháp / Đã nộp / Trả lại / Đã duyệt). *Rà soát* → *Duyệt* hoặc *Trả lại kèm bình luận* (bắt buộc ghi). BU thấy bình luận, sửa, nộp lại. Bản đã duyệt có thể *Mở lại*. Lịch sử quyết định lưu 20 lần gần nhất.
5. **Chốt** — bảng tổng hợp theo pháp nhân so với định hướng, tô màu: xanh = đạt; vàng = hụt nhẹ (doanh thu hụt ≤ 5%, biên hụt ≤ 2 điểm, capex ≥ 90% trần); đỏ = lệch lớn. Tick *Chỉ tính bản đã nộp/đã duyệt* khi chốt. Số cộng thẳng, **chưa loại trừ nội bộ** (làm trong mô hình #1).
6. **Xuất sang Excel** — chọn theo tháng hoặc quý, bấm *Sao chép bảng (TSV)* rồi dán vào ô A1 sheet nhập liệu (hoặc *Sao chép CSV*). Cột: `company, bu, month|quarter, line, amount`. `line` ∈ `revenue, cogs, gross_profit, payroll, opex, contribution, capex, headcount` (tr đ; `headcount` là số người). BU nhập theo quý được chia đều 3 tháng khi xuất theo tháng; headcount lấy số cuối kỳ. Capex xuất đúng tháng thanh toán.

**Mùa sau:** dùng lại cùng link. Khi bắt đầu mùa mới, nhờ Claude xóa/sao lưu dữ liệu cũ (`ArtifactData`) và đổi năm `YEAR` trong file HTML rồi publish lại vào cùng URL.

## Chia sẻ link cho trưởng BU

Trang **riêng tư**: chỉ Khôi mở được. Khôi phải tự chia sẻ — Claude không chia sẻ thay được.

1. Mở link trang trên claude.ai → menu **Share**.
2. Thêm từng trưởng BU (cùng tổ chức) với mức **Contributor** (đóng góp): đọc và lưu được giả định BU, **không** sửa được định hướng hay duyệt/trả lại.
3. Không cấp **Editor** cho trưởng BU: Editor có quyền quản trị (duyệt, sửa định hướng). Viewer/Commenter chỉ xem, không lưu được.
4. Gửi link kèm mã BU của từng người.

Lưu ý quyền:
- Quyền ghi được kiểm soát ở máy chủ: định hướng (`cfg/`) và quyết định duyệt (`review/`) chỉ chủ trang/Editor ghi được; giả định BU (`bu/<mã BU>`) mọi Contributor ghi được.
- Trang **không** khóa theo từng BU: một Contributor có thể xem và (về kỹ thuật) sửa BU khác. Trang ghi lại ai lưu lần cuối và lúc nào. Nếu cần tách bạch tuyệt đối, dùng một bản trang riêng cho mỗi BU.
- Hai người sửa cùng một BU một lúc: bản lưu sau thắng; trang báo "Có người khác vừa lưu bản mới" để tải lại.

## Dữ liệu mẫu

Nút **Xem dữ liệu mẫu** (đầu trang) mở bộ số minh họa có dải "DỮ LIỆU MẪU" — không phải số thật của Alta, thao tác trong chế độ này không lưu. Khi kho còn trống, tab CFO hiện hướng dẫn bắt đầu. Mở trang ngoài claude.ai (không có kho dữ liệu) sẽ tự vào chế độ mẫu.

## Cấu trúc dữ liệu (cho Claude/công cụ khác đọc)

- `cfg/guidance`: `{message, deadline, entities:{ALTA|APL|AME:{base, growth, gm, capexCap}}, at, by}`
- `bu/<mã BU>`: `{bu, company, granularity:"Q"|"M", status:"draft"|"submitted", revenue[{kind,name,unit,price,gm,vol[]}], headcount[{dept,salary,hc[]}], opex[{name,amt[]}], capex[{item,amount,month,note}], risks[{type,desc,impact,prob}], confidence, confidenceNote, notes, savedAt, submittedAt, lastSubmittedAt, editedBy}`
- `review/<mã BU>`: `{decision:"returned"|"approved", comment, at, by, forSubmittedAt, history[]}` — trạng thái hiển thị = quyết định nếu `forSubmittedAt` khớp lần nộp hiện tại.
- `editedBy`/`by` là id người dùng claude.ai (không lưu tên).
