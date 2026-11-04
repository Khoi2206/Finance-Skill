---
name: vn-finance-compliance
description: Tuân thủ kế toán – thuế – kiểm toán – đóng sổ theo quy định Việt Nam cho Alta Group. Dùng khi hỏi về chế độ kế toán (VAS, TT200/TT99, TT133), thuế TNDN, GTGT, TNCN, thuế nhà thầu, hóa đơn điện tử, giao dịch liên kết (NĐ132), giới hạn chi phí lãi vay 30% EBITDA, lịch kê khai/nộp thuế, quyết toán, chuẩn bị kiểm toán, checklist đóng sổ tháng, kiểm soát nội bộ, hoặc rủi ro thanh tra thuế.
---

# Tuân thủ Tài chính – Kế toán – Thuế Việt Nam

> ⚠️ Quy định VN thay đổi thường xuyên. Mọi mức thuế suất/ngưỡng/thời hạn dưới đây là **điểm xuất phát để kiểm tra**, không phải kết luận. Luôn đối chiếu văn bản hiện hành (thuvienphapluat.vn, gdt.gov.vn) và ghi "cần kế toán thuế/kiểm toán xác nhận" trong đầu ra. Nếu có công cụ tìm kiếm web, tra lại văn bản trước khi trả lời câu hỏi về mức/ngưỡng cụ thể.

## 1. Khung pháp lý cần kiểm tra (bản đồ văn bản)

| Lĩnh vực | Văn bản gốc | Ghi chú cần kiểm tra hiệu lực |
|---|---|---|
| Chế độ kế toán DN | TT200/2014/TT-BTC; TT133/2016 (DNNVV) | TT99/2025/TT-BTC thay thế TT200 từ năm tài chính 2026 — rà soát hệ thống tài khoản & mẫu BCTC mới trên Fast |
| BCTC hợp nhất | TT202/2014/TT-BTC, VAS 25 | Xem `group-consolidation-ic` |
| Thuế TNDN | Luật 67/2025/QH15 và văn bản hướng dẫn | Thuế suất phổ thông 20%; ưu đãi DN nhỏ; tạm nộp quý, 4 quý ≥ 80% số quyết toán |
| Thuế GTGT | Luật 48/2024/QH15 (từ 1/7/2025) | 0% / 5% / 10%; kiểm tra chính sách giảm 2% đang áp dụng; điều kiện khấu trừ & thanh toán không dùng tiền mặt |
| Hóa đơn điện tử | NĐ123/2020 sửa đổi bởi NĐ70/2025 | Thời điểm lập hóa đơn dịch vụ, hóa đơn điều chỉnh/thay thế |
| Giao dịch liên kết | NĐ132/2020 (sửa đổi NĐ20/2025) | Alta Mẹ – Plastic – Media là bên liên kết → Phụ lục kê khai, hồ sơ xác định giá, trần lãi vay 30% EBITDA |
| Quản lý thuế | Luật Quản lý thuế 38/2019, NĐ126/2020 | Lịch kê khai, phạt chậm nộp 0,03%/ngày |
| Thuế nhà thầu | TT103/2014 | Thanh toán cho nhà cung cấp nước ngoài (phần mềm, quảng cáo nền tảng, bản quyền nội dung LED) |
| TNCN, BHXH | Luật TNCN, Luật BHXH 2024 | Quyết toán TNCN thay người lao động |

## 2. Lịch tuân thủ năm (mẫu — điều chỉnh theo kỳ kê khai thực tế của từng MST)

| Thời hạn | Việc | Áp dụng |
|---|---|---|
| Ngày 20 tháng sau / ngày cuối tháng đầu quý sau | Tờ khai GTGT, TNCN khấu trừ | Theo kỳ tháng/quý của từng công ty |
| Ngày 30 tháng đầu quý sau | Tạm nộp TNDN quý | Cả 3 công ty |
| 31/3 năm sau | Quyết toán TNDN, TNCN, nộp BCTC năm đã kiểm toán (nếu thuộc diện), Phụ lục GDLK | Cả 3 công ty |
| Trước 30/4 (theo điều lệ) | ĐHĐCĐ/HĐTV thường niên | Công ty Mẹ |
| Hàng tháng N+5 | Đóng sổ quản trị | Cả 3 |

## 3. Checklist đóng sổ tháng (Close calendar N+5)

**N+1** — Khóa nhập liệu kỳ; đối chiếu tiền & ngân hàng (sổ phụ từng tài khoản); xuất bảng kê hóa đơn bán ra/mua vào từ Fast.
**N+2** — Đối chiếu doanh thu với hóa đơn điện tử đã phát hành (bao gồm TK 13111T: xuất kho chưa có hóa đơn ở Plastic, cho thuê không hóa đơn ở Mẹ); trích trước chi phí (điện, lãi vay, thưởng, chi phí sự kiện Media chưa có hóa đơn); phân bổ chi phí trả trước; khấu hao.
**N+3** — Tồn kho Plastic: giá thành, chênh lệch kiểm kê, dự phòng giảm giá; dự phòng phải thu khó đòi theo tuổi nợ; đối chiếu công nợ nội bộ 3 công ty (phải khớp 100%).
**N+4** — Lập BCTC từng công ty; giải trình biến động >10% và >500 triệu so với kỳ trước/kế hoạch (dùng `an-variance-commentary`).
**N+5** — Hợp nhất quản trị, báo cáo cho CEO/HĐQT (`board-management-pack`).

Kiểm soát chốt: bảng cân đối thử cân; tiền khớp sổ phụ; công nợ nội bộ khớp; thuế GTGT đầu ra trên sổ = tờ khai = hóa đơn; không còn tài khoản trung gian treo số dư không giải thích.

## 4. Điểm rủi ro thuế đặc thù Alta (kiểm tra mỗi kỳ)

1. **Giao dịch nội bộ** (cho thuê của Mẹ, bán hàng Plastic ↔ Media, cho vay nội bộ): giá có theo nguyên tắc giao dịch độc lập? Có hợp đồng, hóa đơn đầy đủ? Lãi vay nội bộ có vượt trần 30% EBITDA?
2. **Doanh thu ghi nhận trước hóa đơn** (13111T): rủi ro chênh lệch thời điểm xuất hóa đơn → phạt hóa đơn. Theo dõi tuổi các khoản xuất chưa hóa đơn.
3. **Chi phí sự kiện/quảng cáo Media**: chứng từ thanh toán không dùng tiền mặt cho hóa đơn ≥ ngưỡng quy định; chi phí không có hóa đơn hợp lệ → loại khỏi chi phí được trừ.
4. **Thuế nhà thầu** với dịch vụ nền tảng nước ngoài (Google, Meta, phần mềm LED).
5. **Hoàn thuế/khấu trừ GTGT** dự án đầu tư dài hạn.

## 5. Chuẩn bị kiểm toán (PBC)
Dùng `ps-audit-pbc-auditor-query-responder` + `cm-audit-preparation`. Danh sách tối thiểu: BCĐ số phát sinh, sổ cái, xác nhận số dư ngân hàng/công nợ (gửi trước 31/12), biên bản kiểm kê tiền–hàng–TSCĐ 31/12, bảng khấu hao, hợp đồng vay & lịch trả nợ, hợp đồng lớn, hồ sơ GDLK, biên bản họp HĐQT về các quyết định trọng yếu.

## 6. Đầu ra
- Câu trả lời: Kết luận ngắn → căn cứ (văn bản, điều khoản) → rủi ro/phạt nếu sai → việc cần làm → "cần xác nhận".
- Checklist dạng bảng có cột Người phụ trách | Hạn | Trạng thái.
