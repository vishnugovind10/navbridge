# Tolerance Policy Guide

Tolerance settings live on `FundConfig`:

- `tolerance_bps`: routine divergence threshold.
- `materiality_bps`: threshold for material review.
- `oracle_update_frequency_minutes`: expected oracle cadence.
- `alignment_window_minutes`: maximum timestamp distance for matching records.

The policy advisor uses observed absolute divergence values and recommends a 97th percentile tolerance. This is a starting point for review, not a legal or regulatory conclusion.

Institutional users should set tolerance based on fund type, asset liquidity, pricing source quality, redemption terms, collateral usage, and administrator methodology.
