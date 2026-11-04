# ALTA GROUP — FAST ERP Data Architecture & Analytics Workflow

**Version:** 1.1 (revised from v1.0, same date)
**Date:** 2026-11-04
**Audience:** Claude Code / ALTA Strategy & Development, CFO, Finance, BU owners
**Purpose:** An auditable, extensible workflow from FAST exports to reconciled accounting data, a 13-week cash forecast and management dashboards, with every figure traceable to its source file and row.

---

## Tóm tắt thay đổi so với v1.0 (cho người duyệt)

| # | Thay đổi | Lý do |
|---|---|---|
| 1 | **Phạm vi pháp nhân sửa lại:** 3 pháp nhân Alta (Mẹ) / Alta Plastic / Alta Media với MST cụ thể. **In 3D là BU nằm trong pháp nhân Alta Plastic**, không phải pháp nhân riêng | v1.0 gộp "3D Printing" vào danh sách pháp nhân. Dữ liệu bán hàng 9T/2026 cho thấy 3D là một mảng doanh thu của Alta Plastic → phải tách `legal entity` và `business unit` |
| 2 | **Thêm 2 báo cáo đã quan sát thực tế** (`Bảng kê hóa đơn bán hàng, dịch vụ`, `Bảng kê mua hàng`) với bố cục đã biết, gắn `[ALTA OBSERVED]` | v1.0 không có. Đây là 2 báo cáo duy nhất đã được dùng thực tế (quy trình báo cáo bán hàng 9T/2026) |
| 3 | **Một nguồn sự thật cho phát sinh:** sổ NKC / sổ chi tiết tài khoản có mã đối tượng là *fact* duy nhất. Sổ quỹ, sổ tiền gửi, sổ chi tiết công nợ 131/331, sổ chi tiết doanh thu 511 là **báo cáo đối chiếu (control)**, không nạp thành fact riêng | v1.0 đã nêu nguyên tắc "report is a view" (§1) nhưng §2 lại xếp ~20 báo cáo P0, nhiều báo cáo là cùng một bút toán nhìn theo góc khác → nguy cơ cộng trùng và gánh nặng xuất file |
| 4 | **Thu hẹp P0 còn 6 báo cáo + 1 nguồn ngoài** (§2) | 20 báo cáo P0 × 3 công ty × 12 tháng là không khả thi cho Phase 0; mở rộng theo từng báo cáo khi có mẫu thật |
| 5 | **Công nghệ Phase 0–2: DuckDB + Parquet + Python** (không máy chủ), PostgreSQL từ Phase 6 khi IT duyệt | Không cần cài DB server, chạy trên laptop Finance, cùng SQL; chuyển sang PostgreSQL bằng cùng mô hình |
| 6 | **Ghi nhận prototype đã có:** `dashboard/` (HTML chạy trong trình duyệt, truy xuất tới file + dòng) là **công cụ khám phá Phase 0**, không phải dashboard production. Production đọc *gold data pack* do pipeline xuất, không đọc Excel thô | Tuân thủ §14 v1.0 "dashboards should not read raw Excel in production" mà vẫn dùng được ngay |
| 7 | **Chính sách đang dùng tạm được ghi rõ là `[PROPOSED POLICY]`** (EBITDA, lãi vay, loại trừ nội bộ, phân loại dòng tiền), có chỗ ký duyệt của CFO | v1.0 yêu cầu "documented policy" nhưng chưa có bản nháp để duyệt |
| 8 | **Thêm trạng thái dữ liệu hiển thị trên dashboard** (`PRELIMINARY` / `RECONCILIATION_FAILED` / `RECONCILED` / `APPROVED`) | Đưa state machine §15 vào giao diện |
| 9 | **Bỏ các tham chiếu không kiểm chứng được** trong môi trường thực thi (thư mục Drive, `SD_MEMORY`) khỏi phần "phải làm"; giữ ở phần quản trị | Claude Code chạy trên cloud không truy cập được Drive hay máy có FAST |
| 10 | **Thêm §22 "Hiện trạng triển khai"** và danh sách câu hỏi mở có người chịu trách nhiệm | Biến câu hỏi mở thành việc cần làm |

---

> **Read first — Status of evidence.** This is a **target architecture and implementation specification**, not a verified dictionary of ALTA's FAST export columns, except where tagged `[ALTA OBSERVED]`. Fields tagged `[PROPOSED SCHEMA]` are normalized targets; their presence in FAST must be tested with genuine files. Do not fabricate missing data or auto-map ambiguous fields.
>
> **Non-negotiable:** Read-only with respect to FAST. Never modify FAST records, original uploads, source files or sharing permissions. CFO/Finance validates accounting figures; BU owners validate operating drivers and future commitments; S&D owns analytics, challenge and management reporting.

## 0. Objective, scope and evidence hierarchy

