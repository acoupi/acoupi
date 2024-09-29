import datetime
import logging
from typing import Callable, List, Optional, TypeVar

from acoupi import data
from acoupi.components import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


T = TypeVar("T", bound=types.RecordingCondition, covariant=True)


def generate_recording_task(
    recorder: types.AudioRecorder,
    store: types.Store,
    logger: logging.Logger = logger,
    recording_conditions: Optional[List[T]] = None,
) -> Callable[[], Optional[data.Recording]]:
    """Generate a recording task."""

    def recording_task() -> Optional[data.Recording]:
        """Record audio."""
        now = datetime.datetime.now()
        logger.info("Starting recording process.")

        # Check if recording conditions are met
        if not all(
            condition.should_record(now)
            for condition in recording_conditions or []
        ):
            # If conditions are not met exit process
            logger.info("Recording conditions not met.")
            return

        # Get current deployment
        deployment = store.get_current_deployment()

        # Record audio
        logger.info("Recording audio")
        recording = recorder.record(deployment)

        # Store recording metadata
        store.store_recording(recording)
        logger.info("Recording metadata stored")

        return recording

    return recording_task
