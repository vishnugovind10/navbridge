# Break Classification Guide

NavBridge V1 uses auditable rules, not machine learning.

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
