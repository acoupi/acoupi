"""Path constants for acoupi system."""
import os
from pathlib import Path

ACOUPI_HOME = Path(os.environ.get("ACOUPI_HOME", str(Path.home() / ".acoupi")))
APP_NAME = "app"
PROGRAM_PATH = ACOUPI_HOME / (APP_NAME + ".py")
PROGRAM_CONFIG_FILE = ACOUPI_HOME / "config.json"
CELERY_CONFIG_PATH = ACOUPI_HOME / "config" / "celery"
RUN_DIR = ACOUPI_HOME / "run"
LOG_DIR = ACOUPI_HOME / "log"
LOG_LEVEL = "INFO"
START_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-workers-start.sh"
STOP_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-workers-stop.sh"
RESTART_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-workers-restart.sh"
BEAT_SCRIPT_PATH = ACOUPI_HOME / "bin" / "acoupi-beat.sh"
ACOUPI_SERVICE_FILE = "acoupi.service"
ACOUPI_BEAT_SERVICE_FILE = "acoupi-beat.service"
