from datetime import UTC, datetime, time
from decimal import Decimal

from navbridge.administrator.csv_ingester import CsvAdministratorIngester
from navbridge.classifier.engine import BreakClassifier
from navbridge.core.fund import FundConfig
from navbridge.core.report import DivergenceReport
from navbridge.monitor.engine import MonitorEngine
from navbridge.oracle.simulated import SimulatedOracle, get_drift_model
from navbridge.reporter.json_reporter import report_to_json
from navbridge.reporter.markdown_reporter import report_to_markdown
from navbridge.reporter.audit_manifest import AUDIT_MANIFEST_SCHEMA_VERSION


def test_reporters_emit_round_trippable_json_and_required_markdown(tmp_path) -> None:
    csv_path = tmp_path / "nav.csv"
    csv_path.write_text("fund_id,timestamp_utc,nav_per_unit,currency\nFUND_001,2026-01-01T21:00:00Z,1.0,USD\n", encoding="utf-8")
    config = FundConfig(
        "FUND_001",
        "money_market",
        "USD",
        "daily",
        "America/New_York",
        time(9, 30),
        time(16, 0),
    )
    admin = CsvAdministratorIngester(csv_path, config.fund_id, config.base_currency)
    oracle = SimulatedOracle(config, Decimal("1"), 60, get_drift_model("BUIDL_STYLE"), seed=42)
    report = MonitorEngine(config, oracle, admin, BreakClassifier(config)).run(
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 2, tzinfo=UTC),
        advise_policy=True,
    )
    assert DivergenceReport.from_dict(__import__("json").loads(report_to_json(report))).fund_id == "FUND_001"
    markdown = report_to_markdown(report)
    assert "Run ID" in markdown
    assert "## Summary" in markdown
    assert "## Break Distribution" in markdown
    assert "## Material Breaks" in markdown
    assert AUDIT_MANIFEST_SCHEMA_VERSION == "navbridge.audit_manifest.v1"
