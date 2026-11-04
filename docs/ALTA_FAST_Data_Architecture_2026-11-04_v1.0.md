# ALTA GROUP — FAST ERP Data Architecture & Analytics Workflow

**Version:** 1.0  
**Date:** 2026-11-04  
**Audience:** Claude Code / ALTA Strategy & Development, CFO, Finance, BU owners  
**Purpose:** Build an auditable, extensible workflow from FAST Business Online exports to a financial data warehouse, reconciled accounting models, 13-week cash forecast, and management dashboards.

> **Read first — Status of evidence.** This is a **target architecture and implementation specification**, NOT a verified dictionary of the actual FAST Excel export columns at ALTA. The field lists marked `[PROPOSED SCHEMA]` are normalized target schemas; their presence in FAST must be tested with genuine files. The FAST report families described below are based on public FAST help/documentation and earlier working discussions. They do not prove ALTA has enabled each module or that exports use these exact column names. Do not fabricate missing data or map ambiguous fields automatically.
>
> **Non-negotiable:** Do not modify FAST source records, original uploads, source files, or sharing permissions. The system is read-only with respect to FAST. CFO/Finance validates accounting figures; BU owners validate operating drivers and future commitments; S&D owns analytics/challenge/management reporting.

## 0. Objective, scope and evidence hierarchy

### Business outcomes
1. Extract/export FAST accounting and operating records in an approved way.
2. Store immutable copies with full extraction/filter/provenance metadata.
3. Parse, standardize, reconcile, and version multi-company data.
4. Produce P&L, Balance Sheet, accounting Cash Flow, AR/AP, inventory, cash/bank, revenue/customer/product/project economics, and fixed assets.
5. Produce 13-week **direct** cash forecast with true receipts/payments timing, Base/Downside scenarios, variance tracking, funding gaps, and accountable owners.
6. Produce CEO, CFO, Media, Plastics, and Strategy/FP&A dashboards with drill-down to source.
7. Support 9M2026 review, Q4/FY2026 forecast, and driver-based Budget 2027 without confusing preliminary assumptions with approved amounts.

### Evidence tags to put on every report and mapped field
- `[FAST DOCUMENTED]`: a report/business function appears in FAST documentation; **not** confirmation of ALTA's export layout.
- `[ALTA OBSERVED]`: directly verified in ALTA export, with sample filename, sheet, row and source metadata.
- `[PROPOSED SCHEMA]`: canonical field/table designed for the target data warehouse.
- `[ALTA VALIDATION REQUIRED]`: missing sample, uncertain functionality, unclear mapping, or unapproved allocation.

### Relevant existing working context (not audited source data)
- ALTA Group scope includes Alta Plastics, Alta Media and 3D Printing, plus related entities where legally relevant. Legal-entity boundaries, BU attribution and intercompany transactions require explicit master mappings.
- Media: project/job-level economics, AR/AP and cash. Never trust a project-profit report showing cost = 0 without testing missing cost records. No overhead allocation without approved cost drivers.
- Plastics: distinguish manufacturing production data, inventory and GL; do not infer capacity from factory area. CAPEX/funding in older planning files are drafts, not approved.
- 3D: do not allocate common costs by default, follow latest defined scope; exclude foam bags where requested, verify items and asset assignments.
- The current priority is 9M2026 actual review → FY2026/Q4 forecast → Budget 2027.

### Source of truth / Drive governance
Official root: `https://drive.google.com/drive/folders/1onBMQTdxJfrb8pVlrLXp3IjkbBK9D21z`  
Existing folders: `00_BatDau_MucLuc`, `01_Review_Performance`, `02_ChienLuoc_5Nam_HDQT`, `03_Corporate_Development`, `04_DuAn_NhaMayMoi`, `90_Nguon_BaoCao_2025_KeHoach_2026`, `99_LuuTru_PhienBanCu`.

Deliverables belong in the appropriate existing folder with `YYYY-MM-DD` and version in filename. Verify upload metadata/content; do not claim success without it. Do not move/overwrite originals. Google Drive is archival/collaboration storage; do not assume it can access local FAST or the local computer.

---

## 1. Reference architecture

```text
FAST Business Online (approved, read-only exports / supported integration)
        + external BU files (contract/backlog, payroll, PO, bank statements)
                            |
                            v
                 Extraction + file manifest
                            |
                            v
           RAW / BRONZE: immutable original files
                            |
                            v
       STAGING / SILVER: versioned report-specific parsers
       normalized units, types, codes, grain and mapping
                            |
                            v
      DATA QUALITY: reconciliations, exceptions, approvals
                            |
                            v
         GOLD: dimensional facts, accounting mart,
              operating marts, forecast marts
                            |
                            v
     CEO / CFO / Media / Plastics / S&D dashboards
                  + 13-week cash forecast
```

**Important distinction:** A FAST report is a *view* on underlying postings, not necessarily an independent transaction dataset. Do not ingest GL, sales ledger and financial statements as additive facts and sum them together. Design each report's grain, use some as sources and others as reconciliation controls.

## 2. Report catalog and priority

