"""Default paramaters for Batdetect2 Program"""
import datetime
from pathlib import Path

"""Default audio recording parameters."""
DEFAULT_SAMPLE_RATE = 192000
DEFAULT_AUDIO_CHANNELS = 1
DEFAULT_CHUNK_SIZE = 8192
#DEFAULT_CHUNK_SIZE = 4096
# DEFAULT_CHUNK_SIZE = 2^x

"""Default audio recording length in seconds."""
DEFAULT_RECORDING_DURATION = 3
"""Default recording interval in seconds."""
DEFAULT_RECORDING_INTERVAL = 10

"""Default timezone of the deployed device"""
DEFAULT_TIMEZONE = 'Europe/London'

"""Default start and end audio recording"""
START_RECORDING_TIME = datetime.time(hour=12, minute=0, second=0)
END_RECORDING_TIME = datetime.time(hour=21, minute=0, second=0)

"""Defaults options for saving recordings"""
START_SAVING_RECORDING = datetime.time(hour=21, minute=30, second=0) 
END_SAVING_RECORDING = datetime.time(hour=23, minute=30, second=0) 
BEFORE_DAWNDUSK_DURATION = 10
AFTER_DAWNDUSK_DURATION = 10
SAVE_FREQUENCY_DURATION = 5
SAVE_FREQUENCY_INTERVAL = 30

"""Default detection probabilities threshold"""
DEFAULT_THRESHOLD = 0.2

"""Default database path"""
#DEFAULT_DB_PATH = Path.home()/"acoupi"/"storages"/"acoupi.db"
DEFAULT_DB_PATH = Path("acoupi.db")

"""Default timeformat to name the audio recording files"""
DEFAULT_TIMEFORMAT = '%Y%m%d_%H%M%S' #Year-Month-Day Hour-Minute-Second

"""Default directories to save audio recordings and detections"""
DIR_RECORDING_TRUE = Path.home()/"storages"/"bats"/"recordings"
DIR_RECORDING_FALSE = Path.home()/"storages"/"no_bats"/"recordings"

"""Default Microphone device Index"""
DEVICE_INDEX = 1
