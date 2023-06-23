"""Test the acoupi package."""
import threading
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import config
import config_mqtt
from acoupi import components, data
from acoupi import system

#from config import DEFAULT_RECORDING_DURATION, DEFAULT_SAMPLERATE, DEFAULT_AUDIO_                AUDIO_CHANNELS, DEFAULT_CHUNK_SIZE, DEVICE_INDEX, DEFAULT_RECORDING_INTERVAL, DEFAULT_THRESHOLD
#from config import START_RECORDING, END_RECORDING, DEFAULT_TIMEFORMAT, DEFAULT_TIMEZONE
#from config import DEFAULT_DB_PATH
#from config import START_SAVING_RECORDING, END_SAVING_RECORDING, SAVE_RECORDING_DURATION, SAVE_RECORDING_FREQUENCY, SAVE_DAWNDUSK_DURATION
#from config import DIR_RECORDING_TRUE, DIR_RECORDING_FALSE, DIR_DETECTION_TRUE, DIR_DETECTION_FALSE
#from config_mqtt import DEFAULT_MQTT_HOST, DEFAULT_MQTT_PORT, DEFAULT_MQTT_CLIENT_USER, DEFAULT_MQTT_CLIENT_PASS, DEFAULT_MQTT_CLIENTID, DEFAULT_MQTT_TOPIC

from acoupi.data import TimeInterval

# Setup the main logger
logging.basicConfig(
    filename='acoupi.log',
    filemode='w', 
    format='%(levelname)s - %(message)s',
    level=logging.INFO
)


