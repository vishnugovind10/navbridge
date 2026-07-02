from datetime import UTC, datetime, time
from decimal import Decimal

import pytest

from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceEvent
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord
from navbridge.core.report import DivergenceReport


def test_fund_config_round_trip() -> None:
    config = FundConfig(
        fund_id="FUND_001",
        fund_type="money_market",
        base_currency="USD",
        nav_frequency="daily",
        market_timezone="America/New_York",
        market_open=time(9, 30),
        market_close=time(16, 0),
    )
    assert FundConfig.from_dict(config.to_dict()) == config


def test_nav_record_requires_utc() -> None:
    with pytest.raises(ValueError):
        NavRecord("FUND_001", "oracle", datetime(2026, 1, 1), Decimal("1.0"), "USD", {})


def test_report_round_trip() -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    oracle = NavRecord("FUND_001", "oracle", timestamp, Decimal("1.001"), "USD", {})
    admin = NavRecord("FUND_001", "administrator", timestamp, Decimal("1.000"), "USD", {})
    event = DivergenceEvent(
        "FUND_001",
        oracle,
        admin,
        10.0,
        "oracle_above",
        BreakType.METHODOLOGY_DRIFT,
        "critical",
        1.0,
        "test",
    )
    report = DivergenceReport(
        fund_id="FUND_001",
        report_window_start=timestamp,
        report_window_end=timestamp,
        total_observations=1,
        total_breaks=1,
        material_breaks=1,
        critical_breaks=1,
        mean_divergence_bps=10.0,
        max_divergence_bps=10.0,
        break_type_distribution={BreakType.METHODOLOGY_DRIFT: 1},
        policy_compliance=False,
        events=[event],
        generated_at=timestamp,
    )
    assert DivergenceReport.from_dict(report.to_dict()).events[0].break_type == BreakType.METHODOLOGY_DRIFT
