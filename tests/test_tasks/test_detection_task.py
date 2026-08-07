"""Test suite for the detection task generator."""

from unittest.mock import call

from acoupi import data
from acoupi.tasks import generate_detection_task


def test_detection_task_stores_all_messages_from_builder(
    recording,
    model_output,
    mocker,
):
    """Test that detection tasks store every message returned by a builder."""
    model = mocker.Mock()
    model.run.return_value = model_output
    store = mocker.Mock()
    message_store = mocker.Mock()
    messages = [
        data.Message(content="first"),
        data.Message(content="second"),
    ]
    message_factory = mocker.Mock()
    message_factory.build_message.return_value = messages

    task = generate_detection_task(
        store=store,
        model=model,
        message_store=message_store,
        message_factories=[message_factory],
    )

    task(recording)

    message_factory.build_message.assert_called_once_with(model_output)
    assert message_store.store_message.call_args_list == [
        call(messages[0]),
        call(messages[1]),
    ]


def test_detection_task_still_stores_single_message(
    recording,
    model_output,
    mocker,
):
    """Test that existing single-message builder behaviour is preserved."""
    model = mocker.Mock()
    model.run.return_value = model_output
    store = mocker.Mock()
    message_store = mocker.Mock()
    message = data.Message(content="single")
    message_factory = mocker.Mock()
    message_factory.build_message.return_value = message

    task = generate_detection_task(
        store=store,
        model=model,
        message_store=message_store,
        message_factories=[message_factory],
    )

    task(recording)

    message_store.store_message.assert_called_once_with(message)


def test_detection_task_skips_none_message_from_builder(
    recording,
    model_output,
    mocker,
):
    """Test that builders can still opt out by returning None."""
    model = mocker.Mock()
    model.run.return_value = model_output
    store = mocker.Mock()
    message_store = mocker.Mock()
    message_factory = mocker.Mock()
    message_factory.build_message.return_value = None

    task = generate_detection_task(
        store=store,
        model=model,
        message_store=message_store,
        message_factories=[message_factory],
    )

    task(recording)

    message_factory.build_message.assert_called_once_with(model_output)
    message_store.store_message.assert_not_called()
