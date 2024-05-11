"""Summariser for acoupi.

The Summariser is reponsible summarising information related to the deployment of acoupi to a remote server.
"""

import json
import datetime
from typing import List, Dict

from acoupi import data
from acoupi.components import types

__all__ = ["DetectionsSummariser"]


class DetectionsSummariser(types.Summariser):
    def __init__(
        self,
        interval: float = 120,
    ):
        """Initialise the Summariser.

        Args:
          start_time: The start time to summarise detections.
          end_time: The end time to summarise detections.
        """

        self.interval = interval

    def build_summary(self, summary) -> data.Message:
        """Build a message from a summary."""
        return data.Message(content=json.dumps(summary))


class PredictedTagsSummariser(types.Summariser):
    """A Summariser that builds hourly detections summary.

    This Summariser builds an hourly message to summarise the detections stored the SQLite DB.
    The created message includes the following information:

    - Names of detected species
    - Number of detection for each species
    - Number of detections for each threshold bands."""

    def __init__(
        self,
        threshold_lowband: float = 0.5,
        threshold_midband: float = 0.7,
        threshold_highband: float = 0.9,
    ):
        """Initialise the Summariser.

        Args:
          summary_interval: The interval to summarise detections.
          threshold_lowband: The lower threshold for detection.
          threshold_midband: The mid threshold for detection.
          threshold_highband: The higher threshold for detection.
        """

        self.threshold_highband = threshold_highband
        self.threshold_midband = threshold_midband
        self.threshold_lowband = threshold_lowband

    def get_species_name(
        self, model_outputs: List[types.ModelOutput]
    ) -> List[str]:
        """Get the unique set of species names found in the PredictedTags.

        Args:
          model_outputs: The model_outputs to get the species names from.

        Returns:
          The list of species names.
        """

        species_name = []

        for model_output in model_outputs:
            print(f"GETTING MODELOutputs: {model_output}")
            for detection in model_output.detections:
                print(f"LOOKING AT THE DETECTIONS: {detection}")
                for tag in detection.tags:
                    print(f"LOOKING AT THE TAGS: {tag}")
                    print(f"Trying to access tag.key: {tag.tag.key}")
                    if tag.tag.key == "species" and tag.tag.value not in species_name:
                        species_name.append(tag.tag.value)


        return species_name

    def get_species_count_in_bands(
        self, species_name: List[str], model_outputs: List[types.ModelOutput]
    ) -> Dict[str, int]:
        """Count the number of dections for each species in each threshold band."""

        detection_count = {"low_band": 0, "mid_band": 0, "high_band": 0}

        for model_output in model_outputs:
            for detection in model_output.detections:
                for tag in detection.tags:
                    if (
                        tag.tag.key == "species"
                        and tag.tag.value == species_name
                    ):
                        if (
                            tag.classification_probability
                            >= self.threshold_highband
                        ): 
                            detection_count["high_band"] += 1
                        if (
                            tag.classification_probability
                            >= self.threshold_midband
                            and tag.classification_probability
                            < self.threshold_highband
                        ):
                            detection_count["mid_band"] += 1
                        if (
                            tag.classification_probability
                            >= self.threshold_lowband
                            and tag.classification_probability
                            < self.threshold_midband
                        ):
                            detection_count["low_band"] += 1

        return detection_count

    def build_summary(
        self, model_outputs: List[types.ModelOutput]
    ) -> data.Message:
        """Summarise the detections.

        Args:
          model_outputs: The model_outputs to summarise.

        Returns:
          The summary message.
        """

        # Create Summary Message
        summary = {
            "summary_date": datetime.datetime.now().isoformat(),
            "species": {},
        }

        # Get species names and counts
        species_name = self.get_species_name(model_outputs)

        for specie in species_name:
            print(f"COUNTING DETECTIONS FOR SPECIE: {specie}")
            detection_count = self.get_species_count_in_bands(
                specie, model_outputs
            )
            print(f"NUMBER OF DETECTIONS FOR SPECIE: {detection_count}")
            summary["species"][specie] = detection_count

        print(f"SUMMARY OF DETECTIONS: {summary}")

        return data.Message(content=json.dumps(summary))
