#import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
#import multiprocessing 

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL
from audio_recording import PyAudioRecorder
from model import BatDetect2
#from detection_filters import Threshold_DetectionFilter
from model_output import CleanModelOutput
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from storages.sqlite import SqliteStore
#from recording_filters import ThresholdRecordingFilter

#from acoupi.file_managers import FileManager
#from acoupi.audio_recording import PyAudioRecorder
#from acoupi.models import BatDetect2
#from acoupi.recording_managers import MultiIntervalRecordingManager
#from acoupi.scheduler_managers import ConstantScheduler
#from acoupi.storages.sqlite import SqliteStore

# Create scheduler manager
#scheduler = ConstantScheduleManager(DEFAULT_RECORDING_INTERVAL) 
#storage = SqliteStore(config["storage"])

def main():

    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    #scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) # every 10 seconds

    # Create audio_recorder object
    audio_recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                                 sample_rate=DEFAULT_SAMPLE_RATE,
                                 channels=DEFAULT_AUDIO_CHANNELS,
                                 chunk=DEFAULT_CHUNK_SIZE,
                                 device_index=DEVICE_INDEX)

    # Create Interval start_time, end_time object
    #start_time = datetime.strptime(config['start_recording'],"%H:%M:%S").time()
    #end_time = datetime.strptime(config['end_recording'], "%H:%M:%S").time()

    recording_intervals = [Interval(start=start_time, end=datetime.strptime("23:59:59","%H:%M:%S").time()),
                           Interval(start=datetime.strptime("00:00:00","%H:%M:%S").time(), end=end_time)]

    #recording_condition = IsInIntervals(recording_intervals, ZoneInfo(config['timezone']))

    storage = SqliteStore(config['sqlite']['storage'])

    # recording_filter = ThresholdRecordingFilter(DETECTION_THRESHOLD)

    def process():

        # Get the time 
        now = datetime.now()
        # Schedule next recording - Use Scheduler to determine when next recording should happen.
        threading.Timer((scheduler.time_until_next_recording(now)), process).start()

        # Check if we should record
        if not recording_condition.should_record(datetime.now()):
            return

        # Record audio
        print("")
        print(f"Recording Audio Start: {time.asctime()}")
        recording = audio_recorder.record()
        print(f"Recording Audio End: {time.asctime()}")
        # check if an audio file has been recorded
        print("")
        print(f"Recorded file: {recording.path}")
        print(f"Recording Time: {recording.datetime}")

        # Load model 
        print("")
        print(f"Loading BatDetect2 Model Start: {time.asctime()}")
        model = BatDetect2(recording=recording)
        print(f"Loading BatDetect2 Model End: {time.asctime()}")
        # Run model - Get detections
        print("")
        print(f"Running Model BatDetect2 Start: {time.asctime()}")
        detections = model.run(recording)
        print(f"Running Model BatDetect2 End: {time.asctime()}")
        print("")

        # Detection Filter
        store_detections = Threshold_DetectionFilter(detections)
        print("Store Detections - Threshold DF")
        print(store_detections)
        print("")
        #clean_detection = recording_filter(recording, detections)

        # Clean Model Output
        print(f"Start Cleaning Model Output {time.asctime()}")
        cdetection = CleanModelOutput(detections)
        clean_predict = cdetection.getDetection_aboveThreshold()
        print(f"End Cleaning Model Output {time.asctime()}")
        print(f"Clean Prediction : {clean_predict}")

        # Save detections to local store
        storage.store_detections(recording, store_detections)
    #     #print("Detections stored")

    #     # Delete recording
    #     #file_manager.delete_recording(recording)

    # # Start processing
    process()

if __name__ == "__main__":
    main()