| Module | Source report / export family | Purpose | Priority | Expected grain / caveat |
|---|---|---|---|---|
| GL | General Journal (Nhật ký chung) | Journal/postings | P0 | Journal line or Dr/Cr pair; sample required |
| GL | Sổ chi tiết tài khoản | Account transaction detail | P0 | Account-movement row; avoid parent/child summation |
| GL | Bảng cân đối số phát sinh | GL reconciliation | P0 | Company × period × account |
| GL | Danh mục tài khoản | COA & hierarchy | P0 | Company × account (effective-dated) |
| Sales | Sổ chi tiết doanh thu / TK511 | Recognized revenue | P0 | GL posting; may differ from sales invoices |
| Sales | Sổ chi tiết bán hàng | Sold products/services | P0 | Invoice/item line or report summary |
| Sales | Sales invoice detail | Billing and product/customer sales | P0 | Invoice header + lines |
| Sales | Sales orders, contracts, backlog | Future invoicing | P1 | Order/milestone; may exist outside FAST |
| AR | Sổ chi tiết công nợ phải thu / TK131 | AR movements | P0 | Movement by customer/document |
| AR | AR Aging / đối chiếu công nợ | Outstanding and overdue | P0 | As-of snapshot/invoice if available |
| AR | Thu tiền theo hóa đơn / allocations | Actual settlement | P0 | Receipt × invoice allocation |
| AP | Sổ chi tiết công nợ phải trả / TK331 | AP movements | P0 | Movement by supplier/document |
| AP | AP Aging | Outstanding obligations | P0 | As-of snapshot/invoice |
| AP | Purchase invoice detail | Purchase classification | P0 | Invoice lines |
| Procurement | Purchase orders / open commitments | Future purchase cash obligations | P1 | PO line; verify usage |
| Cash | Sổ nhật ký thu tiền | Historical cash receipts | P0 | Cash movement/document line |
| Cash | Sổ nhật ký chi tiền | Historical cash payments | P0 | Cash movement/document line |
| Cash | Sổ quỹ tiền mặt / Sổ tiền gửi ngân hàng | Cash transactions/balances | P0 | Account movement or daily closing |
| Cash | Bank statements (external) | Verify balance/settlement | P0 | Bank transaction |
| Inventory | Báo cáo nhập xuất tồn | Period inventory balances | P0 | Item × warehouse × period |
| Inventory | Sổ chi tiết vật tư / thẻ kho | Stock movements | P0 | Item/document/warehouse movement |
| Inventory | Danh mục vật tư, kho | Dimensions | P0 | Item / warehouse |
| Manufacturing | Production orders | Orders/output | P1 | Order/item |
| Manufacturing | Xuất NVL cho sản xuất | Material consumption | P1 | Issue line × order |
| Costing | Giá thành sản phẩm, WIP, cost pool | Manufacturing cost | P1 | Cost object × period |
| Manufacturing | BOM / standard cost | Price/usage/yield drivers | P1 | BOM line/effective date, if available |
| Fixed assets | Asset register / thẻ TSCĐ | Asset balances | P1 | Asset |
| Fixed assets | Tăng giảm TSCĐ; depreciation | Capex/depreciation controls | P1 | Asset × event/month |
| CAPEX | TK241 details | Construction in progress | P1 | Posting/project |
| Projects | Sổ theo công trình / vụ việc | Job revenue & cost | P1 | Project × posting or cost bucket |
| Finance | P&L, Balance Sheet, Cash Flow statement | Financial statement control | P0 | Company × period × line |
| Master data | Customer, supplier, staff, departments, jobs | Join dimensions | P0 | Company × code/effective dates |

The above is a **requested extraction inventory**, not a guarantee each report exists or is populated in ALTA's configured FAST instance.

---

## 3. Data contracts for every source report

For each real export, Claude Code must generate a physical data dictionary containing:

```yaml
report_id: GL_DETAIL
fast_display_name: "Sổ chi tiết tài khoản"
module: GL
status: ALTA_VALIDATION_REQUIRED
sample_file: null
file_format: xlsx
sheet_names: []
header_row: null
data_start_row: null
period_from: null
period_to: null
company_filter: null
all_export_filters: {}
raw_column_names: []
column_types: {}
column_examples_redacted: {}
grain_definition: null
candidate_keys: []
subtotal_row_patterns: []
footer_row_patterns: []
opening_closing_balance_rows: []
possible_duplicates: []
target_tables: []
transformation_rules: []
reconciliation_targets: []
known_exceptions: []
owner: Finance
approval_status: preliminary
```

Include the raw exact Vietnamese column labels and preserve the report template's peculiarities (merged cells, repeated headers, hidden rows, multiple sheets, filter banners). Do not rewrite raw originals. If ambiguous, capture a human mapping question and block auto-approval.

**Standard required provenance on all staging transactions:** `extraction_id`, `source_file_hash`, `source_filename`, `source_sheet`, `source_row_number`, `report_id`, `company_id`, `report_period_start`, `report_period_end`, `source_filters_json`, `parser_version`, `ingested_at`, `data_quality_status`.

---

## 4. General Ledger / Accounting

### 4.1 General Journal — `[PROPOSED SCHEMA]`

```text
company_id, posting_date, document_date, document_number,
document_type, journal_entry_id, line_number, account_code,
debit_account, credit_account, debit_amount, credit_amount,
currency, exchange_rate, description, counterparty_id,
department_id, project_id, source_document_id
```

