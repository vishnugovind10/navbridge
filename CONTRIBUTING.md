# Contributing

NavBridge is intentionally small. Keep pull requests scoped to one behavior change, one adapter, or one documentation improvement.

## Local Setup

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Standards

- Keep core logic dependency-light.
- Add or update tests for classifier, ingestion, monitor, and reporter changes.
- Keep JSON report fields stable unless a versioned schema change is documented.
- Prefer explicit rule functions over opaque scoring or ML classifiers.
- Document production limitations when adding new adapters.

## Good First Issues

- Add more administrator-file mapping examples.
- Improve documentation for real-world tolerance policies.
- Add additional deterministic drift presets.
- Add live oracle adapter stubs without enabling network calls by default.
