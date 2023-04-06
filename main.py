import datetime
import yaml

from src.acoupi.config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from src.acoupi.audio_recording import AudioRecorder
#from acoupi.file_managers import FileManager
#from acoupi.models import BatDetect2
#from acoupi.recording_managers import MultiIntervalRecordingManager
#from acoupi.scheduler_managers import ConstantScheduler
#from acoupi.storages.sqlite import SqliteStore

# Load Configuration
with open("config.yaml") as f:
  config = yaml.load(f, Loader=yaml.FullLoader)

"""Test the audio file recording."""
recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, sample_rate=DEFAULT_SAMPLE_RATE,
                        channels=DEFAULT_AUDIO_CHANNELS, chunk=DEFAULT_CHUNK_SIZE)

# record audio
recording = recorder.record_audio()

# do something with the recording object
print(f"Recorded file: {recording.path}")