**Critical grain decision:** Some extracts are **journal lines** (`account_code`, `debit_amount`, `credit_amount`), some show **Dr/Cr pairs** (`debit_account`, `credit_account`, `amount`). Do NOT reconstruct pairs by cartesian joining multiple debits and credits in a multi-line journal. Require sample-based mapping and balanced voucher controls.

### 4.2 Sổ chi tiết tài khoản / GL detail — `[PROPOSED SCHEMA]`

```text
company_id, account_code, account_name, posting_date,
document_date, document_number, document_type, description,
debit_amount, credit_amount, running_balance,
counterparty_code, department_code, project_code, currency
```

`running_balance` depends on filter, opening date and ordering; do not treat it as a movement. Preserve account hierarchy. The relevant reference account families may include `111,112,131,152,154,155,156,211,214,241,331,334,341,511,521,621,622,627,632,641,642,635,711,811,911`; **ALTA's actual chart of accounts and current accounting regime must be verified**. Do not hardcode a statutory chart as the company's source of truth.

### 4.3 Trial Balance — `[PROPOSED SCHEMA]`

**Grain:** company × period × leaf account.

```text
company_id, period, account_code, account_name,
opening_debit, opening_credit, period_debit, period_credit,
closing_debit, closing_credit
```

Controls: opening + movement → closing with debit/credit sign rules; total debits and credits reconcile; parent and leaf not double-counted; variance tolerance configurable and justified.

---

## 5. Revenue, invoicing, sales orders

### 5.1 Sổ chi tiết doanh thu / TK511 — `[PROPOSED SCHEMA]`

```text
company_id, revenue_account, posting_date, invoice_date,
invoice_number, customer_id, customer_name, item_id,
item_description, quantity, unit, unit_price,
gross_sales_amount, discount_amount, net_sales_amount,
vat_amount, project_id, department_id, sales_person_id,
revenue_category
```

Do not assume a TK511 detail has item/quantity/salesperson fields. If missing, enrich from invoice lines, item master, sales roster or project master with a proven join. Revenue recognized by GL may differ from invoice/billing totals by posting timing, adjustments, taxes, credit notes and scope.

### 5.2 Sales invoice header/lines — `[PROPOSED SCHEMA]`

```text
invoice_header: invoice_id, company_id, invoice_number,
invoice_series, invoice_date, customer_id, payment_terms,
due_date, currency, exchange_rate, subtotal, discount,
vat, total_amount, project_id, status

invoice_line: invoice_id, line_number, item_id, quantity,
unit, unit_price, discount, net_amount, vat_amount,
revenue_account, warehouse_id, project_id
```

An invoice number alone is not globally unique. Use legal entity, series/type, document identifiers and adjustments. Maintain immutable invoice identity and change history.

### 5.3 Sales order, contract, backlog — `[PROPOSED SCHEMA]`

```text
sales_order_id, company_id, order_date, customer_id,
item_id, ordered_quantity, delivered_quantity,
remaining_quantity, contract_value, invoiced_value,
remaining_contract_value, planned_delivery_date,
expected_invoice_date, expected_collection_date,
project_id, order_status
```

Future milestone-based billing may be managed outside FAST. Contract value ≠ backlog ≠ recognized revenue ≠ cash collections. For Plastics, sales forecasting requires **volume × ASP** normalized into appropriate kg/tonne units. For Media, track contracted backlog, unbilled milestones, and project stages separately.

---

## 6. Accounts receivable, AR aging and allocations

### 6.1 AR subledger / TK131 — `[PROPOSED SCHEMA]`

```text
company_id, customer_id, customer_name, account_code,
posting_date, document_number, document_type,
invoice_number, opening_balance, debit_movement,
credit_movement, closing_balance, due_date, project_id,
currency
```

**Grain:** AR movement, not automatically invoice. Opening/closing balances on report subtotal lines are controls, not transaction rows.

### 6.2 AR aging snapshot — `[PROPOSED SCHEMA]`

```text
snapshot_date, company_id, customer_id, invoice_id,
invoice_date, due_date, original_amount,
applied_payment_amount, outstanding_amount,
days_past_due, aging_bucket
```

Recommended aging buckets: not due, 1–30, 31–60, 61–90, 91–180, >180 days. Buckets configurable, not claimed FAST defaults. Handle credit balances and customer advances separately.

### 6.3 Receipt allocation — `[PROPOSED SCHEMA]`

```text
receipt_document_id, receipt_date, company_id,
customer_id, invoice_id, invoice_number,
allocation_line, allocated_payment_amount, currency,
bank_account_id, project_id
```

Build `fact_ar_payment_allocations` at receipt × invoice × allocation line. Partial receipts, multiple invoices per payment, multi-currency and unapplied receipts are supported. Cash matching should use invoice/customer/description and validated references, **not project code alone**.

Metrics: actual collection lag (including partial-payment weighted days), overdue %, collection on-time %, DSO (document precise method), customer concentration, probability/confidence of collection.

---

## 7. Accounts payable and procurement

### 7.1 AP subledger / TK331 — `[PROPOSED SCHEMA]`

