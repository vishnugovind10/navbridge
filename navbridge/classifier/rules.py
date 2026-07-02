from __future__ import annotations

from zoneinfo import ZoneInfo

from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceEvent
from navbridge.core.fund import FundConfig


def classify_event(event: DivergenceEvent, config: FundConfig, all_events: list[DivergenceEvent]) -> tuple[BreakType | None, float, str]:
    if abs(event.divergence_bps) == 0:
        return None, 1.0, "Oracle and administrator NAV are equal."
    stale_minutes = event.oracle_record.metadata.get("stale_duration_minutes")
    if stale_minutes is not None and stale_minutes > 2 * config.oracle_update_frequency_minutes:
        return BreakType.DATA_FEED_FAILURE, 1.0, "Oracle NAV stayed stale beyond 2x the configured update interval."
    if event.oracle_record.nav_per_unit == 0:
        return BreakType.DATA_FEED_FAILURE, 1.0, "Oracle NAV was zero."
    if event.oracle_record.metadata.get("corporate_action_delay"):
        return BreakType.CORPORATE_ACTION_LAG, 1.0, "Divergence coincided with the simulated corporate action delay window."
    if not _is_market_open(config, event.administrator_record.timestamp):
        return BreakType.MARKET_HOURS_ASYMMETRY, 0.9, "Divergence was observed outside configured market hours."
    if _persistent_same_direction(all_events, event):
        return BreakType.METHODOLOGY_DRIFT, 0.8, "Divergence was directionally consistent across market-hours observations."
    if event.oracle_record.metadata.get("timing_lag_minutes", 0) > 0:
        return BreakType.TIMING_DRIFT, 0.8, "Divergence was observed inside market hours with a configured oracle timing lag."
    return BreakType.TIMING_DRIFT, 0.5, "Divergence was present but did not match a stronger rule."


def _is_market_open(config: FundConfig, timestamp) -> bool:
    local = timestamp.astimezone(ZoneInfo(config.market_timezone))
    if local.weekday() >= 5:
        return False
    return config.market_open <= local.time() <= config.market_close


def _persistent_same_direction(events: list[DivergenceEvent], event: DivergenceEvent) -> bool:
    material = [item for item in events if abs(item.divergence_bps) > 0 and item.divergence_direction != "equal"]
    if len(material) < 3:
        return False
    same_direction = sum(1 for item in material if item.divergence_direction == event.divergence_direction)
    return same_direction / len(material) >= 0.8
