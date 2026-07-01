"""Utility helpers for the Textual config TUI."""

from __future__ import annotations

import datetime as dt
import json
import types
from enum import Enum
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel
from pydantic import ValidationError
from typing_extensions import Annotated, get_args, get_origin


def titleize(name: str) -> str:
    return name.replace("_", " ").strip().capitalize()


def json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def split_annotated(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    if get_origin(annotation) == Annotated:
        args = get_args(annotation)
        return args[0], tuple(args[1:])
    return annotation, ()


def is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    return origin in (Union, types.UnionType) and type(None) in get_args(
        annotation
    )


def strip_optional(annotation: Any) -> Any:
    if not is_optional(annotation):
        return annotation
    args = tuple(arg for arg in get_args(annotation) if arg is not type(None))
    if len(args) == 1:
        return args[0]
    return Union[args]


def unwrap_annotation(annotation: Any) -> tuple[Any, tuple[Any, ...]]:
    base, metadata = split_annotated(annotation)
    base = strip_optional(base)
    nested_base, nested_metadata = split_annotated(base)
    return nested_base, metadata + nested_metadata


def is_basemodel_type(annotation: Any) -> bool:
    try:
        return isinstance(annotation, type) and issubclass(
            annotation, BaseModel
        )
    except TypeError:
        return False


def default_value(field: Any) -> Any:
    if field.default_factory is not None:
        return field.get_default(call_default_factory=True)
    if getattr(field, "default", None) is not None:
        return field.default
    return None


def get_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = data
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def set_value(data: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    current = data
    for part in path[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    if value is None:
        current.pop(path[-1], None)
    else:
        current[path[-1]] = value


def coerce_scalar(annotation: Any, raw: str) -> Any:
    if annotation is str:
        return raw
    if annotation is int:
        return int(raw)
    if annotation is float:
        return float(raw)
    if annotation is bool:
        lower = raw.strip().lower()
        if lower in {"true", "t", "yes", "y", "1", "on"}:
            return True
        if lower in {"false", "f", "no", "n", "0", "off"}:
            return False
        raise ValueError("Enter yes/no or true/false.")
    if annotation is Path:
        return Path(raw).expanduser()
    if annotation is dt.time:
        return dt.time.fromisoformat(raw)
    if annotation is dt.date:
        return dt.date.fromisoformat(raw)
    if annotation is dt.datetime:
        return dt.datetime.fromisoformat(raw)
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        for option in annotation:
            if raw == option.name or raw == str(option.value):
                return option
        raise ValueError("Choose one of the listed options.")
    return raw


def to_display_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, BaseModel):
        return json.dumps(value.model_dump(mode="json"), indent=2)
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, indent=2, default=str)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Enum):
        return str(value.value)
    if isinstance(value, (dt.date, dt.time, dt.datetime)):
        return value.isoformat()
    return str(value)


def friendly_type_name(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin is list:
        return "List"
    if origin is dict:
        return "Object"
    if origin is tuple:
        return "List"
    if isinstance(annotation, type) and issubclass(annotation, Enum):
        return "Choice"
    if annotation is Path:
        return "Path"
    if annotation is dt.time:
        return "Time"
    if annotation is dt.date:
        return "Date"
    if annotation is dt.datetime:
        return "Date and time"
    if annotation is bool:
        return "On or off"
    if annotation is int:
        return "Whole number"
    if annotation is float:
        return "Number"
    if annotation is str:
        return "Text"
    if is_basemodel_type(annotation):
        return "Section"
    return getattr(annotation, "__name__", "Value")


def summarize_value(value: Any) -> str:
    if value is None:
        return "missing"
    if isinstance(value, dict):
        return f"{len(value)} items"
    if isinstance(value, list):
        return f"{len(value)} items"
    text = to_display_value(value).replace("\n", " ")
    return text[:28] + ("..." if len(text) > 28 else "")


def validation_errors_by_path(error: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for item in error.errors():
        location = item.get("loc", ())
        if not location:
            continue
        path = ".".join(str(part) for part in location)
        errors[path] = item.get("msg", "Invalid value")
    return errors
