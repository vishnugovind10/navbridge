# NavBridge

NAV integrity monitoring for tokenized funds.

NavBridge is an open-source Python framework for detecting, classifying, and documenting divergence between on-chain oracle NAV and off-chain fund administrator NAV.

It is designed to be adapted by fund operations, oracle, tokenization, and protocol risk teams that need explainable NAV integrity controls instead of a demo dashboard.

## Real Report Sample

Generated from `examples/mmf_scenario`:

```markdown
**Schema:** navbridge.report.v1
**Run ID:** 36284246c568b7e8

## Summary
| Metric | Value |
|---|---|
| Total NAV observations | 31 |
| Oracle records read | 744 |
| Administrator records read | 31 |
| Total divergence events | 31 |
| Material breaks | 0 |
| Critical breaks | 0 |
| Mean divergence | 0.80 bps |
| Max divergence | 2.72 bps |
| Policy compliance | Yes |

## Break Distribution
| Break Type | Count | % of breaks |
|---|---:|---:|
| Market Hours Asymmetry | 9 | 29% |
| Methodology Drift | 22 | 71% |
```

## The Problem

Every tokenized fund has two NAV sources. The on-chain source is the oracle NAV used by DeFi protocols, collateral managers, and secondary-market participants. The off-chain source is the administrator NAV used for subscriptions, redemptions, audit support, and regulatory records.

Those numbers are rarely identical. Timing lag, methodology differences, market-hours asymmetry, corporate actions, and oracle outages can all create measurable divergence.

Most institutions handle this with proprietary reconciliation scripts. NavBridge gives fund teams, protocol risk teams, and builders a shared open-source framework for modeling the gap and documenting a NAV integrity policy.

## What NavBridge Does

- Monitor: ingest simulated oracle NAV and administrator NAV files, then compute per-record divergence.
- Classify: assign rule-based break types and severity levels.
- Report: write structured JSON and human-readable Markdown reports.

## Quickstart

```powershell
python -m pip install -e ".[dev]"

navbridge validate-admin-file `
  --config examples/mmf_scenario/config.json `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31

navbridge monitor `
  --config examples/mmf_scenario/config.json `
  --oracle simulated `
  --drift-model BUIDL_STYLE `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31 `
  --output-md - `
  --advise-policy
```

Run all examples:

```powershell
python examples/mmf_scenario/run.py
python examples/treasury_fund_scenario/run.py
python examples/market_hours_scenario/run.py
```

Run tests:

```powershell
python -m pytest -q
```

## The Three Scenarios

- `examples/mmf_scenario`: tokenized money market fund with weekend and after-hours drift.
- `examples/treasury_fund_scenario`: treasury fund with a simulated coupon/corporate-action lag.
- `examples/market_hours_scenario`: oracle feed degradation where stale NAV is classified as critical.

## Architecture

See `ARCHITECTURE.md`.

```text
administrator files -> ingesters -> monitor -> classifier -> report object -> JSON/Markdown
simulated oracle ----^
```

Key operational documents:

- `docs/adapter_contracts.md`: integration contract for internal oracle and administrator adapters.
- `docs/controls_matrix.md`: control objectives mapped to code and report evidence.
- `docs/data_validation.md`: pre-run validation workflow for administrator files and adapter output.
- `docs/internal_adoption_guide.md`: recommended path for adapting NavBridge internally.
- `docs/model_risk_and_validation.md`: model-risk notes and validation expectations.
- `docs/report_schema_v1.json`: JSON report schema.
- `SECURITY.md`: security boundary and vulnerability policy.

## Limitations

V1 uses simulated oracle data only. Administrator NAV files must be transformed into the NavBridge CSV or JSON schema before ingestion. The classifier is heuristic and rule-based, not exhaustive. Real production breaks may need institution-specific policy overrides.

See `docs/limitations.md`.

## Roadmap

- Live oracle adapters for Chainlink, RedStone, and Pyth.
- Fund administrator API connectors.
- ERC-4626 vault read adapters.
- Alerting and workflow integrations.
- Optional dashboard after the core monitoring contract is stable.

## Background

NavBridge is built from the fund-operations side of tokenized assets. It treats NAV divergence as a reconciliation and audit-control problem first, and a blockchain data problem second. That boundary keeps V1 focused on explainable monitoring instead of token issuance, KYC, or fund accounting.