### Business outcomes
1. Export FAST accounting records in an approved, repeatable way (manual export in Phase 0).
2. Store immutable copies with hash, period, entity, filter and provenance metadata.
3. Parse, standardize, reconcile and version multi-company data.
4. Produce P&L, balance sheet, accounting cash flow, AR/AP, inventory, cash/bank, revenue/customer/project economics and fixed assets.
5. Produce a 13-week **direct** cash forecast with real receipt/payment timing, Base/Downside scenarios, variance tracking, funding gaps and named owners.
6. Produce CEO, CFO, Media, Plastics and S&D/FP&A dashboards with drill-down to source file and row.
7. Support the 9M2026 review, Q4/FY2026 forecast and driver-based Budget 2027, keeping preliminary assumptions separate from approved amounts.

### Evidence tags (on every report, mapped field and dashboard figure)
- `[FAST DOCUMENTED]` — the report or function appears in FAST documentation. It does **not** confirm ALTA's export layout.
- `[ALTA OBSERVED]` — verified in an ALTA export: sample filename, sheet, header row and source are recorded.
- `[PROPOSED SCHEMA]` / `[PROPOSED POLICY]` — designed target or draft rule awaiting approval.
- `[ALTA VALIDATION REQUIRED]` — missing sample, uncertain function, unclear mapping or unapproved allocation.

### Legal entities and business units

| Legal entity (`dim_company`) | Tax code (MST) | Known BUs / revenue streams (`dim_business_unit`) | Evidence |
|---|---|---|---|
| Alta (Mẹ) — `ALTA` | 0301420079 | Rental of premises, technology equipment & projects, electricity recharge, intercompany lending, resale of bags | `[ALTA OBSERVED]` sales list 9M2026 |
| Alta Plastic — `APL` | 0312414944 | Plastic bags & packaging, trading of plastic resin, scrap, **3D printing products & services**, services, other goods | `[ALTA OBSERVED]` sales list 9M2026 |
| Alta Media — `AME` | 0305904835 | LED screen rental (job prefix `LED`), equipment & solutions (`BA`), multimedia system rental (`TTB`), services & revenue share (`DVK`), software & design (`TKL`) | `[ALTA OBSERVED]` job-code prefixes in sales list |

- A BU may span legal entities; a legal entity holds several BUs. Never infer BU from legal entity alone.
- The 3D BU sits inside Alta Plastic. Its costs need an approved attribution rule (`map_business_unit`). Do not allocate common costs to 3D by default; exclude foam bags where requested; verify item and asset assignment. `[ALTA VALIDATION REQUIRED]`
- Other related entities enter scope only when Finance confirms legal relevance.
- Intercompany = counterparty code whose first 10 digits equal another group MST. `[PROPOSED POLICY]`

### Working context (not audited source data)
- Media: judge project economics at job level. Never trust a project-profit report that shows cost = 0 without testing for missing cost records. No overhead allocation without approved cost drivers.
- Plastics: keep production data, inventory and GL separate. Do not infer capacity from factory area. CAPEX and funding in older planning files are drafts, not approvals.
- Priority order: 9M2026 actual review → FY2026/Q4 forecast → Budget 2027.

### Source of truth and file governance
- Official archive: ALTA Google Drive root folder (`00_BatDau_MucLuc`, `01_Review_Performance`, `02_ChienLuoc_5Nam_HDQT`, `03_Corporate_Development`, `04_DuAn_NhaMayMoi`, `90_Nguon_BaoCao_2025_KeHoach_2026`, `99_LuuTru_PhienBanCu`). Deliverables go in the matching folder with `YYYY-MM-DD` and version in the filename.
- **Landing folder for FAST exports** (new, proposed): `90_Nguon_BaoCao_2025_KeHoach_2026/FAST_Exports/<YYYY-MM>/` with one file per report × entity × period.
- Verify every upload by reading back its metadata; never claim success without it. Never move or overwrite originals.
- Drive is archive and collaboration storage. Neither Drive nor a cloud Claude session can reach the local FAST client; exports are produced by Finance.

---

## 1. Reference architecture

```text
FAST (approved, read-only manual exports)          External sources
  sổ NKC / sổ chi tiết TK, CĐPS, danh mục TK,        bank statements, contracts/backlog,
  bảng kê bán hàng, bảng kê mua hàng, danh mục ĐT    payroll, PO, CAPEX schedule, plan
                     │                                        │
                     └──────────────┬─────────────────────────┘
                                    ▼
             LANDING: Drive folder FAST_Exports/<YYYY-MM>/  (Finance uploads)
                                    ▼
             RAW / BRONZE: content-addressed copy (sha256) + manifest.jsonl
                                    ▼
             CLASSIFY: title + header fingerprint → report_id → parser (versioned)
                                    ▼
             STAGING / SILVER (Parquet): typed rows + provenance; totals kept as
             control objects; unparseable rows → quarantine (never dropped)
                                    ▼
             DATA QUALITY: control matrix (§15) → status per entity × period
                                    ▼
             GOLD (DuckDB views): fact_gl_lines, fact_tb, fact_sales_lines,
             dims, marts (P&L, BS, cash, AR, IC) + lineage keys
                                    ▼
             Gold data pack (JSON/Parquet) ──► CEO / CFO / BU / S&D dashboards
                                           └─► 13-week cash model (separate)
```

