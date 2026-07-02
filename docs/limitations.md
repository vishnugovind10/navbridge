# Limitations

V1 is simulation-first.

- Oracle data is simulated. There are no live Chainlink, RedStone, Pyth, or custom oracle reads.
- Administrator NAV input must already be mapped to the NavBridge CSV or JSON schema.
- The classifier rules are heuristic and auditable, but not exhaustive.
- Alignment uses nearest timestamp matching within `alignment_window_minutes`. If no oracle record is found inside the window, NavBridge creates a zero-NAV failure event and classifies it as `data_feed_failure`.
- Report schema v1 is stable for V1 fields, but the project is still pre-1.0. Breaking schema changes should be versioned as a new schema file.
- Single share class funds are supported. Multi-share-class funds are deferred.
- No database, auth, alerting, dashboard, or multi-user backend is included.

The alignment window is the most likely source of spurious breaks in production. Teams should validate timestamp conventions for oracle feeds, administrator files, and market close calculations before using reports as audit evidence.
