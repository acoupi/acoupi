import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
#import multiprocessing 

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL, DETECTION_THRESHOLD
from config import DIR_RECORDING_TRUE, DIR_RECORDING_FALSE, DIR_DETECTION_TRUE, DIR_DETECTION_FALSE
from audio_recording import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from model_output import CleanModelOutput
from detection_filters import ThresholdDetectionFilter
from recording_filters import ThresholdRecordingFilter
from saving_managers import Directories, RecordingSavingManager, DetectionSavingManager


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

    # Create recording_filter and detection_filter object
    detection_filter = ThresholdDetectionFilter(DETECTION_THRESHOLD)
    recording_filter = ThresholdRecordingFilter(DETECTION_THRESHOLD)

    # Specify Directories to save recordings and detections. 
    save_dir_recording = Directories(dirpath_true=DIR_RECORDING_TRUE, dirpath_false=DIR_RECORDING_FALSE)
    print(f'Directories Recording Save True: {save_dir_recording.dirpath_true}')
    print(f'Directories Recording Save False: {save_dir_recording.dirpath_false}')
    save_dir_detection = Directories(dirpath_true=DIR_DETECTION_TRUE, dirpath_false=DIR_DETECTION_FALSE)
    print(f'Directories Detection Save: {save_dir_detection}')
    print('')
    # Create the recording savingmanager object
    recording_savingmanager = RecordingSavingManager(save_dir_recording)
   
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

        # Detection Filter
        #store_detections = Threshold_DetectionFilter(detections)
        #print("Store Detections - Threshold DF")
        keep_detection_bool = detection_filter.should_keep_detection(detections)
        print(f"Threshold Detection Filter Decision: {keep_detection_bool}")

        # Recording Filter
        keep_recording_bool = recording_filter.should_keep_recording(recording, detections)
        print(f"Threshold Recording Filter Decision: {keep_recording_bool}")
        print("")

        # Recording Saving Manager
        save_recording = recording_savingmanager.save_recording(recording, keep_recording_bool)
        print(f"Saving Recording Directory: {save_recording.sdir}")
        print(f"Saving Recording Path: {save_recording.recording.path}")
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
