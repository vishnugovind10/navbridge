# NavBridge Architecture

NavBridge V1 is a Python library and CLI. It has no database, auth layer, web UI, or live oracle dependency.

## Module Layout

```text
navbridge/
  core/            typed domain models
  oracle/          oracle source adapters, V1 simulation only
  administrator/   CSV and JSON administrator NAV ingesters
  classifier/      rule-based break classification
  monitor/         alignment, divergence calculation, report assembly
  policy/          versioned institutional policy packs
  reporter/        JSON, Markdown, and tolerance recommendation output
  cli.py           command-line entry point
```

## Data Flow

1. `AdministratorAdapter` loads administrator NAV records.
2. `OracleAdapter` returns oracle NAV records for the same window.
3. Optional `PolicyPack` overrides configured tolerance/materiality thresholds and evidence requirements.
4. `MonitorEngine` aligns records by nearest timestamp inside `alignment_window_minutes`.
5. The monitor computes signed divergence in basis points.
6. `BreakClassifier` applies explicit rules for the five V1 break types.
7. `DivergenceReport` is serialized to JSON and Markdown.

## Report Contract

JSON reports are versioned with `schema_version="navbridge.report.v1"`. Each report includes:

- `run_id`: deterministic digest over fund, window, config, input counts, and run algorithm.
- `input_record_counts`: oracle, administrator, and aligned record counts.
- `monitor_parameters`: alignment window, oracle update interval, and policy-advisor setting.
- `config_snapshot`: fund policy and market-hours configuration used for the run.

The schema is documented in `docs/report_schema_v1.json`.

## Policy Execution

Policy Packs are versioned JSON artifacts with thresholds, escalation expectations, and evidence requirements. When a policy pack is applied, reports include the policy snapshot under `policy_pack`, Markdown identifies the evaluated policy, and the CLI enforces required evidence such as `--audit-manifest`.

## V1 Break Types

- `timing_drift`
- `methodology_drift`
- `market_hours_asymmetry`
- `corporate_action_lag`
- `data_feed_failure`

## Scope Boundaries

NavBridge does not issue tokens, calculate legal NAV, run KYC, or replace fund accounting systems. It monitors and explains divergence between records supplied by other systems.
