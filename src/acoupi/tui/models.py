"""Schema model helpers for the Textual config TUI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .behaviors import FieldBehavior, extract_field_behavior
from .utils import is_basemodel_type, titleize, unwrap_annotation


@dataclass(frozen=True)
class FieldNode:
    """Description of a field in the configuration tree."""

    path: tuple[str, ...]
    field_name: str
    title: str
    annotation: Any
    field_info: Any
    parent_model: type[BaseModel]
    metadata: tuple[Any, ...]
    editor_factory: Any = None
    behavior: FieldBehavior | None = None

    @property
    def dotted_path(self) -> str:
        return ".".join(self.path)

    @property
    def description(self) -> str:
        return self.field_info.description or ""

    @property
    def required(self) -> bool:
        return self.field_info.is_required()

    @property
    def effective_annotation(self) -> Any:
        annotation, _ = unwrap_annotation(self.annotation)
        return annotation

    @property
    def is_section(self) -> bool:
        return is_basemodel_type(self.effective_annotation)

    @property
    def enum_type(self) -> type[Enum] | None:
        annotation = self.effective_annotation
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return annotation
        return None


def extract_editor_factory(metadata: tuple[Any, ...]) -> Any:
    for item in metadata:
        if isinstance(item, type):
            return item
    return None


def walk_schema(
    schema: type[BaseModel],
    prefix: tuple[str, ...] = (),
) -> list[FieldNode]:
    nodes: list[FieldNode] = []
    for field_name, field in schema.model_fields.items():
        annotation = field.annotation
        if annotation is None:
            continue

        _, metadata = unwrap_annotation(annotation)
        field_metadata = tuple(getattr(field, "metadata", ()))
        combined_metadata = metadata + field_metadata
        node = FieldNode(
            path=prefix + (field_name,),
            field_name=field_name,
            title=field.title or titleize(field_name),
            annotation=annotation,
            field_info=field,
            parent_model=schema,
            metadata=combined_metadata,
            editor_factory=extract_editor_factory(combined_metadata),
            behavior=extract_field_behavior(combined_metadata),
        )
        nodes.append(node)

        if node.is_section:
            nodes.extend(
                walk_schema(node.effective_annotation, prefix=node.path)
            )
    return nodes
