---
name: board-management-pack
description: Báo cáo quản trị tháng/quý và tài liệu họp HĐQT cho Alta Group — dashboard KPI, phân tích biến động so với kế hoạch và cùng kỳ, bình luận kết quả, rủi ro, và đề xuất quyết định. Dùng khi cần "báo cáo quản trị tháng", "báo cáo HĐQT", "board pack", "tình hình kinh doanh quý", "flash report", hoặc thư gửi cổ đông/nhà đầu tư.
---

# Báo cáo quản trị & HĐQT

## 1. Cấu trúc board pack (≤ 15 trang + phụ lục)
1. **Tóm tắt điều hành (1 trang)**: 3 con số chính, đánh giá chung (Xanh/Vàng/Đỏ), quyết định cần HĐQT, 3 rủi ro hàng đầu.
2. **Dashboard KPI** (1 trang): Doanh thu, Doanh thu ngoài tập đoàn, Lợi nhuận gộp & biên, EBITDA & biên, LNST, Dòng tiền hoạt động, Tiền & hạn mức khả dụng, Nợ vay ròng/EBITDA, DSO/DIO/DPO — mỗi KPI có Thực tế | Kế hoạch | Cùng kỳ | Δ% | xu hướng 6 kỳ.
3. **Kết quả hợp nhất**: KQKD (A vs B vs N−1), cầu nối EBITDA (EBITDA bridge: giá, sản lượng, cơ cấu, chi phí NVL, nhân sự, khác).
4. **Theo mảng**: Mẹ, Plastic, Media — mỗi mảng 1 trang: kết quả, động lực, khách hàng lớn, vấn đề & hành động.
5. **Dòng tiền & bảng cân đối**: dòng tiền 13 tuần (tóm tắt từ `cash-13-week-treasury`), vốn lưu động, nợ vay, covenant.
6. **Sáng kiến chiến lược & capex**: trạng thái danh mục sáng kiến (từ `strategy-dev-director`), giải ngân capex vs duyệt.
7. **Rủi ro & tuân thủ**: sổ đăng ký rủi ro (khả năng × tác động, chủ rủi ro, biện pháp), lịch thuế/kiểm toán (`vn-finance-compliance`).
8. **Dự báo cả năm** (rolling forecast) vs kế hoạch.
9. **Đề xuất nghị quyết** (văn bản cụ thể cần biểu quyết).
Phụ lục: BCTC từng công ty, đối chiếu nội bộ, chi tiết biến động.

## 2. Bình luận biến động (variance commentary)
- Ngưỡng giải trình: |Δ| > 10% **và** > 500 triệu VND (Khôi có thể điều chỉnh).
- Mỗi bình luận: *Cái gì* (số, %) → *Tại sao* (nguyên nhân gốc, tách giá/lượng/cơ cấu/thời điểm) → *Một lần hay lặp lại* → *Hành động* (ai, khi nào) → *Tác động dự báo cả năm*.
- Cấm bình luận kiểu "doanh thu giảm do doanh thu giảm"; cấm tính từ không định lượng.
- Dùng `an-variance-commentary` cho bảng biến động chi tiết.

## 3. Phong cách
- Action title mỗi trang (vd. "EBITDA 9T đạt 92% kế hoạch do biên Plastic giảm 2,1pt vì giá hạt nhựa").
- Biểu đồ: cột cho so sánh kỳ, waterfall cho bridge, đường cho xu hướng; 1 thông điệp/biểu đồ (skill `dataviz` nếu làm HTML).
- Định dạng: VND tỷ, 1 chữ số thập phân; số âm trong ngoặc; ghi kỳ & trạng thái số liệu (chưa kiểm toán).
- Gửi trước họp ≥ 5 ngày làm việc; kèm biên bản họp kỳ trước & bảng theo dõi việc HĐQT giao.

## 4. Công cụ tự tạo deck (`tools/board-pack/`)
Khi số liệu đã nạp vào `alta-finance-intelligence` (`afi ingest` → `afi reconcile` → CFO duyệt trong `data/approvals.yaml`), dựng deck bằng công cụ thay vì làm tay:
```bash
afi boardpack --month 2026-10 --plan data/plan_2026.csv            # tháng
afi boardpack --month 2026-09 --mode ytd --plan data/plan_2026.csv # lũy kế (quý)
python tools/board-pack/build_board_pack.py --sample               # deck mẫu (dữ liệu tổng hợp)
```
- Kế hoạch: CSV `company,month,line,amount` (VND; `line` theo `account_map.yaml` + `interest_expense`). Không có file → so với cùng kỳ.
- Deck có sẵn: tóm tắt điều hành, KPI, KQKD hợp nhất, giải trình biến động, cầu nối EBITDA, 1 trang/pháp nhân, tiền & vốn lưu động, rủi ro, đề xuất nghị quyết, phụ lục (mục 1 ở trên; mục 6 và 8 chưa có nguồn dữ liệu → ô `[CFO điền]`).
- Tự áp dụng mục 2–3: ngưỡng giải trình (`--threshold-pct`, `--threshold-amount`), action title, tỷ đồng 1 số lẻ, số âm trong ngoặc, trạng thái dữ liệu APPROVED/RECONCILED/SƠ BỘ trên từng trang, biểu đồ native, nguồn từng số (file + dòng Excel) trong speaker notes.
- **Việc của Claude/CFO sau khi sinh deck**: điền mọi ô `[CFO điền]` (hành động, người phụ trách, thời hạn, tác động cả năm; khả năng/tác động rủi ro; nội dung nghị quyết); "Tại sao" của công cụ chỉ là dữ kiện — nguyên nhân gốc (giá/lượng/thời điểm) phải xác minh với BU trước khi viết thêm. Không gửi HĐQT khi trang còn trạng thái SƠ BỘ mà không nêu rõ.
- Chi tiết, hạn chế: `tools/board-pack/README.md`.

## 5. Đầu ra & kỹ năng liên quan
- Deck (skill `pptx`) hoặc trang HTML; Excel dữ liệu đi kèm (skill `xlsx`).
- `ar-board-deck-builder`, `ar-board-meeting`, `w95-board-meeting-prep`, `cm-board-reporting`, `w95-kpi-dashboard`, `w95-executive-communication`; số liệu bán hàng từ `alta-sales-report`.
- Kiểm tra cuối: `financial-analysis:ib-check-deck` (số khớp giữa các trang).
