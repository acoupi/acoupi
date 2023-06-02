import time
from datetime import datetime
from pathlib import Path
import logging
from os import getpid

from multiprocessing import Process, Queue, Value
import queue

#logger = logging.getLogger(__name__)
# Setup the main logger
logging.basicConfig(filename='acoupi.log',filemode='w', 
                    format='%(levelname)s - %(message)s',
                    level=logging.INFO)


# Worker to record audio
def audio_recorder_worker(audio_recorder, audio_recording_queue, gp):
    """
    This function enable continous audio recording of 3s length. 
    :param audio_recorder: PyAudioRecorder object
    :param audio_recording_queue: Queue object to store audio_recording file path
    :param go: bool run signal to share data between processes 
    """
    
    #while True: 
    print("audioworker")
    # Record Audio
    print(f"[Process id {getpid()}] Start recording audio: {time.asctime()}")
    recording = audio_recorder.record()
    print(f"[Process id {getpid()}] End Recording Audio: {time.asctime()}")
    # Put the recording into the queue for further process
    audio_recording_queue.put(recording)
    print(f"[Process id {getpid()}] Recording saved to queue: {recording.path} - Time: {time.asctime()}")
    if go.value == 0:
        print("go why", go.value)
        return


# Worker to run model on audio recording
def detections_worker(model, audio_recording_queue, message_detections_queue, detection_filter, recording_filter, sqlitedb, go):

    while True:
        print("detectionworker")
        # try:
        #     # Check if there are detections to be sent in the clean_detections_queuee
        #     recording = audio_recording_queue.get(timeout=30)
        # except audio_recording_queue.Empty:
        #     continue
        if go.value == 0 and audio_recording_queue.empty():
            return

        recording = audio_recording_queue.get() 

        print(f'[Process id {getpid()}] Get Recording item: {recording.path} - Time: {time.asctime()}')
        
        # Run the model on the recording
        print(f"[Process id {getpid()}] Start Running Model: {time.asctime()}")
        print(f"[Process id {getpid()}] Audio Recording Path: {recording.path}")
        detections = model.run(recording)
        print(f"[Process id {getpid()}] End Running Model: {time.asctime()}")

        # Check if detections and recordings should be saved.  
        keep_detections_bool = detection_filter.should_store_detection(detections)
        print(f"[Process id {getpid()}] Detections Filter Decision: {keep_detections_bool}")
        clean_detections_obj = detection_filter.get_clean_detections_obj(detections, keep_detections_bool)
        keep_recording_bool = recording_filter.should_store_recording(recording, detections)

        # SqliteDB Store Recording, Detections
        sqlitedb.store_recording(recording)
        if keep_detections_bool:
            sqlitedb.store_detections(recording, clean_detections_obj)
            #logger.info("Detections saved in database.")
            print(f"[Process id {getpid()}] Detections Save in DB: {time.asctime()}")

        # Put clean detections into the queue for further processing
        message_detections_queue.put(clean_detections_obj)
        print(f"[Process id {getpid()}] Clean Detections saved to Queue - Time: {time.asctime()}")


# Worker to send detections via mqtt
def mqtt_worker(mqtt_messenger, transmission_messagedb, message_detections_queue, go):
    
    while True:
        print("mqttworker")
        # try:
        #     # Check if there are detections to be sent in the clean_detections_queuee
        #     clean_detections = message_detections_queue.get(timeout=30)
        # except message_detections_queue.Empty:
        #     continue
        
        # Check if there are detections to be sent in the clean_detections_queue
        if go.value == 0 and message_detections_queue.empty():
            return

        # Get the clean detections from the queue.
        clean_detections = message_detections_queue.get()
        
        # Prepare and send the detections messages via MQTT
        mqtt_detections_messages = [build_detection_message(detection) for detection in clean_detections]
        print(f"[Process id {getpid()}] Detections Sent via MQTT: {time.asctime()}")
        response = [mqtt_messenger.send_message(message) for message in mqtt_detections_messages]

        # Store Detection Message to SqliteDB
        transmission_messagedb.store_detection_message(clean_detections, response)

