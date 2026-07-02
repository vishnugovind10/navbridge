# Administrator Adapters

V1 ships CSV and JSON ingesters for the NavBridge administrator NAV schema.

Production administrator files should be transformed into this schema before ingestion. Adapter errors should raise `NavIngestionError` with a clear message instead of leaking parser exceptions.
