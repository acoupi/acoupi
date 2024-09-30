"""Program templates.

This module provides functions that facilitate the creation of programs.
"""

import datetime
import zoneinfo
from logging import Logger
from pathlib import Path
from typing import Annotated, Callable, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic_extra_types.timezone_name import TimeZoneName

from acoupi import components, data, tasks
from acoupi.components import types
from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.data import TimeInterval
from acoupi.programs import (
    AcoupiProgram,
    AcoupiWorker,
    NoUserPrompt,
    WorkerConfig,
)
from acoupi.system.files import get_temp_dir

__all__ = []


class AudioConfiguration(BaseModel):
    duration: int = 3
    """Duration of each audio recording in seconds."""

    interval: int = 5
    """Interval between each audio recording in seconds."""

    chunksize: Annotated[int, NoUserPrompt] = 8192
    """Chunksize of audio recording."""

    schedule: List[TimeInterval] = Field(
        default_factory=lambda: [
            TimeInterval(start=datetime.time.min, end=datetime.time.max)
        ]
    )


class DataConfiguration(BaseModel):
    tmp: Path = Field(default_factory=get_temp_dir)

    audio: Path = Field(default_factory=lambda: Path.home() / "audio")

    metadata: Path = Field(
        default_factory=lambda: Path.home() / "storages" / "metadata.db",
    )


class BasicConfiguration(BaseModel):
    timezone: TimeZoneName = Field(default=TimeZoneName("Europe/London"))

    microphone: MicrophoneConfig

    audio: AudioConfiguration = Field(default_factory=AudioConfiguration)

    data: DataConfiguration = Field(default_factory=DataConfiguration)


ProgramConfig = TypeVar("ProgramConfig", bound=BasicConfiguration)


class BasicProgram(AcoupiProgram[ProgramConfig]):
    logger: Logger

    worker_config: Optional[WorkerConfig] = WorkerConfig(
        workers=[
            AcoupiWorker(
                name="recording",
                queues=["recording"],
                concurrency=1,
            ),
            AcoupiWorker(
                name="default",
                queues=["celery"],
            ),
        ],
    )

    recorder: types.AudioRecorder

    store: types.Store

    file_manager: types.RecordingSavingManager

    def setup(self, config: ProgramConfig) -> None:
        self.validate_dirs(config)
        self.recorder = self.configure_recorder(config)
        self.store = self.configure_store(config)
        self.file_manager = self.configure_file_manager(config)
        self.register_recording_task(config)
        self.register_file_management_task(config)

    def configure_recorder(
        self,
        config: ProgramConfig,
    ) -> types.AudioRecorder:
        microphone = config.microphone
        return components.PyAudioRecorder(
            duration=config.audio.duration,
            samplerate=microphone.samplerate,
            audio_channels=microphone.audio_channels,
            device_name=microphone.device_name,
            chunksize=config.audio.chunksize,
            audio_dir=config.data.tmp,
        )

    def configure_store(
        self,
        config: ProgramConfig,
    ) -> types.Store:
        return components.SqliteStore(config.data.metadata)

    def configure_file_manager(
        self,
        config: ProgramConfig,
    ) -> types.RecordingSavingManager:
        return components.DateFileManager(config.data.audio)

    def get_recording_conditions(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingCondition]:
        return [
            components.IsInIntervals(
                intervals=config.audio.schedule,
                timezone=zoneinfo.ZoneInfo(config.timezone),
            )
        ]

    def get_recording_filters(
        self,
        config: ProgramConfig,
    ) -> list[types.RecordingSavingFilter]:
        return []

    def get_recording_callbacks(
        self,
        config: ProgramConfig,
    ) -> list[Callable[[Optional[data.Recording]], None]]:
        return []

    def create_recording_task(
        self,
        config: ProgramConfig,
    ) -> Callable[[], Optional[data.Recording]]:
        recording_conditions = self.get_recording_conditions(config)
        return tasks.generate_recording_task(
            recorder=self.recorder,
            store=self.store,
            logger=self.logger.getChild("recording"),
            recording_conditions=recording_conditions,
        )

    def register_recording_task(
        self,
        config: ProgramConfig,
    ) -> None:
        recording_task = self.create_recording_task(config)
        self.add_task(
            function=recording_task,
            schedule=datetime.timedelta(seconds=config.audio.interval),
            callbacks=self.get_recording_callbacks(config),
            queue="recording",
        )

    def create_file_management_task(
        self,
        config: ProgramConfig,
    ) -> Callable[[], None]:
        file_filters = self.get_recording_filters(config)
        return tasks.generate_file_management_task(
            store=self.store,
            logger=self.logger.getChild("file_management"),
            file_managers=[self.file_manager],
            file_filters=file_filters,
            tmp_path=config.data.tmp,
        )

    def register_file_management_task(
        self,
        config: ProgramConfig,
    ) -> None:
        file_management_task = self.create_file_management_task(config)
        self.add_task(
            function=file_management_task,
            schedule=datetime.timedelta(minutes=1),
            queue="celery",
        )

    def on_start(self, deployment: data.Deployment):
        super().on_start(deployment)
        self.store.store_deployment(deployment)

    def on_end(self, deployment: data.Deployment) -> None:
        super().on_end(deployment)
        self.store.update_deployment(deployment)

    def validate_dirs(self, config: ProgramConfig):
        if not config.data.tmp.exists():
            config.data.tmp.mkdir(parents=True)

        if not config.data.audio.exists():
            config.data.audio.mkdir(parents=True)

        if not config.data.metadata.parent.exists():
            config.data.metadata.parent.mkdir(parents=True)

    def check(self, config: ProgramConfig):
        if isinstance(self.recorder, components.PyAudioRecorder):
            self.recorder.check()
