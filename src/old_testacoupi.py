import threading
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLERATE, DEFAULT_AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL, DEFAULT_THRESHOLD
from config import START_RECORDING, END_RECORDING, DEFAULT_TIMEFORMAT, DEFAULT_TIMEZONE
from config import DEFAULT_DB_PATH
from config import START_SAVING_RECORDING, END_SAVING_RECORDING, SAVE_RECORDING_DURATION, SAVE_RECORDING_FREQUENCY, SAVE_DAWNDUSK_DURATION
from config import DIR_RECORDING_TRUE, DIR_RECORDING_FALSE, DIR_DETECTION_TRUE, DIR_DETECTION_FALSE
from config_mqtt import DEFAULT_MQTT_HOST, DEFAULT_MQTT_PORT, DEFAULT_MQTT_CLIENT_USER, DEFAULT_MQTT_CLIENT_PASS, DEFAULT_MQTT_CLIENTID, DEFAULT_MQTT_TOPIC

from audio_recorder import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from detection_filters import ThresholdDetectionFilter
from messengers import MQTTMessenger, build_detection_message
from storages.sqlite import SqliteStore, SqliteMessageStore
from saving_filters import TimeInterval, FrequencySchedule, Before_DawnDuskTimeInterval, After_DawnDuskTimeInterval
from saving_managers import Directories, SaveRecording, SaveDetection

# Setup the main logger
logging.basicConfig(filename='acoupi.log',filemode='w', 
                    format='%(levelname)s - %(message)s',
                    level=logging.INFO)


def main():

    scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) # every 10 seconds

    # Specify Directories to save recordings and detections. 
    save_dir_recording = Directories(dirpath_true=DIR_RECORDING_TRUE, dirpath_false=DIR_RECORDING_FALSE)
    save_dir_detection = Directories(dirpath_true=DIR_DETECTION_TRUE, dirpath_false=DIR_DETECTION_FALSE)

    # Create the saving recording objects - check if recordings should be saved or not. 
    saving_recording_start = datetime.strptime(START_SAVING_RECORDING,"%H:%M:%S").time()
    saving_recording_end = datetime.strptime(END_SAVING_RECORDING,"%H:%M:%S").time()

    save_recording_timeinterval = TimeInterval(Interval(start=saving_recording_start, end=saving_recording_end), timezone=ZoneInfo(DEFAULT_TIMEZONE))
    #save_recording_freqschedule = FrequencySchedule(duration=SAVE_RECORDING_DURATION, frequency=SAVE_RECORDING_FREQUENCY)
    #save_recording_dawnduskinterval = DawnDuskTimeInterval(duration=SAVE_DAWNDUSK_DURATION, timezone=ZoneInfo(DEFAULT_TIMEZONE))

    # Create the recording and detection SavingManager object
    recording_savingmanager = SaveRecording(timeformat=DEFAULT_TIMEFORMAT, save_dir=save_dir_recording)
    detection_savingmanager = SaveDetection(timeformat=DEFAULT_TIMEFORMAT, save_dir=save_dir_detection)

    def process():

        #print('System Running - Please Wait.')

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
        # Run model - Get detections
        # SqliteDB Store recordings, detections

        # Send Message via MQTT
        mqtt_detections_messages = [build_detection_message(detection) for detection in clean_detections_obj]
        response = [mqtt_messenger.send_message(message) for message in mqtt_detections_messages]
        print(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")
        #logging.info(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")

        # Store Detection Message to SqliteDB
        transmission_messagedb.store_detection_message(clean_detections_obj, response)
        #print(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        #print(f"[Thread {thread_id}] Response Status: {response[0].status}")

        # Check if recording should be saved 
        save_rec_timeint_bool = save_recording_timeinterval.should_save_recording(recording)
        #save_rec_freq_bool = save_recording_freqschedule.should_save_recording(recording)
        #save_rec_dawndusk_bool = save_recording_dawnduskinterval.should_save_recording(recording)
        #print("")
        print(f"[Thread {thread_id}] Time Interval - Saving Recording Decision: {save_rec_timeint_bool}")
        #print(f"[Thread {thread_id}] Frequency Schedule - Saving Recording Decision: {save_rec_freq_bool}")
        #print(f"[Thread {thread_id}] DawnDusk Interval - Saving Recording Decision: {save_rec_dawndusk_bool}")
        #print("")
        #logging.info(f"[Thread {thread_id}] DawnDusk Interval - Saving Recording Decision: {save_rec_dawndusk_bool}")
        
        # Recording and Detection Saving Manager
        save_rec = recording_savingmanager.save_recording(recording, save_rec_timeint_bool, keep_detections_bool)    
        #save_rec = recording_savingmanager.save_recording(recording, save_rec_freq_bool)    
        #save_rec = recording_savingmanager.save_recording(recording, save_rec_dawndusk_bool, keep_detections_bool)    
        save_det = detection_savingmanager.save_detections(recording, clean_detections_obj, keep_detections_bool)
        print(f"[Thread {thread_id}] END THREAD: {time.asctime()}")
        print("")
        #logging.info(f"[Thread {thread_id}] Recording & Detection save - END: {time.asctime()}")
        #logging.info("")

    # Start processing
    process()

if __name__ == "__main__":
    main()