```text
company_id, supplier_id, supplier_name, account_code,
posting_date, document_number, invoice_number,
invoice_date, opening_balance, debit_movement,
credit_movement, closing_balance, project_id, currency
```

### 7.2 AP aging — `[PROPOSED SCHEMA]`

```text
snapshot_date, company_id, supplier_id, invoice_id,
invoice_date, due_date, original_amount, paid_amount,
outstanding_amount, days_past_due, aging_bucket
```

### 7.3 Purchase invoice detail — `[PROPOSED SCHEMA]`

```text
purchase_invoice_id, company_id, supplier_id, invoice_date,
item_id, quantity, unit_price, net_amount, vat_amount,
total_amount, inventory_account, expense_account,
project_id, department_id
```

### 7.4 Open purchase orders and commitments — `[PROPOSED SCHEMA]`

```text
purchase_order_id, company_id, supplier_id, order_date,
item_id, ordered_quantity, received_quantity,
remaining_quantity, unit_price, outstanding_commitment,
expected_receipt_date, expected_payment_date, order_status
```

Do not equate expense recognition with cash payment. Do not double count open PO amounts subsequently invoiced into AP. Keep supplier payment terms, planned vs contractual dates, and critical supplier risk separately.

---

## 8. Cash, bank, direct cash flow

### 8.1 Cash receipts journal — `[PROPOSED SCHEMA]`

```text
company_id, receipt_date, posting_date, document_number,
document_type, description, cash_account, offset_account,
customer_id, project_id, department_id, receipt_amount,
currency, bank_account_id
```

### 8.2 Cash payments journal — `[PROPOSED SCHEMA]`

```text
company_id, payment_date, posting_date, document_number,
document_type, description, cash_account, offset_account,
supplier_id, project_id, department_id, payment_amount,
currency, bank_account_id
```

Enriched fields: `cash_transaction_id`, `cash_flow_category`, `is_internal_transfer`, `is_intercompany`, `is_operating`, `bank_reconciled_status`, provenance. These must be added by a **reviewable mapping engine**, not assumed to be FAST columns.

**Preliminary mapping (requires voucher review):**
- offset `131`: probable customer collection;
- offset `511`: possible direct sales receipts, but do not duplicate AR-derived collections;
- offset `341`: possible borrowing/disbursement or repayment;
- `111 ↔ 112` and `112 ↔ 112`: possible cash/bank transfers, exclude both sides from external cash flows after matching;
- `331`: likely supplier settlement, but must join invoice/PO for economic category (material/service/CAPEX);
- other/unknown account: `UNCLASSIFIED` until evidenced.

**Never** equate all receipts less all payments in a journal to operating cash flow or free cash flow without transaction classification and transfer elimination.

### 8.3 Bank/cash ledger and balance — `[PROPOSED SCHEMA]`

```text
bank_ledger: company_id, bank_account_id, transaction_date,
document_number, description, opening_balance,
debit_amount, credit_amount, running_balance, currency,
exchange_rate

fact_bank_balance: company_id, bank_account_id, balance_date,
currency, closing_balance, restricted_cash, available_cash
```

Available cash is not necessarily total ledger cash. Bank statement is an independent source. Matching should use amount, date, bank reference, counterparty and narrative; unresolved matches require exception handling.

### 8.4 Thirteen-week cash forecast

**Frequency:** one row per week in cash bridge; underlying collections/payments by expected actual date.

```text
Beginning Available Cash
+ Customer Collections
+ Other Operating Receipts
- Supplier Payments
- Payroll
- OPEX Payments
- Taxes
- CAPEX Cash Payments
- Interest
- Principal Repayments
+ Financing Drawdowns
+/- Other External Cash Movements
= Ending Available Cash
Ending Available Cash - Minimum Liquidity Floor = Headroom
```

Maintain `Base` and `Downside` scenarios, version, owner, confidence, evidence/reference and payment priority. Do not use historical monthly/weekly average as a committed future collection. Historical cash journals only seed a baseline and customer/supplier behavioral analysis. Future starting cash requires verified bank/cash snapshot; future AR/AP requires as-of outstanding invoices and payment schedules; future CAPEX requires payment milestones, not fixed asset additions.

Historical last 13 weeks and forward 13 weeks must be shown **separately**. Weekly actual-vs-prior-forecast variance and cash bridge roll-forward mandatory. Consolidated cash flow must eliminate matched internal transfers/intercompany flows, while preserving separate legal-entity liquidity.

---

## 9. Inventory and warehouses

### 9.1 Inventory receipts/issues/balances — `[PROPOSED SCHEMA]`

```text
inventory_period_balance: company_id, warehouse_id, item_id,
item_name, item_category, unit, period,
opening_quantity, opening_value, receipt_quantity,
receipt_value, issue_quantity, issue_value,
closing_quantity, closing_value

inventory_movement: company_id, posting_date, document_number,
transaction_type, warehouse_id, item_id, unit,
quantity_in, quantity_out, value_in, value_out,
production_order_id, project_id, department_id
```

### 9.2 Item master — `[PROPOSED SCHEMA]`

```text
item_id, company_id, item_name, item_group, item_type,
base_unit, purchase_unit, sales_unit, conversion_factor,
product_family, material_type, is_active,
effective_from, effective_to
```

