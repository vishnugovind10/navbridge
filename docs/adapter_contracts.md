# Adapter Contracts

NavBridge adapters are intentionally small so institutions can replace V1 file/simulation sources with internal systems.

## OracleAdapter

Implement:

```python
def get_nav_series(start: datetime, end: datetime) -> list[NavRecord]:
    ...
```

Required behavior:

- Return `NavRecord` objects with `source="oracle"`.
- Return UTC timestamps.
- Return records for one fund and one currency per monitor run.
- Do not return duplicate timestamps for the same fund and currency.
- Do not perform network calls at import time.
- Put provenance in `metadata`, for example `feed_id`, `provider`, `update_tx`, `block_number`, or `observed_at`.

## AdministratorAdapter

Implement:

```python
def get_nav_series(start: datetime, end: datetime) -> list[NavRecord]:
    ...
```

Required behavior:

- Return `NavRecord` objects with `source="administrator"`.
- Return UTC timestamps.
- Preserve calculation method and source-file lineage in `metadata`.
- Raise a typed adapter error for malformed input.
- Keep any institution-specific transformation outside the monitor engine.

## Monitor Enforcement

`MonitorEngine` rejects records with the wrong source, wrong fund ID, wrong currency, duplicate timestamps, or invalid time windows. That enforcement is deliberate: adapter failures should be visible at the boundary rather than appearing as ordinary NAV breaks.
