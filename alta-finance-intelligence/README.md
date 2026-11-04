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
afi boardpack --month 2026-10 [--mode ytd] [--plan plan.csv]  # board pack PPTX (tools/board-pack)
afi status                                # manifest (all extractions, incl. superseded/quarantined)
```
CFO approval of a reconciled month: add it to `data/approvals.yaml`:
```yaml
approvals:
  - {company_id: APL, month: "2026-10", by: "Tên CFO", at: "2026-11-05"}
```

## Layout
| Path | Role |
|---|---|
| `config/report_registry.yaml` | Report fingerprints (title + header), canonical ↔ raw column aliases, evidence status |
| `config/entity_map.yaml` | Legal entities (MST) and business units (3D inside Alta Plastic) |
| `config/account_map.yaml`, `config/cash_flow_map.yaml` | `[PROPOSED POLICY]` P&L and cash-flow mapping, versioned |
| `src/afi/ingestion/store.py` | Content-addressed raw store, append-only `manifest.jsonl`, supersede by sequence |
| `src/afi/parsers/` | `base` (header/merged header/totals/period/company), `gl_journal`, `trial_balance`, `sales_list` |
| `src/afi/reconciliations/controls.py` | FILE_TOTALS, GL_DR_EQ_CR, GL_VOUCHER_BALANCE (warn), TB_DR_EQ_CR, TB_ROLLFORWARD, TB_EQ_GL_MOVEMENT, REVENUE_BRIDGE |
| `src/afi/models/warehouse.py` | DuckDB: `effective`, `fact_gl_lines`, `fact_tb`, `fact_sales_lines`, `pl_lines_lineage` (with account, counterparty, description), `mart_pl_monthly` |
| `src/afi/dictionary.py` | Data contract YAML (spec §3) with redacted examples and open questions |
| `tests/` | Synthetic fixtures: multi-line voucher, Dr/Cr pair layout, merged-header TB, observed sales list layout; `group_dataset()` = 3 entities × 22 months (GL, TB, sales list) used by tools/board-pack |

## Not yet built (by phase)
Purchase list parser, COA/party masters (Phase 1) · intercompany control in pipeline, gold data pack for the dashboard (Phase 2) · 13-week cash model (Phase 3) · inventory, FA, jobs (Phase 4).
