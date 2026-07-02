from __future__ import annotations

import hashlib
import json
from typing import Any


REPORT_SCHEMA_VERSION = "navbridge.report.v1"
RUN_ID_ALGORITHM = "sha256-16"


def stable_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
