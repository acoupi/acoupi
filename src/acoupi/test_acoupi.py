import threading
import datetime
import yaml

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL, START_RECORDING, END_RECORDING
from audio_recording import PyAudioRecorder
from model import BatDetect2
from model_output import CleanModelOutput
#from schedule_managers import ConstantScheduleManager
from recording_managers import MultiIntervalRecordingManager

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

    recording_manager = MultiIntervalRecordingManager(
        [config['start_recording'], "24:00"],["00:00", config['end_recording']],
        timezone=config["timezone"],
    )
                                
    def process():
        # Schedule next processing
        threading.Timer(DEFAULT_RECORDING_INTERVAL, process).start()

        # Check if we should record
        if not recording_manager.should_record(datetime.datetime.now().time()):
            return

        # Record audio
        recording = audio_recorder.record()
        # check if an audio file has been recorded
        print(f"Recorded file: {recording.path}")

        # Load model 
        model = BatDetect2(recording=recording)

        # Run model - Get detections
        detection = model.run(recording)

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
