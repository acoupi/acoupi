import threading
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL
from audio_recording import PyAudioRecorder
from model import BatDetect2
from model_output import CleanModelOutput
#from schedule_managers import ConstantScheduleManager
from recording_managers import MultiIntervalRecordingManager, Interval
#from recording_filters import ThresholdRecordingFilter

#from acoupi.file_managers import FileManager
#from acoupi.audio_recording import PyAudioRecorder
#from acoupi.models import BatDetect2
#from acoupi.recording_managers import MultiIntervalRecordingManager
#from acoupi.scheduler_managers import ConstantScheduler
#from acoupi.storages.sqlite import SqliteStore

# Load Configuration
#with open("config.yaml") as f:
#  config = yaml.load(f, Loader=yaml.FullLoader)

# Create scheduler manager
#scheduler = ConstantScheduleManager(DEFAULT_RECORDING_INTERVAL) 
#storage = SqliteStore(config["storage"])

def main():

    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    # Create audio_recorder object
    audio_recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                                 sample_rate=DEFAULT_SAMPLE_RATE,
                                 channels=DEFAULT_AUDIO_CHANNELS,
                                 chunk=DEFAULT_CHUNK_SIZE,
                                 device_index=DEVICE_INDEX)

    # Create Interval start_time, end_time object
    start_time = datetime.strptime(config['start_recording'],"%H:%M:%S").time()
    end_time = datetime.strptime(config['end_recording'], "%H:%M:%S").time()

    recording_intervals = [Interval(start=start_time, end=datetime.strptime("23:59:59","%H:%M:%S").time()),
                           Interval(start=datetime.strptime("00:00:00","%H:%M:%S").time(), end=end_time)]

    recording_manager = MultiIntervalRecordingManager(recording_intervals, ZoneInfo(config['timezone']))

    # recording_filter = ThresholdRecordingFilter(DETECTION_THRESHOLD)

                                
    def process():
        # Schedule next processing
        threading.Timer(DEFAULT_RECORDING_INTERVAL, process).start()

        # Check if we should record
        if not recording_manager.should_record(datetime.now()):
            return

        # Record audio
        recording = audio_recorder.record()
        # check if an audio file has been recorded
        print(f"Recorded file: {recording.path}")
        print("")

        # Load model 
        model = BatDetect2(recording=recording)
        print("Model Loaded")

        # Run model - Get detections
        detections = model.run(recording)
        print('Clean Model Output - Detections')
        print("")

        # Recording Filter
        #clean_detection = recording_filter(recording, detections)

        # Clean Model Output
        cdetection = CleanModelOutput(detection)
        clean_predict = cdetection.getDetection_aboveThreshold()
        print(f"Clean Prediction : {clean_predict}")

        # Save detections to local store
        #storage.store_detections(recording, clean_predict)
        #print("Detections stored")

        # Delete recording
        #file_manager.delete_recording(recording)

    # Start processing
    process()

if __name__ == "__main__":
    main()
