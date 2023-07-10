import datetime
import time
from pathlib import Path

import threading
import logging

from acoupi import components, data
from acoupi import config
from acoupi import config_mqtt


# Setup the main logger
logging.basicConfig(filename='acoupi.log',filemode='w', format='%(levelname)s - %(message)s', level=logging.INFO)
#logger.setLevel(logging.INFO)
#logger = logging.getLogger(__name__)

def main():

    """Audio recordings interval scheduler."""
    scheduler = components.IntervalScheduler(config.DEFAULT_RECORDING_INTERVAL) # every 10 seconds

    """Audio and microphone configuration parameters."""
    audio_recorder = components.PyAudioRecorder(duration=config.DEFAULT_RECORDING_DURATION, 
                                                samplerate=config.DEFAULT_SAMPLE_RATE,
                                                audio_channels=config.DEFAULT_AUDIO_CHANNELS,
                                                chunk=config.DEFAULT_CHUNK_SIZE,
                                                device_index=config.DEVICE_INDEX,
    )
    
    """Recording Interval configuration."""
    # Audio recording will only happen in the specific time interval 
    recording_condition = components.IsInIntervals(
        intervals = [data.TimeInterval(start=config.START_RECORDING_TIME, end=datetime.datetime.strptime("23:59:59","%H:%M:%S").time()), 
                     data.TimeInterval(start=datetime.datetime.strptime("00:00:00","%H:%M:%S").time(), end=config.END_RECORDING_TIME)],
        timezone=config.DEFAULT_TIMEZONE,
    )

    """BatDetect2 Model for audio processing."""
    model = components.BatDetect2()

    """Sqlite DB configuration parameters."""
    dbstore = components.SqliteStore(db_path=config.DEFAULT_DB_PATH)
    dbstore_message = components.SqliteMessageStore(db_path=config.DEFAULT_DB_PATH)

    """Model Outputs Cleaning configuration parameters."""
    output_cleaners = components.ThresholdDetectionFilter(threshold=config.DEFAULT_THRESHOLD)
    
    """Message Factories configuration"""
    message_factories = [components.FullModelOutputMessageBuilder()]

    """MQTT configuration to send messages"""
    mqtt_messenger = components.MQTTMessenger(host=config_mqtt.DEFAULT_MQTT_HOST, 
                                              port=config_mqtt.DEFAULT_MQTT_PORT, 
                                              username=config_mqtt.DEFAULT_MQTT_CLIENT_USER, 
                                              password=config_mqtt.DEFAULT_MQTT_CLIENT_PASS, 
                                              topic=config_mqtt.DEFAULT_MQTT_TOPIC,
                                              clientid=config_mqtt.DEFAULT_MQTT_CLIENTID,
    )

    """Recording saving options configuration."""
    file_manager = components.SaveRecording(dirpath_true=config.DIR_RECORDING_TRUE, dirpath_false=config.DIR_RECORDING_FALSE, 
                                            timeformat=config.DEFAULT_TIMEFORMAT, threshold=config.DEFAULT_THRESHOLD)

    dawndusk_saving = [components.Before_DawnDuskTimeInterval(duration=config.BEFORE_DAWNDUSK_DURATION, timezone=config.DEFAULT_TIMEZONE),
                       components.After_DawnDuskTimeInterval(duration=config.AFTER_DAWNDUSK_DURATION, timezone=config.DEFAULT_TIMEZONE)]

    frequency_saving = components.FrequencySchedule(duration=config.SAVE_FREQUENCY_DURATION, frequency=config.SAVE_FREQUENCY_INTERVAL)


    def process():

        # Get the thread id
        thread_id = threading.get_ident()
        
        """Step 1 - Record audio.""" 
        now = datetime.datetime.now()
        
        # Schedule next recording - Use Scheduler to determine when next recording should happen.
        threading.Timer((scheduler.time_until_next_recording(now)), process).start()

        # Check if recording conditions are met
        if not recording_condition.should_record(now):
            logger.info("Recording conditions not met.")
            return

        # Get current deployment
        deployment = dbstore.get_current_deployment()

        # Record audio
        logging.info("")
        logging.info(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        print("")
        print(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        recording = audio_recorder.record(deployment)
        print(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")

        """Step 2 - Run Model & Generate Detections.""" 
        logging.info(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        print(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        model_outputs = model.run(recording)
        print(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")

        # Clean model outputs 
        clean_model_outputs = output_cleaners.clean(model_outputs)
         
        # SqliteDB Store Recording Metadata and Detections
        dbstore.store_recording(recording)
        dbstore.store_model_output(clean_model_outputs)
        print(f"[Thread {thread_id}] Detections saved in db: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] Detections saved in db: {time.asctime()}")

        """Optional (Step 3 - Save Audio Recordings)."""
        ## TODO

        """Step 4 - Create and Send Messages."""
        # Create Messages
        messages = [message_factory.build_message(clean_model_outputs) for message_factory in message_factories]
        #message_store = [dbstore_message.store_message(message) for message in messages]
        [dbstore_message.store_message(message) for message in messages]

        # Send Messages via MQTT
        mqtt_messages = [mqtt_messenger.send_message(message) for message in dbstore_message.get_unsent_messages()]
        response_store = [dbstore_message.store_response(mqtt_message) for mqtt_message in mqtt_messages]
        print(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")
        print(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        print(f"[Thread {thread_id}] -- END")
        print("")
        logging.info(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] -- END")
        logging.info("")

    # Start processing
    process()

if __name__ == "__main__":
    main()
