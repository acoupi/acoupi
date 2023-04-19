"""Configuration file with default configuration of Acoupi."""

"""Default device parameters"""
LATITUDE = 51.5381
LONGITUDE = -0.0099

"""Default audio recording parameters."""
DEFAULT_SAMPLE_RATE = 192000
DEFAULT_AUDIO_CHANNELS = 1
DEFAULT_CHUNK_SIZE = 2048
# DEFAULT_CHUNK_SIZE = 1024

"""Default start and end audio recording"""
START_RECORDING = "20:00"
END_RECORDING = "08:00"

"""Default audio recording lenght in seconds."""
DEFAULT_RECORDING_DURATION = 3

"""Default recording interval in seconds."""
DEFAULT_RECORDING_INTERVAL = 9

"""Default detection probabilities threshold"""
DETECTION_THRESHOLD = 0.1

"""Default directories to save audio recordings and detections"""
DIR_RECORDING_TRUE = 'storage/bats/recordings'
DIR_RECORDING_FALSE = 'storage/no_bats/recordings'
DIR_DETECTION_TRUE = 'storage/bats/detections'
DIR_DETECTION_FALSE = 'storage/no_bats/detections'

DEVICE_INDEX = 1
