from enum import Enum


class BreakType(Enum):
    TIMING_DRIFT = "timing_drift"
    METHODOLOGY_DRIFT = "methodology_drift"
    MARKET_HOURS_ASYMMETRY = "market_hours_asymmetry"
    CORPORATE_ACTION_LAG = "corporate_action_lag"
    DATA_FEED_FAILURE = "data_feed_failure"
