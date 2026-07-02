from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from navbridge.classifier.types import BreakType
from navbridge.core.nav_record import NavRecord


DivergenceDirection = Literal["oracle_above", "oracle_below", "equal"]
Severity = Literal["negligible", "within_tolerance", "warning", "material", "critical"]


@dataclass
class DivergenceEvent:
    fund_id: str
    oracle_record: NavRecord
    administrator_record: NavRecord
    divergence_bps: float
    divergence_direction: DivergenceDirection
    break_type: BreakType | None
    severity: Severity
    classification_confidence: float
    notes: str
    classification_rule_id: str | None = None
    classification_ruleset_version: str | None = None
    classification_evidence: dict[str, Any] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DivergenceEvent":
        return cls(
            fund_id=payload["fund_id"],
            oracle_record=NavRecord.from_dict(payload["oracle_record"]),
            administrator_record=NavRecord.from_dict(payload["administrator_record"]),
            divergence_bps=float(payload["divergence_bps"]),
            divergence_direction=payload["divergence_direction"],
            break_type=BreakType(payload["break_type"]) if payload.get("break_type") else None,
            severity=payload["severity"],
            classification_confidence=float(payload["classification_confidence"]),
            notes=payload["notes"],
            classification_rule_id=payload.get("classification_rule_id"),
            classification_ruleset_version=payload.get("classification_ruleset_version"),
            classification_evidence=dict(payload.get("classification_evidence", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fund_id": self.fund_id,
            "oracle_record": self.oracle_record.to_dict(),
            "administrator_record": self.administrator_record.to_dict(),
            "divergence_bps": round(self.divergence_bps, 6),
            "divergence_direction": self.divergence_direction,
            "break_type": self.break_type.value if self.break_type else None,
            "severity": self.severity,
            "classification_confidence": self.classification_confidence,
            "classification_rule_id": self.classification_rule_id,
            "classification_ruleset_version": self.classification_ruleset_version,
            "classification_evidence": self.classification_evidence or {},
            "notes": self.notes,
        }
