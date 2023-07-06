import datetime
from pathlib import Path

import threading
import logging

from acoupi import config
from acoupi import config_mqtt

from acoupi import compoments, data


from audio_recorder import PyAudioRecorder
from recording_schedulers import IntervalScheduler
from recording_conditions import IsInIntervals, Interval
from model import BatDetect2
from detection_filters import ThresholdDetectionFilter
from recording_filters import ThresholdRecordingFilter
from messengers import MQTTMessenger, build_detection_message
from storages.sqlite import SqliteStore, SqliteMessageStore


# Setup the main logger
#logging.basicConfig(filename='acoupi.log',filemode='w', format='%(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():

    """Audio recordings interval scheduler."""
    scheduler = IntervalScheduler(DEFAULT_RECORDING_INTERVAL) # every 10 seconds

    """Audio and microphone configuration parameters."""
    # Create audio_recorder object to initiate audio recording
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
    dbpath = compoments.SqliteStore(db_path=config.DEFAULT_DB_PATH)
    dbpath_message = compoments.SqliteMessageStore(db_path=config.DEFAULT_DB_PATH)

    """Model Outputs Cleaning configuration parameters."""
    output_cleaners = components.ThresholdDetectionFilter(threshod=config.DEFAULT_THRESHOLD)
    
    """Message Factories configuration"""
    message_factory = [compoments.FullModelOutputMessageBuilder(),]

    """MQTT configuration to send messages"""
    mqtt_messenger = components.MQTTMessenger(host=config.DEFAULT_MQTT_HOST, 
                                              port=DEFAULT_MQTT_PORT, 
                                              username=DEFAULT_MQTT_CLIENT_USER, 
                                              password=DEFAULT_MQTT_CLIENT_PASS, 
                                              topic=DEFAULT_MQTT_TOPIC,
                                              clientid=DEFAULT_MQTT_CLIENTID,
    )

    """Recording saving options configuration."""
    file_manager = compoments.SaveRecording(dirpath_true=config.DIR_RECORDING_TRUE, dirpath_false=DIR_RECORDING_FALSE, 
                                            timeformat=DEFAULT_TIMEFORMAT, threshold=DEFAULT_THRESHOLD)

    dawndusk_saving = [components.Before_DawnDuskTimeInterval(duration=config.BEFORE_DAWNDUSK_DURATION, timezone=config.DEFAULT_TIMEZONE),
                       compoments.After_DawnDuskTimeInterval(duration=config.AFTER_DAWNDUSK_DURATION, timezone=config.DEFAULT_TIMEZONE)]

    frequency_saving = components.FrequencySchedule(duration=config.SAVE_FREQUENCY_DURATION, frequency=SAVE_FREQUENCY_INTERVAL)


    def process():

        # Get the thread id
        thread_id = threading.get_ident()
        
        """Step 1 - Record audio.""" 
        now = datetime.datetime.now()
        #logger.info("Starting recording process")
        
        # Schedule next recording - Use Scheduler to determine when next recording should happen.
        threading.Timer((scheduler.time_until_next_recording(now)), process).start()

        # Check if recording conditions are met
        if not recording_condition.should_record(now):
            logger.info("Recording conditions not met.")
            return

        # Get current deployment
        deployment = store.get_current_deployment()

        # Record audio
        print("")
        print(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
        recording = audio_recorder.record(deployment)
        print(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")

        # Store recording metadata
        print(f"[Thread {thread_id}] Store Recording Metadata in db.: {recording.path}")
        dbpath.store_recording(recording)
        #logger.info("Recording metadata stored")

        """Step 2 - Generate Detections.""" 
        # Run model - Get detections
        print(f"[Thread {thread_id}] Start Running Model BatDetect2: {time.asctime()}")
        model_output = model.run(recording)
        print(f"[Thread {thread_id}] End Running Model BatDetect2: {time.asctime()}")
        print("")

        # Clean model outputs 
        #for cleaner in output_cleaners or []:
        #    model_output = cleaner.clean(model_output)
        model_output = output_cleaners.clean(model_output)
         
        # SqliteDB Store Detections
        dbpath.store_model_output(model_output)
        print(f"[Thread {thread_id}] Detections saved in db: {time.asctime()}")

        # Create Messages
        messages = [message_factory.build_message(model_output)]
        messages_store = dbpath_message.store_response(message)

        # Send Messages
        mqtt_message = [mqtt_messenger.send_message(message) for message in messages_store.get_unsent_messages()]
        response_store = messages_store.store_response(mqtt_message)
        print(f"[Thread {thread_id}] Detections Message sent via MQTT: {time.asctime()}")
        print(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        
        # Send Message via MQTT
        #mqtt_detections_messages = [build_detection_message(detection) for detection in clean_detections_obj]
        #response = [mqtt_messenger.send_message(message) for message in mqtt_detections_messages]

        # Store Detection Message to SqliteDB
        transmission_messagedb.store_detection_message(clean_detections_obj, response)
        #print(f"[Thread {thread_id}] Response Status Store in DB: {time.asctime()}")
        #print(f"[Thread {thread_id}] Response Status: {response[0].status}")

    # Start processing
    process()

if __name__ == "__main__":
    main()
