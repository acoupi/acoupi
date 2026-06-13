"""Tests for detection summarisers."""

import datetime
import json
from pathlib import Path

from acoupi import data
from acoupi.components.stores import SqliteStore
from acoupi.components.summariser import ThresholdsDetectionsSummariser


def test_build_summary(tmp_path: Path) -> None:
    """Build a threshold-based summary message."""
    now = datetime.datetime(2024, 1, 1, 12, 0, 0)
    deployment = data.Deployment(name="test_deployment")
    recording = data.Recording(
        path=tmp_path / "test.wav",
        duration=1,
        samplerate=256000,
        audio_channels=1,
        deployment=deployment,
        created_on=now,
    )
    model_output = data.ModelOutput(
        recording=recording,
        name_model="test_model",
        detections=[
            data.PresenceDetection(
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="specie_a"),
                        confidence_score=0.05,
                    )
                ]
            ),
            data.PresenceDetection(
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="specie_b"),
                        confidence_score=0.45,
                    )
                ]
            ),
            data.PresenceDetection(
                tags=[
                    data.PredictedTag(
                        tag=data.Tag(key="species", value="specie_c"),
                        confidence_score=0.85,
                    )
                ]
            ),
        ],
        created_on=now,
    )
    store = SqliteStore(tmp_path / "test.db")
    store.store_recording(recording)
    store.store_model_output(model_output)
    summariser = ThresholdsDetectionsSummariser(
        store=store,
        interval=60,
        low_band_threshold=0.1,
        mid_band_threshold=0.5,
        high_band_threshold=0.9,
    )

    summary = summariser.build_summary(now)

    assert isinstance(summary, data.Message)
    payload = json.loads(summary.content)
    assert payload["specie_a"] == {
        "count_low_threshold": 1,
        "count_mid_threshold": 0,
        "count_high_threshold": 0,
        "mean_low_threshold": 0.05,
        "mean_mid_threshold": 0,
        "mean_high_threshold": 0,
    }
    assert payload["specie_b"] == {
        "count_low_threshold": 0,
        "count_mid_threshold": 1,
        "count_high_threshold": 0,
        "mean_low_threshold": 0,
        "mean_mid_threshold": 0.45,
        "mean_high_threshold": 0,
    }
    assert payload["specie_c"] == {
        "count_low_threshold": 0,
        "count_mid_threshold": 0,
        "count_high_threshold": 1,
        "mean_low_threshold": 0,
        "mean_mid_threshold": 0,
        "mean_high_threshold": 0.85,
    }
    assert payload["timeinterval"] == {
        "starttime": (now - datetime.timedelta(seconds=60)).isoformat(),
        "endtime": now.isoformat(),
    }
