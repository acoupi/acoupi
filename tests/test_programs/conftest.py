from pathlib import Path

import pytest

from acoupi.components.audio_recorder import MicrophoneConfig
from acoupi.components.messengers import HTTPConfig
from acoupi.programs.templates import (
    AudioConfiguration,
    DataConfiguration,
    MessagingConfig,
)
from acoupi.system.constants import CeleryConfig