**One fact per economic event.** A FAST report is a *view* on postings, so reports are split into two roles:

| Role | Reports | Use |
|---|---|---|
| **Fact source** | Sổ nhật ký chung or Sổ chi tiết các tài khoản (journal line with account, contra account and counterparty code) | Every posting-based metric |
| **Fact source (document detail)** | Bảng kê hóa đơn bán hàng, Bảng kê mua hàng | Customer, item, job and salesperson detail that the GL lacks |
| **Balance source** | Bảng cân đối số phát sinh | Opening/closing balances per leaf account |
| **Control only** | Sổ quỹ, sổ tiền gửi, sổ chi tiết công nợ 131/331, sổ chi tiết doanh thu 511, BCTC B01/B02/B03 | Reconcile to the facts. Never add to them |

Never sum GL, sales ledger and financial statements together.

## 2. Report catalog and priority (revised)

### P0 — needed for Phase 1 (per entity, monthly)

| ID | FAST report | Role | Grain | Status |
|---|---|---|---|---|
| `GL_JOURNAL` | **Sổ nhật ký chung** (alternative: Sổ chi tiết các tài khoản, all accounts) — template that includes *Mã khách/Mã đối tượng* and *Vụ việc* | Fact | Journal line (account side) | `[FAST DOCUMENTED]` `[ALTA VALIDATION REQUIRED]` sample needed |
| `TB` | **Bảng cân đối số phát sinh các tài khoản**, lowest account level | Balance + control | Entity × period × account (parents included → leaf-only aggregation) | `[FAST DOCUMENTED]` `[ALTA VALIDATION REQUIRED]` |
| `COA` | Danh mục tài khoản | Dimension | Entity × account | `[ALTA VALIDATION REQUIRED]` |
| `SALES_LIST` | **Bảng kê hóa đơn bán hàng, dịch vụ** | Fact (document detail) | Invoice/voucher line | `[ALTA OBSERVED]` layout in §5.0 |
| `PURCH_LIST` | **Bảng kê mua hàng** (stock receipts) | Fact (document detail) | Receipt line | `[ALTA OBSERVED]` layout in §7.0; covers stock purchases only |
| `PARTY` | Danh mục khách hàng / nhà cung cấp (đối tượng) | Dimension | Entity × party code | `[ALTA VALIDATION REQUIRED]` |
| `BANK_STMT` | Bank statements (external) | Independent control, opening cash for 13W | Bank transaction / daily balance | `[ALTA VALIDATION REQUIRED]` |

### P1 — Phase 2–4

| ID | Report | Role |
|---|---|---|
| `AR_AGING` / `AP_AGING` | Báo cáo tuổi nợ / số dư công nợ theo hóa đơn, if FAST tracks invoice-level settlement | Fact for open items (otherwise derive with FIFO and label `DERIVED`) |
| `AR_LEDGER` / `AP_LEDGER` | Sổ chi tiết công nợ 131 / 331 | Control vs GL |
| `CASH_LEDGER` | Sổ quỹ tiền mặt, sổ tiền gửi ngân hàng | Control vs GL 111/112 and bank |
| `INV_BAL` | Báo cáo tổng hợp nhập – xuất – tồn (item × warehouse) | Fact for inventory |
| `FA_REG` | Sổ / thẻ TSCĐ, bảng tính khấu hao | Fact for assets, control vs 211/214 |
| `JOB` | Sổ chi tiết theo vụ việc / công trình | Control for Media job economics |
| `FS` | B01-DN, B02-DN, B03-DN | Statement control |
| External | Contracts/backlog, CAPEX schedule, loan schedules, payroll calendar, plan/budget | 13W forecast inputs |

### P2 — Phase 4+
Production orders, material issues for production, product costing / WIP (154, 621, 622, 627), BOM or standard cost (likely outside FAST), sales and purchase orders.

The catalog is a **request list**, not proof that each report exists or is populated in ALTA's FAST setup.

---

## 3. Data contract per source report

For every genuine sample, the pipeline generates (`afi dictionary <file>`) a physical dictionary:

```yaml
report_id: GL_JOURNAL
fast_display_name: "Sổ nhật ký chung"
status: ALTA_VALIDATION_REQUIRED      # → ALTA_OBSERVED after Finance confirms
sample_file: "NKC 2026-10 - Alta Plastic.xlsx"
source_file_hash: sha256:…
sheet_names: [...]
title_rows: ["…", "Từ ngày 01/10/2026 đến ngày 31/10/2026"]
header_row: 6
header_rows_merged: false
data_start_row: 7
period_from: 2026-10-01
period_to: 2026-10-31
company_detected: APL
raw_column_names: ["Ngày ct", "Số ct", "Diễn giải", "Tk", "Tk đ/ư", "Ps nợ", "Ps có", ...]
column_mapping: {posting_date: "Ngày ct", ...}   # canonical → raw
unmapped_columns: [...]
column_types: {...}
column_examples_redacted: {...}
grain_definition: "one row per journal line (account side)"
subtotal_row_patterns: ["Tổng cộng"]
control_totals: {debit: …, credit: …}
parsed_totals: {debit: …, credit: …}
quarantined_rows: 0
open_questions: [...]
approval_status: preliminary
```

