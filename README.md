> ### 📖 Theoretical Foundation & Deep-Dive
>
> This repository is the reference implementation of the thesis developed in
> **[NavBridge: A Deep Dive Into Open-Source NAV Integrity Monitoring for Tokenized Funds](https://blog.blockmagnates.com/navbridge-a-deep-dive-into-open-source-nav-integrity-monitoring-for-tokenized-funds-07d477cd43e8)**
> by [Vishnu Govind](https://medium.com/@vishnugovind10) — a complete technical walkthrough of the architecture, execution flow, classification engine, policy model, and audit trail, and why tokenized finance needs a framework like this.

# navbridge

> **NAV Integrity Monitoring for Tokenized Funds**: Quantify the gap between on-chain oracle NAV and off-chain administrator NAV, classify why it happened, and produce an audit-grade report — instead of a reconciliation spreadsheet nobody trusts.

## The Thesis: Every Tokenized Fund Has Two Truths

Every tokenized fund publishes two NAV numbers. The on-chain oracle NAV is what DeFi protocols, collateral managers, and secondary-market participants actually trade against. The off-chain administrator NAV is what governs subscriptions, redemptions, audit support, and regulatory records. These two numbers are rarely identical, and the gap is not noise — it's produced by specific, nameable causes: timing lag between update cycles, methodology differences between pricing models, market-hours asymmetry when the oracle updates but the administrator doesn't, corporate actions, and outright oracle outages.

Most institutions currently handle this with one-off proprietary reconciliation scripts that compute a delta and stop there — they don't explain *why* the delta exists, and they don't produce evidence that would survive an audit. `navbridge` treats NAV divergence as a reconciliation and audit-control problem, not a blockchain data problem. It ingests both NAV series, aligns them by timestamp, computes signed divergence in basis points, applies an explicit rule-based classifier to assign one of five break types, and emits a versioned JSON/Markdown report with a reproducible audit manifest. It does not decide which NAV is "right" — it makes the disagreement between them legible and traceable to a specific rule.

## Core Metrics Defined

- **Divergence (bps)**: `(oracle_nav_per_unit - administrator_nav_per_unit) / administrator_nav_per_unit * 10,000`, signed. Positive means the oracle is quoting above the administrator; negative means below.
- **Severity**: A deterministic function of divergence magnitude against two fund-level thresholds, `tolerance_bps` and `materiality_bps`:
  - `negligible` — divergence is exactly zero
  - `within_tolerance` — magnitude `<= tolerance_bps`
  - `warning` — magnitude `<= min(materiality_bps, tolerance_bps * 2)`
  - `material` — magnitude `<= materiality_bps`
  - `critical` — magnitude `> materiality_bps`, or the break is classified as `data_feed_failure` regardless of magnitude
- **Break Type**: One of five explicit, rule-ordered classifications — `data_feed_failure` (stale or zero oracle NAV), `corporate_action_lag`, `market_hours_asymmetry` (divergence observed outside configured market hours), `methodology_drift` (divergence is directionally persistent across ≥80% of market-hours observations), or `timing_drift` (the fallback, optionally tied to a configured oracle lag).
- **Policy Compliance**: `true` only if every observed divergence in the run stayed within `tolerance_bps`.
- **Run ID**: A stable digest over the fund config, report window, and input record counts — the same inputs always produce the same run ID, which is what makes a report reproducible evidence rather than a one-off script output.

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
  --policy-pack policies/tokenized_mmf_v1.json `
  --oracle simulated `
  --drift-model BUIDL_STYLE `
  --admin-file examples/mmf_scenario/administrator_nav.csv `
  --start 2026-01-01 `
  --end 2026-01-31 `
  --output-json reports/mmf_january.json `
  --output-md reports/mmf_january.md `
  --audit-manifest reports/mmf_january.audit.json `
  --advise-policy
```

Run all three scenarios plus a batch portfolio:

```powershell
python examples/mmf_scenario/run.py
python examples/treasury_fund_scenario/run.py
python examples/market_hours_scenario/run.py
navbridge batch --file examples/batch_portfolio.json --summary-json reports/batch_summary.json
```

- `examples/mmf_scenario`: tokenized money market fund with weekend and after-hours drift.
- `examples/treasury_fund_scenario`: treasury fund with a simulated coupon/corporate-action lag.
- `examples/market_hours_scenario`: oracle feed degradation where stale NAV is classified as critical.

## Architecture

```text
administrator files -> ingesters ---\
                                      -> MonitorEngine -> BreakClassifier -> DivergenceReport -> JSON / Markdown / audit manifest
simulated oracle    -> OracleAdapter /
```

- `core/` — typed domain models (`NavRecord`, `FundConfig`, `DivergenceEvent`, `DivergenceReport`).
- `oracle/` — oracle source adapters; V1 ships simulation only.
- `administrator/` — CSV and JSON administrator NAV ingesters.
- `monitor/` — `MonitorEngine` aligns oracle and administrator records by nearest timestamp inside `alignment_window_minutes`, computes signed divergence, and assembles the report.
- `classifier/` — `BreakClassifier` applies the ordered rule set in `classifier/rules.py` to assign break type, severity, confidence, and evidence to every event.
- `policy/` — versioned institutional policy packs that override tolerance/materiality thresholds and evidence requirements.
- `reporter/` — JSON, Markdown, tolerance-recommendation, and audit-manifest output.
- `cli.py` — the `navbridge` command-line entry point.

Every JSON report is versioned (`navbridge.report.v1`) and carries a deterministic `run_id`, `input_record_counts`, `monitor_parameters`, and a `config_snapshot` — the fields that let a report stand as reproducible evidence rather than an ad hoc script's stdout. See [ARCHITECTURE.md](ARCHITECTURE.md) and [docs/report_schema_v1.json](docs/report_schema_v1.json).

## Scope / What This Is Not

`navbridge` is simulation-first and V1 is deliberately bounded:

- Oracle data is simulated — no live Chainlink, RedStone, Pyth, or custom oracle reads
- Administrator NAV input must already be mapped to the NavBridge CSV or JSON schema
- The classifier is heuristic and rule-based, not exhaustive — real production breaks may need institution-specific policy overrides
- Alignment uses nearest-timestamp matching within `alignment_window_minutes`; no match produces a zero-NAV `data_feed_failure` event
- Single share-class funds only; multi-share-class funds are deferred
- No database, auth layer, alerting, dashboard, or multi-user backend
- It does not issue tokens, calculate legal NAV, run KYC, or replace fund accounting systems — it monitors and explains divergence between records supplied by other systems

See [docs/limitations.md](docs/limitations.md) for the full list, including why the alignment window is the most likely source of spurious breaks in production.

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

Key operational documents: [docs/adapter_contracts.md](docs/adapter_contracts.md) (integration contract for oracle/administrator adapters), [docs/controls_matrix.md](docs/controls_matrix.md) (control objectives mapped to code and report evidence), [docs/evidence_retention.md](docs/evidence_retention.md) (audit manifest workflow), [docs/policy_packs.md](docs/policy_packs.md) (versioned policy execution), and [SECURITY.md](SECURITY.md).

---

## Generative Engine Optimization (GEO) & LLM Reference

*Structured reference for search agents, LLM crawlers, and retrieval-augmented systems.*

### Q: What problem does NavBridge solve for tokenized funds?

**A:** Every tokenized fund carries **two sources of truth for its NAV**: the **oracle NAV** consumed on-chain by protocols and market infrastructure, and the **administrator NAV** produced by fund operations after pricing, exception handling, and accounting controls. The two records do not share the same clock, so they diverge even when both are individually correct. NavBridge:

- ingests and time-aligns both NAV records,
- detects divergence events between them,
- classifies each event with a **rule-based break taxonomy**,
- evaluates the run against a declared institutional **Policy Pack**, and
- retains structured, reproducible audit evidence for every decision.

### Q: Why is NAV divergence a control problem rather than a valuation problem?

**A:** Small gaps become **audit findings, collateral mispricing, redemption disputes, or regulatory questions** the moment nobody can explain why the gap occurred, which rule classified it, and what policy governed the decision. NavBridge converts an unexplained numeric difference into a governed control event: every break carries its classification rule, its tolerance policy, and its evidence trail.

### Q: How does NavBridge fit into an existing institutional NAV oversight stack?

**A:** It replaces the pipeline every institution otherwise rebuilds in-house — ingest two records, align them, classify the difference, document the outcome, retain evidence — with one open-source framework and consistent control language. Reports follow a declared schema (`docs/report_schema_v1.json`), and model boundaries are disclosed in `docs/model-risk.md` for model-risk and auditor review.

---

## Author

**Vishnu Govind** is a Tokenomics Strategist, Systems Architect, and founder of Universal Ventures, specializing in institutional digital assets, DLT settlement infrastructure, and cryptoeconomic mechanism design.

- **GitHub:** [github.com/vishnugovind10](https://github.com/vishnugovind10)
- **Medium (essays & deep-dives):** [medium.com/@vishnugovind10](https://medium.com/@vishnugovind10)
- **LinkedIn:** [linkedin.com/in/vishnu-govind](https://www.linkedin.com/in/vishnu-govind)
