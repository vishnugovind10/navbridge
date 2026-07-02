from __future__ import annotations

from navbridge.classifier.decision import CLASSIFIER_RULESET_VERSION
from navbridge.classifier.rules import classify_event
from navbridge.classifier.types import BreakType
from navbridge.core.divergence import DivergenceEvent, Severity
from navbridge.core.fund import FundConfig


def severity(divergence_bps: float, config: FundConfig) -> Severity:
    magnitude = abs(divergence_bps)
    if magnitude == 0:
        return "negligible"
    if magnitude <= config.tolerance_bps:
        return "within_tolerance"
    if magnitude <= min(config.materiality_bps, config.tolerance_bps * 2):
        return "warning"
    if magnitude <= config.materiality_bps:
        return "material"
    return "critical"


class BreakClassifier:
    def __init__(self, config: FundConfig) -> None:
        self.config = config

    def classify(self, events: list[DivergenceEvent]) -> list[DivergenceEvent]:
        classified: list[DivergenceEvent] = []
        for event in events:
            decision = classify_event(event, self.config, events)
            event.break_type = decision.break_type
            event.classification_confidence = decision.confidence
            event.notes = decision.notes
            event.classification_rule_id = decision.rule_id
            event.classification_ruleset_version = CLASSIFIER_RULESET_VERSION
            event.classification_evidence = {
                **decision.evidence,
                "tolerance_bps": self.config.tolerance_bps,
                "materiality_bps": self.config.materiality_bps,
            }
            event.severity = "critical" if decision.break_type == BreakType.DATA_FEED_FAILURE else severity(event.divergence_bps, self.config)
            classified.append(event)
        return classified
