from unittest.mock import Mock

from acoupi import data
from acoupi.tasks import generate_summariser_task


def test_summary_task_skips_storing_none_messages():
    summariser = Mock()
    summariser.build_summary.return_value = None
    message_store = Mock()

    task = generate_summariser_task(
        summarisers=[summariser],
        message_store=message_store,
    )

    task()

    summariser.build_summary.assert_called_once()
    message_store.store_message.assert_not_called()


def test_summary_task_stores_summary_messages():
    summary_message = data.Message(content="summary")
    summariser = Mock()
    summariser.build_summary.return_value = summary_message
    message_store = Mock()

    task = generate_summariser_task(
        summarisers=[summariser],
        message_store=message_store,
    )

    task()

    summariser.build_summary.assert_called_once()
    message_store.store_message.assert_called_once_with(summary_message)