Keep the exact Vietnamese labels and template quirks (merged headers, repeated headers, filter banners). Never rewrite raw originals. When a mapping is ambiguous, record a human question and block auto-approval.

**Provenance on every staging row:** `extraction_id` (= file sha256), `source_filename`, `source_sheet`, `source_row_number` (Excel 1-based), `report_id`, `company_id`, `report_period_start`, `report_period_end`, `parser_version`, `ingested_at`, `dq_status`.

---

## 4. General Ledger

### 4.1 Journal line — `[PROPOSED SCHEMA]`
```text
company_id, posting_date, document_number, document_type, description,
account_code, contra_account_code, debit_amount, credit_amount,
counterparty_code, counterparty_name, job_code, department_code,
currency, fx_rate, + provenance
```

**Grain decision.** Two layouts exist:
- *Journal line* (`Tk`, `Tk đ/ư`, `Ps nợ`, `Ps có`) — each row is one account side. This is the target layout.
- *Dr/Cr pair* (`Tk nợ`, `Tk có`, `Số tiền`) — each row is a pair. Split into two lines (one debit, one credit). **Never** rebuild pairs by joining debits and credits of a multi-line voucher (cartesian product).

The contra account (`Tk đ/ư`) on a multi-line voucher is the counterpart printed by FAST. Treat it as descriptive, not as a reliable pairing, until a sample shows how FAST fills it for 1-to-many vouchers. `[ALTA VALIDATION REQUIRED]`

### 4.2 Trial balance — `[PROPOSED SCHEMA]`
Grain: company × period × account, with `is_leaf` computed per file (no other account in the same file starts with this code).
```text
company_id, period_start, period_end, account_code, account_name, is_leaf,
opening_debit, opening_credit, period_debit, period_credit, closing_debit, closing_credit
```
Controls: Σ leaf opening Dr = Cr; Σ leaf movement Dr = Cr; Σ leaf closing Dr = Cr; opening + movement = closing per account; leaf movement = GL movement for the same period.

### 4.3 Chart of accounts
Reference families (111, 112, 131, 133, 136, 138, 141, 15x, 211, 214, 241, 242, 331, 333, 334, 335, 336, 338, 341, 411, 421, 511, 515, 521, 632, 635, 641, 642, 711, 811, 821, 911) follow the VAS regime. **TT 99/2025/TT-BTC replaces TT 200/2014 from fiscal year 2026**; confirm the regime and any account renumbering applied in ALTA's FAST before locking `account_map.yaml`. ALTA uses company-specific sub-accounts (for example `13111T`). Never hardcode the statutory chart as ALTA's chart.

---

## 5. Revenue and invoicing

### 5.0 Bảng kê hóa đơn bán hàng, dịch vụ — `[ALTA OBSERVED]`
Source: report used for the 9M2026 sales review (layout encoded in the `alta-sales-report` parser). Re-capture a sample to record hash and sheet name.
- Title in rows 1–5, including `Từ ngày dd/mm/yyyy đến ngày dd/mm/yyyy`. Header in **row 6**.
- Columns: `Ngày ct`, `Mã ct`, `Số ct`, `Mã khách`, `Tên khách`, `Tiền` (net of VAT), `Thuế`, `Chiết khấu`, `Phải thu`, `Diễn giải`, `Tài khoản`, `Nv bán hàng`, `Vụ việc`.
- Last row `Tổng cộng` = control total (not a transaction).
- `Mã khách` is usually the customer's MST (10 digits, optional `-xxx` branch suffix) → intercompany detection works on the first 10 digits.
- Negative `Tiền` = adjusting voucher. `Tiền` = 0 rows exist.
- Company-specific conventions: Alta Plastic `13111T` = goods issued without a VAT invoice yet (reversed when invoiced). Alta (Mẹ) `13111T` with VAT = 0 = rental without a VAT invoice. `[ALTA VALIDATION REQUIRED]` that these conventions still hold.
- Revenue streams: Alta Plastic and Alta (Mẹ) by keywords in `Diễn giải`; Alta Media by `Vụ việc` prefix after the 4-digit year. Keyword rules are a draft mapping (`map_business_unit`), reviewed each period when the "Other / unassigned" share rises.

### 5.1 Recognized revenue
Recognized revenue = GL 511 net of 521, excluding closing entries to 911. The sales list (billing) must bridge to GL 511 per entity × month. Differences are expected (interest booked to 511, rentals without invoices, adjustments, timing) and must be listed with evidence, not netted silently.

### 5.2 Invoice identity
An invoice number is not globally unique. Key = company + voucher type (`Mã ct`) + voucher number (`Số ct`) + date. Keep the invoice series when FAST exports it.

