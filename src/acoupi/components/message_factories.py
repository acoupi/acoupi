"""Message factories for acoupi."""
import json
from typing import Dict

from acoupi import data
from acoupi.components import types

__all__ = [
    "FullModelOutputMessageBuilder",
    "SummaryMessageBuilder",
]


class FullModelOutputMessageBuilder(types.MessageBuilder):
    """A MessageBuilder that builds message from model outputs.

    This message builder builds a message from a model output. The created
    message will contain the full model output as a JSON string. This
    includes information about:

    - the model used.
    - the recording processed, including deployment info.
    - the predicted tags at the recording level.
    - predicted detections with their tags and confidence scores.
    """

    def build_message(self, model_output: data.ModelOutput) -> data.Message:
        """Build a message from a recording and model outputs."""
        return data.Message(content=model_output.model_dump_json())


class SummaryMessageBuilder(types.MessageBuilder):
    """A SummaryMessageBuilder that builds message from summariser outputs.

    This mesage builder builds a message from a summary. The created
    message will contain the summary as a JSON string. This includes
    information about:

    - the summary content.
    - the summary timeinterval with starttime and endtime.
    """

    def build_message(
        self, timeinterval: Dict, summary_content: Dict
    ) -> data.Message:
        """Build a message from a recording and model outputs."""
        return data.Message(
            content=json.dumps(
                {"timeinterval": timeinterval, "summary_content": summary_content}
            )
        )
