from datetime import UTC, datetime, time
from decimal import Decimal

from navbridge.classifier.engine import BreakClassifier
from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceEvent
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord


def _config() -> FundConfig:
    return FundConfig(
        fund_id="FUND_001",
        fund_type="treasury_bond",
        base_currency="USD",
        nav_frequency="intraday",
        market_timezone="America/New_York",
        market_open=time(9, 30),
        market_close=time(16, 0),
    )


def _event(metadata=None, timestamp=datetime(2026, 1, 8, 15, tzinfo=UTC), bps=3.0) -> DivergenceEvent:
    admin = NavRecord("FUND_001", "administrator", timestamp, Decimal("100.00"), "USD", {})
    oracle = NavRecord("FUND_001", "oracle", timestamp, Decimal("100.03"), "USD", metadata or {"timing_lag_minutes": 60})
    return DivergenceEvent("FUND_001", oracle, admin, bps, "oracle_above", None, "warning", 0.0, "")


def test_data_feed_failure_rule() -> None:
    event = _event({"stale_duration_minutes": 180})
    assert BreakClassifier(_config()).classify([event])[0].break_type == BreakType.DATA_FEED_FAILURE


def test_corporate_action_rule() -> None:
    event = _event({"corporate_action_delay": True})
    assert BreakClassifier(_config()).classify([event])[0].break_type == BreakType.CORPORATE_ACTION_LAG


def test_market_hours_rule() -> None:
    event = _event(timestamp=datetime(2026, 1, 10, 21, tzinfo=UTC))
    assert BreakClassifier(_config()).classify([event])[0].break_type == BreakType.MARKET_HOURS_ASYMMETRY


def test_clean_data_has_no_break_type() -> None:
    event = _event(bps=0.0)
    event.divergence_direction = "equal"
    event.oracle_record = NavRecord("FUND_001", "oracle", event.oracle_record.timestamp, Decimal("100.00"), "USD", {})
    assert BreakClassifier(_config()).classify([event])[0].break_type is None