### 5.3 Contracts, backlog, milestones — external, `[PROPOSED SCHEMA]`
Contract value ≠ backlog ≠ recognized revenue ≠ cash. Plastics forecasts use volume (kg/tonne) × ASP once units are validated. Media tracks contracted backlog, unbilled milestones and project stage separately.

---

## 6. Accounts receivable

- **Movements** come from GL lines on 131* with counterparty code (fact). The 131 subledger report is a control.
- **Open items:** if FAST exports invoice-level outstanding/settlement (`AR_AGING`), use it as the fact. Otherwise derive open items by FIFO per customer (receipts settle the oldest invoices first) and label the result `DERIVED – FIFO`. The part of the 131 balance that comes from the opening balance without invoice detail is shown as *unaged*, never spread across buckets.
- Buckets (configurable): not due, 1–30, 31–60, 61–90, 91–180, >180 days past due. Without due dates, age from invoice date and say so.
- Customer advances (credit balances) are shown separately, not netted against receivables of other customers.
- Metrics: DSO (period method and invoice method), overdue %, collection lag weighted by amount, customer concentration (top 5 / top 10 share).

## 7. Accounts payable and procurement

### 7.0 Bảng kê mua hàng — `[ALTA OBSERVED]`
Header in row 6. Columns include `Ngày ct`, `Số ct`, `Mã ncc`, `Tên ncc`, `Mã hàng`, `Tên hàng`, `Số lượng`, `Giá`, `Tiền`, warehouse, closing `Tổng cộng` row. **It covers stock receipts only.** Services (electricity, rent, interest, fees) do not appear, so intercompany purchase-vs-sale differences on services are expected.

### 7.1 AP
Same pattern as AR: GL 331* lines are the fact, the 331 subledger is a control, open items come from FAST aging if available or FIFO otherwise. Expense recognition ≠ payment. Never double count open POs that are later invoiced.

---

## 8. Cash, bank and the 13-week forecast

### 8.1 Historical cash transactions (fact = GL lines on 111*/112*/113*)
Enriched by a **reviewable mapping engine** (`config/cash_flow_map.yaml`, versioned):

| Contra account | Preliminary category | Note |
|---|---|---|
| 131 | Customer collections | |
| 511, 3331 | Direct sales receipts | Must not duplicate 131-based collections |
| 331, 15x, 133, 6xx, 242 | Supplier and expense payments | Economic split (material/service/CAPEX) needs invoice/PO join |
| 334 | Payroll | |
| 338, 335 | Social insurance and other payables | |
| 333 | Taxes | |
| 211–217, 241 | CAPEX | |
| 121, 128, 22x | Investments and lending | |
| 515 | Interest and dividends received | |
| 711 | Disposal and other income | |
| 341, 311, 315, 343 | Borrowing drawdown / repayment | |
| 411, 421 | Capital and dividends | |
| 136, 336, and lines whose counterparty is a group MST | **Intercompany** | Eliminated in group view, kept per entity |
| 111 ↔ 112 ↔ 113 | **Internal transfer** | Excluded from external cash flow after matching |
| anything else | `UNCLASSIFIED` | Shown and counted until a reviewer classifies it |

Receipts minus payments is **never** labelled operating or free cash flow without this classification and transfer elimination.

### 8.2 Balances
Ledger cash = TB closing 111/112/113. **Available cash** = bank statement balance − restricted cash (deposits, escrow, LC margin). The 13W forecast starts from available cash on a verified date.

### 8.3 Thirteen-week direct forecast (separate model, separate versions)
```text
Beginning available cash (verified bank snapshot)
+ Customer collections           ← open AR items × expected date (owner, confidence)
+ Other operating receipts
− Supplier payments              ← open AP items + committed POs × payment date
− Payroll and social insurance   ← payroll calendar
− Opex payments
− Taxes                          ← tax calendar (VAT monthly/quarterly, CIT quarterly)
− CAPEX payments                 ← contract milestones, not asset additions
− Interest and principal         ← loan schedules
+ Financing drawdowns            ← approved facilities only
± Intercompany (entity view only)
= Ending available cash
− Minimum liquidity floor        ← CFO-approved
= Headroom
```
Rules: Base and Downside scenarios; every line has source, due date, expected date, amount, owner and confidence; unknowns are `DATA REQUIRED`. Historical averages may seed behaviour (collection lag per customer) but never become committed amounts. Show the last 13 weeks of actuals and the next 13 weeks of forecast separately, with weekly actual-vs-prior-forecast variance and a roll-forward. The group view eliminates matched intercompany flows while each entity's liquidity stays visible.

---

## 9–12. Inventory, manufacturing, fixed assets, projects

