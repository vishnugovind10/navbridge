from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from navbridge.core.nav_record import NavRecord


class OracleAdapter(ABC):
    @abstractmethod
    def get_nav_series(self, start: datetime, end: datetime) -> list[NavRecord]:
        raise NotImplementedError
