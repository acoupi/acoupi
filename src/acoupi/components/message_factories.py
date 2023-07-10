"""Message factories for acoupi."""
from acoupi import data
from acoupi.components import types

__all__ = ["FullModelOutputMessageBuilder"]


class FullModelOutputMessageBuilder(types.ModelOutputMessageBuilder):
    """A ModelOutputMessageBuilder that builds message from model outputs.

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
        print
        return data.Message(content=model_output.json())


class QEOP_MessageBuilder(types.ModelOutputMessageBuilder):
    """A ModelOutputMessageBuilder that builds message from model outputs.

    This message builder builds a message from a model output. The created
    message will contain the full model output as a JSON string. This
    includes information about:
        - the model used.
        - the recording processed, including deployment info.
        - the predicted tags at the recording level.
        - predicted detections with their tags and confidence scores.
    """

    def build_message(self) -> data.Message:
        return 
