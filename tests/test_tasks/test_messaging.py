"""Tests for messaging tasks."""

import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from acoupi import components, data, tasks


def test_generate_send_messages_task_rejects_non_positive_max_messages():
    message_store = Mock()
    messenger = Mock()

    with pytest.raises(ValueError, match="positive integer or None"):
        tasks.generate_send_messages_task(
            message_store=message_store,
            messengers=[messenger],
            max_messages=0,
        )


def test_generate_send_messages_task_rejects_missing_messengers():
    message_store = Mock()

    with pytest.raises(ValueError, match="At least one messenger"):
        tasks.generate_send_messages_task(
            message_store=message_store,
            messengers=None,
        )


def test_generate_send_messages_task_rejects_empty_messengers():
    message_store = Mock()

    with pytest.raises(ValueError, match="At least one messenger"):
        tasks.generate_send_messages_task(
            message_store=message_store,
            messengers=[],
        )


def test_generate_send_messages_task_passes_limit_and_order_to_store():
    message_store = Mock()
    message_store.get_unsent_messages.return_value = []
    messenger = Mock()

    task = tasks.generate_send_messages_task(
        message_store=message_store,
        messengers=[messenger],
        max_messages=3,
        order="newest_first",
    )

    task()

    message_store.get_unsent_messages.assert_called_once_with(
        limit=3,
        order="newest_first",
    )


def test_generate_send_messages_task_sends_limited_messages_in_order(
    tmp_path: Path,
):
    message_store = components.SqliteMessageStore(tmp_path / "messages.db")
    messenger = Mock()
    created_on = datetime.timezone.utc
    messages = [
        data.Message(
            content=f"test message {index}",
            created_on=datetime.datetime(2024, 1, index, tzinfo=created_on),
        )
        for index in range(1, 4)
    ]

    for message in messages:
        message_store.store_message(message)

    messenger.send_message.side_effect = [
        data.Response(status=data.ResponseStatus.SUCCESS, message=messages[2]),
        data.Response(status=data.ResponseStatus.SUCCESS, message=messages[1]),
    ]

    task = tasks.generate_send_messages_task(
        message_store=message_store,
        messengers=[messenger],
        max_messages=2,
        order="newest_first",
    )

    task()

    sent_messages = [
        call.args[0].content for call in messenger.send_message.call_args_list
    ]
    assert sent_messages == [b"test message 3", b"test message 2"]

    remaining_messages = message_store.get_unsent_messages(
        order="oldest_first"
    )
    assert [message.content for message in remaining_messages] == [
        b"test message 1"
    ]
