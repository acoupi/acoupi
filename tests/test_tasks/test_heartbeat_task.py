import datetime
import json
from unittest.mock import Mock

import pytest

from acoupi import data
from acoupi.devices import get_device_id
from acoupi.tasks import generate_heartbeat_task


class TestGenerateHeartbeatTask:
    def test_fails_if_no_messengers_are_provided(self):
        """Require at least one messenger to build the task."""
        with pytest.raises(ValueError):
            generate_heartbeat_task(messengers=[])


class TestHeartbeatTask:
    def test_sends_message(self, patched_now):
        """Send a JSON heartbeat message with the current device id."""
        messenger = Mock()

        now = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
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
        assert isinstance(message.content, str)
        assert device_id in message.content
        payload = json.loads(message.content)
        assert payload["sent_on"] == "2024-01-01T00:00:00Z"

    def test_sends_message_with_all_messengers(self):
        """Send the same heartbeat through each configured messenger."""
        messenger1 = Mock()
        messenger2 = Mock()

        task = generate_heartbeat_task(messengers=[messenger1, messenger2])

        task()

        messenger1.send_message.assert_called()
        messenger2.send_message.assert_called()

    def test_includes_metrics_in_payload(self):
        """Serialize collected metrics into the heartbeat payload."""
        messenger = Mock()

        task = generate_heartbeat_task(
            messengers=[messenger],
            metrics=[
                lambda: data.Metric(
                    name="cpu_usage", value=12.5, unit="percent"
                )
            ],
        )

        task()

        message = messenger.send_message.mock_calls[0][1][0]
        payload = json.loads(message.content)
        assert payload["metrics"] == [
            {
                "name": "cpu_usage",
                "value": 12.5,
                "captured_on": payload["metrics"][0]["captured_on"],
                "unit": "percent",
            }
        ]

    def test_uses_custom_serializer(self):
        """Use the provided serializer output as the message content."""
        messenger = Mock()
        serializer = Mock(return_value="serialized")

        task = generate_heartbeat_task(
            messengers=[messenger],
            serializer=serializer,
        )

        task()

        serializer.assert_called_once()
        message = messenger.send_message.mock_calls[0][1][0]
        assert message.content == "serialized"
