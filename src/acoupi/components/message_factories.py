"""Message factories for acoupi."""
from typing import List
import json
import datetime

from acoupi import data
from acoupi.components import types

__all__ = [
    "FullModelOutputMessageBuilder", 
    "QEOP_MessageBuilder",
]


class FullModelOutputMessageBuilder(types.ModelOutputMessageBuilder):
    """A ModelOutputMessageBuilder that builds message from model outputs.

    This message builder builds a message from a model output. The created
    message will contain the full model output as a JSON string. This
    includes information about:
        - the model used.
        - the recording processed, including deployment info.
        - the predicted tags at the recording level.
        - predicted detections with their tags and confidence scores.
    """

    def build_message(self, model_output: data.ModelOutput) -> data.Message:
        """Build a message from a recording and model outputs."""
        return data.Message(content=model_output.model_dump_json())


class QEOP_MessageBuilder(types.ModelOutputMessageBuilder):
    """A ModelOutputMessageBuilder that builds message from model outputs.
    
    Format Result for QEOP devices with the following arguments:
        {
            'ts': <recording timestamp in unix ms>,
            'id': <detection_id>
            'ct': <start_time_detection - coordinate x0>,
            'pb': <detection probability>,
            'cl': [
                {
                    'c': <class name>,
                    'p': <class name probability>
                },
                    ...
            ]
        }
    """

    def build_message(self, model_output: data.ModelOutput) -> List[data.Message]:

        json_model_output = json.loads(model_output.model_dump_json())  # Parse JSON string
        
        data_json = []
        
        # Get the detection in the clean_tags model_output
        for detection in json_model_output['detections']:
            
            row_data = {}

            #get the timestamp from the recordings
            timestamp = json_model_output['recording']['datetime']
            unix_timestamp_ms = int((datetime.datetime.fromisoformat(timestamp)).timestamp() * 1000)
            row_data['ts'] = unix_timestamp_ms
            row_data['id'] = detection['id']
            row_data['pb'] = detection['probability']
            row_data['ct'] = detection['location']['coordinates'][0]

            classifications = []
            # Get the species associated with the detection
            for tag in range(len(detection['tags'])):
              nextClass = {}
              nextClass['c'] = detection['tags'][tag]['tag']['value']
              nextClass['p'] = detection['tags'][tag]['probability']
              classifications.append(nextClass)

            row_data["cl"] = classifications
            data_json.append(row_data)
        
        print("--- DATA ----")
        print(data_json)

        messages = []
        for item in data_json:
            content = json.dumps(item)  # Convert dictionary to JSON string
            print("--CONTENT--")
            print(content)
            print("")
            message = data.Message(content=content)
            #message = data.Message(content=content.model_dump_json())
            messages.append(message)
            print("--- MESSAGE ---")
            print(message)

        return messages
