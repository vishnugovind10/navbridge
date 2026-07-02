from datetime import UTC, datetime, time
from decimal import Decimal
import json
from pathlib import Path

import pytest

from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.administrator.base import AdministratorAdapter
from navbridge.classifier.engine import BreakClassifier
from navbridge.classifier.types import BreakType
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord
from navbridge.monitor.engine import MonitorEngine
from navbridge.monitor.engine import MonitorEngineError
from navbridge.oracle.base import OracleAdapter
from navbridge.oracle.simulated import SimulatedOracle, get_drift_model


def _run_example(folder: str, drift: str):
    root = Path(__file__).resolve().parents[1] / "examples" / folder
    config = FundConfig.from_dict(json.loads((root / "config.json").read_text(encoding="utf-8")))
    admin = CsvAdministratorIngester(root / "administrator_nav.csv", config.fund_id, config.base_currency)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC)
    first = admin.get_nav_series(start, end)[0]
    oracle = SimulatedOracle(config, first.nav_per_unit.quantize(Decimal("0.000001")), config.oracle_update_frequency_minutes, get_drift_model(drift), seed=42)
    return MonitorEngine(config, oracle, admin, BreakClassifier(config)).run(start, end, advise_policy=True)


def test_mmf_scenario_produces_market_hours_breaks() -> None:
    report = _run_example("mmf_scenario", "BUIDL_STYLE")
    assert report.total_observations == 31
    assert report.break_type_distribution[BreakType.MARKET_HOURS_ASYMMETRY] >= 8
    assert report.schema_version == "navbridge.report.v1"
    assert report.run_id
    assert report.input_record_counts["aligned"] == 31
    assert report.monitor_parameters["alignment_window_minutes"] == 30


def test_market_hours_scenario_detects_feed_failure() -> None:
    report = _run_example("market_hours_scenario", "MARKET_HOURS_STRESS")
    assert report.break_type_distribution[BreakType.DATA_FEED_FAILURE] >= 1
    assert report.critical_breaks >= 1


def test_monitor_rejects_invalid_windows() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "mmf_scenario"
    config = FundConfig.from_dict(json.loads((root / "config.json").read_text(encoding="utf-8")))
    admin = CsvAdministratorIngester(root / "administrator_nav.csv", config.fund_id, config.base_currency)
    oracle = SimulatedOracle(config, Decimal("1"), config.oracle_update_frequency_minutes, get_drift_model("BUIDL_STYLE"), seed=42)
    engine = MonitorEngine(config, oracle, admin, BreakClassifier(config))

    with pytest.raises(MonitorEngineError):
        engine.run(datetime(2026, 1, 2, tzinfo=UTC), datetime(2026, 1, 1, tzinfo=UTC))


def test_monitor_rejects_duplicate_adapter_timestamps() -> None:
    config = FundConfig(
        "FUND_001",
        "money_market",
        "USD",
        "daily",
        "America/New_York",
        time(9, 30),
        time(16, 0),
    )
    timestamp = datetime(2026, 1, 1, 21, tzinfo=UTC)
    admin = _StaticAdministrator([
        NavRecord("FUND_001", "administrator", timestamp, Decimal("1.0"), "USD", {}),
    ])
    oracle = _StaticOracle([
        NavRecord("FUND_001", "oracle", timestamp, Decimal("1.0"), "USD", {}),
        NavRecord("FUND_001", "oracle", timestamp, Decimal("1.0"), "USD", {}),
    ])

    with pytest.raises(MonitorEngineError, match="duplicate timestamp"):
        MonitorEngine(config, oracle, admin, BreakClassifier(config)).run(
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        )


class _StaticOracle(OracleAdapter):
    def __init__(self, records: list[NavRecord]) -> None:
        self.records = records

    def get_nav_series(self, start: datetime, end: datetime) -> list[NavRecord]:
        return self.records


class _StaticAdministrator(AdministratorAdapter):
    def __init__(self, records: list[NavRecord]) -> None:
        self.records = records

    def get_nav_series(self, start: datetime, end: datetime) -> list[NavRecord]:
        return self.records
