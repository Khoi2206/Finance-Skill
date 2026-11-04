# alta-finance-intelligence — FAST read-only pipeline (Phase 0)

Implements the "First run" of `docs/ALTA_FAST_Data_Architecture_2026-11-04_v1.1.md`:
raw manifest → report registry → parsers with quarantine → control matrix → gold views with lineage.
All test data is **synthetic**; no ALTA sample has been processed yet.

## Install
```bash
pip install -e ".[dev]"
```

## Use
```bash
afi dictionary data/inbox/*.xlsx          # physical data dictionary per sample → docs/data_contracts/
afi ingest data/inbox/*.xlsx              # raw copy (sha256, idempotent) + parse to data/staging/
afi reconcile                             # controls → data/dq/dq_report.md, status per company × month
afi pl --company APL --month 2026-10 --lineage net_revenue
afi export-pl --year 2026 --out actuals_2026.csv   # CSV company,month,line,amount (đồng) → tools/budget-model
afi boardpack --month 2026-10 [--mode ytd] [--plan plan.csv]  # board pack PPTX (tools/board-pack)
afi status                                # manifest (all extractions, incl. superseded/quarantined)
afi cash13w --inputs data/cash13w/2026-11-09 --start 2026-11-09   # 13-week cash forecast (mỗi thứ Hai)
```
CFO approval of a reconciled month: add it to `data/approvals.yaml`:
```yaml
approvals:
  - {company_id: APL, month: "2026-10", by: "Tên CFO", at: "2026-11-05"}
```

## Dòng tiền 13 tuần — `afi cash13w` (Phase 3, spec §8.3)

Chạy mỗi thứ Hai, sau khi đã `afi ingest` sổ nhật ký chung tới hết tuần trước:
```bash
afi cash13w --templates data/cash13w/2026-11-09          # lần đầu: tạo file CSV trống + params.yaml
# kế toán điền CSV (UTF-8, có dòng tiêu đề), CFO duyệt params.yaml
afi cash13w --inputs data/cash13w/2026-11-09 --start 2026-11-09
```
Kết quả: `data/forecasts/cash13w/out/CF13W-<ngày>-<giờ>-<hash>.xlsx` và `.json`; mỗi lần chạy lưu một **phiên bản bất biến** trong `data/forecasts/cash13w/` (thêm `--no-save` để chạy thử). Lần chạy sau tự so với phiên bản gần nhất có ngày bắt đầu sớm hơn. Mở JSON bằng `tools/cash-13w/cash13w.html` (kéo thả, xử lý trong trình duyệt).

Dữ liệu mẫu để thử: `afi cash13w --start 2026-11-02 --write-sample /tmp/s` → ingest `/tmp/s/gl/*.xlsx` → chạy `inputs_2026-10-26` (start 2026-10-26) rồi `inputs_2026-11-02`. **Toàn bộ là số tổng hợp, không phải số Alta.**

### Mẫu đầu vào (thư mục `--inputs`)
Ngày: `YYYY-MM-DD` hoặc `dd/mm/yyyy`. Số tiền: VND, dương (hướng thu/chi do loại file quyết định). `confidence`: `Cao` / `Trung bình` / `Thấp`. `company`: mã trong `config/entity_map.yaml` (ALTA, APL, AME). `counterparty_company` điền khi là giao dịch nội bộ → dòng Nội bộ, giữ ở pháp nhân, loại ở hợp nhất.

| File | Cột | Ghi chú |
|---|---|---|
| `bank_balances.csv` | company, bank, bank_account, date, balance, restricted, verified_by, source | Tiền đầu kỳ = Σ(balance − restricted) của dòng **có verified_by** và ngày trước ngày bắt đầu. Dòng chưa xác minh bị loại → DATA REQUIRED |
| `ar_open.csv` | company, customer, invoice, invoice_date, due_date, outstanding, expected_date, confidence, owner, counterparty_company | Thu từ khách hàng theo từng hóa đơn |
| `ap_open.csv` | company, supplier, invoice, invoice_date, due_date, outstanding, expected_date, confidence, owner, counterparty_company | Trả NCC (kể cả PO đã cam kết nếu có hóa đơn) |
| `debt_schedule.csv` | company, lender, facility, flow, due_date, expected_date, amount, confidence, owner, approved | flow = PRINCIPAL / INTEREST / DRAWDOWN; giải ngân chỉ tính khi `approved` = Y |
| `facilities.csv` | company, lender, facility, limit, drawn, expiry_date, committed | Hạn mức cam kết chưa dùng (tới ngày hết hạn) → thanh khoản khả dụng |
| `payroll.csv`, `taxes.csv`, `capex.csv` | company, item, reference, due_date, expected_date, amount, confidence, owner | Capex theo **mốc thanh toán hợp đồng**, không theo ghi tăng tài sản |
| `other.csv` | company, item, reference, direction (thu/chi), due_date, expected_date, amount, confidence, owner, counterparty_company | Thu/chi khác, hợp đồng đã ký chưa xuất HĐ, PO đã đặt |
| `params.yaml` | ngưỡng tối thiểu theo công ty + người duyệt, kịch bản Base/Downside, ngưỡng giải thích chênh lệch | `[PROPOSED POLICY]` — CFO duyệt |

