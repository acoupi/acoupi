"""Configuration file with default configuration of Acoupi."""
import datetime
from pathlib import Path

"""Default device parameters"""
LATITUDE = 51.5381
LONGITUDE = -0.0099

"""Default timezone of the deployed device"""
DEFAULT_TIMEZONE = "Europe/London"

"""Default database file name"""
DEFAULT_DB_PATH = Path("acoupi.db")

"""Default audio recording parameters."""
DEFAULT_SAMPLERATE = 192000
DEFAULT_AUDIOCHANNELS = 1
DEFAULT_CHUNK_SIZE = 8192
# DEFAULT_CHUNK_SIZE = 2^x

"""Default start and end audio recording"""
START_RECORDING_TIME = datetime.time(hour=12, minute=0, second=0)
END_RECORDING_TIME = datetime.time(hour=21, minute=0, second=0)

"""Default audio recording length in seconds."""
DEFAULT_DURATION = 3
"""Default recording interval in seconds."""
DEFAULT_INTERVAL = 10

"""Default detection probabilities threshold"""
DEFAULT_THRESHOLD = 0.2

"""Default timeformat to name the audio recording files"""
DEFAULT_TIMEFORMAT = "%Y%m%d_%H%M%S"  # Year-Month-Day Hour-Minute-Second

"""Default saving recordings"""
# Based on time intervals such as between 9pm and 10pm
START_SAVING_RECORDING = datetime.time(hour=12, minute=30, second=0) 
END_SAVING_RECORDING = datetime.time(hour=14, minute=0, second=0)

# Based on duration before or after dawn and dusk time (duration in minutes)
BEFORE_DAWNDUSK_DURATION = 10
AFTER_DAWNDUSK_DURATION = 10

# Based on duration (in minutes) and time frequeny (in minutes)
SAVE_RECORDING_DURATION = 1
SAVE_RECORDING_FREQUENCY = 30

"""Default directories to save audio recordings and detections"""
DIR_RECORDING_TRUE = Path("storages/bats/recordings")
DIR_RECORDING_FALSE = Path("storages/no_bats/recordings")
DIR_DETECTION_TRUE = Path("storages/bats/detections")
DIR_DETECTION_FALSE = Path("storages/no_bats/detections")

DEVICE_INDEX = 1
