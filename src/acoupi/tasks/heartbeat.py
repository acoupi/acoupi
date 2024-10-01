import datetime
import logging
from typing import Callable, List

from pydantic import BaseModel, Field

from acoupi.components import types
from acoupi.data import Message
from acoupi.devices import get_device_id

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Heartbeat(BaseModel):
    sent_on: datetime.datetime = Field(default_factory=datetime.datetime.now)
    device_id: str
    status: str = "OK"


def generate_heartbeat_task(
    messengers: List[types.Messenger],
    logger: logging.Logger = logger,
) -> Callable[[], None]:
    """Generate a heartbeat task.

    The heartbeat task creates a heartbeat message and emits them using the
    provided messengers.

    Parameters
    ----------
    messengers : Optional[List[types.Messenger]]
        A list of messenger instances to pass the heartbeat message to.
    logger : logging.Logger
        Logger instance for logging heartbeat status.

    Returns
    -------
    Callable[[], None]
        A function that sends a heartbeat message when called.
    """
    if not messengers:
        raise ValueError(
            "At least one messenger is required to send a heartbeat message."
        )

    def heartbeat_task() -> None:
        device_id = get_device_id()

        now = datetime.datetime.now()

        heartbeat = Heartbeat(device_id=device_id, sent_on=now)
        message = Message(
            content=heartbeat.model_dump_json(),
            created_on=now,
        )

        for messenger in messengers:
            response = messenger.send_message(message)
            logger.info(f"Heartbeat Sent - Response Status: {response.status}")

    return heartbeat_task
