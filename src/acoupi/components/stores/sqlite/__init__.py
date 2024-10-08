"""Sqlite storage backend for acoupi.

The SqliteStore class is used to store the recordings, detections and
deployments locally. The data is stored in a sqlite database file in the given
path.

Whenever a recording or a detection is made, it should be stored to
keep track of the data. Current deployment information can be retrieved and
updated.

To use the store, create an instance of the SqliteStore class, and use the
methods to store and retrieve data.

Example:
    Load the store:

    >>> from acoupi.storages.sqlite import SqliteStore

    Create a new store instance, pointing to a database file:

    >>> store = SqliteStore("acoupi.db")

    Get the current deployment:

    >>> deployment = store.get_current_deployment()
    >>> deployment
    Deployment(id=1, started_on=datetime.datetime(2021, 1, 1, 0, 0), latitude=0, longitude=0)

    Create a new deployment:

    >>> deployment = Deployment(
    ...     started_on=datetime.datetime(2021, 1, 1, 0, 0),
    ...     device_id="0000000000000000",
    ...     latitude=0.0,
    ...     longitude=0.0,
    ... )
    >>> store.store_deployment(deployment)

    Store a new recording:

    >>> recording = Recording(
    ...     datetime=datetime.datetime(2021, 1, 1, 0, 0),
    ...     duration=10,
    ...     samplerate=44100,
    ...     audio_channels=1,
    ... )
    >>> store.store_recording(recording)

    Store a new detection:

    >>> detection = Detection(
    ...     species_name="species",
    ...     score=0.5,
    ... )
    >>> store.store_detections(recording, [detection])

"""

from acoupi.components.stores.sqlite.store import SqliteStore

__all__ = [
    "SqliteStore",
]
