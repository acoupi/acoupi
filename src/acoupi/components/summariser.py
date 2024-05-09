"""Summariser for acoupi.

The Summariser is reponsible summarising information related to the deployment of acoupi to a remote server.
"""

import json
import datetime
from typing import List, Dict

from acoupi import data
from acoupi.components import types

__all__ = []


class DetectionsSummariser(types.Summariser):
    """A Summariser that builds hourly detections summary.

    This Summariser builds an hourly message to summarise the detections stored the SQLite DB.
    The created message includes the following information:

    - Names of detected species
    - Number of detection for each species
    - Number of detections for each threshold bands."""

    def __init__(
        self,
        summary_interval: float,
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

        self.summary_interval = summary_interval
        self.threshold_highband = threshold_highband
        self.threshold_midband = threshold_midband
        self.threshold_lowband = threshold_lowband

    # def get_model_outputs(self, model_outputs: List[types.ModelOutput]) -> List[types.ModelOutput]:
    #   """Get the model outputs from the SQLite database."""
    #   return model_outputs

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
            for tag in model_output.tags:
                for value in tag.value:
                    if tag.key == "species" and value not in species_name:
                        species_name.append(value)

        return species_name

    def get_species_count_in_bands(
        self, species_name: str, model_outputs: List[types.ModelOutput]
    ) -> Dict[str, int]:
        """Count the number of dections for each species in each threshold band."""

        detection_count = {"low_band": 0, "mid_band": 0, "high_band": 0}

        for model_output in model_outputs:
            for detection in model_output.detections:
                if (
                    detection.tags.tag.key == "species"
                    and detection.tags.tag.value == species_name
                ):
                    if (
                        detection.tags.classification_probability
                        >= self.threshold_highband
                    ):
                        detection_count["high_band"] += 1
                    if (
                        detection.tags.classification_probability
                        >= self.threshold_midband
                        and detection.tags.classification_probability
                        < self.threshold_highband
                    ):
                        detection_count["mid_band"] += 1
                    if (
                        detection.tags.classification_probability
                        >= self.threshold_lowband
                        and detection.tags.classification_probability
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
            detection_count = self.get_species_count_in_bands(
                specie, model_outputs
            )
            summary["species"][specie] = detection_count

        return data.Message(content=json.dumps(summary))
