"""Summariser for acoupi.

The Summariser is reponsible summarising information related to the deployment of acoupi to a remote server.
"""
import json
import numpy as np
from typing import Dict

from acoupi import data
from acoupi.components import types

__all__ = [
    "StatisticsDetectionsSummariser",
    "ThresholdsDetectionsSummariser",
]

class StatisticsDetectionsSummariser(types.Summariser):
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

    def build_summary(self, summary) -> Dict:
        """Build a message from a summary."""

        if len(summary) == 0:
            return data.Message(content=json.dumps({}))

        else:
            db_species_name = set(t.tag.value for t in summary)
            db_species_stats = {}

            for species_name in db_species_name:
                species_probabilities = [t.classification_probability for t in summary if t.tag.value == species_name]

                stats = {
                    "mean": np.round(np.mean(species_probabilities),3),
                    "min": np.min(species_probabilities),
                    "max": np.max(species_probabilities),
                    "count": len(species_probabilities),
                }

                db_species_stats[species_name] = {
                    "mean": stats["mean"],
                    "min": stats["min"],
                    "max": stats["max"],
                    "count": stats["count"],
                }

        return db_species_stats

class ThresholdsDetectionsSummariser(types.Summariser):
    def __init__(
        self,
        interval: float = 120,
        low_band_threshold: float = 0.1,
        mid_band_threshold: float = 0.5,
        high_band_threshold: float = 0.9,
    ):
        """Initialise the Summariser.

        Args:
            interval: Define the start time and end time of detections to retrieve.

            low_band_threshold: The low band threshold for the summary.
            mid_band_threshold: The mid band threshold for the summary.
            high_band_threshold: The high band threshold for the summary.
        """

        self.interval = interval
        self.low_band_threshold = low_band_threshold
        self.mid_band_threshold = mid_band_threshold
        self.high_band_threshold = high_band_threshold

    def build_summary(self, summary) -> Dict:
        """Build a message from a summary."""

        if len(summary) == 0:
            return data.Message(content=json.dumps({}))

        else:
            db_species_name = set(t.tag.value for t in summary)
            db_species_stats = {}

            for species_name in db_species_name:
                species_probabilities = [
                    t.classification_probability
                    for t in summary
                    if t.tag.value == species_name
                ]

                stats = {
                    "count_low_threshold": len(
                        [
                            d
                            for d in species_probabilities
                            if d <= self.low_band_threshold
                        ]
                    ),
                    "count_mid_threshold": len(
                        [
                            d
                            for d in species_probabilities
                            if self.low_band_threshold
                            < d
                            <= self.mid_band_threshold
                        ]
                    ),
                    "count_high_threshold": len(
                        [
                            d
                            for d in species_probabilities
                            if self.mid_band_threshold < d
                        ]
                    ),
                    "mean_low_threshold": np.round(
                        np.mean(
                            [
                                d
                                for d in species_probabilities
                                if d <= self.low_band_threshold
                            ]
                        ),
                        3,
                    ),
                    "mean_mid_threshold": np.round(
                        np.mean(
                            [
                                d
                                for d in species_probabilities
                                if self.low_band_threshold
                                < d
                                <= self.mid_band_threshold
                            ]
                        ),
                        3,
                    ),
                    "mean_high_threshold": np.round(
                        np.mean(
                            [
                                d
                                for d in species_probabilities
                                if self.mid_band_threshold < d
                            ]
                        ),
                        3,
                    ),
                }

                db_species_stats[species_name] = {
                    "count_low_threshold": stats["count_low_threshold"],
                    "count_mid_threshold": stats["count_mid_threshold"],
                    "count_high_threshold": stats["count_high_threshold"],
                    "mean_low_threshold": stats["mean_low_threshold"],
                    "mean_mid_threshold": stats["mean_mid_threshold"],
                    "mean_high_threshold": stats["mean_high_threshold"],
                }

        return db_species_stats
