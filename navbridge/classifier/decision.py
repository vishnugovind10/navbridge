from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from navbridge.classifier.types import BreakType


CLASSIFIER_RULESET_VERSION = "navbridge.classifier.rules.v1"


@dataclass(frozen=True)
class ClassificationDecision:
    break_type: BreakType | None
    confidence: float
    notes: str
    rule_id: str
    evidence: dict[str, Any] = field(default_factory=dict)
