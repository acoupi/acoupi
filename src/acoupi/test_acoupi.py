import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
#import multiprocessing 

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL
from audio_recording import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from model_output import CleanModelOutput
#from detection_filters import Threshold_DetectionFilter
#from recording_filters import ThresholdRecordingFilter
from saving_managers import RecordingSavingManager, DetectionSavingManager


# Create scheduler manager
scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) 

def main():

    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    #scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) # every 10 seconds

    # Create audio_recorder object to initiate audio recording
    audio_recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                                 sample_rate=DEFAULT_SAMPLE_RATE,
                                 channels=DEFAULT_AUDIO_CHANNELS,
                                 chunk=DEFAULT_CHUNK_SIZE,
                                 device_index=DEVICE_INDEX)

    # Create Interval start_time, end_time object
    # Audio recording will only happen in the specific time interval 
    start_time = datetime.strptime(config['start_recording'],"%H:%M:%S").time()
    end_time = datetime.strptime(config['end_recording'], "%H:%M:%S").time()

    # Create the recording_interval object
    recording_intervals = [Interval(start=start_time, end=datetime.strptime("23:59:59","%H:%M:%S").time()),
                           Interval(start=datetime.strptime("00:00:00","%H:%M:%S").time(), end=end_time)]

    # Create the recording_condition object - check if it is time to record audio (time.now() IsInInterval)
    recording_condition = IsInIntervals(recording_intervals, ZoneInfo(config['timezone']))

    # recording_filter = ThresholdRecordingFilter(DETECTION_THRESHOLD)

    def process():

        # Get the time 
        now = datetime.now()
        # Schedule next recording - Use Scheduler to determine when next recording should happen.
        threading.Timer((scheduler.time_until_next_recording(now)), process).start()

        # Check if we should record
        if not recording_condition.should_record(datetime.now()):
            print("Outside Recording Interval")
            print(f"Recording Start at: {start_time} and End at: {end_time}")
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
        print(f"Detections species name: {detections.species_name}")
        print(f"Detections probability: {detections.probability}")

        # Detection Filter
        store_detections = Threshold_DetectionFilter(detections)
        print("Store Detections - Threshold DF")
        print(store_detections)
        print("")

        # Clean Model Output
        print(f"Start Cleaning Model Output {time.asctime()}")
        cdetection = CleanModelOutput(detections)
        clean_predict = cdetection.getDetection_aboveThreshold()
        print(f"End Cleaning Model Output {time.asctime()}")
        print(f"Clean Prediction : {clean_predict}")
        print("")

        # Save detections to local store

    # Start processing
    process()

if __name__ == "__main__":
    main()
