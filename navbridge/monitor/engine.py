from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from navbridge.administrator.base import AdministratorAdapter
from navbridge.classifier.engine import BreakClassifier, severity
from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceDirection, DivergenceEvent
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord
from navbridge.core.report import DivergenceReport
from navbridge.oracle.base import OracleAdapter
from navbridge.reporter.policy_advisor import recommend_tolerance_bps


class MonitorEngine:
    def __init__(
        self,
        config: FundConfig,
        oracle: OracleAdapter,
        administrator: AdministratorAdapter,
        classifier: BreakClassifier,
    ) -> None:
        self.config = config
        self.oracle = oracle
        self.administrator = administrator
        self.classifier = classifier

    def run(self, start: datetime, end: datetime, advise_policy: bool = False) -> DivergenceReport:
        oracle_records = sorted(self.oracle.get_nav_series(start, end), key=lambda item: item.timestamp)
        administrator_records = sorted(self.administrator.get_nav_series(start, end), key=lambda item: item.timestamp)
        events = [self._event_for(admin, oracle_records) for admin in administrator_records]
        events = self.classifier.classify(events)
        distribution = Counter(event.break_type for event in events if event.break_type is not None)
        magnitudes = [abs(event.divergence_bps) for event in events]
        report = DivergenceReport(
            fund_id=self.config.fund_id,
            report_window_start=start,
            report_window_end=end,
            total_observations=len(events),
            total_breaks=sum(1 for value in magnitudes if value > 0),
            material_breaks=sum(1 for event in events if event.severity in {"material", "critical"}),
            critical_breaks=sum(1 for event in events if event.severity == "critical"),
            mean_divergence_bps=sum(magnitudes) / len(magnitudes) if magnitudes else 0.0,
            max_divergence_bps=max(magnitudes) if magnitudes else 0.0,
            break_type_distribution=dict(distribution),
            policy_compliance=all(value <= self.config.tolerance_bps for value in magnitudes),
            events=events,
            recommended_tolerance_bps=recommend_tolerance_bps(events) if advise_policy else None,
            generated_at=datetime.now(UTC),
        )
        return report

    def _event_for(self, admin: NavRecord, oracle_records: list[NavRecord]) -> DivergenceEvent:
        oracle = self._nearest_oracle(admin, oracle_records)
        if oracle is None:
            oracle = NavRecord(
                fund_id=admin.fund_id,
                source="oracle",
                timestamp=admin.timestamp,
                nav_per_unit=Decimal("0"),
                currency=admin.currency,
                metadata={"alignment_failure": True},
            )
        signed = float((oracle.nav_per_unit - admin.nav_per_unit) / admin.nav_per_unit * Decimal("10000"))
        return DivergenceEvent(
            fund_id=admin.fund_id,
            oracle_record=oracle,
            administrator_record=admin,
            divergence_bps=signed,
            divergence_direction=_direction(signed),
            break_type=BreakType.DATA_FEED_FAILURE if oracle.nav_per_unit == 0 else None,
            severity=severity(signed, self.config),
            classification_confidence=0.0,
            notes="Unclassified before rule evaluation.",
        )

    def _nearest_oracle(self, admin: NavRecord, oracle_records: list[NavRecord]) -> NavRecord | None:
        window = timedelta(minutes=self.config.alignment_window_minutes)
        candidates = [
            item
            for item in oracle_records
            if item.fund_id == admin.fund_id
            and item.currency == admin.currency
            and abs(item.timestamp - admin.timestamp) <= window
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: abs(item.timestamp - admin.timestamp))


def _direction(signed_bps: float) -> DivergenceDirection:
    if signed_bps > 0:
        return "oracle_above"
    if signed_bps < 0:
        return "oracle_below"
    return "equal"
