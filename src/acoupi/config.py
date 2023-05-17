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
END_RECORDING = '08:00:00'

"""Default audio recording length in seconds."""
DEFAULT_RECORDING_DURATION = 3
"""Default recording interval in seconds."""
DEFAULT_RECORDING_INTERVAL = 6

"""Default detection probabilities threshold"""
DEFAULT_THRESHOLD = 0.70

"""Default timeformat to name the audio recording files"""
DEFAULT_TIMEFORMAT = '%Y%m%d_%H%M%S' #Year-Month-Day Hour-Minute-Second

"""Default saving recordings"""
# Based on time intervals such as between 9pm and 10pm
DEFAULT_RECORDING_SAVE_START_TIME = ''
DEFAULT_RECORDING_SAVE_END_TIME = ''

DEFAULT_RECORDING_SAVE_DAWN_TIME = ''
DEFAULT_RECORDING_SAVE_DUSK_TIME = ''

# Based on duration e.g. for 5, 10 minutes every 30 minutes, 1 hour ...
DEFAULT_RECORDING_SAVE_DURATION = ''
DEFAULT_RECORDING_SAVE_INTERVAL = ''


"""Default directories to save audio recordings and detections"""
DIR_RECORDING_TRUE = 'storage/bats/recordings'
DIR_RECORDING_FALSE = 'storage/no_bats/recordings'
DIR_DETECTION_TRUE = 'storage/bats/detections'
DIR_DETECTION_FALSE = 'storage/no_bats/detections'

DEVICE_INDEX = 1
