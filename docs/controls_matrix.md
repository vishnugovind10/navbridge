# NAV Integrity Controls Matrix

This matrix maps NavBridge V1 behavior to controls an institutional team would normally evaluate before adapting the framework.

| Control Objective | NavBridge Mechanism | Evidence Artifact |
|---|---|---|
| Confirm oracle/admin NAV divergence is measured consistently | `MonitorEngine` aligns records and computes signed bps divergence | JSON report `events[*].divergence_bps` |
| Preserve source lineage | `NavRecord.metadata` carries feed, file, and calculation context | JSON report `oracle_record.metadata` and `administrator_record.metadata` |
| Detect missing or stale oracle data | Alignment failures and stale oracle records classify as `data_feed_failure` | JSON report `break_type_distribution`, Markdown material breaks |
| Avoid silent adapter drift | Monitor validates source, fund ID, currency, and duplicate timestamps | `MonitorEngineError` |
| Explain break categories | Rule-based classifier emits break type, confidence, and notes | JSON report `events[*].break_type`, `classification_confidence`, `notes` |
| Separate policy from measurement | Thresholds live on `FundConfig`, not hidden constants | JSON report `config_snapshot` |
| Support audit repeatability | Reports carry `schema_version`, `run_id`, input counts, and parameters | JSON report header fields |
| Provide readable control evidence | Markdown reporter summarizes material breaks and policy status | Markdown report output |
| Avoid scaling bottlenecks in batch runs | Monitor uses indexed nearest-timestamp lookup for oracle alignment | `navbridge/monitor/engine.py` |

## Non-Goals

NavBridge V1 does not approve trades, calculate legal NAV, issue tokens, custody assets, or replace fund accounting. It produces explainable control evidence for NAV divergence.
