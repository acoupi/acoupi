from typing import List

from pydantic import BaseModel

from acoupi import data
from acoupi.components import FullModelOutputMessageBuilder, types
from acoupi.programs import (
    AcoupiProgram,
)
from acoupi.programs.templates import DetectionConfig, DetectionProgramMixin


class ModelConfig(BaseModel):
    threshold: float


class Config(DetectionConfig[ModelConfig]):
    model: ModelConfig


class Model(types.Model):
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def run(self, recording: data.Recording) -> data.ModelOutput:
        return data.ModelOutput(name_model="test2", recording=recording)

    @classmethod
    def from_config(cls, config: ModelConfig) -> "Model":
        return cls(threshold=config.threshold)


class Program(DetectionProgramMixin[ModelConfig], AcoupiProgram):
    config_schema = Config

    model_class = Model

    def get_message_factories(
        self,
        config: Config,
    ) -> List[types.MessageBuilder]:
        return [
            FullModelOutputMessageBuilder(),
        ]