Optional Plastics dimensions requiring ALTA validation: material grade, virgin/recycled/biobased, thickness, width, film type, finished-product family.

KPI definitions: Inventory turnover = period COGS / average inventory; DIO = average inventory / period COGS × days; movement-based slow-mover; negative stock exceptions; material consumption; warehouse-to-GL inventory reconciliation. Unit conversions and inventory valuation methods must be verified. Do not infer physical capacity from space or inventory movements.

---

## 10. Manufacturing, WIP, BOM, COGS

### 10.1 Production orders — `[PROPOSED SCHEMA]`

```text
production_order_id, company_id, product_id,
production_start_date, production_end_date,
planned_quantity, actual_output_quantity,
department_id, work_center_id, production_status
```

### 10.2 Material consumption — `[PROPOSED SCHEMA]`

```text
production_order_id, company_id, material_id, warehouse_id,
issue_date, issued_quantity, returned_quantity,
net_consumed_quantity, material_cost
```

### 10.3 Production costing — `[PROPOSED SCHEMA]`

```text
company_id, period, production_order_id, product_id,
cost_center_id, direct_material_cost, direct_labor_cost,
manufacturing_overhead, outsourced_processing_cost,
total_production_cost, completed_quantity,
unit_production_cost
```

### 10.4 Work-in-progress — `[PROPOSED SCHEMA]`

```text
period, company_id, production_order_id, product_id,
opening_wip, current_material_cost, current_labor_cost,
current_overhead, completed_cost, closing_wip
```

### 10.5 BOM — `[PROPOSED SCHEMA]`

```text
bom_id, company_id, finished_product_id,
component_material_id, standard_quantity,
standard_scrap_rate, effective_from, effective_to
```

BOM, machine time, standard yield and capacity may live outside FAST. Do not hallucinate them. Reconcile cost pools and TK154/621/622/627/632 using cost-flow logic, work-in-process timing and accepted accounting method. Do not assume all overhead is correctly allocated in existing FAST reports.

Plastics analytical bridge: revenue = volume × ASP; COGS drivers = raw materials, labor, OH, outsourced processing, mix/yield. Profit bridge separates volume, ASP, mix, material cost, production efficiency once valid units and matching periods exist. Do not label changes as inefficiency before mix/price/costing checks.

---

## 11. Fixed assets, depreciation, construction and CAPEX

```text
asset_register: company_id, asset_id, asset_name,
asset_category, acquisition_date, capitalization_date,
original_cost, useful_life_months, depreciation_method,
monthly_depreciation, accumulated_depreciation,
net_book_value, department_id, location_id, project_id,
asset_status

asset_movement: company_id, asset_id, movement_date,
movement_type, increase_cost, decrease_cost,
depreciation_change, disposal_value, transfer_department

depreciation: company_id, asset_id, period, department_id,
cost_center_id, depreciation_expense, expense_account,
accumulated_depreciation

construction_in_progress: company_id, project_id,
document_date, supplier_id, document_number,
capex_category, amount, account_code, description
```

**CAPEX accounting != CAPEX cash payment.** Fixed-asset additions and depreciation must not directly populate future cash payments. Cash CAPEX must trace contract/PO → invoice/AP → bank settlement/payment milestone. Reconcile asset register against GL 211/214 and TK241, flag all differences to CFO. Asset attribution to Plastics/Media/3D must be verified at individual asset level.

---

## 12. Project, job, BU profitability

```text
project_master: company_id, project_id, project_name,
business_unit_id, customer_id, project_manager_id,
start_date, end_date, project_status, contract_value,
approved_budget

project_revenue: company_id, project_id, invoice_id,
revenue_account, posting_date, recognized_revenue

project_direct_costs: company_id, project_id, document_id,
cost_date, expense_account, supplier_id, cost_category,
direct_cost_amount
```

Expected waterfall:

```text
Project Revenue
- Identified Direct Supplier/Material/Labor/Other Direct Cost
= Project Contribution
- Approved, Driver-based Allocated Overhead (if any)
= Project Operating Profit (only if complete and approved)
```

For Alta Media, if project reports show zero cost or direct expenses cannot be traced through 632/154/622/627, flag `INCOMPLETE COST` and suppress purported project margin/profit. Keep unallocated pools separately. Project AR/AP, collections and milestones need invoice/customer/reference matching, not just project name. Budget, labor timesheets, PM owner, utilization and allocation drivers may need external sources.

---

## 13. Financial statements and master data

### P&L — `[PROPOSED SCHEMA]`

```text
company_id, period, business_unit_id, net_revenue, cogs,
gross_profit, selling_expenses, administrative_expenses,
operating_profit, finance_income, finance_expense,
other_income, other_expense, profit_before_tax,
income_tax, net_profit
```

### Balance sheet — `[PROPOSED SCHEMA]`

```text
company_id, period, cash, short_term_investments,
accounts_receivable, inventory, other_current_assets,
fixed_assets, construction_in_progress,
other_noncurrent_assets, accounts_payable,
short_term_debt, other_current_liabilities,
long_term_debt, other_noncurrent_liabilities, equity
```

### Accounting cash flow — `[PROPOSED SCHEMA]`

```text
company_id, period, operating_cash_flow,
investing_cash_flow, financing_cash_flow,
net_cash_change, opening_cash, closing_cash
```

