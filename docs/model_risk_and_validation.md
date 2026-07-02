# Model Risk and Validation

NavBridge V1 uses deterministic simulation and rule-based classification. It should be reviewed as an operational control framework, not as a pricing model or legal NAV calculator.

## What Requires Validation

- Administrator-file mapping into the NavBridge schema.
- Oracle adapter timestamp and value semantics.
- Market-hours configuration for each fund.
- Tolerance and materiality thresholds.
- Corporate-action source and timing assumptions.
- Stale-feed detection interval.
- Rule ordering in `classifier/rules.py`.

## What the V1 Simulation Proves

The simulation proves that the monitor, classifier, reporter, and policy advisor can process realistic NAV divergence patterns without live dependencies. It does not prove that a specific live oracle feed, administrator file, or fund methodology is correct.

## Recommended Validation Evidence

- Historical backtest over at least one month of known administrator NAV.
- Parallel run against existing reconciliation output.
- Sample review of JSON report events against source records.
- Exception review for every `data_feed_failure`, `material`, and `critical` event.
- Change-control approval for any classifier-rule modification.

## Known Model-Risk Controls

- No hidden ML scoring.
- No hardcoded threshold outside `FundConfig`.
- JSON reports include schema version, run ID, input counts, monitor parameters, and config snapshot.
- Adapter boundary validation fails fast on wrong fund, wrong currency, wrong source, and duplicate timestamps.
