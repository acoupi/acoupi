"""Path constants for acoupi system."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings for acoupi system."""

    model_config = SettingsConfigDict(
        env_prefix="ACOUPI_",
    )

    home: Path = Path.home() / ".acoupi"
    app_name: str = "app"
    program_file: Path = home / (app_name + ".py")
    program_name_file: Path = home / "config" / "name"
    program_config_file: Path = home / "config" / "program.json"
    celery_config_file: Path = home / "config" / "celery.json"
    deployment_file: Path = home / "config" / "deployment.json"
    env_file: Path = home / "config" / "env"
    run_dir: Path = home / "run"
    log_dir: Path = home / "log"
    log_level: str = "INFO"
    start_script_path: Path = home / "bin" / "acoupi-workers-start.sh"
    stop_script_path: Path = home / "bin" / "acoupi-workers-stop.sh"
    restart_script_path: Path = home / "bin" / "acoupi-workers-restart.sh"
    beat_script_path: Path = home / "bin" / "acoupi-beat.sh"
    acoupi_service_file: str = "acoupi.service"
    acoupi_beat_service_file: str = "acoupi-beat.service"
