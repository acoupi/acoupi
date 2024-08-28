"""Acoupi components."""

from acoupi.components.audio_recorder import MicrophoneConfig, PyAudioRecorder
from acoupi.components.message_factories import (
    DetectionThresholdMessageBuilder,
    FullModelOutputMessageBuilder,
    SummaryMessageBuilder,
)
from acoupi.components.message_stores.sqlite import SqliteMessageStore
from acoupi.components.messengers import HTTPMessenger, MQTTMessenger
from acoupi.components.output_cleaners import ThresholdDetectionCleaner
from acoupi.components.recording_conditions import IsInInterval, IsInIntervals
from acoupi.components.recording_schedulers import IntervalScheduler
from acoupi.components.saving_filters import (
    After_DawnDuskTimeInterval,
    Before_DawnDuskTimeInterval,
    DetectionTags,
    DetectionTagValue,
    FrequencySchedule,
    SaveIfInInterval,
    SavingThreshold,
)
from acoupi.components.saving_managers import (
    DateFileManager,
    IDFileManager,
    SaveRecordingManager,
)
from acoupi.components.stores.sqlite import SqliteStore
from acoupi.components.summariser import (
    StatisticsDetectionsSummariser,
    ThresholdsDetectionsSummariser,
)

__all__ = [
    "After_DawnDuskTimeInterval",
    "Before_DawnDuskTimeInterval",
    "DateFileManager",
    "DetectionTags",
    "DetectionTagValue",
    "FrequencySchedule",
    "DetectionThresholdMessageBuilder",
    "FullModelOutputMessageBuilder",
    "IDFileManager",
    "IntervalScheduler",
    "IsInInterval",
    "IsInIntervals",
    "MicrophoneConfig",
    "MQTTMessenger",
    "HTTPMessenger",
    "PyAudioRecorder",
    "SaveIfInInterval",
    "SaveRecordingManager",
    "SqliteMessageStore",
    "SqliteStore",
    "StatisticsDetectionsSummariser",
    "ThresholdsDetectionsSummariser",
    "SummaryMessageBuilder",
    "ThresholdDetectionCleaner",
    "SavingThreshold",
]
