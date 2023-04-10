from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE
from audio_recording import PyAudioRecorder
from model import BatDetect2
from model_output import CleanModelOutput
#from acoupi.file_managers import FileManager
#from acoupi.audio_recording import PyAudioRecorder
#from acoupi.models import BatDetect2
#from acoupi.recording_managers import MultiIntervalRecordingManager
#from acoupi.scheduler_managers import ConstantScheduler
#from acoupi.storages.sqlite import SqliteStore

# Load Configuration
#with open("config.yaml") as f:
#  config = yaml.load(f, Loader=yaml.FullLoader)

# Create objects
audio_recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                                 sample_rate=DEFAULT_SAMPLE_RATE,
                                 channels=DEFAULT_AUDIO_CHANNELS,
                                 chunk=DEFAULT_CHUNK_SIZE)
cdetections = CleanModelOutput()

# Record audio
recording = recorder.record()
# check if an audio file has been recorded
print(f"Recorded file: {recording.path}")

# Load model 
model = BatDetect2(recording=recording)

# Run model - Get detections
detections = model.run(recording)
print(f"Detections: {detections}")

# Clean Model Output
clean_predict = cdetections.get_highest_pdetection(detections)
print(f"Clean Predictions : {clean_predict}")