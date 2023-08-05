"""Argument Parsing for configs."""

import argparse
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import click
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import Protocol, get_args, get_origin

from acoupi.programs.configs import BaseConfigSchema, NoUserPrompt

__all__ = [
    "parse_config_from_args",
]


A = TypeVar("A", bound=BaseConfigSchema)


ArgumentParserProtocol = Union[
    argparse.ArgumentParser,
    argparse._ArgumentGroup,
]


def parse_config_from_args(
    schema: Type[A],
    args: Optional[List[str]] = None,
    prompt: bool = True,
) -> A:
    """Parse configurations from user provided arguments.

    This function will parse the configurations from the user provided
    in the command line arguments. It will return the parsed
    configuration.

    It will override the default configuration with the user provided
    configuration, and ask the user for any missing configuration.

    This function will raise an error if the user provided configuration
    is invalid.

    Parameters
    ----------
    schema: Type[A]
        The configuration schema to use.
    args: Optional[list[str]]
        The arguments to parse. If None, will use an empty list.
    prompt: bool
        Whether to prompt the user for missing configuration.

    Returns
    -------
    config
        The parsed configuration.

    """
    if args is None:
        args = []

    values = {}
    for field_name, field in schema.model_fields.items():
        instance = parse_field_from_args(
            field_name,
            field,
            args,
            prompt=prompt,
        )
        values[field_name] = instance
    try:
        return schema(**values)
    except ValidationError as error:
        raise argparse.ArgumentError(
            None,
            f"Invalid configuration: {error}.",
        ) from error


def should_prompt(field: FieldInfo, prompt: bool = True) -> bool:
    """Check whether a field should be prompted to the user."""
    if not prompt:
        return False

    if hasattr(field, "metadata"):
        return NoUserPrompt not in field.metadata

    return True


def get_field_dtype(field: FieldInfo) -> type:
    """Get the dtype of a field."""
    annotation = field.annotation

    if annotation is None:
        raise ValueError(f"Field {field} has no annotation.")

    # Remove typing.Annotated if present
    if hasattr(annotation, "__metadata__"):
        annotation = get_args(annotation)[0]

    origin = get_origin(annotation)
    if origin is None:
        return annotation

    return origin


def parse_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    parent: str = "",
) -> object:
    """Parse a field from the command line arguments."""
    for dtype, _parse_argument in FIELD_PARSERS.items():
        if issubclass(get_field_dtype(field), dtype):
            return _parse_argument(
                field_name,
                field,
                args,
                prompt=should_prompt(field, prompt=prompt),
                parent=parent,
            )

    raise NotImplementedError(f"Cannot parse argument for field {field}.")


def parse_pydantic_model_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: list[str],
    prompt: bool = True,
    parent: str = "",
) -> BaseModel:
    """Parse a pydantic model field from the command line arguments."""
    model = field.annotation

    if model is None:
        raise ValueError(f"Field {field} has no annotation.")

    if not issubclass(model, BaseModel):
        raise ValueError(f"Field {field} is not a pydantic model.")

    parent = f"{parent}.{field_name}" if parent else field_name

    values = {}
    for field_name, field in model.model_fields.items():
        instance = parse_field_from_args(
            field_name,
            field,
            args,
            prompt=prompt,
            parent=parent,
        )
        values[field_name] = instance

    return model(**values)


def parse_list_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    parent: str = "",
    max_items: int = 20,
) -> list:
    """Parse a list field from the command line arguments.

    Will assume that the list elements are strings.
    """
    parser = argparse.ArgumentParser()
    name = f"--{parent}.{field_name}" if parent else f"--{field_name}"

    for num_item in range(max_items):
        parser.add_argument(
            f"{name}.{num_item}",
            dest=f"item_{num_item}",
            type=str,
            help=field.description,
        )
    parsed_args, _ = parser.parse_known_args(args)
    value = [
        getattr(parsed_args, f"item_{num_item}")
        for num_item in range(max_items)
        if getattr(parsed_args, f"item_{num_item}") is not None
    ]

    if not prompt:
        return value

    return value


def parse_tuple_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    parent: str = "",
) -> tuple:
    """Parse a tuple field from the command line arguments."""
    parser = argparse.ArgumentParser()
    name = f"--{parent}.{field_name}" if parent else f"--{field_name}"
    parser.add_argument(
        name,
        dest="value",
        type=str,
        default=field.default,
        nargs="+",
        help=field.description,
    )
    parsed_args, _ = parser.parse_known_args(args)

    if not prompt:
        return tuple(parsed_args.value)

    return tuple(parsed_args.value)


def cast_to_bool(value: str) -> bool:
    """Cast a string to a boolean."""
    lower = value.lower()

    if lower in ["true", "t", "yes", "y"]:
        return True

    if lower in ["false", "f", "no", "n"]:
        return False

    raise ValueError(f"Cannot cast {value} to boolean.")


class FieldParser(Protocol):
    """Protocol for field parser."""

    def __call__(
        self,
        field_name: str,
        field: FieldInfo,
        args: list[str],
        prompt: bool = True,
        parent: str = "",
    ) -> object:
        """Parse a field from the command line arguments."""


DType = Union[
    type,
    Callable[[str], Any],
]


def build_simple_field_parser(dtype: DType) -> FieldParser:
    def field_parser(
        field_name: str,
        field: FieldInfo,
        args: List[str],
        prompt: bool = True,
        parent: str = "",
    ):
        parser = argparse.ArgumentParser()
        name = f"{parent}.{field_name}" if parent else f"{field_name}"

        default = (
            field.default if field.default is not PydanticUndefined else None
        )

        action = parser.add_argument(
            f"--{name}",
            dest="value",
            type=dtype,
            default=default,
            help=field.description,
        )
        parsed_args, _ = parser.parse_known_args(args)
        value = parsed_args.value

        if not prompt:
            if value is None and default is None:
                raise argparse.ArgumentError(
                    action, f"Missing value for {field_name}."
                )

            return value

        if value is not None:
            if click.confirm(
                "Would you like to set "
                f"{click.style(name, fg='blue', bold=True)}="
                f"{click.style(repr(value), fg='yellow', bold=True)}?",
                default=True,
            ):
                return value

        help = (
            click.style(f" Help: {field.description}", italic=True)
            if field.description
            else ""
        )

        return click.prompt(
            (
                "Please provide a value for "
                f"{click.style(name, fg='blue', bold=True)}."
                f"{help}"
            ),
            type=dtype,
            default=field.default,
        )

    return field_parser


FIELD_PARSERS: Dict[type, FieldParser] = {
    BaseModel: parse_pydantic_model_field_from_args,
    bool: build_simple_field_parser(cast_to_bool),
    str: build_simple_field_parser(str),
    int: build_simple_field_parser(int),
    float: build_simple_field_parser(float),
    list: parse_list_field_from_args,
    tuple: parse_tuple_field_from_args,
}
