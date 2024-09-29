"""Test acoupi recording filters."""

from acoupi import components, data


def test_focus_species_filter_rejects_recordings_without_detections(
    recording: data.Recording,
):
    """Test focus species recording filter rejects recordings without detections."""
    filter = components.DetectionTags(
        tags=[data.Tag(key="species", value="test")],
        saving_threshold=0.5,
    )
    assert not filter.should_save_recording(recording, [])


def test_focus_species_filter_rejects_if_no_target_species_found(
    recording: data.Recording,
):
    """Test focus species recording filter rejects if no target species found."""
    filter = components.DetectionTags(
        tags=[data.Tag(key="species", value="test")],
        saving_threshold=0.5,
    )
    model_output = data.ModelOutput(
        name_model="test",
        recording=recording,
        detections=[
            data.Detection(
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test2"),
                        classification_probability=0.6,
                    ),
                ],
            ),
        ],
    )
    assert not filter.should_save_recording(recording, [model_output])


def test_focus_species_filter_rejects_low_confidence_detections(
    recording: data.Recording,
):
    """Test focus species recording filter rejects low confidence detections."""
    filter = components.DetectionTags(
        tags=[data.Tag(key="species", value="test")],
        saving_threshold=0.5,
    )
    model_output = data.ModelOutput(
        name_model="test",
        recording=recording,
        detections=[
            data.Detection(
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test2"),
                        classification_probability=0.4,
                    ),
                ],
            ),
        ],
    )
    assert not filter.should_save_recording(recording, [model_output])


def test_focus_species_filter_keeps_high_confidence_detections(
    recording: data.Recording,
):
    """Test focus species recording filter keeps high confidence detections."""
    filter = components.DetectionTags(
        tags=[data.Tag(key="species", value="test")],
        saving_threshold=0.5,
    )
    model_output = data.ModelOutput(
        name_model="test",
        recording=recording,
        detections=[
            data.Detection(
                detection_probability=0.6,
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test"),
                        classification_probability=0.6,
                    ),
                ],
            ),
        ],
    )

    assert filter.should_save_recording(recording, [model_output])


def test_focus_species_filter_rejects_even_with_confident_non_target(
    recording: data.Recording,
):
    """Test focus species recording filter rejects correctly.

    Even in the case with confident non-target detections.
    """
    filter = components.DetectionTags(
        tags=[data.Tag(key="species", value="test")],
        saving_threshold=0.5,
    )
    model_output = data.ModelOutput(
        name_model="test",
        recording=recording,
        detections=[
            data.Detection(
                detection_probability=0.6,
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test2"),
                        classification_probability=0.6,
                    ),
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test"),
                        classification_probability=0.4,
                    ),
                ],
            ),
        ],
    )
    assert not filter.should_save_recording(recording, [model_output])


def test_focus_species_filter_keeps_with_at_least_one_target_species(
    recording: data.Recording,
):
    """Test focus species recording filter keeps correctly.

    It should keep recordings with at least one target species detection
    with a probability above the provided threshold.
    """
    filter = components.DetectionTags(
        tags=[
            data.Tag(key="species", value="test"),
            data.Tag(key="species", value="test2"),
        ],
        saving_threshold=0.5,
    )
    model_output = data.ModelOutput(
        name_model="test",
        recording=recording,
        detections=[
            data.Detection(
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test2"),
                        classification_probability=0.6,
                    ),
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="test"),
                        classification_probability=0.4,
                    ),
                ],
            ),
        ],
    )
    assert filter.should_save_recording(recording, [model_output])
