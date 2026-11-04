# Finance-Skill — Bộ skill CFO & Strategy Director cho Alta Group

Thư viện skill cho Claude (Claude Code, Claude.ai, Cowork) để Khôi đảm nhiệm hai vai trò:
**Giám đốc Tài chính (CFO)** và **Giám đốc Chiến lược & Phát triển (Strategy & Development Director)**.

- `core/` — **10 skill lõi** viết riêng cho Alta Group (tiếng Việt, VAS/thuế VN, 3 pháp nhân Mẹ/Plastic/Media).
- `library/` — **92 skill tuyển chọn** từ 8 repo GitHub mã nguồn mở (MIT/Apache-2.0), chia 10 nhóm nghiệp vụ. Mỗi skill có `SOURCE.md` (nguồn) và `LICENSE.txt`.
- `CATALOG.md` — danh mục đầy đủ, mô tả, nguồn, giấy phép; kèm các repo đã rà soát nhưng chưa nhập.
- `PLAN.md` — lộ trình 90 ngày dùng bộ skill này trong công việc.
- `dashboard/` — **Alta CFO · CEO Dashboard**: kéo thả file xuất từ FAST Business → dashboard CEO/CFO/Bán hàng, kiểm tra đối chiếu, truy xuất ngược từng con số về chứng từ gốc. Xem `dashboard/README.md`.

## Bắt đầu nhanh

Chỉ cần nhớ 2 điểm vào — chúng tự chọn skill chuyên sâu:

| Gõ | Skill | Ví dụ |
|---|---|---|
| `/cfo-command-center` hoặc "với vai trò CFO…" | Tài chính | "Lập dòng tiền 13 tuần cho Plastic", "Board pack Q3", "Kiểm tra covenant Vietcombank" |
| `/strategy-dev-director` hoặc "chiến lược…" | Chiến lược | "Kế hoạch 3 năm cho Alta Media", "Sàng lọc 5 mục tiêu M&A ngành bao bì nhựa" |

## Cài đặt

**Claude Code (máy cá nhân):**
```bash
git clone https://github.com/khoi2206/finance-skill.git
```
```bash
bash finance-skill/scripts/install.sh
```
(cài vào `~/.claude/skills`; hoặc chép từng thư mục skill vào `.claude/skills/` của một dự án).

**Claude.ai / Cowork:** tạo file zip rồi tải lên tại *Settings → Capabilities → Skills → Upload skill*:
```bash
bash finance-skill/scripts/package.sh
```
Nên tải trước 9 skill lõi + các skill được định tuyến tới nhiều nhất (xem PLAN.md, mục "Bộ khởi đầu").

## Nhóm skill

| Nhóm | Thư mục | Số skill |
|---|---|---|
| CFO – tư duy & điều phối | `library/01-cfo-leadership` | 4 |
| FP&A – ngân sách & dự báo | `library/02-fpa-budget-forecast` | 9 |
| Ngân quỹ, dòng tiền & vốn vay | `library/03-treasury-cash-capital` | 8 |
| Kế toán, đóng sổ & kiểm soát | `library/04-accounting-close-controls` | 11 |
| Báo cáo HĐQT & nhà đầu tư | `library/05-board-investor-reporting` | 6 |
| Gọi vốn & thị trường vốn | `library/06-fundraising-capital-markets` | 8 |
| Lợi nhuận, chi phí & giá | `library/07-profitability-cost-pricing` | 10 |
| Chiến lược & hoạch định | `library/08-strategy-planning` | 16 |
| Phát triển DN & M&A | `library/09-corporate-development-ma` | 14 |
| Thị trường & đối thủ | `library/10-market-competitive-intel` | 6 |

Skill đã có sẵn trong tài khoản và được các skill lõi gọi tới (không nhập lại): `xlsx`, `pptx`, `docx`, `pdf`, `deep-research`, `alta-sales-report`, `am-im-skill`, plugin `financial-analysis` (DCF, LBO, comps, 3-statement), plugin `investment-banking` (CIM, teaser, merger model, buyer list).

## Lưu ý
- Skill trong `library/` giữ nguyên nội dung gốc (tiếng Anh, nhiều skill viết cho bối cảnh Mỹ/Ấn Độ/startup); chỉ đổi trường `name:` thêm tiền tố nguồn để tránh trùng tên. Skill lõi bổ sung bối cảnh Việt Nam.
- Các mức thuế, ngưỡng pháp lý trong `vn-finance-compliance` và `corp-dev-ma-vn` là điểm xuất phát để kiểm tra — luôn đối chiếu văn bản hiện hành.
- Script Python đi kèm một số skill chỉ dùng thư viện chuẩn; đã rà soát không có lệnh mạng/thực thi hệ thống.
