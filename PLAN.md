# Lộ trình 90 ngày — vận hành vai trò CFO & Strategy Director với bộ skill

## Bộ khởi đầu (tải lên Cowork trước — 20 skill)
Lõi: `cfo-command-center`, `strategy-dev-director`, `cash-13-week-treasury`, `board-management-pack`, `group-consolidation-ic`, `vn-finance-compliance`, `strategic-plan-budget`, `investment-appraisal`, `corp-dev-ma-vn`.
Thư viện: `ar-cfo-advisor`, `ar-ceo-advisor`, `cm-scenario-planning`, `cm-budget-creation-management`, `an-variance-commentary`, `ps-debt-covenant-dscr-monitor`, `cm-working-capital-optimization`, `cm-profitability-analysis`, `wd-good-strategy-bad-strategy`, `ar-competitive-intel`, `an-dd-checklist`.

## Tháng 1 — Nắm quyền kiểm soát số liệu & tiền (CFO trước)
| Tuần | Việc | Skill | Đầu ra |
|---|---|---|---|
| 1 | Báo cáo bán hàng 9T/2026 + hiện trạng 3 công ty | `alta-sales-report`, `cfo-command-center` | Trang tổng quan + danh sách vấn đề |
| 1–2 | Dựng dòng tiền 13 tuần & bảng nợ vay, covenant | `cash-13-week-treasury`, `ps-debt-covenant-dscr-monitor` | Excel 13W, cập nhật mỗi thứ Hai |
| 2–3 | Ma trận đối chiếu nội bộ & hợp nhất quản trị | `group-consolidation-ic` | File hợp nhất + chênh lệch cần xử lý |
| 3–4 | Chuẩn hóa lịch đóng sổ N+5 & lịch thuế; rà soát chuyển sang TT99 | `vn-finance-compliance`, `cm-monthly-close-process` | Close calendar, checklist |
| 4 | Board pack tháng đầu tiên | `board-management-pack` | Deck + Excel |

## Tháng 2 — Kế hoạch 2027 (giao thoa CFO × Chiến lược)
| Việc | Skill |
|---|---|
| Rà soát chiến lược từng mảng: chẩn đoán, thị trường, đối thủ | `strategy-dev-director`, `wd-good-strategy-bad-strategy`, `ar-competitive-intel`, `an-sector-overview` |
| Định hướng top-down + ngân sách bottom-up driver-based | `strategic-plan-budget`, `cm-budget-creation-management`, `cm-revenue-forecasting` |
| 3 kịch bản + dòng tiền + covenant | `cm-scenario-planning`, `ar-scenario-war-room` |
| BSC/OKR 2027, gắn thưởng | `strategic-plan-budget`, `ar-strategic-alignment` |
| Trình HĐQT tháng 12 | `board-management-pack` |

## Tháng 3 — Phát triển & phân bổ vốn (Chiến lược)
| Việc | Skill |
|---|---|
| Danh mục sáng kiến chiến lược + kill criteria | `strategy-dev-director` |
| Thẩm định các dự án capex lớn (LED, máy móc Plastic) | `investment-appraisal`, `cm-business-case-modeling` |
| Chuẩn bị gọi vốn Alta Media: IM, mô hình, data room, term sheet | `am-im-skill`, `corp-dev-ma-vn`, `cm-fundraising-financials`, `cm-data-room-management`, `ps-cap-table-dilution-simulator` |
| Pipeline M&A/đối tác: tiêu chí, long-list, sàng lọc | `corp-dev-ma-vn`, `an-deal-sourcing`, `an-deal-screening`, `ar-partnerships-architect` |
| Chương trình tối ưu chi phí & vốn lưu động | `cm-cost-optimization`, `cm-working-capital-optimization` |

## Nhịp định kỳ đề xuất (có thể đặt thành scheduled task)
- **Thứ Hai hằng tuần**: cập nhật 13 tuần + tuổi nợ quá hạn.
- **Ngày 5 hằng tháng**: đóng sổ, báo cáo bán hàng, hợp nhất, board pack tháng.
- **Tuần 2 tháng đầu quý**: rolling forecast, covenant, tạm nộp TNDN, đánh giá OKR & danh mục sáng kiến.

## Về "memory của Claude Cowork"
Phiên này chạy trên cloud nên không đọc được memory/Projects của Cowork trên máy Khôi. Bối cảnh đã dùng lấy từ 2 skill có sẵn trong tài khoản (`alta-sales-report`, `am-im-skill`): 3 pháp nhân, MST nội bộ, mã vụ việc Media, phần mềm Fast, IM gọi vốn Alta Media. Để bổ sung: trong Cowork, nhờ Claude xuất memory/bối cảnh rồi dán vào mục "Bối cảnh cố định" của `core/cfo-command-center/SKILL.md` và `core/strategy-dev-director/SKILL.md` (tỷ lệ sở hữu, ngân hàng đang vay, kế hoạch năm, cơ cấu HĐQT…).
