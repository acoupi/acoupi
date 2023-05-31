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
def audio_recorder_worker(audio_recorder, audio_recording_queue):
    """
    This function enable continous audio recording of 3s length. 
    :param audio_recorder: PyAudioRecorder object
    :param audio_recording_queue: Queue object to store audio_recording file path
    :param go: bool run signal to share data between processes 
    """
    while True: 
        # Record Audio
        print(f"[Process id {getpid()}] Start recording audio: {time.asctime()}")
        recording = audio_recorder.record()
        print(f"[Process id {getpid()}] End Recording Audio: {time.asctime()}")
        # Put the recording into the queue for further process
        audio_recording_queue.put(recording)
        print(f"[Process id {getpid()}] Recording saved to queue: {recording.path} - Time: {time.asctime()}")
        

# Worker to run model on audio recording
def run_model_worker(model, audio_recording_queue, manage_detections_queue):

    while True:
        if audio_recording_queue.empty():
            return

        recording = audio_recording_queue.get() 

        print(f'[Process id {getpid()}] Get Recording item: {recording.path} - Time: {time.asctime()}')
        
        # Run the model on the recording
        print(f"[Process id {getpid()}] Start Running Model: {time.asctime()}")
        print(f"[Process id {getpid()}] Audio Recording Path: {recording.path}")
        detections = model.run(recording)
        print(f"[Process id {getpid()}] End Running Model: {time.asctime()}")
    
        # Put the recording into the queue for further process
        manage_detections_queue.put(detections)
        print(f"[Process id {getpid()}] Detections saved to queue - Time: {time.asctime()}")


# Worker to manage detections 
def audio_results_worker(audio_recording_queue, manage_detections_queue, 
                         detection_filter, recording_filter, sqlitedb):
    
    while True:
        
        #try:
        #    # Check if there is detections in the manage_detections_queue
        #    recording = audio_recording_queue.get(timeout=30)
        #    detections = manage_detections_queue.get(timeout=30)
        #except manage_detections_queue.Empty:
        #    continue
        
        # Check if there is detections in the manage_detections_queue
        if manage_detections_queue.empty():
            return

        # Get the recordings and detections from the queue. 
        recording = audio_recording_queue.get()
        detections = manage_detections_queue.get()

        # Check if detections and recordings should be saved.  
        keep_detections_bool = detection_filter.should_store_detection(detections)
        #logger.info("Decisions to store detections: %s", keep_detections_bool) 
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
        clean_detections_queue.put(clean_detections_obj)

# Worker to send detections via mqtt
def mqtt_worker(mqtt_messenger, transmission_messagedb, manage_detections_queue, clean_detections_queue):
    
    while True:
        #try:
        #    # Check if there are detections to be sent in the clean_detections_queuee
        #    clean_detections = clean_detections_queue.get(timeout=30)
        #except clean_detections_queue.Empty:
        #    continue
        
        # Check if there are detections to be sent in the clean_detections_queue
        if clean_detections_queue.empty():
            return

        # Get the clean detections from the queue.
        clean_detections = clean_detections_queue.get()
        
        # Prepare and send the detections messages via MQTT
        mqtt_detections_messages = [build_detection_message(detection) for detection in clean_detections]
        print(f"[Process id {getpid()}] Detections Sent via MQTT: {time.asctime()}")
        response = [mqtt_messenger.send_message(message) for message in mqtt_detections_messages]

        # Store Detection Message to SqliteDB
        transmission_messagedb.store_detection_message(clean_detections, response)

