import datetime
import logging
import threading
import time
from pathlib import Path

from acoupi import components, config, config_mqtt, data

# Setup the main logger
logging.basicConfig(
    filename="acoupi.log",
    filemode="w",
    format="%(levelname)s - %(message)s",
    level=logging.INFO,
)
# logger.setLevel(logging.INFO)
# logger = logging.getLogger(__name__)


def main():
    """Audio recordings interval scheduler."""
    scheduler = components.IntervalScheduler(
        config.DEFAULT_RECORDING_INTERVAL
    )  # every 10 seconds

    """Audio and microphone configuration parameters."""
    audio_recorder = components.PyAudioRecorder(
        duration=config.DEFAULT_RECORDING_DURATION,
        samplerate=config.DEFAULT_SAMPLE_RATE,
        audio_channels=config.DEFAULT_AUDIO_CHANNELS,
        chunksize=config.DEFAULT_CHUNK_SIZE,
        device_index=config.DEVICE_INDEX,
    )

    """Recording Interval configuration."""
    # Audio recording will only happen in the specific time interval
    recording_condition = components.IsInIntervals(
        intervals=[
            data.TimeInterval(
                start=config.START_RECORDING_TIME, 
                end=datetime.datetime.strptime("23:59:59", "%H:%M:%S").time(),
                ),
            data.TimeInterval(
                start=datetime.datetime.strptime("00:00:00", "%H:%M:%S").time(),
                end=config.END_RECORDING_TIME,
            ),
        ],
        timezone=config.DEFAULT_TIMEZONE,
    )

    """BatDetect2 Model for audio processing."""
    model = components.BatDetect2()

    """Sqlite DB configuration parameters."""
    dbstore = components.SqliteStore(db_path=config.DEFAULT_DB_PATH)
    dbstore_message = components.SqliteMessageStore(
        db_path=config.DEFAULT_DB_PATH
    )

    """Model Outputs Cleaning configuration parameters."""
    detection_cleaner = components.DetectionProbabilityCleaner(
        threshold=config.DEFAULT_THRESHOLD, 
    )
    tags_cleaner = components.TagKeyCleaner(
        tag_keys=['species']
    )

    """Message Factories configuration"""
    message_factories = [components.QEOP_MessageBuilder()]

    """MQTT configuration to send messages"""
    mqtt_messenger = components.MQTTMessenger(
        host=config_mqtt.DEFAULT_MQTT_HOST,
        port=config_mqtt.DEFAULT_MQTT_PORT,
        username=config_mqtt.DEFAULT_MQTTSTUDENT_USER,
        password=config_mqtt.DEFAULT_MQTTSTUDENT_PASS,
        topic=config_mqtt.DEFAULT_MQTTSTUDENT_CLIENTID,
        clientid=config_mqtt.DEFAULT_MQTTSTUDENT_TOPIC,
    )

    """HTTP Request configuration"""
    http_request = components.HTTPMessenger( 
        base_url=config_mqtt.DEFAULT_BASEURL,
        base_params={'client-id':config_mqtt.DEFAULT_CLIENTID, 'password':config_mqtt.DEFAULT_PASS},
        headers={'Accept':config_mqtt.DEFAULT_ACCEPT,'Authorization':config_mqtt.DEFAULT_APIKEY},
    )

    """Recording saving options configuration."""
    file_manager = components.SaveRecording(
        dirpath_true=config.DIR_RECORDING_TRUE,
        dirpath_false=config.DIR_RECORDING_FALSE,
        timeformat=config.DEFAULT_TIMEFORMAT,
        threshold=config.DEFAULT_THRESHOLD,
    )

    dawndusk_saving = [
        components.Before_DawnDuskTimeInterval(
            duration=config.BEFORE_DAWNDUSK_DURATION,
            timezone=config.DEFAULT_TIMEZONE,
        ),
        components.After_DawnDuskTimeInterval(
            duration=config.AFTER_DAWNDUSK_DURATION,
            timezone=config.DEFAULT_TIMEZONE,
        ),
    ]

    frequency_saving = components.FrequencySchedule(
        duration=config.SAVE_FREQUENCY_DURATION,
        frequency=config.SAVE_FREQUENCY_INTERVAL,
    )

    def process():
        # Get the thread id
        thread_id = threading.get_ident()

        """Step 1 - Record audio."""
        now = datetime.datetime.now()

        # Schedule next recording - Use Scheduler to determine when next recording should happen.
        threading.Timer((scheduler.time_until_next_recording(now)), process).start()

        # Check if recording conditions are met
        if not recording_condition.should_record(now):
            logging.info("Recording conditions not met.")
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
        clean_detections = detection_cleaner.clean(model_outputs)
        clean_tags = tags_cleaner.clean(clean_detections)

        # SqliteDB Store Recording Metadata and Detections
        dbstore.store_recording(recording)
        dbstore.store_model_output(clean_tags)
        print(f"[Thread {thread_id}] Detections saved in db: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] Detections saved in db: {time.asctime()}")

        """Optional (Step 3 - Save Audio Recordings)."""
        ## TODO

        """Step 4 - Create and Send Messages."""
        # Create HTTP Messages
        http_messages = [
            message_factory.build_message(clean_tags)
            for message_factory in message_factories
        ]
        # Store Messages in DB
        message_store = [
            dbstore_message.store_message(message) 
            for messages in http_messages
            for message in messages
            ]

        # Send Messages via MQTT
        #mqtt_messages = [mqtt_messenger.send_message(message) for message in dbstore_message.get_unsent_messages()]
        http_post = [http_request.send_message(message) for message in dbstore_message.get_unsent_messages()]
        response_store = [ 
            dbstore_message.store_response(http_response)
            for http_response in http_post
        ]
        print(f"[Thread {thread_id}] Detections Message sent via HTTP: {time.asctime()}")
        print(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        print(f"[Thread {thread_id}] -- END")
        print("")
        logging.info(f"[Thread {thread_id}] Detections Message sent via HTTP: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        logging.info(f"[Thread {thread_id}] -- END")
        logging.info("")

    # Start processing
    process()


if __name__ == "__main__":
    main()
