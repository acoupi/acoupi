"""Test Summariser."""

import datetime
from pathlib import Path
from typing import List

import pytest

from acoupi import data
from acoupi.components import summariser


@pytest.fixture
def create_test_model_output():
    """Return a model output."""
    deployment = data.Deployment(
        name="test_deployment",
    )

    recording = data.Recording(
        path=Path("test.wav"),
        duration=1,
        samplerate=256000,
        audio_channels=1,
        deployment=deployment,
        created_on=datetime.datetime.now(),
    )

    def factory(
        tags: List[data.PredictedTag],
    ) -> data.ModelOutput:
        """Return a model output."""
        return data.ModelOutput(
            recording=recording,
            name_model="test_model",
            tags=tags,
        )

    return factory


@pytest.fixture
def create_test_predictedtags():
    """Fixture for creating random predicted tags.

    Will create multiple random tags.
    """

    def factory(
        tag_key: str = "species",
    ) -> List[data.PredictedTag]:
        """Return a random detection."""
        return [
            data.PredictedTag(
                tag=data.Tag(
                    key=tag_key,
                    value="specie_a",
                ),
                confidence_score=0.45,
            ),
            data.PredictedTag(
                tag=data.Tag(
                    key=tag_key,
                    value="specie_b",
                ),
                confidence_score=0.65,
            ),
            data.PredictedTag(
                tag=data.Tag(
                    key=tag_key,
                    value="specie_c",
                ),
                confidence_score=0.85,
            ),
        ]

    return factory

    def test_get_species_name(
        create_test_model_output,
        create_test_predictedtags,
    ):
        """Test get species name."""
        model_output = create_test_model_output(
            tags=create_test_predictedtags(),
        )
        summariser_tester = summariser.Summariser(
            threshold_lowband=0.5,
            threshold_midband=0.7,
            threshold_highband=0.9,
        )
        species_name = summariser_tester.get_species_name(
            model_outputs=[model_output],
        )
        assert species_name == ["specie_a", "specie_b", "specie_c"]

    def test_get_species_count_in_bands(
        create_test_model_output,
        create_test_predictedtags,
    ):
        """Test get species count in bands."""
        model_output = create_test_model_output(
            tags=create_test_predictedtags(),
        )
        summariser_tester = summariser.Summariser(
            threshold_lowband=0.5,
            threshold_midband=0.7,
            threshold_highband=0.9,
        )
        species_count = summariser_tester.get_species_count_in_bands(
            species_name="specie_c",
            model_outputs=[model_output],
        )
        assert species_count == {
            "low_band": 0,
            "mid_band": 0,
            "high_band": 1,
        }

        def test_build_summary(
            create_test_model_output,
            create_test_predictedtags,
        ):
            """Test build summary."""
            model_output = create_test_model_output(
                tags=create_test_predictedtags(),
            )
            summariser_tester = summariser.Summariser(
                threshold_lowband=0.5,
                threshold_midband=0.7,
                threshold_highband=0.9,
            )
            summary = summariser_tester.build_summary(
                model_outputs=[model_output],
            )
            assert summary == data.Message(
                species_count={
                    "specie_a": {
                        "low_band": 0,
                        "mid_band": 0,
                        "high_band": 0,
                    },
                    "specie_b": {
                        "low_band": 1,
                        "mid_band": 0,
                        "high_band": 0,
                    },
                    "specie_c": {
                        "low_band": 0,
                        "mid_band": 0,
                        "high_band": 1,
                    },
                },
            )
