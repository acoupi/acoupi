"""Path constants for acoupi system."""
import os
from pathlib import Path

ACOUPI_HOME = Path(os.environ.get("ACOUPI_HOME", str(Path.home() / ".acoupi")))

PROGRAM_PATH = ACOUPI_HOME / "app.py"
CONFIG_PATH = ACOUPI_HOME / "config.json"