Unchanged in substance from v1.0 (schemas `[PROPOSED SCHEMA]`, Phase 4). Key rules kept:
- Inventory: reconcile `INV_BAL` closing value to GL 15x per entity and month; verify the valuation method and units; no capacity inferred from space or movements.
- Manufacturing: BOM, machine time, yield and capacity may live outside FAST, so do not invent them. Reconcile 154/621/622/627/632 with cost-flow logic. Plastics profit bridge (volume, ASP, mix, material cost, efficiency) only once units and periods are validated.
- Fixed assets: **CAPEX accounting ≠ CAPEX cash.** Reconcile the register to 211/214/241. Attribute assets to Plastics, Media or 3D asset by asset.
- Projects (Media): revenue by job code − identified direct cost = contribution. If direct cost cannot be traced (632/154/622/627 by job), flag `INCOMPLETE COST` and suppress the margin. Keep unallocated pools visible.

---

## 13. Financial statements and policies

Statement schemas as in v1.0. Draft policies for CFO approval (`docs/accounting_policies.md`):

| Policy | Draft rule `[PROPOSED POLICY]` | Approver |
|---|---|---|
| Closing entries | Exclude every GL line whose account or contra account starts with 911 from P&L facts | CFO |
| Net revenue | Credit − debit on 511 and 521 | CFO |
| Interest expense | 635 lines whose description contains "lãi vay / lãi tiền vay" or whose contra is 335/341/3388/311 | CFO (confirm sub-accounts) |
| EBITDA | Profit before tax + interest expense + depreciation charged to P&L = **credit − debit on 214 whose contra account is 6xx, 154 or 632** (not the net 214 movement; disposals, transfers and adjustments are shown separately). Months without journal detail show "Chưa đủ dữ liệu" | CFO (same rule for all three entities, or documented exceptions) |
| Consolidation (management) | Sum entities; eliminate intercompany revenue (511 lines with a group MST counterparty) against cost of sales; eliminate intercompany interest (515 vs 635). Unrealized profit in inventory not yet eliminated | CFO |
| Intercompany balances | Counterparty balances on 131/331/136/336/138/338/341/128 must offset pairwise; difference → exception list | Chief Accountant |
| Working-capital days | DSO = AR ÷ (3-month revenue × 1.1) × 91; DIO = inventory ÷ 3-month COGS × 91; DPO = AP ÷ (3-month COGS × 1.1) × 91 | CFO |
| Statutory consolidation | Out of scope for this system (VAS 25 / TT 202, audited) | — |

Master/dimension tables as in v1.0. Every key is scoped by company (account and party codes collide across companies). Use effective-dated mappings.

---

## 14. Storage and data model

| Phase | Store | Reason |
|---|---|---|
| 0–2 | **Raw:** content-addressed files `data/raw/<sha256>.<ext>` + `manifest.jsonl`. **Staging:** Parquet per report. **Gold:** DuckDB views | No server, runs on a Finance laptop, versionable, same SQL as PostgreSQL |
| 3–5 | Same + gold data pack (JSON/Parquet) published to dashboards | Dashboards stop reading Excel |
| 6 | PostgreSQL (or IT-approved warehouse) with the same tables | Multi-user, RBAC, scheduled jobs |

Facts: `fact_gl_lines`, `fact_tb`, `fact_sales_lines`, `fact_purchase_lines` (Phase 1); AR/AP open items, cash transactions (derived views), inventory, assets, projects (later). Planning facts stay separate: `plan_*`, `forecast_*` with `scenario_id` and `forecast_version_id`.

---

## 15. Parsing and reconciliation requirements

### Raw layer
Store untouched files with sha256, size, original name, uploader, ingest time and parser version. **Idempotent:** the same hash is never ingested twice. A corrected export for the same report × entity × period creates a **new extraction version** that supersedes the old one for those months. The old version is kept for audit and restatement history.

### Staging layer
- Identify the report by title and header fingerprint, not by filename. The filename may supply entity and period only when the content does not.
- Detect title/filter banners, merged two-row headers (`Số dư đầu kỳ` → `Nợ` / `Có`), repeated headers, blank rows, subtotals and grand totals.
- Totals (`Tổng cộng`, `Cộng`) become **control objects**, not transactions.
- Parse Vietnamese dates (dd/mm/yyyy, Excel serials) and number formats (`1.234.567`, `1,234,567`, `(1.000)`).
- Keep codes as text (leading zeros, suffixes such as `13111T`, `-001`).
- Rows that cannot be parsed go to **quarantine** with reason and row number. Nothing is silently dropped.
- `parser_registry` maps `report_id → parser + version`. Multiple template versions per report are supported.

### Control matrix (status per entity × period)

| Control | Test | Phase |
|---|---|---|
| File totals | Parsed totals = `Tổng cộng` row (debit, credit, amount, VAT) | 0 |
| GL balance | Σ debit = Σ credit per entity × period, and per voucher where the voucher id is reliable | 0 |
| TB integrity | Σ leaf Dr = Cr (opening, movement, closing); opening + movement = closing per account | 0 |
| TB ↔ GL | Leaf movement = GL movement per account and period | 0 |
| Revenue bridge | GL 511 net vs sales list `Tiền`, with listed reconciling items | 0 |
| Intercompany | Pairwise counterparty balances offset | 1 |
| AR / AP | GL 131/331 vs subledger and open items at cutoff | 2 |
| Cash / bank | GL 111/112 vs cash and bank ledgers vs bank statements | 2–3 |
| Inventory, FA, WIP, projects | As in v1.0 | 4 |

