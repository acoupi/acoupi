"""Acoupi detection and classification Models."""

from batdetect2 import api

from acoupi import data
from acoupi.components import types

class BatDetect2(types.Model):
    "BatDetect2 Model to analyse the audio recording"

    def run(self, recording: data.Recording) -> List[data.ModelOutput]:

        """Run the model on the recording."""
        # Get the audio path of the recorded file
        audio_file_path = recording.path

        if not audio_file_path:
            return data.ModelOutput(
                model_name="BatDetect2",
                recording=recording,
            )

        # Load the audio file and compute spectrograms
        audio = api.load_audio(audio_file_path)
        print(f"Audio Loaded in Model: {audio}")

        spec = api.generate_spectrogram(audio)

        # Process the audio or the spectrogram with the model
        raw_detections, _ = api.process_spectrogram(spec)
        print(f"Detections Return from Model: {raw_detections}")

        # Convert the raw detections to a list of detections
        detections = [
            data.Detection(
                probability=detection["det_prob"],
                location=data.BoundingBox.from_coordinates(
                    detection["start_time"],
                    detection["low_freq"],
                    detection["end_time"],
                    detection["high_freq"],
                ),
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value=detection["class"]),
                        probability=detection["class_prob"],
                    ),
                    data.PredictedTag(
                        tag=data.Tag(key="event", value=detection["event"]),
                    ),
                ],
            )
            for detection in raw_detections
        ]

        return data.ModelOutput(
            model_name="BatDetect2",
            recording=recording,
            detections=detections,
        )