def main():
    """Main function to run the program."""
    
    # Get the current deployment
    deployment = system.get_current_deployment()

    scheduler = components.IntervalScheduler(config.DEFAULT_INTERVAL) # every 10 seconds

    # Create the model object to analyse an audio recording
    model = components.BatDetect2()

    # Create audio_recorder object to initiate audio recording
    audio_recorder = components.PyAudioRecorder(
        duration=config.DEFAULT_DURATION, 
        samplerate=config.DEFAULT_SAMPLERATE,
        audio_channels=config.DEFAULT_AUDIO_CHANNELS,
        chunk=config.DEFAULT_CHUNK_SIZE,
        device_index=config.DEVICE_INDEX
    )

    # Create Recording TimeInterval start_time, end_time objects
    # Audio recording will only happen in the specific time interval 
    recording_intervals = [
        data.TimeInterval(
            start=config.START_RECORDING, 
            end=datetime.strptime("23:59:59","%H:%M:%S").time(),
        ),
        data.TimeInterval(
            start=datetime.strptime("00:00:00","%H:%M:%S").time(), 
            end=config.END_RECORDING,
        ),
    ]

    # Create the recording_condition object - check if it is time to record audio (time.now() IsInInterval)
    recording_condition = components.IsInIntervals(
        recording_intervals,
        ZoneInfo(config.DEFAULT_TIMEZONE)
    )

    # Create recording_filter and detection_filter object
    detection_filter = components.ThresholdDetectionFilter(threshold=config.DEFAULT_THRESHOLD)

    # Specify sqlite database to store recording and detection
    sqlitedb = components.SqliteStore(config.DEFAULT_DB_PATH)

    # Specify sqlite message to keep track of records sent
    transmission_messagedb = components.SqliteMessageStore(config.DEFAULT_DB_PATH)

    # Sending Detection to MQTT
    mqtt_messenger = components.MQTTMessenger(
        host=config_mqtt.DEFAULT_MQTT_HOST, 
        username=config_mqtt.DEFAULT_MQTT_CLIENT_USER, 
        password=config_mqtt.DEFAULT_MQTT_CLIENT_PASS, 
        port=config_mqtt.DEFAULT_MQTT_PORT, 
        client_id=config_mqtt.DEFAULT_MQTT_CLIENTID, 
        topic=config_mqtt.DEFAULT_MQTT_TOPIC
    )

    # Messages to send to MQTT
    message_builder = components.FullModelOutputMessageBuilder()

    # Create the saving recording objects - decide when to save recordings.
    save_recording_timeinterval = components.SaveIfInInterval(
        data.TimeInterval(
            start=config.START_SAVING_RECORDING,
            end=config.END_SAVING_RECORDING,
        ),
        timezone=ZoneInfo(config.DEFAULT_TIMEZONE),
    )

    save_recording_beforedawndusk = components.Before_DawnDuskTimeInterval(
        duration=config.BEFORE_DAWNDUSK_DURATION,
        timezone=ZoneInfo(config.DEFAULT_TIMEZONE),
    )

    save_recording_afterdawndusk = components.After_DawnDuskTimeInterval(
        duration=config.AFTER_DAWNDUSK_DURATION,
        timezone=ZoneInfo(config.DEFAULT_TIMEZONE),
    )


    # Create the recording and detection SavingManager object
    recording_savingmanager = components.SaveRecording(
        timeformat=config.DEFAULT_TIMEFORMAT,
        dirpath_true=config.DIR_DETECTION_TRUE,
        dirpath_false=config.DIR_DETECTION_FALSE,
    )

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
            #logging.info(f"Recording Start at: {start_time} and End at: {end_time}")
            return

        # Record audio
        #logging.info(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        #print("")
        print(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        recording = audio_recorder.record(deployment)
        print(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")
        #logging.info(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")

        # Run model - Get detections
        #logging.info(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        print(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        model_outputs = model.run(recording)
        print(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")
        print("")
        #logging.info(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")
        #logging.info("")

        # Detection and Recording Filter
        model_outputs = detection_filter.clean(model_outputs)
        #print(f"[Thread {thread_id}] Threshold Detection Filter Decision: {model_outputs}")
        #logging.info(f"[Thread {thread_id}] Threshold Detection Filter Decision: {keep_detections_bool}") 
        #logging.info(f"[Thread {thread_id}] Threshold Recording Filter Decision: {keep_recording_bool}")
        
        # SqliteDB Store Recroding, Detections
        sqlitedb.store_recording(recording)
        sqlitedb.store_model_output(model_outputs)
        print(f"[Thread {thread_id}] Recording and Detections saved in db: {time.asctime()}")
        #logging.info(f"[Thread {thread_id}] Recording and Detections saved in db: {time.asctime()}")

        # Send Message via MQTT
        message = message_builder.build_message(model_outputs)
        response = mqtt_messenger.send_message(message)
        print(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")
        #logging.info(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")

        # Store Detection Message to SqliteDB
        transmission_messagedb.store_message(message)
        transmission_messagedb.store_response(response)

        # Check if recording should be saved 
        save_rec_timeint_bool = save_recording_timeinterval.should_save_recording(recording)
        #save_rec_freq_bool = save_recording_freqschedule.should_save_recording(recording)
        #save_rec_before_dawndusk_bool = save_recording_beforedawndusk.should_save_recording(recording)
        #save_rec_after_dawndusk_bool = save_recording_afterdawndusk.should_save_recording(recording)
        print(f"[Thread {thread_id}] Time Interval - Saving Recording Decision: {save_rec_timeint_bool}")
        #print(f"[Thread {thread_id}] Frequency Schedule - Saving Recording Decision: {save_rec_freq_bool}")
        #print(f"[Thread {thread_id}] Before DawnDusk Interval - Saving Recording Decision: {save_rec_before_dawndusk_bool}")
        #print(f"[Thread {thread_id}] After DawnDusk Interval - Saving Recording Decision: {save_rec_after_dawndusk_bool}")
        #print("")
        
        # Recording and Detection Saving Manager
        recording_savingmanager.save_recording(recording, [model_outputs])    
        #ecording_savingmanager.save_recording(recording, save_rec_freq_bool, keep_detections_bool)    
        #recording_savingmanager.save_recording(recording, save_rec_before_dawndusk_bool, keep_detections_bool)  
        #recording_savingmanager.save_recording(recording, save_rec_after_dawndusk_bool, keep_detections_bool)    
        print(f"[Thread {thread_id}] END THREAD: {time.asctime()}")
        print("")

    # Start processing
    process()

if __name__ == "__main__":
    main()
