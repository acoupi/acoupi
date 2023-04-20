import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
#import multiprocessing 

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL, DEFAULT_THRESHOLD
from config import DIR_RECORDING_TRUE, DIR_RECORDING_FALSE, DIR_DETECTION_TRUE, DIR_DETECTION_FALSE
from config import DEFAULT_TIMEFORMAT
from audio_recorder import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from detection_filters import ThresholdDetectionFilter
from recording_filters import ThresholdRecordingFilter
from model_output import CleanModelOutput
from saving_managers import Directories, SaveRecording, SaveDetection

# Create scheduler manager
scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) 


def main():

    with open("config.yaml") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    scheduler = IntervalScheduler(timeinterval=DEFAULT_RECORDING_INTERVAL) # every 10 seconds

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

    # Create recording_filter and detection_filter object
    detection_filter = ThresholdDetectionFilter(threshold=DEFAULT_THRESHOLD)
    recording_filter = ThresholdRecordingFilter(threshold=DEFAULT_THRESHOLD)

    # Specify Directories to save recordings and detections. 
    save_dir_recording = Directories(dirpath_true=DIR_RECORDING_TRUE, dirpath_false=DIR_RECORDING_FALSE)
    save_dir_detection = Directories(dirpath_true=DIR_DETECTION_TRUE, dirpath_false=DIR_DETECTION_FALSE)

    # Create the recording and detection SavingManager object
    recording_savingmanager = SaveRecording(timeformat=DEFAULT_TIMEFORMAT, save_dir=save_dir_recording)
    detection_savingmanager = SaveDetection(timeformat=DEFAULT_TIMEFORMAT, save_dir=save_dir_detection)
   
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
        print("")
        print(f"Running Model BatDetect2 End: {time.asctime()}")

        # Detection Filter
        print("")
        print(f"Probability Threshold: {DEFAULT_THRESHOLD}")
        keep_detections_bool = detection_filter.should_keep_detections(detections) 
        clean_detections = detection_filter.get_clean_detections(detections, keep_detections_bool)
        
        # Recording Filter
        keep_recording_bool = recording_filter.should_keep_recording(recording, detections)
        print("")
        print(f"Threshold Recording Filter Decision: {keep_recording_bool}")
        print(f"Threshold Detection Filter - Decision: {keep_detections_bool}")


        # Recording Saving Manager
        save_rec = recording_savingmanager.save_recording(recording, keep_recording_bool)
        print("")
        print(f"Recording Save in Directory: {save_rec}")
        
        # Detection Saving Manager
        save_det = detection_savingmanager.save_detections(recording, clean_detections, keep_detections_bool)
        print("")
        print(f"Return Save Detection Object: {save_det}")
        print("")

        # Save detections to local store

    # Start processing
    process()

if __name__ == "__main__":
    main()
