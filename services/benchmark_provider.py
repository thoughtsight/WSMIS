from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BenchmarkProvider(ABC):
    """
    Interface for providing business thresholds and benchmarks.
    Allows decoupling benchmark retrieval from hardcoded settings or DB calls.
    """
    @abstractmethod
    def get_benchmark(self, key: str) -> Any:
        pass


class DefaultBenchmarkProvider(BenchmarkProvider):
    """
    Default implementation that reads from config.settings.
    """
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        self.overrides = overrides or {}
        # Lazy import to avoid circular dependency issues
        from config.settings import LABOUR_DISC_BENCH, HIGH_DISC_ALERT, YOY_DECLINE_ALERT, VOR_ALERT_THRESHOLD
        self._defaults = {
            "labour_discount_target": LABOUR_DISC_BENCH,
            "high_discount_alert": HIGH_DISC_ALERT,
            "yoy_decline_alert": YOY_DECLINE_ALERT,
            "vor_alert_threshold": VOR_ALERT_THRESHOLD,
        }

    def get_benchmark(self, key: str) -> Any:
        if key in self.overrides:
            return self.overrides[key]
        if key in self._defaults:
            return self._defaults[key]
        raise KeyError(f"Benchmark key '{key}' not found in DefaultBenchmarkProvider.")
