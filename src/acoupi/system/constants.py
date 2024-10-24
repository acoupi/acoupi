"""Path constants for acoupi system."""

from pathlib import Path
from typing import List, Literal

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
    celery_pool_type: Literal[
        "threads",
        "prefork",
        "eventlet",
        "gevent",
        "solo",
        "processes",
    ] = "threads"


class CeleryConfig(BaseModel):
    """Configuration settings for Celery in Acoupi.

    This class defines the settings used to configure the Celery
    task queue specifically for the Acoupi application.
    """

    enable_utc: bool = True
    """Whether to enable UTC for Celery.

    It's generally recommended to keep this enabled for consistency across
    different Acoupi deployments.
    """

    timezone: str = "UTC"
    """The timezone to use for Celery."""

    broker_url: str = "pyamqp://guest@localhost//"
    """The URL of the message broker used by Celery.

    Acoupi uses RabbitMQ with the default guest user. You may need to
    update this if your RabbitMQ setup is different.
    """

    broker_connection_retry_on_startup: bool = True
    """Retry to establish the connection to the AMQP broker on startup.

    Automatically try to re-establish the connection to the AMQP broke
    if lost after the initial connection is made."""

    result_backend: str = "rpc://"
    """ The URL for storing task results. 

    'rpc://' indicates that results are sent back directly to the client.
    """

    result_persistent: bool = False
    """Whether to persist task results. 

    In Acoupi deployments, task results are not typically needed after the task
    has completed, as all essential data is stored in an independent database.
    This setting helps to avoid unnecessary storage overhead.
    """

    task_serializer: str = "pickle"
    result_serializer: str = "pickle"
    accept_content: List[str] = Field(default_factory=lambda: ["pickle"])

    task_acks_late: bool = True
    """Whether to acknowledge tasks after they have been executed. 
    
    True means that tasks are acknowledged after they have been executed, 
    not right before.
    """

    worker_prefetch_multiplier: int = 1
    """The number of tasks a worker can prefetch.

    Setting this to 1 prevents tasks from being delayed due to other tasks in
    the queue. Celery defaults to prefetching tasks in batches, which can cause
    a fast task to wait for a slower one in the same batch.
    """

    task_soft_time_limit: int = 30
    """The soft time limit (in seconds) for task execution.

    If a task exceeds this limit, it will receive a warning.

    If you have tasks that are expected to run longer than this limit,
    you should increase this value or specify the time limit directly.
    """

    task_time_limit: int = 60
    """The hard time limit (in seconds) for task execution.

    If a task exceeds this limit, it will be terminated.

    If you have tasks that are expected to run longer than this limit,
    you should increase this value or specify the time limit directly.
    """
