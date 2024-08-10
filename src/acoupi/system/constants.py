"""Path constants for acoupi system."""

from pathlib import Path
from typing import List

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "CeleryConfig"]


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


class CeleryConfig(BaseModel):
    """Celery config."""

    enable_utc: bool = True
    timezone: str = "UTC"
    broker_url: str = "pyamqp://guest@localhost//"
    result_backend: str = "rpc://"
    result_persistent: bool = False
    task_serializer: str = "pickle"
    result_serializer: str = "pickle"
    accept_content: List[str] = Field(default_factory=lambda: ["pickle"])
