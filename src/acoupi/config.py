"""Configuration file with default configuration of Acoupi."""

"""Default device parameters"""
LATITUDE = 51.5381
LONGITUDE = -0.0099

"""Default timezone of the deployed device"""
DEFAULT_TIMEZONE = 'Europe/London'

"""Default database file name"""
DEFAULT_DB_PATH = 'acoupi.db'

"""Default audio recording parameters."""
DEFAULT_SAMPLE_RATE = 192000
DEFAULT_AUDIO_CHANNELS = 1
DEFAULT_CHUNK_SIZE = 8192
#DEFAULT_CHUNK_SIZE = 4096
# DEFAULT_CHUNK_SIZE = 2^x

"""Default start and end audio recording"""
START_RECORDING = '10:00:00'
END_RECORDING = '18:00:00'

"""Default audio recording length in seconds."""
DEFAULT_RECORDING_DURATION = 3
"""Default recording interval in seconds."""
DEFAULT_RECORDING_INTERVAL = 10

"""Default detection probabilities threshold"""
DEFAULT_THRESHOLD = 0.2

"""Default timeformat to name the audio recording files"""
DEFAULT_TIMEFORMAT = '%Y%m%d_%H%M%S' #Year-Month-Day Hour-Minute-Second

"""Default saving recordings"""
# Based on time intervals such as between 9pm and 10pm
START_SAVING_RECORDING = '20:00:00'
END_SAVING_RECORDING = '07:00:00'

# Based on duration after dawn and dusk time (duratino in minutes)
SAVE_DAWNDUSK_DURATION = 10

# Based on duration (in minutes) and time frequeny (in minutes)
SAVE_RECORDING_DURATION = 1
SAVE_RECORDING_FREQUENCY = 30

"""Default directories to save audio recordings and detections"""
DIR_RECORDING_TRUE = 'storages/bats/recordings'
DIR_RECORDING_FALSE = 'storages/no_bats/recordings'
DIR_DETECTION_TRUE = 'storages/bats/detections'
DIR_DETECTION_FALSE = 'storages/no_bats/detections'

DEVICE_INDEX = 1
