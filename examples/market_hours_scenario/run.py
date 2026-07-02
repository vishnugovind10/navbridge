from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from navbridge.cli import main

raise SystemExit(main([
    "monitor",
    "--config", str(Path(__file__).with_name("config.json")),
    "--oracle", "simulated",
    "--drift-model", "MARKET_HOURS_STRESS",
    "--admin-file", str(Path(__file__).with_name("administrator_nav.csv")),
    "--start", "2026-01-01",
    "--end", "2026-01-09",
    "--output-json", str(ROOT / "reports" / "market_hours_stress.json"),
    "--output-md", str(ROOT / "reports" / "market_hours_stress.md"),
    "--advise-policy",
]))
