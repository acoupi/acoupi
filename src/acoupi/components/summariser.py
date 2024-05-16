"""Summariser for acoupi.

The Summariser is reponsible summarising information related to the deployment
of acoupi to a remote server.
"""

import datetime
import json
from statistics import mean
from typing import Union

from acoupi import data
from acoupi.components import types
from acoupi.components.stores import SqliteStore

__all__ = [
    "StatisticsDetectionsSummariser",
    "ThresholdsDetectionsSummariser",
]


class StatisticsDetectionsSummariser(types.Summariser):
    store: SqliteStore
    interval: datetime.timedelta

    def __init__(
        self,
        store: SqliteStore,
        interval: Union[float, int, datetime.timedelta] = 120,
    ):
        """Initialise the Summariser.

        Parameters
        ----------
        store : SqliteStore
            The store to get the detections from.
        interval : Union[float, datetime.timedelta], optional
            The interval to get the detections from. If a float is provided, it
            is interpreted as the number of minutes to get the detections from,
            by default 120.
        """
        if isinstance(interval, (float, int)):
            interval = datetime.timedelta(minutes=interval)

        self.store = store
        self.interval = interval

    def build_summary(self, now: datetime.datetime) -> data.Message:
        """Build a message from a summary."""

        predicted_tags = self.store.get_predicted_tags(
            before=now,
            after=now - self.interval,
        )

        db_species_name = set(t.tag.value for t in predicted_tags)
        db_species_stats = {}

        for species_name in db_species_name:
            species_probabilities = [
                t.classification_probability
                for t in predicted_tags
                if t.tag.value == species_name
            ]

            stats = {
                "mean": round(mean(species_probabilities), 3),
                "min": min(species_probabilities),
                "max": max(species_probabilities),
                "count": len(species_probabilities),
            }

            db_species_stats[species_name] = {
                "mean": stats["mean"],
                "min": stats["min"],
                "max": stats["max"],
                "count": stats["count"],
            }

        db_species_stats['species_stats'] = db_species_stats

        db_species_stats['timeinterval'] = {
            "starttime": (now - self.interval).isoformat(),
            "endtime": now.isoformat(),
        }

        return data.Message(content=json.dumps(db_species_stats))


class ThresholdsDetectionsSummariser(types.Summariser):
    store: SqliteStore
    interval: datetime.timedelta

    def __init__(
        self,
        store: SqliteStore,
        interval: Union[float, int, datetime.timedelta] = 120,
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
        self.store = store

        if isinstance(interval, (float, int)):
            interval = datetime.timedelta(minutes=interval)

        self.interval = interval
        self.low_band_threshold = low_band_threshold
        self.mid_band_threshold = mid_band_threshold
        self.high_band_threshold = high_band_threshold

    def build_summary(self, now: datetime.datetime) -> data.Message:
        """Build a message from a summary."""

        predicted_tags = self.store.get_predicted_tags(
            before=now,
            after=now - self.interval,
        )

        db_species_name = set(t.tag.value for t in predicted_tags)
        db_species_stats = {}

        for species_name in db_species_name:
            species_probabilities = [
                t.classification_probability
                for t in predicted_tags
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
                "mean_low_threshold": round(
                    mean(
                        [
                            d
                            for d in species_probabilities
                            if d <= self.low_band_threshold
                        ]
                    ),
                    3,
                ),
                "mean_mid_threshold": round(
                    mean(
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
                "mean_high_threshold": round(
                    mean(
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

        db_species_stats['species_stats'] = db_species_stats

        db_species_stats['timeinterval'] = {
            "starttime": (now - self.interval).isoformat(),
            "endtime": now.isoformat(),
        }

        return data.Message(content=json.dumps(db_species_stats))