Tolerance: 0 VND for file totals and TB integrity; ≤ 1,000 VND rounding elsewhere unless the CFO approves otherwise. Unexplained differences keep the period at `RECONCILIATION_FAILED`.

### State machine (shown on every dashboard)
`RAW → PARSED → VALIDATED → RECONCILED → APPROVED`, or `QUARANTINED / REJECTED`. `APPROVED` requires a named CFO/Chief Accountant and timestamp in `approvals.yaml`. Dashboards show refresh time, period, entity, status and open exceptions next to the figures.

---

## 16. Dashboards

Content as in v1.0 (CEO, CFO, Media, Plastics, S&D/FP&A). Navigation standard: group → entity/BU → account/customer/job/product → voucher → **source file and Excel row**.

The Phase 0 prototype (`dashboard/Alta_CFO_CEO_Dashboard.html`) already provides CEO, CFO, Sales and Data/Reconciliation pages with drill-down to file and row. Its role:
- **Phase 0–1:** an exploration and validation tool for Finance. It runs locally in the browser and sends no data anywhere.
- **Phase 2+:** reads the gold data pack produced by the pipeline (one set of definitions), not raw Excel.
- Media job economics and Plastics manufacturing pages are added only after Phase 4 data passes controls.

---

## 17. Extraction and automation

**Phase 0:** manual approved Excel exports by Finance to the landing folder, following `docs/fast_export_checklist.md` (report, template, period, filters, filename). No FAST API, direct SQL or remote browser access is assumed.

Future options, evaluated separately: scheduled manual exports; authorized browser automation (no hard-coded credentials, no bypassing access control); vendor-supported read-only API (preferred if officially available and licensed).

**Security:** least privilege; secrets in environment or a secret manager, never in git; encrypted storage; masked customer/vendor identifiers in test fixtures (all fixtures in this repo are synthetic); private dashboards; no external deployment without IT/security approval. **Uploading transaction-level data to an AI service requires ALTA authorization.** Aggregated, anonymized outputs are preferred for AI-assisted analysis.

---

## 18. Twelve non-functional requirements
Unchanged from v1.0: source preservation, idempotent ingestion, incremental and full refresh, historical restatement, multi-company keys, lineage, reconciliation ≠ parsing success, transparent BU mapping, actual/budget/forecast isolation, role-based access, exception visibility, no unsupported allocation.

---

## 19. Roadmap (revised)

| Phase | Scope | Output | Gate | Status (2026-11-04) |
|---|---|---|---|---|
| 0 | Genuine samples, layout fingerprints, dictionaries, raw manifest, registry, first parsers and controls | `alta-finance-intelligence/` Phase 0 code + tests; dashboard prototype | Finance confirms layout and grain for each sample | **Code done on synthetic fixtures; waiting for real samples** |
| 1 | GL, TB, sales list, purchase list, COA, parties for 3 entities × Jan 2025 → latest month | Staging + gold MVP; DQ report per entity × month | All P0 controls pass or documented | Not started |
| 2 | Management P&L, BS, cash (historical), working capital, intercompany; gold data pack → dashboard | CEO/CFO dashboards on gold data | CFO reconciles statements and signs policies (§13) | Prototype only |
| 3 | 13W cash: bank snapshot, open AR/AP, commitments, loan schedules, scenarios | 13W Base/Downside + variance | CFO approves opening cash, floor and assumptions | **Model built (`afi cash13w`, `tools/cash-13w/`) on synthetic data; waiting for bank snapshots, open AR/AP, loan schedules** |
| 4 | Inventory, costing, Media jobs, fixed assets | BU economics | BU owners + CFO confirm mapping | Not started |
| 5 | FY2026 forecast, Budget 2027 drivers and scenarios | Planning model | CEO decision log | Not started |
| 6 | Automation, PostgreSQL, monitoring, deployment | Production system | IT/security review | Not started |

### Repository layout (implemented in this repo)
```text
finance-skill/
  docs/                                   # this spec, policies, export checklist
  dashboard/                              # browser prototype (Phase 0 tool)
  alta-finance-intelligence/
    README.md, pyproject.toml
    config/report_registry.yaml, entity_map.yaml, account_map.yaml, cash_flow_map.yaml
    src/afi/ingestion/   manifest + content-addressed raw store
    src/afi/parsers/     base (header/total/quarantine) + gl_journal, trial_balance, sales_list
    src/afi/reconciliations/  control matrix → dq status
    src/afi/models/      DuckDB gold views + lineage queries
    src/afi/dictionary.py   physical data dictionary generator
    src/afi/cli.py          afi ingest | dictionary | reconcile | pl | status
    tests/               synthetic fixtures: multi-line journal, merged-header TB, sales list
    data/                (gitignored) raw/, staging/, warehouse.duckdb
```

