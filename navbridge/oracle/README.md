# Oracle Adapters

V1 ships only `SimulatedOracle`.

Future live adapters should implement `OracleAdapter.get_nav_series(start, end)` and return UTC `NavRecord` objects. Do not perform network calls at import time.
