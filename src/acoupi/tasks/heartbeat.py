import datetime
import logging
from typing import Callable

from pydantic import BaseModel, Field

from acoupi.components import types
from acoupi.data import Message, Metric, utc_now
from acoupi.devices import get_device_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


MetricFn = Callable[[], Metric]


class Heartbeat(BaseModel):
    sent_on: datetime.datetime = Field(default_factory=utc_now)
    device_id: str
    status: str = "OK"
    metrics: list[Metric] = Field(
        default_factory=list,
        exclude_if=lambda x: not x,
    )


HeartbeatSerializer = Callable[[Heartbeat], str | bytes]


def _to_json(heartbeat: Heartbeat) -> str:
    return heartbeat.model_dump_json()


def generate_heartbeat_task(
    messengers: list[types.Messenger],
    metrics: list[MetricFn] | None = None,
    serializer: HeartbeatSerializer = _to_json,
    logger: logging.Logger = logger,
) -> Callable[[], None]:
    """Generate a heartbeat task.

    The heartbeat task creates a heartbeat payload, optionally augments it with
    runtime metrics, serializes it, and emits it using the provided
    messengers.

    Metrics are supplied as callables so values are captured at send time. Each
    callable must return an ``acoupi.data.Metric``.

    The serializer receives the ``Heartbeat`` model and must return the message
    content as ``str`` or ``bytes``.

    Parameters
    ----------
    messengers : list[types.Messenger]
        A list of messenger instances to pass the heartbeat message to.
    metrics : list[MetricFn] | None, default=None
        Optional metric collector functions evaluated when the task runs. See
        ``acoupi.devices.metrics`` for built-in heartbeat metrics.
    serializer : HeartbeatSerializer, default=_to_json
        Function used to serialize the heartbeat payload before sending.
    logger : logging.Logger
        Logger instance for logging heartbeat status.

    Returns
    -------
    Callable[[], None]
        A function that sends a heartbeat message when called.

    Notes
    -----
    When a metric function needs arguments bound in advance, prefer
    ``functools.partial`` over lambdas so the task configuration is more
    serialization-friendly in Celery environments.

    Examples
    --------
    >>> from functools import partial
    >>> from pathlib import Path
    >>> from acoupi.devices.metrics import (
    ...     get_free_memory,
    ...     get_remaining_storage,
    ... )
    >>> task = generate_heartbeat_task(
    ...     messengers=[messenger],
    ...     metrics=[
    ...         get_free_memory,
    ...         partial(get_remaining_storage, Path("/tmp")),
    ...     ],
    ... )
    >>> task()
    """
    if not messengers:
        raise ValueError(
            "At least one messenger is required to send a heartbeat message."
        )

    def heartbeat_task() -> None:
        device_id = get_device_id()

        now = utc_now()

        measurements = [metric() for metric in metrics or []]

        heartbeat = Heartbeat(
            device_id=device_id,
            sent_on=now,
            metrics=measurements,
        )
        content = serializer(heartbeat)
        message = Message(content=content, created_on=now)

        for messenger in messengers:
            response = messenger.send_message(message)
            logger.info(f"Heartbeat Sent - Response Status: {response.status}")

    return heartbeat_task
