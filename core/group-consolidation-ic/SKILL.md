---
name: group-consolidation-ic
description: Hợp nhất báo cáo tài chính quản trị và theo VAS 25/TT202 cho Alta Group (Mẹ, Plastic, Media) và đối chiếu, loại trừ giao dịch nội bộ. Dùng khi cần BCTC hợp nhất, báo cáo kết quả theo mảng, đối chiếu công nợ/doanh thu nội bộ giữa 3 công ty, xác định doanh thu ngoài tập đoàn, lợi ích cổ đông không kiểm soát, hoặc lãi chưa thực hiện trong tồn kho nội bộ.
---

# Hợp nhất & Giao dịch nội bộ — Alta Group

## 1. Nhận diện nội bộ
- MST nội bộ: **0301420079** (Alta Mẹ) · **0312414944** (Alta Plastic) · **0305904835** (Alta Media). Dòng nào trên bảng kê bán/mua có MST đối tác thuộc danh sách này = giao dịch nội bộ. Có công ty con mới → hỏi Khôi bổ sung MST.
- Hỏi (một lần, rồi ghi nhớ trong cuộc trò chuyện) tỷ lệ sở hữu của Mẹ tại Plastic và Media để tính lợi ích cổ đông không kiểm soát (NCI). Nếu không biết, trình bày hợp nhất 100% và ghi rõ giả định.

## 2. Quy trình
1. **Thu thập** BCTC/bảng cân đối thử từng công ty cùng kỳ, cùng hệ thống tài khoản; kiểm tra từng bộ tự cân.
2. **Ma trận đối chiếu nội bộ** (IC matrix) — mỗi cặp công ty, mỗi loại:
   | Bên A | Bên B | Loại (bán hàng / cho thuê / dịch vụ / cho vay / lãi / cổ tức) | Số theo A | Số theo B | Chênh lệch | Nguyên nhân |
   Nguyên nhân thường gặp: hàng đang đi đường, hóa đơn chưa nhận, chênh lệch thời điểm, hạch toán sai đối tượng, dịch vụ (điện, thuê, lãi, phí) không qua kho → không có trên bảng kê mua hàng nhập kho (bình thường, đối chiếu bằng sổ công nợ).
3. **Bút toán loại trừ** (mỗi bút toán có diễn giải):
   - Doanh thu – giá vốn nội bộ: Nợ Doanh thu / Có Giá vốn.
   - Lãi chưa thực hiện trong tồn kho cuối kỳ (Plastic bán cho Media chưa bán ra ngoài): Nợ Giá vốn / Có Hàng tồn kho = tồn kho nội bộ × biên lợi nhuận gộp của bên bán; ghi nhận thuế hoãn lại nếu trọng yếu.
   - Công nợ nội bộ: Nợ Phải trả / Có Phải thu.
   - Cho vay & lãi vay nội bộ: Nợ Doanh thu tài chính / Có Chi phí lãi vay; Nợ Vay / Có Cho vay.
   - Cho thuê nội bộ của Mẹ: Nợ Doanh thu cho thuê / Có Chi phí thuê.
   - Cổ tức từ con: Nợ Doanh thu tài chính / Có Lợi nhuận chưa phân phối.
   - Khoản đầu tư vào công ty con vs vốn chủ sở hữu công ty con tại ngày mua; lợi thế thương mại (nếu có).
   - Tách NCI trên lợi nhuận và tài sản thuần.
4. **Kiểm tra sau hợp nhất**: BCĐKT hợp nhất cân; tổng loại trừ doanh thu = tổng loại trừ chi phí (trừ phần lãi chưa thực hiện); dòng tiền hợp nhất khớp tiền đầu–cuối kỳ.
5. **Báo cáo theo mảng**: Mẹ (cho thuê/dịch vụ), Plastic (theo nhóm sản phẩm), Media (LED, BA, TTB, DVK, TKL) — doanh thu ngoài tập đoàn, lợi nhuận gộp, EBITDA, vốn sử dụng (capital employed), ROCE.

## 3. Đầu ra
- File Excel (skill `xlsx`): sheet `TB_Me`, `TB_Plastic`, `TB_Media`, `IC_Matrix`, `Elims` (mỗi dòng là 1 bút toán có công thức), `Consol_PL`, `Consol_BS`, `Consol_CF`, `Segments`, `Checks` (mọi check = 0).
- Tóm tắt: Doanh thu hợp nhất, % doanh thu nội bộ bị loại trừ, chênh lệch đối chiếu chưa giải thích (phải = 0 hoặc liệt kê), 3 điểm cần kế toán xử lý.
- Nhắc: báo cáo hợp nhất theo TT202 cho mục đích luật định cần kiểm toán xác nhận; bản này là hợp nhất quản trị.
