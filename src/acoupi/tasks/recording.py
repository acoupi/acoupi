"""Recording task module.

This module contains the function to generate a recording task. The recording
task is a function that records audio and stores the metadata in the store.
The recording process contains the following steps:

    1. Check if the recording conditions are met.
    2. Get the current deployment information.
    3. Record audio.
    4. Store the recording metadata in the store.
"""

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
        """Record audio.

        Returns
        -------
        Optional[data.Recording]
            The recording metadata if the recording was successful, otherwise None.

        Notes
        -----
        The recording process calls the following methods:

        condition.should_record(now) -> bool
            Check if the conditions are met to record audio.
            See acoupi.components.recording_conditions for implementations of types.RecordingCondition.
        store.get_current_deployment() -> data.Deployment
            Get the current deployment information.
            See acoupi.components.stores.sqlite.store for implementation of types.Store.
        recorder.record(deployment) -> data.Recording
            Record audio and return the recording metadata.
            See acoupi.components.audio_recorders for implementation of types.AudioRecorder.
        store.store_recording(recording) -> None
            Store the recording metadata in the store.
            See acoupi.components.stores.sqlite.store for implementation of types.Store.
        """
        logger.info("Starting recording process.")

        # Check if recording conditions are met
        if not all(
            condition.should_record()
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
