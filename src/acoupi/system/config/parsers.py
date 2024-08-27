"""Argument Parsing for configs."""

import argparse
import datetime
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

import click
from pydantic import BaseModel, ValidationError
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from typing_extensions import Annotated, Protocol, get_args, get_origin

from acoupi.programs.core.base import NoUserPrompt
from acoupi.system.exceptions import ParameterError

__all__ = [
    "parse_config_from_args",
]


A = TypeVar("A", bound=BaseModel)


ArgumentParserProtocol = Union[
    argparse.ArgumentParser,
    argparse._ArgumentGroup,
]
"""

When configurations are nested, they can be parsed from the command
line arguments using the following syntax:

    --field.subfield=value

"""


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

    Args:
        schema: The configuration schema to use.
        args: The arguments to parse. If None, will use an empty list.
        prompt: Whether to prompt the user for missing configuration.

    Returns
    -------
        config: The parsed configuration.
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

    origin = get_origin(annotation)

    # Remove typing.Annotated if present
    if origin == Annotated:
        annotation = get_args(annotation)[0]

    # Check for optional fields and remove the
    # typing.Optional if present
    if origin == Union:
        nested = get_args(annotation)[0]
        return nested

    origin = get_origin(annotation)
    if origin is None:
        return annotation

    return origin


def parse_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    prefix: str = "",
) -> object:
    """Parse a field from the command line arguments."""
    for dtype, _parse_argument in FIELD_PARSERS.items():
        field_type = get_field_dtype(field)
        if issubclass(field_type, dtype):
            return _parse_argument(
                field_name,
                field,
                args,
                prompt=should_prompt(field, prompt=prompt),
                prefix=prefix,
            )

    raise NotImplementedError(f"Cannot parse argument for field {field}.")


def parse_pydantic_model_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    prefix: str = "",
) -> Optional[BaseModel]:
    """Parse a pydantic model field from the command line arguments."""
    model = get_field_dtype(field)

    assert issubclass(model, BaseModel)

    prefix = f"{prefix}.{field_name}" if prefix else field_name

    setup = getattr(model, "setup", None)
    if setup is not None and callable(setup):
        return setup(args, prompt=prompt, prefix=prefix)

    if not field.is_required():
        has_some_arg = any(arg.startswith(f"--{prefix}") for arg in args)
        if not has_some_arg:
            default_value = field.get_default(call_default_factory=True)

            if not prompt:
                return default_value

            if not click.confirm(
                (
                    "Would you like to set "
                    f"{click.style(field_name, fg='blue', bold=True)}?"
                ),
                default=False,
            ):
                return default_value

    if field.annotation is None:
        raise ValueError(f"Field {field} has no annotation.")

    model = get_field_dtype(field)

    if model is None:
        raise ValueError(f"Field {field} has no annotation.")

    if not issubclass(model, BaseModel):
        raise ValueError(f"Field {field} is not a pydantic model.")

    values = {}
    for field_name, field in model.model_fields.items():
        instance = parse_field_from_args(
            field_name,
            field,
            args,
            prompt=prompt,
            prefix=prefix,
        )
        values[field_name] = instance

    return model(**values)


def parse_list_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    prefix: str = "",
    max_items: int = 20,
) -> list:
    """Parse a list field from the command line arguments.

    Will assume that the list elements are strings.
    """
    parser = argparse.ArgumentParser()
    name = f"--{prefix}.{field_name}" if prefix else f"--{field_name}"

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

    if not value and field.default_factory:
        return field.default_factory()

    return value


def parse_tuple_field_from_args(
    field_name: str,
    field: FieldInfo,
    args: List[str],
    prompt: bool = True,
    prefix: str = "",
) -> tuple:
    """Parse a tuple field from the command line arguments."""
    parser = argparse.ArgumentParser()
    name = f"--{prefix}.{field_name}" if prefix else f"--{field_name}"
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
        args: List[str],
        prompt: bool = True,
        prefix: str = "",
    ) -> object:
        """Parse a field from the command line arguments."""


class CustomFieldParser(Protocol):
    """Protocol for custom field parser."""

    def __call__(
        self,
        args: List[str],
        prompt: bool = True,
        prefix: str = "",
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
        prefix: str = "",
    ):
        parser = argparse.ArgumentParser()
        name = f"{prefix}.{field_name}" if prefix else f"{field_name}"

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
        try:
            parsed_args, _ = parser.parse_known_args(args)
        except SystemExit:
            raise argparse.ArgumentError(
                action, f"Invalid value for {field_name}."
            ) from None

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

        while True:
            try:
                return click.prompt(
                    (
                        "Please provide a value for "
                        f"{click.style(name, fg='blue', bold=True)}."
                        f"{help}"
                    ),
                    value_proc=dtype,
                    default=field.default,
                )
            except ParameterError as error:
                msg = (
                    "Invalid value for "
                    f"{click.style(name, fg='blue', bold=True)}: "
                    f"{click.style(error.message, fg='red', bold=True)}"
                )
                if error.help is not None:
                    msg += f" {error.help}"
                click.echo(msg)

    return field_parser


# Time format (HH:MM:SS), but minutes and seconds are optional
TIME_FORMAT = re.compile(r"(\d{1,2}):?(\d{2})?:?(\d{2})?")


def parse_time(value: str) -> datetime.time:
    """Parse a time from a string."""
    match = TIME_FORMAT.search(value)

    if match is None:
        raise ParameterError(
            value=value,
            message="Invalid time format.",
            help="Please use the format HH:MM:SS.",
        ) from None

    hours = int(match.group(1))
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    if hours > 23:
        raise ParameterError(
            value=value,
            message="Invalid time format.",
            help="Hours must be between 0 and 23.",
        ) from None

    if minutes > 59:
        raise ParameterError(
            value=value,
            message="Invalid time format.",
            help="Minutes must be between 0 and 59.",
        ) from None

    if seconds > 59:
        raise ParameterError(
            value=value,
            message="Invalid time format.",
            help="Seconds must be between 0 and 59.",
        ) from None

    return datetime.time(hours, minutes, seconds)


def parse_date(value: str) -> datetime.date:
    """Parse a date from a string."""
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise ParameterError(
            value=value,
            message="Invalid date format.",
            help="Please use the format YYYY-MM-DD.",
        ) from None


FIELD_PARSERS: Dict[type, FieldParser] = {
    BaseModel: parse_pydantic_model_field_from_args,
    bool: build_simple_field_parser(cast_to_bool),
    str: build_simple_field_parser(str),
    int: build_simple_field_parser(int),
    float: build_simple_field_parser(float),
    list: parse_list_field_from_args,
    tuple: parse_tuple_field_from_args,
    datetime.date: build_simple_field_parser(parse_date),
    datetime.time: build_simple_field_parser(parse_time),
    datetime.datetime: build_simple_field_parser(datetime.datetime),
    Path: build_simple_field_parser(Path),
}
