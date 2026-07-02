from datetime import UTC, datetime

from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.classifier.engine import BreakClassifier
from navbridge.classifier.types import BreakType
from navbridge.core.fund import FundConfig
from navbridge.monitor.engine import MonitorEngine
from navbridge.oracle.simulated import SimulatedOracle, get_drift_model


def _run_example(folder: str, drift: str):
    import json
    from decimal import Decimal
    from pathlib import Path

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


def test_market_hours_scenario_detects_feed_failure() -> None:
    report = _run_example("market_hours_scenario", "MARKET_HOURS_STRESS")
    assert report.break_type_distribution[BreakType.DATA_FEED_FAILURE] >= 1
    assert report.critical_breaks >= 1
