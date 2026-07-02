from datetime import UTC, datetime, time
from decimal import Decimal

from navbridge.core.fund import FundConfig
from navbridge.oracle.simulated import DRIFT_PRESETS, SimulatedOracle


def _config() -> FundConfig:
    return FundConfig(
        fund_id="FUND_STRESS",
        fund_type="treasury_bond",
        base_currency="USD",
        nav_frequency="intraday",
        market_timezone="America/New_York",
        market_open=time(9, 30),
        market_close=time(16, 0),
    )


def test_simulated_oracle_is_deterministic() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)
    first = SimulatedOracle(_config(), Decimal("100"), 60, DRIFT_PRESETS["ONDO_STYLE"], seed=42).get_nav_series(start, end)
    second = SimulatedOracle(_config(), Decimal("100"), 60, DRIFT_PRESETS["ONDO_STYLE"], seed=42).get_nav_series(start, end)
    assert [item.nav_per_unit for item in first] == [item.nav_per_unit for item in second]


def test_feed_failure_metadata_is_emitted() -> None:
    start = datetime(2026, 1, 8, 13, tzinfo=UTC)
    end = datetime(2026, 1, 8, 18, tzinfo=UTC)
    series = SimulatedOracle(_config(), Decimal("100"), 60, DRIFT_PRESETS["MARKET_HOURS_STRESS"], seed=42).get_nav_series(start, end)
    stale = [item for item in series if item.metadata.get("stale_duration_minutes", 0) > 120]
    assert stale