### Acceptance criteria
Phase 0, 1 and 3 criteria are unchanged from v1.0. Phase 0 additionally requires: one dictionary per genuine sample signed off by Finance, and `pytest` green.

---

## 20. Instructions to Claude Code

> You are the lead data engineer and financial analytics architect for ALTA Group's read-only FAST reporting pipeline. Treat this specification as the target design. Only `[ALTA OBSERVED]` items are verified. Inspect real samples and the existing code (`alta-finance-intelligence/`, `dashboard/`) before changing parsers. Preserve originals. Never guess mappings. Never mark unreconciled figures as approved.

**Next run, once Finance provides samples:**
1. Put samples in `alta-finance-intelligence/data/inbox/` and run `afi dictionary` on each. Compare raw headers with `config/report_registry.yaml`. Add aliases or new template versions. Never rename source columns in the file.
2. Run `afi ingest` and then `afi reconcile`. Every failing control becomes an exception with file and row references.
3. Record the open questions below as action items with an owner. Do not fill gaps with invented data.
4. Extend report by report (P1 list), each with a fixture, parser test and control.

### Open questions (owner → due)

| # | Question | Owner |
|---|---|---|
| 1 | FAST product and version (Business Online or on-premise Business), modules enabled, XLS or XLSX export | Chief Accountant |
| 2 | Which journal report and template include *Mã đối tượng* and *Vụ việc* on every line | Chief Accountant |
| 3 | Chart of accounts after TT 99 transition; sub-accounts for interest (635x), 13111T usage | Chief Accountant |
| 4 | Ownership % of Alta (Mẹ) in Plastic and Media; any other related entities in scope | CFO |
| 5 | BU mapping rules for 3D (items, assets, people) inside Alta Plastic | Plastics BU owner + S&D |
| 6 | Does FAST track invoice-level AR/AP settlement (aging by invoice) or only balances by party? | Chief Accountant |
| 7 | Bank accounts list, restricted cash, statement access for opening cash | CFO |
| 8 | Loan schedules, covenants, minimum liquidity floor | CFO |
| 9 | Sales/purchase orders, BOM, production orders, timesheets: in FAST or external? | BU owners |
| 10 | Approved tolerances, roles, retention, dashboard hosting environment, AI data-sharing policy | CFO + IT |

---

## 21. References
- FAST Business Online help: https://fbohelp.fast.com.vn/ · FAST online help: https://help.faonline.vn/ (verify version applicability).
- Circular 99/2025/TT-BTC (accounting regime replacing TT 200 from FY2026); Circular 202/2014/TT-BTC and VAS 25 (consolidation); Decree 132/2020/ND-CP as amended (related-party transactions, 30% EBITDA interest cap). Verify current versions.
- `SD_MEMORY_2026-10-29_v1.md` is working context, not an audited source. Never ingest figures from it as actuals.

## 22. Current implementation state (2026-11-04)

| Item | Where | State |
|---|---|---|
| Browser dashboard prototype (CEO, CFO, Sales, Data & reconciliation, drill-down to file + row, DQ status badge) | `dashboard/` | Working on synthetic data and synthetic FAST-style files |
| Raw manifest, content-addressed store, idempotent re-ingest | `alta-finance-intelligence/src/afi/ingestion` | Implemented + tested |
| Report classifier and registry | `config/report_registry.yaml`, `parsers/base.py` | Implemented for GL_JOURNAL, TB, SALES_LIST |
| Parsers with quarantine and control totals | `parsers/` | Implemented + tested (multi-line journal, Dr/Cr pair layout, merged-header TB) |
| Physical data dictionary generator | `dictionary.py` | Implemented |
| Control matrix → status per entity × period | `reconciliations/controls.py` | File totals, GL balance, TB integrity, TB↔GL, revenue bridge |
| Gold views + lineage query | `models/warehouse.py` | P&L lines by entity × month with source rows |
| 13-week cash (Phase 3): inputs → DATA REQUIRED, Base/Downside, actuals from GL, versions + variance, Excel/JSON, viewer | `forecasts/cash13w*.py`, `tools/cash-13w/` | Implemented + tested on synthetic data |
| Genuine ALTA samples | — | **Missing: blocks Phase 0 sign-off** |

**End of implementation brief.**

### Addendum 2026-11-04 — AR/AP by invoice, fixed assets, inventory
Additional source reports and columns: `docs/fast_export_requirements_v2.md`. Dashboard pages Công nợ, TSCĐ, Tồn kho implemented with drill-down to file/sheet/row; ageing uses only FAST due dates; slow-moving inventory requires ≥ 3 consecutive monthly NXT files. Pipeline `account_map.yaml` v2026-11-04.2 applies the new depreciation rule (test: `test_depreciation_uses_expense_contra_only`). Parsers for these four reports exist in the dashboard only; pipeline parsers are Phase 1–4 work.
