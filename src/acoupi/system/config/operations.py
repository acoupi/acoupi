"""System functions from managing program config files."""

import json
from pathlib import Path
from typing import (
    Any,
    List,
    Optional,
    Type,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import BaseModel, ValidationError

from acoupi.system import exceptions

__all__ = [
    "dump_config",
    "get_config_field",
    "load_config",
    "set_config_field",
    "write_config",
]


S = TypeVar("S", bound=BaseModel)


def write_config(
    config: Optional[BaseModel],
    path: Path,
) -> None:
    """Write config to file."""
    if config is None:
        return

    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    with open(path, "w") as file:
        file.write(config.model_dump_json())


def load_config(path: Path, schema: Type[S]) -> S:
    """Load config from file.

    Parameters
    ----------
    path
        Path to the config file.
    schema
        Pydantic model to validate the config.

    Returns
    -------
    S
        The loaded config.

    Raises
    ------
    ConfigurationError
        If the configuration is invalid.
    FileNotFoundError
        If the config file does not exist.
    """
    with open(path) as file:
        try:
            return schema.model_validate_json(file.read())
        except (ValueError, ValidationError) as error:
            raise exceptions.ConfigurationError(
                message=f"Invalid configuration in {path}: {error}",
                help="Check the configuration file for errors.",
            ) from error


def get_config_field(config: BaseModel, field: str) -> Any:
    """Retrieve a field or nested field from a configuration object.

    This function allows you to access configuration values by specifying the
    field name, including nested fields using dot notation
    (e.g., 'section.subsection.value'). If no field is provided, the entire
    configuration object is returned.

    It is possible to get nested fields by using a dot notation.

    Parameters
    ----------
    config
        The configuration object, an instance of a Pydantic model.
    field
        The name of the field to retrieve. Use dot notation for nested fields.

    Returns
    -------
    Any
        The value of the specified field. The type depends on the field's
        definition in the Pydantic model.

    Raises
    ------
    AttributeError
        If the specified `field` does not exist within the configuration schema.
    IndexError
        If the `field` refers to an index in a list or tuple that is out of
        bounds.
    NotImplementedError
        If the `field` points to a data type or structure that this function
        does not currently support for retrieval.

    Examples
    --------
    Accessing a root-level field:

    >>> class Config(BaseModel):
    ...     a: int
    ...     b: str
    >>> config = Config(a=1, b="2")
    >>> get_config_field(config, "a")
    >>> 1

    Accessing a nested field:

    >>> class NestedConfig(BaseModel):
    ...     d: bool
    >>> class Config(BaseModel):
    ...     a: int
    ...     b: str
    ...     c: NestedConfig
    >>> config = Config(a=1, b="2", c=NestedConfig(d=True))
    >>> get_config_field(config, "c.d")
    >>> True

    Accessing an element from a list:

    >>> class Config(BaseModel):
    ...     a: List[int]
    >>> config = Config(a=[1, 2, 3])
    >>> get_config_field(config, "a.0")
    >>> 1
    """
    if field is None or field == "":
        return config

    fields = config.model_fields
    prefix, *rest = field.split(".", 1)

    if prefix not in fields:
        valid_fields = "\n\t - ".join(fields.keys())
        raise AttributeError(
            f"Field '{prefix}' is not part of the configuration schema.\n"
            f"Valid fields are:\n\t - {valid_fields}",
        )

    subfield = fields[prefix]
    type_ = subfield.rebuild_annotation()
    origin = get_origin(type_)

    if not rest:
        return getattr(config, prefix)

    if origin is not None and issubclass(origin, (tuple, list)):
        return _get_config_field_from_sequence(
            getattr(config, prefix),
            rest[0],
            type_,
        )

    if issubclass(type_, BaseModel):
        return get_config_field(getattr(config, prefix), rest[0])

    raise NotImplementedError(f"Cannot get field from {type_}.")


def set_config_field(
    config: S,
    field: str,
    value: Any,
    is_json: bool = False,
    strict: bool = False,
    from_attributes: bool = False,
) -> S:
    """Set a specific field in a config object.

    This function enables you to update configuration values by specifying the
    field name, including nested fields using dot notation
    (e.g., 'section.subsection.value'). The provided `value` is validated
    against the field's type definition in the Pydantic model to ensure data
    integrity.

    Parameters
    ----------
    config
        The configuration object to be modified. Must be an instance of a
        Pydantic model.
    field
        The name of the field to set. Use dot notation for nested fields. If an
        empty string, the entire configuration is replaced. This is useful when
        setting the configuration from a JSON string.
    value
        The new value to assign to the specified field. The type should be
        compatible with the field's definition in the Pydantic model.
    is_json
        If True, the `value` is treated as a JSON string and parsed before
        being assigned. Default is False.
    strict
        If True, type coercion is disabled, and the `value` must match the
        field's type exactly. If False (default), type coercion is attempted if
        possible.
    from_attributes
        Relevant only when setting a field that is itself a Pydantic model. If
        True, the `value` is assumed to be an object whose attributes will be
        used to populate the model. See Pydantic's `model_validate`
        documentation for details. Default is False.

    Returns
    -------
    S
        A new configuration object with the specified field modified. The
        original `config` object remains unchanged.

    Raises
    ------
    ValidationError
        If the provided `value` fails validation against the field's type
        definition in the Pydantic model.
    AttributeError
        If the specified `field` does not exist within the configuration
        schema.
    IndexError
        If the `field` refers to an index in a list or tuple that is out of
        bounds.
    NotImplementedError
        If the `field` points to a data type or structure that this function
        does not currently support for setting.

    Examples
    --------
    Setting a root-level field:

    >>> class Config(BaseModel):
    ...     a: int
    ...     b: str
    >>> config = Config(a=1, b="2")
    >>> new_config = set_config_field(config, "a", 3)
    >>> new_config.a
    >>> 3

    Setting a nested field:

    >>> class NestedConfig(BaseModel):
    ...     d: bool
    >>> class Config(BaseModel):
    ...     a: int
    ...     b: str
    ...     c: NestedConfig
    >>> config = Config(a=1, b="2", c=NestedConfig(d=True))
    >>> new_config = set_config_field(config, "c.d", False)
    >>> new_config.c.d

    Setting an element in a list:

    >>> class Config(BaseModel):
    ...     a: List[int]
    >>> config = Config(a=[1, 2, 3])
    >>> new_config = set_config_field(config, "a.0", 4)
    >>> new_config.a[0]
    >>> 4

    Setting a field from a JSON string:

    >>> class Config(BaseModel):
    ...     a: int
    ...     b: str
    >>> config = Config(a=1, b="2")
    >>> new_config = set_config_field(
    ...     config,
    ...     "",
    ...     '{"a": 3, "b": "4"}',
    ...     is_json=True,
    ... )
    >>> new_config.a
    >>> 3

    """
    if is_json and not isinstance(value, str):
        raise ValueError(
            "Value must be a string when setting a field from JSON."
        )

    if not field:
        if isinstance(value, type(config)):
            return value

        if is_json:
            return config.model_validate_json(value, strict=strict)

        return config.model_validate(
            value,
            strict=strict,
            from_attributes=from_attributes,
        )

    new_config = config.model_copy(deep=True)

    # Make sure that the assignment is valid
    new_config.model_config["validate_assignment"] = True
    new_config.model_config["strict"] = True

    prefix, *rest = field.split(".", 1)

    if prefix not in config.model_fields:
        valid_fields = "\n\t - ".join(config.model_fields.keys())
        raise AttributeError(
            f"The field '{prefix}' is not part of the configuration schema.\n"
            f"Valid fields are:\n    - {valid_fields}",
        )

    subconfig = getattr(new_config, prefix)
    subfield = config.model_fields[prefix]
    type_ = subfield.rebuild_annotation()
    origin = get_origin(type_)

    if not rest:
        if is_json:
            value = json.loads(value)

        setattr(new_config, prefix, value)
        return new_config

    if origin is not None and issubclass(origin, (list, tuple)):
        new_subconfig = _set_config_field_in_sequence(
            subconfig,
            value=value,
            field=rest[0],
            is_json=is_json,
            type_=type_,
        )
        setattr(new_config, prefix, new_subconfig)
        return new_config

    if issubclass(type_, BaseModel):
        new_subconfig = set_config_field(
            subconfig,
            field=rest[0],
            value=value,
            is_json=is_json,
            strict=strict,
            from_attributes=from_attributes,
        )
        setattr(config, prefix, new_subconfig)
        return config

    raise NotImplementedError(f"Cannot set field in {type_}.")


class PydanticJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Pydantic models."""

    def default(self, o: Any) -> Any:
        if isinstance(o, BaseModel):
            return o.model_dump()

        return super().default(o)


def dump_config(config: Any, indent: int = 2) -> str:
    """Dump a configuration object to a JSON string."""
    return json.dumps(config, cls=PydanticJSONEncoder, indent=indent)


def _get_config_field_from_sequence(
    config: List[Any],
    field: str,
    type_: Type,
) -> Any:
    prefix, *rest = field.split(".", 1)

    if not prefix.isdigit():
        raise ValueError("Field is not an index.")

    index = int(prefix)
    if index >= len(config) or index < 0:
        raise IndexError("Index out of range.")

    if not rest:
        return config[index]

    args = get_args(type_)

    if not args:
        raise NotImplementedError(
            "Cannot get field from list of non-models.",
        )

    origin = get_origin(type_)
    assert origin is not None

    if issubclass(origin, list):
        type_ = args[0]
    elif issubclass(origin, tuple):
        type_ = args[index]
    else:
        raise NotImplementedError(f"Cannot get field from {origin}.")

    if issubclass(type_, BaseModel):
        return get_config_field(config[index], rest[0])

    raise NotImplementedError(f"Cannot get field from list of {args[0]}")


def _set_config_field_in_sequence(
    config: List[Any],
    value: Any,
    field: str,
    is_json: bool,
    type_: Type,
) -> List[Any]:
    prefix, *rest = field.split(".", 1)

    if not prefix.isdigit():
        raise ValueError("Field is not an index.")

    index = int(prefix)
    if index >= len(config) or index < 0:
        raise IndexError("Index out of range.")

    if not rest:
        if is_json:
            value = json.loads(value)

        config[index] = value
        return config

    args = get_args(type_)
    origin = get_origin(type_)

    if args is None:
        raise NotImplementedError(
            "Cannot set field in list of non-models.",
        )

    assert origin is not None

    if issubclass(origin, list):
        subtype = args[0]
    elif issubclass(origin, tuple):
        subtype = args[index]
    else:
        raise NotImplementedError(f"Cannot set field in {origin}.")

    if issubclass(subtype, BaseModel):
        new_subconfig = set_config_field(
            config[index],
            field=rest[0],
            value=value,
            is_json=is_json,
        )
        config[index] = new_subconfig
        return config

    raise NotImplementedError("Setting fields in lists is not supported.")