### Quy tắc
- **DATA REQUIRED** có 3 mức: *Loại khỏi dự báo* (thiếu số tiền, thiếu cả hai ngày, công ty lạ, ngày thu dự kiến đã qua, số dư chưa xác minh, giải ngân chưa duyệt, thiếu cả file lương/thuế/AR/AP của một công ty); *Đã tính, thiếu thông tin* (thiếu người phụ trách, mức tin cậy → xếp Thấp, thiếu ngày dự kiến → dùng ngày đến hạn; với AR = hạn + độ trễ lịch sử `collection_lag_days`, đánh dấu "ước từ lịch sử", không bao giờ là cam kết, mức tin cậy tối đa Trung bình); *Thông tin* (tuần dưới ngưỡng, tham số bị hiệu chỉnh).
- **Base**: thu × `receipt_factor` theo mức tin cậy (mặc định Cao 1 · TB 1 · Thấp 0,5), giải ngân × `drawdown_factor`. **Downside**: hệ số thấp hơn, khách lớn nhất (top N theo dư nợ hoặc danh sách) thu chậm thêm X ngày, mọi khoản thu chậm Y ngày, chi sớm Z ngày. Tham số Downside bị kẹp để Downside ≤ Base ở mọi tuần.
- **Thực tế 13 tuần**: dòng TK 111/112/113 trong `fact_gl_lines`, phân loại theo `config/cash_flow_map.yaml` (thêm `INTEREST_PAID` = 635); chuyển giữa các TK tiền bị loại; đối tượng có MST thuộc nhóm → Nội bộ. Tuần chưa có sổ hiện "chưa có sổ", không phải 0.
- **So sánh**: đầu kỳ đã xác minh vs tiền cuối tuần đã qua theo dự báo trước; thực tế vs dự báo theo dòng (cần giải thích khi |chênh| > 10% và ≥ 50 triệu, chỉnh trong params); roll-forward tiền cuối tuần.
- **Excel**: `Tom_tat`, `Tien_dau_ky`, `Chi_tiet` (ô xanh = nhập), `Base_<Cty>`/`Down_<Cty>`/`*_HopNhat` (cầu nối bằng công thức SUMIFS từ `Chi_tiet`, có dòng kiểm tra = 0), `Thuc_te_13T`, `Thuc_te_dong` (truy xuất file + dòng Excel), `So_sanh`, `DATA_REQUIRED`, `Tham_so`.

## Layout
| Path | Role |
|---|---|
| `config/report_registry.yaml` | Report fingerprints (title + header), canonical ↔ raw column aliases, evidence status |
| `config/entity_map.yaml` | Legal entities (MST) and business units (3D inside Alta Plastic) |
| `config/account_map.yaml`, `config/cash_flow_map.yaml` | `[PROPOSED POLICY]` P&L and cash-flow mapping, versioned |
| `src/afi/ingestion/store.py` | Content-addressed raw store, append-only `manifest.jsonl`, supersede by sequence |
| `src/afi/parsers/` | `base` (header/merged header/totals/period/company), `gl_journal`, `trial_balance`, `sales_list` |
| `src/afi/reconciliations/controls.py` | FILE_TOTALS, GL_DR_EQ_CR, GL_VOUCHER_BALANCE (warn), TB_DR_EQ_CR, TB_ROLLFORWARD, TB_EQ_GL_MOVEMENT, REVENUE_BRIDGE |
| `src/afi/models/warehouse.py` | DuckDB: `effective`, `fact_gl_lines`, `fact_tb`, `fact_sales_lines`, `pl_lines_lineage`, `mart_pl_monthly` |
| `src/afi/forecasts/cash13w.py` | 13-week direct cash model: inputs → items with DATA REQUIRED, Base/Downside, actuals from GL, versions + comparison |
| `src/afi/forecasts/cash13w_excel.py`, `cash13w_sample.py` | Excel with live bridge formulas; synthetic sample generator |
| `src/afi/models/warehouse.py` | DuckDB: `effective`, `fact_gl_lines`, `fact_tb`, `fact_sales_lines`, `pl_lines_lineage` (with account, counterparty, description), `mart_pl_monthly` |
| `src/afi/dictionary.py` | Data contract YAML (spec §3) with redacted examples and open questions |
| `tests/` | Synthetic fixtures: multi-line voucher, Dr/Cr pair layout, merged-header TB, observed sales list layout; `group_dataset()` = 3 entities × 22 months (GL, TB, sales list) used by tools/board-pack |

## Not yet built (by phase)
Purchase list parser, COA/party masters (Phase 1) · intercompany control in pipeline, gold data pack for the dashboard (Phase 2) · 13-week cash: real bank snapshots, open AR/AP exports from FAST (Phase 3 — model built, waiting for data) · inventory, FA, jobs (Phase 4).
