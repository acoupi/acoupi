import threading
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

#import multiprocessing 

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLE_RATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL, DEFAULT_THRESHOLD
from config import START_RECORDING, END_RECORDING, DEFAULT_TIMEFORMAT, DEFAULT_TIMEZONE
from config import DFAULT_DB_PATH
#from config import DIR_RECORDING_TRUE, DIR_RECORDING_FALSE, DIR_DETECTION_TRUE, DIR_DETECTION_FALSE
from audio_recorder import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from detection_filters import ThresholdDetectionFilter
from recording_filters import ThresholdRecordingFilter
#from saving_managers import Directories, SaveRecording, SaveDetection
from storages.sqlite import SqliteStore

# Setup the main logger
logging.basicConfig(filename='acoupi.log',filemode='w', 
                    format='%(levelname)s - %(message)s',
                    level=logging.INFO)

# Create scheduler manager
scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) 

def main():

    scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) # every 10 seconds

    # Create the model object to analyse an audio recording
    model = BatDetect2()

    # Create audio_recorder object to initiate audio recording
    audio_recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                                 sample_rate=DEFAULT_SAMPLE_RATE,
                                 channels=DEFAULT_AUDIO_CHANNELS,
                                 chunk=DEFAULT_CHUNK_SIZE,
                                 device_index=DEVICE_INDEX)

    # Create Interval start_time, end_time object
    # Audio recording will only happen in the specific time interval 
    start_time = datetime.strptime(START_RECORDING,"%H:%M:%S").time()
    end_time = datetime.strptime(END_RECORDING,"%H:%M:%S").time()

    # Create the recording_interval object
    recording_intervals = [Interval(start=start_time, end=datetime.strptime("23:59:59","%H:%M:%S").time()),
                           Interval(start=datetime.strptime("00:00:00","%H:%M:%S").time(), end=end_time)]

    # Create the recording_condition object - check if it is time to record audio (time.now() IsInInterval)
    recording_condition = IsInIntervals(recording_intervals, ZoneInfo(DEFAULT_TIMEZONE))

    # Create recording_filter and detection_filter object
    detection_filter = ThresholdDetectionFilter(threshold=DEFAULT_THRESHOLD)
    recording_filter = ThresholdRecordingFilter(threshold=DEFAULT_THRESHOLD)

    # Specify sqlite database to store detection
    sqlitedb = SqliteStore(DFAULT_DB_PATH)

    # Specify Directories to save recordings and detections. 
    #save_dir_recording = Directories(dirpath_true=DIR_RECORDING_TRUE, dirpath_false=DIR_RECORDING_FALSE)
    #save_dir_detection = Directories(dirpath_true=DIR_DETECTION_TRUE, dirpath_false=DIR_DETECTION_FALSE)

    # Create the recording and detection SavingManager object
    #recording_savingmanager = SaveRecording(timeformat=DEFAULT_TIMEFORMAT, save_dir=save_dir_recording)
    #detection_savingmanager = SaveDetection(timeformat=DEFAULT_TIMEFORMAT, save_dir=save_dir_detection)
   
    def process():

        print('System Running - Please Wait.')

        # Get the thread id
        thread_id = threading.get_ident()

        # Get the time 
        now = datetime.now()
        # Schedule next recording - Use Scheduler to determine when next recording should happen.
        threading.Timer((scheduler.time_until_next_recording(now)), process).start()

        # Check if we should record
        if not recording_condition.should_record(datetime.now()):
            logging.info(f"Outside Recording Interval - Current Time is {time.asctime()}")
            logging.info(f"Recording Start at: {start_time} and End at: {end_time}")
            return

        # Record audio
        #logging.info(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        print(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        recording = audio_recorder.record()
        print(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")
        #logging.info(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")

        # Run model - Get detections
        #logging.info(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        print(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        detections = model.run(recording)
        print(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")
        #logging.info(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")

        # Detection and Recording Filter
        keep_detections_bool = detection_filter.should_store_detection(detections) 
        clean_detections = detection_filter.get_clean_detections(detections, keep_detections_bool)
        print(f"[Thread {thread_id}] Threshold Detection Filter Decision: {keep_recording_bool}")
        #logging.info(f"[Thread {thread_id}] Threshold Detection Filter Decision: {keep_recording_bool}")
        
        #keep_recording_bool = recording_filter.should_keep_recording(recording, detections)
        #logging.info(f"[Thread {thread_id}] Threshold Recording Filter Decision: {keep_recording_bool}")
        
        # SqliteDB Store Recroding, Detections
        sqlitedb.store_detections(recording)
        sqlitedb.store_detections(recording, detections)

        # Recording and Detection Saving Manager
        #save_rec = recording_savingmanager.save_recording(recording, keep_recording_bool)    
        #save_det = detection_savingmanager.save_detections(recording, clean_detections, keep_detections_bool)
        #logging.info(f"[Thread {thread_id}] Recording & Detection save - END: {time.asctime()}")
        #logging.info("")

    # Start processing
    process()

if __name__ == "__main__":
    main()
