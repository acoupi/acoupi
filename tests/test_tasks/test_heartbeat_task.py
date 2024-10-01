import datetime
from unittest.mock import Mock

import pytest

from acoupi import data
from acoupi.devices import get_device_id
from acoupi.tasks import generate_heartbeat_task


def test_heartbeat_task_sends_message(patched_now):
    messenger = Mock()

    now = datetime.datetime(2024, 1, 1)
    patched_now(now)
    device_id = get_device_id()

    task = generate_heartbeat_task(messengers=[messenger])

    task()

    messenger.send_message.assert_called()
    calls = messenger.send_message.mock_calls
    assert len(calls) == 1
    call = calls[0]
    message = call[1][0]
    assert isinstance(message, data.Message)
    assert device_id in message.content
    assert now.isoformat() in message.content


def test_heartbeat_task_send_message_with_all_messengers():
    messenger1 = Mock()
    messenger2 = Mock()

    task = generate_heartbeat_task(messengers=[messenger1, messenger2])

    task()

    messenger1.send_message.assert_called()
    messenger2.send_message.assert_called()


def test_generate_heartbeat_task_fails_if_no_messengers_are_provided():
    with pytest.raises(ValueError):
        generate_heartbeat_task(messengers=[])
