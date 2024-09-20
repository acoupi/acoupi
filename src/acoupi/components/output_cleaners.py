"""ModelOutput cleaners for acoupi.

ModelOutput Cleaners are responsible for cleaning the outputs of a model (i.e., detections) that
does not meet certain criteria. This can include removing low confidence tags and detections, or
detections and tags that have a specific labels. The ThresholdDetectionCleaner removes any predictions
(i.e., detections and tags) with a probability below a threshold.

The ModelOutputCleaner is implemented as a class that inherits from ModelOutputCleaner. The class
should implement the clean method, which takes a data.ModelOutput object and returns
a cleaned data.ModelOutput object. The modeloutput that does not meet the criteria are removed.

The ModelOutputCleaner is used in the detection task to clean the outputs of the model BEFORE storing
them in the store. The ModelOutputCleaner is passed to the detection task as a list of ModelOutputCleaner
objects. This allows to use multiple ModelOutputCleaners to clean the model output.
"""

from typing import List

from acoupi import data
from acoupi.components import types


class ThresholdDetectionCleaner(types.ModelOutputCleaner):
    """Keeps predictions with a probability higher than a threshold.

    This class implements a model output cleaner that removes any
    predictions with a probability below a threshold. This includes
    removing low confidence tags and detections.
    """

    detection_threshold: float
    """The threshold to use to define when a detection is confident vs. unconfident."""

    def __init__(self, detection_threshold: float):
        """Initiatlise the filter."""
        self.detection_threshold = detection_threshold

    def get_clean_tags(self, tags: List[data.PredictedTag]) -> List[data.PredictedTag]:
        """Remove tags with low probability."""
        return [tag for tag in tags if tag.confidence_score >= self.detection_threshold]

    def get_clean_detections(
        self, detections: List[data.Detection]
    ) -> List[data.Detection]:
        """Remove detections with low probability."""
        return [
            self.clean_detection(detection)
            for detection in detections
            if detection.detection_probability >= self.detection_threshold
        ]

    def clean_detection(self, detection: data.Detection) -> data.Detection:
        """Remove tags with low probability from detection."""
        return data.Detection(
            id=detection.id,
            location=detection.location,
            detection_probability=detection.detection_probability,
            tags=self.get_clean_tags(detection.tags),
        )

    def clean(self, model_output: data.ModelOutput) -> data.ModelOutput:
        """Clean the model output.

        Parameters
        ----------
        model_output : data.ModelOutput
            The model output to clean.

        Returns
        -------
        data.ModelOutput
            The cleaned model output.

        Examples
        --------
        >>> model_output = data.ModelOutput(
        ...     detections=[
        ...         data.Detection(
        ...             detection_probability=0.8,
        ...             tags=[
        ...                 data.PredictedTag(
        ...                     tag=data.Tag(
        ...                         key="species", value="species_1"
        ...                     ),
        ...                     confidence_score=0.7,
        ...                 )
        ...             ],
        ...             tags=[
        ...                 data.PredictedTag(
        ...                     tag=data.Tag(
        ...                         key="species", value="species_2"
        ...                     ),
        ...                     confidence_score=0.4,
        ...                 )
        ...             ],
        ...         )
        ...     ]
        ... )
        >>> cleaner = ThresholdDetectionCleaner(detection_threshold=0.6)
        >>> model_output = cleaner.clean(model_output)
        >>> assert model_output == data.ModelOutput(
        ...     detections=[
        ...         data.Detection(
        ...             detection_probability=0.8,
        ...             tags=[
        ...                 data.PredictedTag(
        ...                     tag=data.Tag(
        ...                         key="species", value="species_1"
        ...                     ),
        ...                     confidence_score=0.7,
        ...                 )
        ...             ],
        ...         )
        ...     ]
        ... )
        """
        return data.ModelOutput(
            name_model=model_output.name_model,
            recording=model_output.recording,
            tags=self.get_clean_tags(model_output.tags),
            detections=self.get_clean_detections(model_output.detections),
        )