Accounting cash flow statement, cash transaction ledger, and forward direct 13-week forecast must remain separate artifacts. EBITDA must follow a documented policy; never force the same simplistic addback across companies with inconsistent financial classifications.

### Dimension/master tables

| Table | Proposed natural business key | Notes |
|---|---|---|
| `dim_company` | company code | Legal entity, reporting currency, parent |
| `dim_account` | company + account | COA hierarchy, effective dates, report mapping |
| `dim_customer` | company + customer code | External IDs, relationships |
| `dim_supplier` | company + supplier code | Intercompany identification |
| `dim_item` | company + item code | Units, product family |
| `dim_warehouse` | company + warehouse code | Warehouse location |
| `dim_department` | company + department code | Effective dates |
| `dim_project` | company + project code | Project and BU attribution |
| `dim_asset` | company + asset code | Actual ownership and scope |
| `dim_bank_account` | company + bank code | Currency and restricted status |
| `dim_business_unit` | managed BU code | May span legal entities |
| `dim_date` | calendar date | Reporting weeks, fiscal periods |
| `map_cost_category` | versioned mapping ID | Approved expense definitions |
| `map_cash_flow_category` | versioned mapping ID | Cash nature and transaction overrides |
| `map_business_unit` | versioned mapping ID | Avoid implicit allocation |
| `map_intercompany` | company pair/relationship | Eliminations only with evidence |
| `map_account_hierarchy` | company + account | Parent/child and leaf-only aggregation |

Use SCD/effective-dated mappings where history can change. Account codes and vendor/customer codes can collide across companies.

---

## 14. Database design: PostgreSQL as proposed default

### Dimensions
`dim_company`, `dim_account`, `dim_customer`, `dim_supplier`, `dim_item`, `dim_warehouse`, `dim_department`, `dim_project`, `dim_asset`, `dim_bank_account`, `dim_date`, `dim_business_unit`.

### Accounting and operations fact tables
`fact_gl_entries`, `fact_sales_invoice_lines`, `fact_purchase_invoice_lines`, `fact_ar_movements`, `fact_ar_payment_allocations`, `fact_ap_movements`, `fact_ap_payment_allocations`, `fact_cash_transactions`, `fact_bank_balances`, `fact_inventory_movements`, `fact_inventory_balances`, `fact_production_orders`, `fact_material_consumption`, `fact_production_costs`, `fact_asset_movements`, `fact_depreciation`, `fact_project_costs`, `fact_project_revenue`.

### Planning facts (SEPARATE actual and forecast)
`plan_revenue`, `plan_opex`, `plan_capex`, `forecast_cash_collections`, `forecast_cash_payments`, `forecast_assumptions`, `forecast_scenarios`, `forecast_versions`.

Example `forecast_cash_collections` fields:

```text
forecast_version_id, scenario_id, company_id,
customer_id, invoice_id, original_due_date,
expected_collection_date, outstanding_amount,
forecast_collection_amount, confidence_level,
assumption_source, owner_id, last_updated_at
```

Model `source_row_id` and `document_id` separately. Use stable internal surrogate keys but preserve compound natural reference keys. Enforce constraints on values and dates. Document sign conventions and currencies at every layer.

---

## 15. Parsing and reconciliation engineering requirements

### Raw layer
Store untouched XLS/XLSX/CSV files with content hash, period, entity, export filters, extraction timestamp, uploader, row count, source path, parser version, and manifest. No writeback to FAST. Store unknown/malformed source files without losing bytes.

### Staging layer
- Identify report type and parser based on report title, layout fingerprint, headers, not just filename.
- Detect merged headers, title/period filter rows, repeated headings, blank rows, subtotals, parent totals and grand totals.
- Keep totals as validation objects, not transactions.
- Parse Vietnam date formats and numeric locale; support currency/FX, negatives, decimals and thousand separators.
- Preserve codes with leading zeros.
- Normalize names/codes only with controlled mapping.
- Quarantine unparseable rows, log issue and source row; never silently drop.
- Create a `parser_registry`: `GL_DETAIL→parse_gl_detail`, `SALES_DETAIL→parse_sales_detail`, `AR_LEDGER→parse_ar_ledger`, `AP_LEDGER→parse_ap_ledger`, `CASH_RECEIPTS→parse_cash_receipts`, `CASH_PAYMENTS→parse_cash_payments`, `INVENTORY→parse_inventory`, `FIXED_ASSETS→parse_fixed_assets`.
- Support multiple Excel template versions and company-specific column variants.
- Idempotency: re-ingesting identical file does not duplicate records.
- Resubmission of corrected period must preserve old extraction and create a new valid run/version; document historical restatements.

### Accounting reconciliation/control matrix

| Control | Required comparison / test |
|---|---|
| GL | Debits = credits at validated voucher/period scope |
| Trial balance | Opening + movements = closing; parent/leaf dedup |
| Revenue | Applicable GL 511/521 vs sales/revenue detail, by same scope/period |
| AR | GL 131 vs customer subledger and invoice aging |
| AP | GL 331 vs supplier subledger and invoice aging |
| Cash | GL 111/112 vs cash/bank ledgers |
| Bank | Accounting closing cash vs bank statement, timing differences explained |
| Inventory | Valuation report vs inventory GL, check method/perimeter |
| Fixed assets | GL 211/214 vs asset register and depreciation |
| WIP | GL 154 vs cost accumulation/WIP roll-forward |
| Projects | Project revenue/cost vs relevant GL and documented scope |
| Cash flow | External cash movement sum, transfers excluded, agrees bank bridge |
| Intercompany | Matched symmetrical entries, entity-level balance preserved |

