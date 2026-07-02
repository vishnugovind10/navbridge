from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceEvent
from navbridge.core.nav_record import format_utc_datetime, parse_utc_datetime
from navbridge.core.schema import REPORT_SCHEMA_VERSION


@dataclass
class DivergenceReport:
    fund_id: str
    report_window_start: datetime
    report_window_end: datetime
    total_observations: int
    total_breaks: int
    material_breaks: int
    critical_breaks: int
    mean_divergence_bps: float
    max_divergence_bps: float
    break_type_distribution: dict[BreakType, int]
    policy_compliance: bool
    events: list[DivergenceEvent] = field(default_factory=list)
    recommended_tolerance_bps: float | None = None
    generated_at: datetime | None = None
    schema_version: str = REPORT_SCHEMA_VERSION
    run_id: str | None = None
    input_record_counts: dict[str, int] = field(default_factory=dict)
    monitor_parameters: dict[str, Any] = field(default_factory=dict)
    config_snapshot: dict[str, Any] = field(default_factory=dict)
    policy_pack: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DivergenceReport":
        return cls(
            fund_id=payload["fund_id"],
            report_window_start=parse_utc_datetime(payload["report_window_start"]),
            report_window_end=parse_utc_datetime(payload["report_window_end"]),
            total_observations=int(payload["total_observations"]),
            total_breaks=int(payload["total_breaks"]),
            material_breaks=int(payload["material_breaks"]),
            critical_breaks=int(payload["critical_breaks"]),
            mean_divergence_bps=float(payload["mean_divergence_bps"]),
            max_divergence_bps=float(payload["max_divergence_bps"]),
            break_type_distribution={
                BreakType(key): int(value)
                for key, value in payload.get("break_type_distribution", {}).items()
            },
            policy_compliance=bool(payload["policy_compliance"]),
            events=[DivergenceEvent.from_dict(item) for item in payload.get("events", [])],
            recommended_tolerance_bps=payload.get("recommended_tolerance_bps"),
            generated_at=parse_utc_datetime(payload["generated_at"])
            if payload.get("generated_at")
            else None,
            schema_version=payload.get("schema_version", REPORT_SCHEMA_VERSION),
            run_id=payload.get("run_id"),
            input_record_counts=dict(payload.get("input_record_counts", {})),
            monitor_parameters=dict(payload.get("monitor_parameters", {})),
            config_snapshot=dict(payload.get("config_snapshot", {})),
            policy_pack=payload.get("policy_pack"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "fund_id": self.fund_id,
            "report_window_start": format_utc_datetime(self.report_window_start),
            "report_window_end": format_utc_datetime(self.report_window_end),
            "input_record_counts": self.input_record_counts,
            "monitor_parameters": self.monitor_parameters,
            "config_snapshot": self.config_snapshot,
            "policy_pack": self.policy_pack,
            "total_observations": self.total_observations,
            "total_breaks": self.total_breaks,
            "material_breaks": self.material_breaks,
            "critical_breaks": self.critical_breaks,
            "mean_divergence_bps": round(self.mean_divergence_bps, 6),
            "max_divergence_bps": round(self.max_divergence_bps, 6),
            "break_type_distribution": {
                break_type.value: count
                for break_type, count in self.break_type_distribution.items()
            },
            "policy_compliance": self.policy_compliance,
            "events": [event.to_dict() for event in self.events],
            "recommended_tolerance_bps": self.recommended_tolerance_bps,
            "generated_at": format_utc_datetime(self.generated_at) if self.generated_at else None,
        }
