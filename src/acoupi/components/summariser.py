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
import sqlite3
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
    """The interval to get the detections from in seconds."""

    def __init__(
        self,
        store: SqliteStore,
        interval: Union[float, int, datetime.timedelta] = 3600,
    ):
        """Initialise the Summariser."""
        if isinstance(interval, (float, int)):
            interval = datetime.timedelta(seconds=interval)

        self.store = store
        self.connection = sqlite3.connect(self.store.db_path)
        self.interval = interval

    def build_summary(self, now: datetime.datetime) -> data.Message:
        """Build a message from a summary.

        Parameters
        ----------
        now : datetime.datetime
            The current time to get the detections from.

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
        start_time = now - self.interval

        # SQL query to summarize detections by confidence min, max, avg bands
        query = """
        SELECT 
            tag.value AS species_name,
            MIN(confidence_score) AS min_confidence,
            MAX(confidence_score) AS max_confidence,
            AVG(confidence_score) AS avg_confidence,
            COUNT(*) AS count_confidence
        FROM 
            predicted_tag
        WHERE 
            datetime >= ? AND datetime <= ?          -- Time interval for detections
        GROUP BY 
            tag.value
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (start_time, now))
        results = cursor.fetchall()

        db_species_stats = {
            row["species_name"]: {
                "mean": round(row["avg_confidence"], 3),
                "min": row["min_confidence"],
                "max": row["max_confidence"],
                "count": row["count_confidence"],
            }
            for row in results
        }

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
    """The interval to get the detections from in seconds."""

    def __init__(
        self,
        store: SqliteStore,
        interval: Union[float, int, datetime.timedelta] = 3600,
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
        self.connection = sqlite3.connect(self.store.db_path)

        if isinstance(interval, (float, int)):
            interval = datetime.timedelta(seconds=interval)

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
        start_time = now - self.interval

        # SQL query to summarize detections by confidence bands
        query = """
        SELECT 
            tag.value AS species_name,
            SUM(CASE WHEN confidence_score >= ? AND confidence_score < ? THEN 1 ELSE 0 END) AS low_band_count,
            SUM(CASE WHEN confidence_score >= ? AND confidence_score < ? THEN 1 ELSE 0 END) AS mid_band_count,
            SUM(CASE WHEN confidence_score >= ? THEN 1 ELSE 0 END) AS high_band_count
        FROM 
            predicted_tag
        WHERE 
            datetime >= ? AND datetime <= ?           -- Time interval for detections
        GROUP BY 
            tag.value                                
        """

        cursor = self.connection.cursor()
        cursor.execute(
            query,
            (
                self.low_band_threshold,
                self.mid_band_threshold,
                self.mid_band_threshold,
                self.high_band_threshold,
                self.high_band_threshold,
                start_time,
                now,
            ),
        )
        results = cursor.fetchall()

        db_species_stats = {
            row["species_name"]: {
                "low_band_count": row["low_band_count"],
                "mid_band_count": row["mid_band_count"],
                "high_band_count": row["high_band_count"],
            }
            for row in results
        }

        db_species_stats["timeinterval"] = {
            "starttime": (now - self.interval).isoformat(),
            "endtime": now.isoformat(),
        }

        return data.Message(content=json.dumps(db_species_stats))
