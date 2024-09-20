"""Summariser for acoupi.

Summarisers are responsible for summarising model outputs (i.e., detections).
Summarisers output a summary of type data.Message. The StatisticsDetectionsSummariser
summarises the detections by calculating the mean, min, max, and count of classifications
probabilities for each species. The ThresholdsDetectionsSummariser summarises the detections
by calculating the count and mean of classifications probabilities for each species
that fall within a low, mid, and high threshold.

The message output by the Summarisers is then used by the Messenger to send the summary
to a remote server. Summarisers are implemented as classes that inherit from Summariser.
Implemntation of the Summarisers should refer to the database, where the classifications
probabilities are stored. The class should implement the build_summary method, which
takes a datetime.datetime object and returns a message in JSON format.
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
    """Summarises detections by calculating the mean, min, max, and count of classification probabilities for each species."""

    store: SqliteStore
    """The store to get the detections from."""

    interval: datetime.timedelta
    """The interval to get the detections from."""

    def __init__(
        self,
        store: SqliteStore,
        interval: Union[float, int, datetime.timedelta] = 120,
    ):
        """Initialise the Summariser."""
        if isinstance(interval, (float, int)):
            interval = datetime.timedelta(minutes=interval)

        self.store = store
        self.interval = interval

    def build_summary(self, now: datetime.datetime) -> data.Message:
        """Build a message from a summary.

        Parameters
        ----------
        now : datetime.datetime
            The current time to get the detections from.
        self.store.get_predicted_tags : List[data.PredictedTag]
            The predicted tags from the store associated with the audio recordings that falls
            within the time interval (current_time - interval_minute).

        Returns
        -------
        data.Message
            A message containing the summary of the detections. The summary includes the mean,
            min, max, and count of classification probabilities for each species.

        Examples
        --------
        >>> store = SqliteStore("test.db")
        >>> summariser = StatisticsDetectionsSummariser(store)
        >>> now = datetime.datetime.now()
        >>> summariser.build_summary(now)
        ... summary_message = data.Message(
        ...     content='{
        ...         "species_1": {
        ...             "mean": 0.5,
        ...             "min": 0.1,
        ...             "max": 0.9,
        ...             "count": 10},
        ...         "species_2": {
        ...             "mean": 0.6,
        ...             "min": 0.2,
        ...             "max": 0.8,
        ...             "count": 20},
        ...         "timeinterval": {
        ...             "starttime": "2021-01-01T00:00:00",
        ...             "endtime": "2021-01-01T00:10:00"}
        ...     }'
        ... )
        """
        predicted_tags = self.store.get_predicted_tags(
            before=now,
            after=now - self.interval,
        )

        db_species_name = set(t.tag.value for t in predicted_tags)
        db_species_stats = {}

        for species_name in db_species_name:
            species_probabilities = [
                t.confidence_score
                for t in predicted_tags
                if t.tag.value == species_name
            ]

            stats = {
                "mean": round(mean(species_probabilities), 3),
                "min": min(species_probabilities),
                "max": max(species_probabilities),
                "count": len(species_probabilities),
            }

            db_species_stats[species_name] = stats

        db_species_stats["timeinterval"] = {
            "starttime": (now - self.interval).isoformat(),
            "endtime": now.isoformat(),
        }

        return data.Message(content=json.dumps(db_species_stats))


class ThresholdsDetectionsSummariser(types.Summariser):
    """Summariser that summarises detections by classification score thresholds."""

    store: SqliteStore
    """The store to get the detections from."""

    interval: datetime.timedelta
    """The interval to get the detections from."""

    def __init__(
        self,
        store: SqliteStore,
        interval: Union[float, int, datetime.timedelta] = 120,
        low_band_threshold: float = 0.1,
        mid_band_threshold: float = 0.5,
        high_band_threshold: float = 0.9,
    ):
        """Initialise the Summariser.

        Parameters
        ----------
        low_band_threshold: float, optional
            The lower threshold for the classification score, by default 0.1.
        mid_band_threshold: float, optional
            The middle threshold for the classification score, by default 0.5.
        high_band_threshold: float, optional
            The higher threshold for the classification score, by default 0.9.
        """
        self.store = store

        if isinstance(interval, (float, int)):
            interval = datetime.timedelta(minutes=interval)

        self.interval = interval
        self.low_band_threshold = low_band_threshold
        self.mid_band_threshold = mid_band_threshold
        self.high_band_threshold = high_band_threshold

    def build_summary(self, now: datetime.datetime) -> data.Message:
        """Build a message from a summary.

        Parameters
        ----------
        now : datetime.datetime
            The current time to get the detections from.
        self.store.get_predicted_tags : List[data.PredictedTag]
            The predicted tags from the store associated with the audio recordings that falls
            within the time interval (current_time - interval_minute).

        Returns
        -------
        data.Message
            A message containing the summary of the detections. The summary includes the count
            and mean of classification probabilities for each species that fall within a low, mid,
            and high threshold.

        Examples
        --------
        >>> store = SqliteStore("test.db")
        >>> summariser = ThresholdsDetectionsSummariser(store)
        >>> now = datetime.datetime.now()
        >>> summariser.build_summary(now)
        ... summary_message = data.Message(
        ...     content='{
        ...         "species_1": {
        ...             "count_low_threshold": 10, "count_mid_threshold": 20, "count_high_threshold": 30,
        ...             "mean_low_threshold": 0.1, "mean_mid_threshold": 0.5, "mean_high_threshold": 0.9},
        ...         "species_2": {
        ...             "count_low_threshold": 15, "count_mid_threshold": 25, "count_high_threshold": 35,
        ...             "mean_low_threshold": 0.2, "mean_mid_threshold": 0.6, "mean_high_threshold": 0.8},
        ...         "timeinterval": {
        ...             "starttime": "2021-01-01T00:00:00",
        ...             "endtime": "2021-01-01T00:10:00"}
        ...    }'
        ... )
        """
        predicted_tags = self.store.get_predicted_tags(
            before=now,
            after=now - self.interval,
        )

        db_species_name = set(t.tag.value for t in predicted_tags)
        db_species_stats = {}

        for species_name in db_species_name:
            species_probabilities = [
                t.confidence_score
                for t in predicted_tags
                if t.tag.value == species_name
            ]

            stats = {
                "count_low_threshold": len(
                    [d for d in species_probabilities if d <= self.low_band_threshold]
                ),
                "count_mid_threshold": len(
                    [
                        d
                        for d in species_probabilities
                        if self.low_band_threshold < d <= self.mid_band_threshold
                    ]
                ),
                "count_high_threshold": len(
                    [d for d in species_probabilities if self.mid_band_threshold < d]
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
                            if self.low_band_threshold < d <= self.mid_band_threshold
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

        db_species_stats["timeinterval"] = {
            "starttime": (now - self.interval).isoformat(),
            "endtime": now.isoformat(),
        }

        return data.Message(content=json.dumps(db_species_stats))