Allow documented rounding tolerance, not unexplained variances. An unbalanced output is `PRELIMINARY` / `RECONCILIATION_FAILED`, not CFO-approved.

### State machine
`RAW → PARSED → VALIDATED → RECONCILED → APPROVED` or `REJECTED/QUARANTINED`. Maintain approval identity/time. Dashboards display last refresh, period, entity, evidence status and unresolved exceptions.

---

## 16. Management dashboards and metrics

### CEO Executive
Revenue actual/budget/YoY/YTD; GP/GPM; operating profit/EBITDA per defined policy; cash; working capital; AR/AP/inventory; BU performance; full-year forecast; alert thresholds; decisions/actions.

### CFO Finance
P&L/BS/accounting CF; GL reconciliation; cash/bank balances; AR/AP aging; inventory; 13-week cash forecast/headroom; debt and CAPEX funding; data-quality exception list.

### Alta Media project economics
Project revenue, identified direct cost, project contribution, **unallocated** cost pools, budgets, cost variance, AR, AP, receipts/payments, backlog/billing milestones. Do not display complete project profit where costs or allocation drivers are missing.

### Alta Plastics manufacturing economics
Revenue by product; volume/ASP/mix; material cost/kg, costing analysis, WIP, gross margin, inventory, scrap/yield and utilization **only with validated production/capacity data**.

### S&D / FP&A
Actual vs budget; FY2026 forecast; Budget 2027 driver model (Base/Target/Downside); CAPEX commitments; funding requirements; consolidated/BU views; strategy execution owner/action log.

**Navigation standard:** group → BU/entity → account/customer/project/product → invoice/journal/receipt → exact original source file and source row. Charts/metric cards cannot obscure preliminary data quality or inconsistent scope.

---

## 17. Extraction and automation workflow

**Phase 0 initially:** Manual approved Excel exports from FAST to a designated landing folder, with report-specific extraction checklist, period and filter manifest. Do not assume FAST API, direct SQL, or unrestricted remote browser access.

**Future options (evaluate independently):**
1. Manual scheduled exports — fastest, transparent, limited automation.
2. Authorized browser automation — sensitive to UI, session, SSO and reporting rights. No credential hardcoding, no bypass of access controls.
3. Vendor-supported API/read-only integration — preferred if officially available and licensed; obtain documentation and access permission.

Suggested processing:

```text
FAST approved export / BU input / bank statement
 → landing + raw file hash + manifest
 → report classifier + parser + quarantine
 → staging type/mapping validations
 → GL/subledger/statement reconciliations
 → review and CFO approval
 → SQL dimensional/management marts
 → dashboard and scenario forecast refresh
 → exception/decision log + historical versions
```

Security: principle of least privilege, credentials in secret manager/environment (never git), encryption at rest/in transit, audit access, masking customer/vendor identifiers in development, private dashboards, retention/backup/recovery and access roles. Do not deploy externally without IT/security approval. Restrict AI/LLM uploads of sensitive transaction details unless authorized by ALTA.

---

## 18. Twelve mandatory non-functional requirements

1. Source preservation — no edits/deletion of FAST, source files, or permission changes.
2. Idempotent ingestion — no duplicate postings on re-run.
3. Incremental & full refresh — support period deltas and corrected historical exports.
4. Historical restatement — audit revisions; do not destroy old reported snapshots.
5. Multi-company keys — company scoped in every fact and dimension.
6. Lineage & audit trail — trace KPI to document/row/file/filter/version.
7. Accounting reconciliation — parsing success ≠ accounting approval.
8. Transparent BU mappings — dated, reviewed, scope-controlled, not inferred.
9. Actual/budget/forecast isolation — scenario and forecast version required.
10. Role-based access control — Finance approvals, S&D analytics, BU scope limits.
11. Exception handling — show every failed parse, missing mapping and variance.
12. No unsupported cost allocation — overhead/intercompany drivers must be approved.

---

## 19. Implementation roadmap and deliverables

| Phase | Scope | Working output | Approval gate |
|---|---|---|---|
| 0 | Capture genuine FAST exports, report layout fingerprints, physical dictionary | `schema_registry`, source samples inventory, parser plan | Finance verifies layout/grain |
| 1 | GL, TB, Revenue, AR, AP, cash/bank, masters | Raw/staging/data warehouse MVP | GL and subledger controls pass |
| 2 | Accounting FS, working capital and control dashboard | CEO/CFO financial dashboards | CFO reconciles statements |
| 3 | 13-week cash: outstanding invoices, bank cash, commitments, scenarios | Historical 13W + forward Base/Downside + variance | CFO approves assumptions and cash opening |
| 4 | Inventory, costing, project costs, FA | BU economics dashboards | BU + CFO confirm operational mapping |
| 5 | Budget, forecast and scenarios | FY forecast / Budget 2027 platform | CEO decision log and approved assumptions |
| 6 | Extraction automation, monitoring, deployment | Controlled scheduled production system | IT/Finance security review |

