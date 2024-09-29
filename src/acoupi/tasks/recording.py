"""Recording Task.

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
    """Generate a recording task.

    Parameters
    ----------
    recorder : types.AudioRecorder
        The audio recorder to record audio.
    store : types.Store
        The store to store the recording metadata.
    logger : logging.Logger, optional
        The logger to log messages, by default logger.
    recording_conditions : Optional[List[T]], optional
        The recording conditions to check if audio should be recorded, by
        default None.

    Returns
    -------
    Callable[[], Optional[data.Recording]]
        The recording metadata if the recording was successful, otherwise None.

    Notes
    -----
    The recording task calls the following methods:

    1. **condition.should_record(now)** -> bool
        - Check if the conditions are met to record audio.
        - See
        [components.recording_conditions][acoupi.components.recording_conditions]
        for implementations of
        [types.RecordingCondition][acoupi.components.types.RecordingCondition].
    2. **store.get_current_deployment()** -> data.Deployment
        - Get the current deployment information.
        - See [components.stores][acoupi.components.stores] for implementation
        of [types.Store][acoupi.components.types.Store].
    3. **recorder.record(deployment)** -> data.Recording
        - Record audio and return the recording metadata.
        - See [components.audio_recorders][acoupi.components.audio_recorder]
        for implementation of
        [types.AudioRecorder][acoupi.components.types.AudioRecorder].
    4. **store.store_recording(recording)** -> None
        - Store the recording metadata in the store.
        - See [components.stores][acoupi.components.stores] for implementation
        of [types.Store][acoupi.components.types.Store].
    """

    def recording_task() -> Optional[data.Recording]:
        """Record audio."""
        logger.info("Starting recording process.")

        # Check if recording conditions are met
        if not all(
            condition.should_record() for condition in recording_conditions or []
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
