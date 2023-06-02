import inotify.adapters

i = inotify.adapters.InotifyTree('/run/shm/')

for event in i.event_gen(yield_nones=False):
    (_, type_names, path, filename) = event
    print("PATH=[{}] FILENAME=[{}] EVENT_TYPES={}".format( path, filename, type_names))


# Configuration to run Acoupi with iNotify
dir_towatch = '/run/shm/'
script_to_call = 'model.py'
event_type_towatch = 'IN_CREATE'

def record_audio():
    
    # Get the time 
    now = datetime.now()

    # Check if we should record
    if not recording_condition.should_record(datetime.now()):
        logging.info(f"Outside Recording Interval - Current Time is {time.asctime()}")
        logging.info(f"Recording Start at: {start_time} and End at: {end_time}")
        return

    # Record audio
    print(f"[Thread {thread_id}] Start Recording Audio: {time.asctime()}")
    recording = audio_recorder.record()
    print(f"[Thread {thread_id}] End Recording Audio: {time.asctime()}")
    return 


def main():

    recording = record_audio()



def process_audio():

    i = inotify.adapters.InotifyTree(dir_towatch)

    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        for event_type in type_names:
            if event_type == event_type_towatch:
                subprocess.call(model.run(filename))
            

