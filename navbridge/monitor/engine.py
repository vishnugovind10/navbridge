from __future__ import annotations

from bisect import bisect_left
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from navbridge.administrator.base import AdministratorAdapter
from navbridge.classifier.engine import BreakClassifier, severity
from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceDirection, DivergenceEvent
from navbridge.core.fund import FundConfig
from navbridge.core.nav_record import NavRecord
from navbridge.core.report import DivergenceReport
from navbridge.core.schema import RUN_ID_ALGORITHM, stable_digest
from navbridge.oracle.base import OracleAdapter
from navbridge.reporter.policy_advisor import recommend_tolerance_bps
from navbridge.validation.contracts import validate_nav_records


class MonitorEngineError(ValueError):
    """Raised when monitor inputs violate NavBridge runtime contracts."""


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
        if start >= end:
            raise MonitorEngineError("monitor start must be before end")
        start = start.astimezone(UTC)
        end = end.astimezone(UTC)
        oracle_records = sorted(self.oracle.get_nav_series(start, end), key=lambda item: item.timestamp)
        administrator_records = sorted(self.administrator.get_nav_series(start, end), key=lambda item: item.timestamp)
        self._validate_records(oracle_records, source="oracle")
        self._validate_records(administrator_records, source="administrator")
        oracle_index = _OracleIndex.from_records(oracle_records)
        events = [self._event_for(admin, oracle_index) for admin in administrator_records]
        events = self.classifier.classify(events)
        distribution = Counter(event.break_type for event in events if event.break_type is not None)
        magnitudes = [abs(event.divergence_bps) for event in events]
        run_id = stable_digest(
            {
                "fund_id": self.config.fund_id,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "config": self.config.to_dict(),
                "oracle_records": len(oracle_records),
                "administrator_records": len(administrator_records),
                "run_id_algorithm": RUN_ID_ALGORITHM,
            }
        )
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
            run_id=run_id,
            input_record_counts={
                "oracle": len(oracle_records),
                "administrator": len(administrator_records),
                "aligned": len(events),
            },
            monitor_parameters={
                "alignment_window_minutes": self.config.alignment_window_minutes,
                "oracle_update_frequency_minutes": self.config.oracle_update_frequency_minutes,
                "run_id_algorithm": RUN_ID_ALGORITHM,
                "advise_policy": advise_policy,
            },
            config_snapshot=self.config.to_dict(),
            policy_pack=self.config.policy,
        )
        return report

    def _event_for(self, admin: NavRecord, oracle_index: "_OracleIndex") -> DivergenceEvent:
        oracle = self._nearest_oracle(admin, oracle_index)
        if oracle is None:
            oracle = NavRecord(
                fund_id=admin.fund_id,
                source="oracle",
                timestamp=admin.timestamp,
                nav_per_unit=Decimal("0"),
                currency=admin.currency,
                metadata={
                    "alignment_failure": True,
                    "alignment_window_minutes": self.config.alignment_window_minutes,
                },
            )
        else:
            oracle = NavRecord(
                fund_id=oracle.fund_id,
                source=oracle.source,
                timestamp=oracle.timestamp,
                nav_per_unit=oracle.nav_per_unit,
                currency=oracle.currency,
                metadata={
                    **oracle.metadata,
                    "alignment_delta_seconds": int(abs((oracle.timestamp - admin.timestamp).total_seconds())),
                    "alignment_window_minutes": self.config.alignment_window_minutes,
                },
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

    def _nearest_oracle(self, admin: NavRecord, oracle_index: "_OracleIndex") -> NavRecord | None:
        window = timedelta(minutes=self.config.alignment_window_minutes)
        candidates = oracle_index.nearest_candidates(admin.timestamp)
        candidates = [
            item
            for item in candidates
            if item.fund_id == admin.fund_id
            and item.currency == admin.currency
            and abs(item.timestamp - admin.timestamp) <= window
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: abs(item.timestamp - admin.timestamp))

    def _validate_records(self, records: list[NavRecord], source: str) -> None:
        result = validate_nav_records(
            records,
            expected_source=source,
            expected_fund_id=self.config.fund_id,
            expected_currency=self.config.base_currency,
            require_non_empty=False,
            allow_zero_nav=source == "oracle",
        )
        errors = [issue for issue in result.issues if issue.severity == "error"]
        if errors:
            first = errors[0]
            raise MonitorEngineError(f"{source} adapter contract failed ({first.code}): {first.message}")


def _direction(signed_bps: float) -> DivergenceDirection:
    if signed_bps > 0:
        return "oracle_above"
    if signed_bps < 0:
        return "oracle_below"
    return "equal"


@dataclass(frozen=True)
class _OracleIndex:
    timestamps: list[datetime]
    records: list[NavRecord]

    @classmethod
    def from_records(cls, records: list[NavRecord]) -> "_OracleIndex":
        return cls([record.timestamp for record in records], records)

    def nearest_candidates(self, timestamp: datetime) -> list[NavRecord]:
        if not self.records:
            return []
        index = bisect_left(self.timestamps, timestamp)
        candidates: list[NavRecord] = []
        if index < len(self.records):
            candidates.append(self.records[index])
        if index > 0:
            candidates.append(self.records[index - 1])
        return candidates
