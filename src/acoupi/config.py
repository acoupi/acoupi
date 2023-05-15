"""Configuration file with default configuration of Acoupi."""

"""Default device parameters"""
LATITUDE = 51.5381
LONGITUDE = -0.0099

"""Default timezone of the deployed device"""
DEFAULT_TIMEZONE = 'Europe/London'

"""Default database file name"""
DFAULT_DB_PATH = 'acoupi.db'

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
DEFAULT_THRESHOLD = 0.2

"""Default timeformat to name the audio recording files"""
DEFAULT_TIMEFORMAT = '%Y%m%d_%H%M%S' #Year-Month-Day Hour-Minute-Second

DEVICE_INDEX = 1
