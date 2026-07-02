# Break Classification Guide

NavBridge V1 uses auditable rules, not machine learning.

Every classified event includes:

- `classification_rule_id`: stable rule identifier for reviewer lookup.
- `classification_ruleset_version`: currently `navbridge.classifier.rules.v1`.
- `classification_evidence`: threshold and observation data used by the rule.

## Rule IDs

| Rule ID | Break Type | Trigger |
|---|---|---|
| `clean_equal_nav` | none | Oracle and administrator NAV are equal. |
| `data_feed_failure_stale_nav` | `data_feed_failure` | Oracle stale duration exceeds 2x configured update interval. |
| `data_feed_failure_zero_nav` | `data_feed_failure` | Oracle NAV is zero. |
| `corporate_action_delay_window` | `corporate_action_lag` | Oracle metadata marks corporate-action delay. |
| `market_hours_closed` | `market_hours_asymmetry` | Administrator observation is outside configured market hours. |
| `methodology_persistent_direction` | `methodology_drift` | At least 80% of non-zero events have the same direction. |
| `timing_lag_configured` | `timing_drift` | Market-hours divergence has configured oracle timing lag. |
| `timing_drift_fallback` | `timing_drift` | Divergence exists but no stronger rule matched. |

## Timing Drift

Used when divergence appears inside market hours with a configured oracle timing lag and no stronger rule applies.

## Methodology Drift

Used when divergence is directionally consistent across most market-hours observations. This usually represents pricing-method differences such as bid, mid, evaluated bid, or fair value.

## Market Hours Asymmetry

Used when divergence is observed outside configured market hours. This is common when on-chain feeds continue to update while administrator NAV is fixed after close.

## Corporate Action Lag

Used when divergence coincides with the simulated corporate-action delay window. This models coupon, dividend, split, or other event timing differences.

## Data Feed Failure

Used when oracle NAV is zero or stale beyond two configured oracle update intervals. Data feed failures are escalated to `critical` severity even when the numerical divergence is small.
