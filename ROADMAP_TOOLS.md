# Lộ trình bộ công cụ CFO & S&D — Alta Group

Mục tiêu: mỗi công cụ làm một lần, dùng lại hằng tháng/quý. Tất cả dùng chung dữ liệu từ pipeline FAST (`alta-finance-intelligence/`) và các skill trong `core/`, để số liệu giữa các công cụ khớp nhau.

Thứ tự ưu tiên bám theo lịch thực tế của Alta: **rà soát 9T/2026 → dự báo cả năm 2026 → Ngân sách 2027 (đang vào mùa: tháng 11–12)**, sau đó là đầu tư nhà máy mới, gọi vốn Alta Media và chiến lược 5 năm cho HĐQT.

Dạng công cụ:
- **Trang web (artifact):** mở bằng link, có thể chia sẻ, lưu dữ liệu dùng chung khi cần.
- **Mô hình Excel:** do script sinh ra, có công thức thật, kế toán và BU sửa được.
- **Skill:** quy trình để Claude làm lại đúng cách mỗi lần.
- **Tác vụ định kỳ:** Claude tự chạy theo lịch (tuần/tháng) và gửi kết quả.

---

## Đợt 1 — Tháng 11–12/2026: mùa kế hoạch (làm ngay)

| # | Công cụ | Dạng | Dùng để | Đầu vào | Dùng lại | Ước lượng |
|---|---|---|---|---|---|---|
| 1 | ✅ **Mô hình Dự báo 2026 & Ngân sách 2027 theo driver** — ĐÃ LÀM: `tools/budget-model/` (script, test, file mẫu `output/`), skill `core/budget-model/SKILL.md` | Excel do script sinh + skill | Plastic: sản lượng × giá bán × giá hạt nhựa; Media: số job/backlog × giá trị × biên; Mẹ: diện tích × đơn giá. 3 kịch bản, ba báo cáo liên kết, hợp nhất loại trừ nội bộ | Số thực tế 9T (pipeline), giả định BU | Mỗi quý cập nhật rolling forecast; mỗi năm làm ngân sách | 2–3 phiên |
| 2 | ✅ **Bộ thu thập giả định ngân sách từ BU** — [đã làm](https://claude.ai/artifact/7a2nEGm5X6UvcsTJUxzkqG), xem `tools/bu-assumptions/` | Trang web có lưu dữ liệu dùng chung | Mỗi trưởng BU điền giả định (khách hàng lớn, sản lượng, giá, nhân sự, capex) vào một form; CFO thấy ai đã nộp, ai chưa, chênh lệch so với định hướng top-down | Danh sách BU, mẫu giả định | Mỗi mùa ngân sách | 1 phiên |
| 3 | ✅ **Dòng tiền 13 tuần** (Phase 3 của đặc tả) — *đã xây 2026-11-04: `afi cash13w` + `tools/cash-13w/cash13w.html`; chờ sao kê, công nợ, lịch vay thật* | Trang web + Excel | Tiền đầu kỳ đã đối chiếu ngân hàng, công nợ phải thu/trả theo hóa đơn, lịch trả nợ, lương, thuế, capex; Base/Downside; so thực tế với dự báo tuần trước | Sao kê, công nợ, lịch vay | Mỗi thứ Hai | 2 phiên |
| 4 | ✅ **Bộ tạo báo cáo HĐQT / báo cáo quản trị tháng** — đã xây: `tools/board-pack/` (`afi boardpack`) | Script sinh PPTX + skill `board-management-pack` | Từ số đã đối chiếu, tự dựng slide: tóm tắt điều hành, KPI, cầu nối EBITDA, theo BU, tiền, rủi ro, đề xuất nghị quyết; bình luận biến động có nguyên nhân | Dữ liệu từ pipeline/dashboard | Mỗi tháng, mỗi quý | 1–2 phiên |

## Đợt 2 — Quý 1/2027: kiểm soát tài chính

| # | Công cụ | Dạng | Dùng để | Dùng lại | Ước lượng |
|---|---|---|---|---|---|
| 5 | **Sổ theo dõi nợ vay & covenant** | Trang web có lưu dữ liệu | Danh sách khoản vay, lãi suất, lịch đáo hạn, tài sản bảo đảm; tính dư địa covenant (DSCR, Nợ/EBITDA), cảnh báo trước 1 quý | Mỗi tháng sau khi đóng sổ | 1 phiên |
| 6 | **Theo dõi đóng sổ tháng** | Trang web dùng chung cho phòng kế toán | Checklist N+1…N+5 có người phụ trách, trạng thái, ngoại lệ đối chiếu nội bộ; lịch sử từng kỳ | Mỗi tháng | 1 phiên |
| 7 | **Lịch thuế & tuân thủ có nhắc việc** | Tác vụ định kỳ + trang lịch | Nhắc hạn GTGT, TNCN, tạm nộp TNDN, quyết toán, báo cáo giao dịch liên kết; nhắc trước 5 ngày | Tự chạy hằng tuần | < 1 phiên |
| 8 | **Đọc hợp đồng vay / hợp đồng lớn → sổ điều khoản** | Skill | Đưa PDF hợp đồng vào, trích điều khoản (lãi, phí, covenant, phạt, gia hạn) vào sổ #5 | Mỗi khi ký hợp đồng mới | 1 phiên |

## Đợt 3 — Quý 1–2/2027: chiến lược & phát triển

| # | Công cụ | Dạng | Dùng để | Dùng lại | Ước lượng |
|---|---|---|---|---|---|
| 9 | **Mô hình đầu tư nhà máy mới / capex lớn** | Excel do script sinh + tờ trình | NPV, IRR, hoàn vốn, nhu cầu vốn theo giai đoạn, độ nhạy giá hạt nhựa/công suất/lãi suất, ảnh hưởng covenant; xuất tờ trình HĐQT (skill `investment-appraisal`) | Mỗi dự án capex | 2 phiên |
| 10 | **Bộ gọi vốn Alta Media** | Excel + danh mục data room + ngân hàng câu hỏi | Định giá (DCF + bội số), mô phỏng pha loãng, danh mục tài liệu data room có trạng thái, bộ hỏi–đáp nhà đầu tư; dùng kèm skill `am-im-skill` | Mỗi vòng gọi vốn | 2 phiên |
| 11 | **Theo dõi thương vụ M&A / đối tác** | Trang web có lưu dữ liệu | Danh sách mục tiêu, chấm điểm sàng lọc, giai đoạn, việc tiếp theo; sinh one-pager và IC memo (skill `corp-dev-ma-vn`) | Liên tục | 1 phiên |
| 12 | **Theo dõi thực thi chiến lược & sổ quyết định HĐQT** | Trang web dùng chung | Danh mục sáng kiến (chủ trì, ngân sách, KPI, Xanh/Vàng/Đỏ), nghị quyết HĐQT và việc được giao, OKR quý | Mỗi tháng, mỗi kỳ họp | 1 phiên |
| 13 | **Bản tin thị trường hằng tuần** | Tác vụ định kỳ | Tóm tắt tin ngành bao bì nhựa, giá hạt nhựa, quảng cáo LED/ngoài trời, in 3D, quy định mới, động thái đối thủ; có nguồn | Tự chạy sáng thứ Hai | < 1 phiên |

## Đợt 4 — Quý 2/2027: hiệu quả từng mảng (cần dữ liệu Phase 4)

| # | Công cụ | Dùng để |
|---|---|---|
| 14 | **Lãi lỗ theo job của Alta Media** | Doanh thu, chi phí trực tiếp, đóng góp theo mã vụ việc; cảnh báo job có chi phí = 0; công nợ và thu tiền theo job |
| 15 | **Kinh tế sản xuất Alta Plastic** | Sản lượng, giá bán, cơ cấu, giá hạt nhựa/kg, biên theo nhóm sản phẩm; cầu nối lợi nhuận (giá, lượng, cơ cấu, nguyên liệu) |
| 16 | **Hiệu quả mảng In 3D** | Doanh thu, chi phí trực tiếp, tài sản riêng; chỉ phân bổ chi phí chung khi tiêu thức đã duyệt |
| 17 | **Gói dữ liệu cho dashboard** | Pipeline xuất số đã đối chiếu; dashboard đọc gói này thay vì Excel thô |

---

## Cách dùng tín dụng cloud hiệu quả
- **Mỗi công cụ là một phiên riêng**, mở bằng câu lệnh ở phần dưới. Phiên đó đọc repo này nên kế thừa bối cảnh Alta, skill và pipeline.
- **Làm Đợt 1 trước**: ngân sách 2027 có hạn chót thật; các đợt sau có thể chờ.
- Công cụ cần dữ liệu thật (#3, #5, #14–16) chỉ nên làm khi đã có mẫu FAST/sao kê; nếu chưa có, phiên đó dựng khung + dữ liệu mẫu rồi dừng.
- Tác vụ định kỳ (#7, #13) tốn ít, nên bật sớm.

## Câu lệnh mở phiên (dán vào một phiên Claude Code mới trên repo này)

1. ✅ (đã làm — `tools/budget-model/`) `Đọc ROADMAP_TOOLS.md mục #1 và core/strategic-plan-budget. Xây mô hình Dự báo 2026 & Ngân sách 2027 theo driver cho Alta (Mẹ, Plastic, Media), script Python sinh file Excel có công thức, 3 kịch bản, hợp nhất loại trừ nội bộ. Dùng dữ liệu mẫu nếu chưa có số thật, ghi rõ là mẫu.`
2. ✅ *(đã làm — `tools/bu-assumptions/`)* `Xây công cụ #2 trong ROADMAP_TOOLS.md: trang web thu thập giả định ngân sách 2027 từ các trưởng BU, lưu dữ liệu dùng chung, có trang tổng hợp cho CFO.`
3. ✅ Đã xong. Chạy hằng tuần: `Chạy dòng tiền 13 tuần cho tuần bắt đầu <ngày>: afi cash13w với thư mục đầu vào <…>, tóm tắt 5 dòng theo core/cash-13-week-treasury và liệt kê DATA REQUIRED theo người phụ trách.`
4. `Xây công cụ #4: script sinh báo cáo HĐQT PPTX hằng tháng theo core/board-management-pack từ số liệu của pipeline.`
5. `Xây công cụ #5 và #8: sổ theo dõi nợ vay & covenant (trang web có lưu dữ liệu) và skill đọc hợp đồng vay vào sổ.`
6. `Xây công cụ #6: trang theo dõi đóng sổ tháng cho phòng kế toán theo checklist trong core/vn-finance-compliance.`
7. `Tạo tác vụ định kỳ #7 (lịch thuế, nhắc trước 5 ngày) và #13 (bản tin thị trường sáng thứ Hai).`
8. `Xây công cụ #9: mô hình đầu tư nhà máy mới theo core/investment-appraisal, kèm mẫu tờ trình HĐQT.`
9. `Xây công cụ #10: bộ gọi vốn Alta Media (định giá, pha loãng, data room, hỏi–đáp) dùng cùng am-im-skill.`
10. `Xây công cụ #11 và #12: theo dõi thương vụ M&A và theo dõi thực thi chiến lược + sổ quyết định HĐQT.`
