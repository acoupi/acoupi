"""Storages for acoupi.

Storages are used to store recordings and detections locally. The
stores keep track of the recordings and detections that have been
made. The stored data can be retrieved later to be sent to a 
remote server.

Storages are implemented as classes that inherit from Storage.
The class should implement the methods for storing and retrieving
data, as well as the methods for retrieving the current deployment
and the recordings and detections for a given deployment. See
the Storage class for more details.

"""

from acoupi.storages.sqlite import SqliteStore


__all__ = [
    "SqliteStore",
]
