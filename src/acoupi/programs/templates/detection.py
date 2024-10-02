"""Detection Program template module."""

from typing import Callable, Generic, List, Type, TypeVar

from pydantic import BaseModel

from acoupi import data
from acoupi.components import types
from acoupi.programs.templates.basic import (
    BasicConfiguration,
    BasicProgramMixin,
)
from acoupi.programs.templates.messaging import (
    MessagingConfigMixin,
    MessagingProgramMixin,
)
from acoupi.tasks import generate_detection_task

ModelConfig = TypeVar("ModelConfig", bound=BaseModel)


Self = TypeVar("Self")


class ModelProtocol(types.Model, Generic[ModelConfig]):
    @classmethod
    def from_config(cls: Type[Self], config: ModelConfig) -> Self: ...


class DetectionConfig(
    BasicConfiguration,
    MessagingConfigMixin,
    Generic[ModelConfig],
):
    model: ModelConfig


class DetectionProgramMixin(
    MessagingProgramMixin,
    BasicProgramMixin[DetectionConfig[ModelConfig]],
    Generic[ModelConfig],
):
    model: ModelProtocol[ModelConfig]

    model_class: Type[ModelProtocol[ModelConfig]]

    def setup(self, config: DetectionConfig[ModelConfig]) -> None:
        self.model = self.configure_model(config)
        super().setup(config)

    def configure_model(
        self, config: DetectionConfig[ModelConfig]
    ) -> ModelProtocol[ModelConfig]:
        return self.model_class.from_config(config.model)

    def get_output_cleaners(
        self, config: DetectionConfig[ModelConfig]
    ) -> List[types.ModelOutputCleaner]:
        return []

    def get_processing_filters(
        self, config: DetectionConfig[ModelConfig]
    ) -> List[types.ProcessingFilter]:
        return []

    def get_message_factories(
        self, config: DetectionConfig[ModelConfig]
    ) -> List[types.MessageBuilder]:
        return []

    def create_detection_task(
        self,
        config: DetectionConfig[ModelConfig],
    ) -> Callable[[data.Recording], None]:
        return generate_detection_task(
            store=self.store,
            model=self.model,
            message_store=self.message_store,
            logger=self.logger.getChild("detection"),
            output_cleaners=self.get_output_cleaners(config),
            processing_filters=self.get_processing_filters(config),
            message_factories=self.get_message_factories(config),
        )

    def get_recording_callbacks(
        self, config: DetectionConfig[ModelConfig]
    ) -> List[Callable]:
        return [self.create_detection_task(config)]

    def check(self, config: DetectionConfig[ModelConfig]):
        super().check(config)

        model_check = getattr(self.model, "check", None)
        if model_check and callable(model_check):
            model_check()
