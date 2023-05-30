import time
from datetime import datetime
from pathlib import Path
import logging

from multiprocessing import Process, Queue, Value
from Queue import Empty

logger = logging.getLogger(__name__)

# Worker to record audio
def audio_recorder_worker(audio_recorder, audio_recording_queue, go):

    while True:
        # Record Audio
        logger.info("Recording audio")
        recording = audio_recorder.record()

        # Put the recording into the queue for further process
        logger.info("Recording saved to file: %s", recording.path)
        audio_recording_queue.put(recording)
     

# Worker to run model on audio recording
def run_model_worker(model, audio_recording_queue, manage_detections_queue, go):

    while True:
        # Check if there is a recording in the audio_recording queue
        try:
            # Get the audio recording from the queue
            recording = audio_recording_queue.get(timeout=1)
            
        except audio_recording_queue.Empty:
            continue
        
        # Get the audio recording from the queue
        #recording = audio_recording_queue.get()

        # Run the model on the recording
        logger.info("Start running model inference")
        detections = model.run(recording)

        # Put the recording into the queue for further process
        manage_detections_queue.put(detections)


# Worker to manage detections 
def audio_results_worker(audio_recording_queue, manage_detections_queue, 
                         detection_filter, recording_filter, sqlitedb):
    
    while True:
        # Check if there is detections in the manage_detections_queue
        try:
            # Get the recordings and detections from the queue. 
            detections = manage_detections_queue.get(timeout=1) 
            recording = audio_recording_queue.get(timeout=1)

        except manage_detections_queue.Empty:
            continue

        # Get the recordings and detections from the queue. 
        #recording = audio_recording_queue.get()
        #detections = manage_detections_queue.get()

        # Check if detections and recordings should be saved.  
        keep_detections_bool = detection_filter.should_store_detection(detections)
        logger.info("Decisions to store detections: %s", keep_detections_bool) 
        clean_detections_obj = detection_filter.get_clean_detections_obj(detections, keep_detections_bool)
        keep_recording_bool = recording_filter.should_store_recording(recording, detections)

        # SqliteDB Store Recording, Detections
        sqlitedb.store_recording(recording)
        if keep_detections_bool:
            sqlitedb.store_detections(recording, clean_detections_obj)
            logger.info("Detections saved in database.") 

        # Put clean detections into the queue for further processing
        clean_detections_queue.put(clean_detections_obj)

# Worker to send detections via mqtt
def mqtt_worker(mqtt_messenger, transmission_messagedb, manage_detections_queue, clean_detections_queue):
    
    while True:
        # Check if there are detections to be sent in the clean_detections_queue
        try:
            # Get the clean detections from the queue.
            clean_detections = clean_detections_queue.get(timeout=1)

        except clean_detections_queue.Empty:
            continue

        # Get the clean detections from the queue.
        #clean_detections = clean_detections_queue.get()
        
        # Prepare and send the detections messages via MQTT
        mqtt_detections_messages = [build_detection_message(detection) for detection in clean_detections]
        response = [mqtt_messenger.send_message(message) for message in mqtt_detections_messages]

        # Store Detection Message to SqliteDB
        transmission_messagedb.store_detection_message(clean_detections, response)

