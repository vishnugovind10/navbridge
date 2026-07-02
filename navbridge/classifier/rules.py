from __future__ import annotations

from zoneinfo import ZoneInfo

from navbridge.classifier.decision import ClassificationDecision
from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceEvent
from navbridge.core.fund import FundConfig


def classify_event(event: DivergenceEvent, config: FundConfig, all_events: list[DivergenceEvent]) -> ClassificationDecision:
    magnitude = abs(event.divergence_bps)
    if abs(event.divergence_bps) == 0:
        return ClassificationDecision(
            None,
            1.0,
            "Oracle and administrator NAV are equal.",
            "clean_equal_nav",
            {"divergence_bps": event.divergence_bps},
        )
    stale_minutes = event.oracle_record.metadata.get("stale_duration_minutes")
    if stale_minutes is not None and stale_minutes > 2 * config.oracle_update_frequency_minutes:
        threshold_minutes = 2 * config.oracle_update_frequency_minutes
        return ClassificationDecision(
            BreakType.DATA_FEED_FAILURE,
            1.0,
            "Oracle NAV stayed stale beyond 2x the configured update interval.",
            "data_feed_failure_stale_nav",
            {"stale_minutes": stale_minutes, "threshold_minutes": threshold_minutes},
        )
    if event.oracle_record.nav_per_unit == 0:
        return ClassificationDecision(
            BreakType.DATA_FEED_FAILURE,
            1.0,
            "Oracle NAV was zero.",
            "data_feed_failure_zero_nav",
            {"oracle_nav_per_unit": str(event.oracle_record.nav_per_unit)},
        )
    if event.oracle_record.metadata.get("corporate_action_delay"):
        return ClassificationDecision(
            BreakType.CORPORATE_ACTION_LAG,
            1.0,
            "Divergence coincided with the simulated corporate action delay window.",
            "corporate_action_delay_window",
            {"corporate_action_delay": True},
        )
    is_market_open = _is_market_open(config, event.administrator_record.timestamp)
    if not is_market_open:
        return ClassificationDecision(
            BreakType.MARKET_HOURS_ASYMMETRY,
            0.9,
            "Divergence was observed outside configured market hours.",
            "market_hours_closed",
            {
                "market_timezone": config.market_timezone,
                "market_open": config.market_open.isoformat(timespec="minutes"),
                "market_close": config.market_close.isoformat(timespec="minutes"),
                "administrator_timestamp": event.administrator_record.timestamp.isoformat(),
            },
        )
    persistent_ratio = _persistent_same_direction_ratio(all_events, event)
    if persistent_ratio >= 0.8:
        return ClassificationDecision(
            BreakType.METHODOLOGY_DRIFT,
            0.8,
            "Divergence was directionally consistent across market-hours observations.",
            "methodology_persistent_direction",
            {"same_direction_ratio": round(persistent_ratio, 6), "threshold_ratio": 0.8},
        )
    if event.oracle_record.metadata.get("timing_lag_minutes", 0) > 0:
        return ClassificationDecision(
            BreakType.TIMING_DRIFT,
            0.8,
            "Divergence was observed inside market hours with a configured oracle timing lag.",
            "timing_lag_configured",
            {"timing_lag_minutes": event.oracle_record.metadata.get("timing_lag_minutes"), "divergence_bps": magnitude},
        )
    return ClassificationDecision(
        BreakType.TIMING_DRIFT,
        0.5,
        "Divergence was present but did not match a stronger rule.",
        "timing_drift_fallback",
        {"divergence_bps": magnitude},
    )


def _is_market_open(config: FundConfig, timestamp) -> bool:
    local = timestamp.astimezone(ZoneInfo(config.market_timezone))
    if local.weekday() >= 5:
        return False
    return config.market_open <= local.time() <= config.market_close


def _persistent_same_direction_ratio(events: list[DivergenceEvent], event: DivergenceEvent) -> float:
    material = [item for item in events if abs(item.divergence_bps) > 0 and item.divergence_direction != "equal"]
    if len(material) < 3:
        return 0.0
    same_direction = sum(1 for item in material if item.divergence_direction == event.divergence_direction)
    return same_direction / len(material)
