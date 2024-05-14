"""Summariser for acoupi.

The Summariser is reponsible summarising information related to the deployment of acoupi to a remote server.
"""

import json
import numpy as np

from acoupi import data
from acoupi.components import types

__all__ = ["StatisticsDetectionsSummariser",]

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

    def build_summary(self, summary) -> data.Message:
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

        return data.Message(content=json.dumps(db_species_stats))
