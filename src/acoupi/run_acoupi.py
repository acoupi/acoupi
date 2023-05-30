import threading
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from config import *
from config_mqtt import *
from audio_recorder import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from detection_filters import ThresholdDetectionFilter
from recording_filters import ThresholdRecordingFilter
from messengers import MQTTMessenger, build_detection_message
from storages.sqlite import SqliteStore, SqliteMessageStore

from multiprocessing import Process, Queue, Value
from workers import audio_recorder_worker, run_model_worker, audio_results_worker, mqtt_worker


# Setup the main logger
logging.basicConfig(filename='acoupi.log',filemode='w', 
                    format='%(levelname)s - %(message)s',
                    level=logging.INFO)

def main():
    #scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) 

    # Create Interval start_time, end_time object
    start_time = datetime.strptime(START_RECORDING,"%H:%M:%S").time()
    end_time = datetime.strptime(END_RECORDING,"%H:%M:%S").time()

    # Create the recording_interval object
    recording_intervals = [Interval(start=start_time, end=datetime.strptime("23:59:59","%H:%M:%S").time()),
                           Interval(start=datetime.strptime("00:00:00","%H:%M:%S").time(), end=end_time)]

    # Create the recording_condition object - check if it is time to record audio (time.now() IsInInterval)
    recording_condition = IsInIntervals(recording_intervals, ZoneInfo(DEFAULT_TIMEZONE))
    
    # Create audio_recorder object to initiate audio recording
    audio_recorder = PyAudioRecorder(duration=DEFAULT_RECORDING_DURATION, 
                                 sample_rate=DEFAULT_SAMPLE_RATE,
                                 channels=DEFAULT_AUDIO_CHANNELS,
                                 chunk=DEFAULT_CHUNK_SIZE,
                                 #device_index=DEVICE_INDEX)
                                 )

    # Create the model object to analyse an audio recording
    model = BatDetect2()
    
    # Create recording_filter and detection_filter object
    detection_filter = ThresholdDetectionFilter(threshold=DEFAULT_THRESHOLD)
    recording_filter = ThresholdRecordingFilter(threshold=DEFAULT_THRESHOLD)

    # Specify sqlite database to store recording and detection
    sqlitedb = SqliteStore(DEFAULT_DB_PATH)
    # Specify sqlite message to keep track of records sent
    transmission_messagedb = SqliteMessageStore(DEFAULT_DB_PATH, sqlitedb)

    # Sending Detection to MQTT
    mqtt_messenger = MQTTMessenger(host=DEFAULT_MQTT_HOST, username=DEFAULT_MQTT_CLIENT_USER, password=DEFAULT_MQTT_CLIENT_PASS, 
                                   port=DEFAULT_MQTT_PORT, client_id=DEFAULT_MQTT_CLIENTID, topic=DEFAULT_MQTT_TOPIC)


    def run():
        
        # Get the time 
        time_now = datetime.now()
        print('Processes starting')

        # Create the queues and shared memory
        audio_recording_queue = Queue()
        manage_detections_queue = Queue()
        clean_detections_queue = Queue()
        mqtt_sendmessage_queue = Queue()

        # Define the worker processes
        processes = {
            'audio_recorder': Process(target=audio_recorder_worker, args=(audio_recorder, audio_recording_queue)),
            'run_model': Process(target=run_model_worker,args=(model, audio_recording_queue, manage_detections_queue)),
            'save_audio_results': Process(target=audio_results_worker, args=(audio_recording_queue,manage_detections_queue, detection_filter, recording_filter,sqlitedb)),
            'send_detections': Process(target=mqtt_worker, args=(mqtt_messenger, transmission_messagedb, manage_detections_queue, clean_detections_queue)),
        }

        # Start processes as daemons
        for process in processes.values():
            process.daemon = True
            process.start()
        print('')
        print(f'Queue Size: {audio_recording_queue.qsize()}')

        # Continue running the loop until recording conditions are not met
        while recording_condition.should_record(time_now):
            pass

        # Stop the worker processes if outside recording conditions
        #if not recording_condition.should_record(time_now):
        for process in processes.values():
            process.terminate()
            process.join()

    # Start running the processes
    run()

if __name__ == "__main__":
    main()
