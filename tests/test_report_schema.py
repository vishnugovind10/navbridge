import json
from datetime import UTC, datetime
from pathlib import Path

from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.classifier.engine import BreakClassifier
from navbridge.core.fund import FundConfig
from navbridge.monitor.engine import MonitorEngine
from navbridge.oracle.simulated import SimulatedOracle, get_drift_model
from navbridge.reporter.json_reporter import report_to_json


def test_json_report_contains_schema_required_fields() -> None:
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "docs" / "report_schema_v1.json").read_text(encoding="utf-8"))
    example = root / "examples" / "mmf_scenario"
    config = FundConfig.from_dict(json.loads((example / "config.json").read_text(encoding="utf-8")))
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, 23, 59, 59, tzinfo=UTC)
    admin = CsvAdministratorIngester(example / "administrator_nav.csv", config.fund_id, config.base_currency)
    first = admin.get_nav_series(start, end)[0]
    oracle = SimulatedOracle(config, first.nav_per_unit, config.oracle_update_frequency_minutes, get_drift_model("BUIDL_STYLE"), seed=42)
    report = MonitorEngine(config, oracle, admin, BreakClassifier(config)).run(start, end, advise_policy=True)
    payload = json.loads(report_to_json(report))

    for field in schema["required"]:
        assert field in payload
    assert payload["schema_version"] == "navbridge.report.v1"
    assert payload["input_record_counts"]["aligned"] == payload["total_observations"]
    assert payload["monitor_parameters"]["alignment_window_minutes"] == config.alignment_window_minutes