### Deliverable structure / proposed repository

```text
alta-finance-intelligence/
  README.md
  pyproject.toml
  .env.example                  # placeholders only, never secrets
  docs/
    architecture.md
    fast_report_inventory.md
    physical_data_dictionary.md
    data_contracts/
    accounting_policies.md
    cash_flow_policy.md
    security_model.md
    decisions_and_open_questions.md
  config/
    report_registry.yaml
    account_map.yaml
    cash_flow_map.yaml
    bu_map.yaml
    entity_map.yaml
  src/
    extraction/
    ingestion/
    parsers/
    standardization/
    reconciliations/
    models/
    forecasts/
    dashboards/
  sql/
    migrations/
    staging/
    marts/
    controls/
  tests/
    fixtures/                     # synthetic/redacted examples
    test_parsers/
    test_reconciliations/
    test_forecast/
    test_idempotency/
  scripts/
  deployment/
  data/                            # gitignored; immutable raw external store preferred
```

**Preferred MVP technology (subject to IT constraints):** Python + PostgreSQL + tested SQL transformations + Streamlit or Metabase. Avoid expensive/custom UI before robust reconciled data. Docker compose is optional for local development, never assume Work/cloud has access to local FAST. Dashboards should not directly read raw Excel files in production.

### Acceptance criteria for Phase 0
- For every sample export, produce a physical dictionary with header offsets, sample sheet, original exact columns, grain and quality issues.
- Report-level source totals reconcile to parsed totals (or documented exceptions block approval).
- No fabricated field presented as exported from FAST.
- Provenance and file hash recorded; same-file re-run produces zero duplicates.
- A test fixture reproduces at least one multiline journal and one subtotal/merged-header report.

### Acceptance criteria for Phase 1
- GL and trial balance reconcile within approved tolerance.
- AR/AP movements and outstanding controls reconcile at defined cutoff.
- Sales invoice and revenue GL bridge highlights differences with evidence.
- Individual company and consolidated scopes are distinct; no undocumented elimination.
- Dashboard figures can be traced to raw file and row, with visible quality status.

### Acceptance criteria for Phase 3 (13-week cash)
- Opening cash ties to verified bank/cash balances on same date.
- Historical actual cash receipts/payments have matched external transfers removed, but individual transactions preserved.
- Every future cash entry has source/due date/expected date/amount/owner/scenario; unknowns explicitly `DATA REQUIRED`.
- No historical averages promoted to committed forecast amounts.
- Base/Downside both bridge week-to-week; minimum cash and headroom calculated.
- Forecast vs actual variance and cash collection delay sensitivity visible.

---

## 20. Instructions to Claude Code — execute carefully

> You are the lead data engineer and financial analytics architect building ALTA Group's FAST Business Online read-only reporting pipeline. Treat this specification as the target design, **not** a verified FAST column schema. First inspect the actual samples and existing codebase. Produce a plan and data dictionary **before** coding general parsers. Preserve original records, do not guess mappings, do not alter FAST, and never mark unreconciled preliminary financials as approved. Use stepwise deliverables and executable tests. Design for Vietnamese accounting/reporting and company-specific chart of accounts. Carry finance-owner approval gates into the application.

**First run:**
1. Inventory available files and the real FAST sample formats; identify absent P0 source reports.
2. Determine the grain, header, subtotal and amount sign conventions of each sample.
3. Implement a raw ingestion manifest and report registry.
4. Build one parser end-to-end (GL detail or cash receipts) including reconciliation and automated tests.
5. Demonstrate a traceable metric and a data quality report, using only verifiable inputs.
6. Request missing samples and accounting mapping approvals **as open action items** rather than filling gaps with invented data.
7. Expand report by report, maintaining versioned documentation and test coverage.

### Open questions that must not be assumed
- Exact FAST version, modules enabled, export XLS vs XLSX formats, headings and filters.
- Official legal entities, report scope and organizational/BU mappings.
- Actual Chart of Accounts under the currently applicable accounting regime.
- Whether sales orders, purchase orders, BOM, production orders and timesheets are in FAST or external systems.
- API/vendored read-only integration availability and permissions.
- Approved project costing / overhead allocation and intercompany elimination policy.
- Historical bank statements and opening balances for cash reconciliation.
- AR/AP invoice-level outstanding, payment terms, settlement allocations and projected collections.
- CAPEX contracts and actual payment schedule, debt schedule, liquidity floor.
- Approved variance tolerances, roles, retention policy, dashboard deployment environment.

---

## 21. Reference resources and caution

Public vendor/help references for report concepts (verify current version and applicability before implementation):
- FAST Business Online help: https://fbohelp.fast.com.vn/
- FAST online product help: https://help.faonline.vn/
- Accounting report families, general ledger, AR/AP, cash, inventory, costing, projects and statements are described in vendor documentation, but their physical export schemas vary.

Project-specific working memory for continuity: `SD_MEMORY_2026-10-29_v1.md` is a summarized working context, not an audited transaction source. Do not ingest historical figures from it as journal actuals.

**End of implementation brief.**
