"""Test suite for config parsing functions."""

from argparse import ArgumentError
from typing import Optional
from unittest.mock import Mock

import click
import pytest
from pydantic import BaseModel, Field

from acoupi.system.parsers import parse_config_from_args


def test_parse_config_with_empty_args_has_default_values():
    """Test that parsing an empty list of args returns default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: str = "bar"

    parsed_config = parse_config_from_args(
        Schema,
        [],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == "bar"


def test_parse_config_overrides_default_values_with_args():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: str = "bar"

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo", "baz"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == "baz"


def test_parse_config_with_boolean_field():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: bool = True

    parsed_config = parse_config_from_args(Schema, ["--foo", "false"], prompt=False)

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo is False


def test_raise_error_when_field_is_required_but_not_provided():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: bool

    with pytest.raises(ArgumentError):
        parse_config_from_args(Schema, [], prompt=False)


def test_parse_config_with_list_field():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: list = ["bar"]

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo.0", "baz", "--foo.1", "foo"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == ["baz", "foo"]


def test_parse_config_with_tuple_field():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: tuple = ("bar",)

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo", "baz", "foo"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == ("baz", "foo")


def test_parse_config_with_int_field():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: int = 3

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo", "4"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == 4


def test_parse_config_with_float_field():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: float = 3.0

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo", "4.2"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == 4.2


def test_parse_config_with_str_field():
    """Test that parsing args overrides default values."""

    class Schema(BaseModel):
        """Test schema."""

        foo: str = "bar"

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo", "baz"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo == "baz"


def test_parse_nested_config_with_defaults():
    """Test that parsing nested configs without args returns default values."""

    class NestedConfig(BaseModel):
        """Nested configuration."""

        a: int = 3

    class Schema(BaseModel):
        """Test schema."""

        b: bool = True

        c: NestedConfig = Field(default_factory=NestedConfig)

    parsed_config = parse_config_from_args(
        Schema,
        [],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert isinstance(parsed_config.c, NestedConfig)
    assert parsed_config.b is True
    assert parsed_config.c.a == 3


def test_parse_nested_config_with_args():
    """Test that parsing nested configs with args overrides default values."""

    class NestedConfig(BaseModel):
        """Nested configuration."""

        a: int = 3

    class Schema(BaseModel):
        """Test schema."""

        b: bool = True

        c: NestedConfig = Field(default_factory=NestedConfig)

    parsed_config = parse_config_from_args(
        Schema,
        ["--b", "false", "--c.a", "4"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert isinstance(parsed_config.c, NestedConfig)
    assert parsed_config.b is False
    assert parsed_config.c.a == 4


def test_parse_simple_field_prompts_user_if_missing(monkeypatch):
    """Test that user is prompted if field is missing."""

    class Schema(BaseModel):
        """Test schema."""

        foo: bool
        """Test field."""

    mock = Mock(return_value="true")
    monkeypatch.setattr(click, "prompt", mock)

    parsed_config = parse_config_from_args(Schema, [])

    mock.assert_called_once()
    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo is True


def test_parse_simple_field_ask_for_confirmation_if_provided(monkeypatch):
    """Test that user is prompted if field is missing."""

    class Schema(BaseModel):
        """Test schema."""

        foo: bool
        """Test field."""

    mock = Mock(return_value="true")
    monkeypatch.setattr(click, "confirm", mock)

    parsed_config = parse_config_from_args(
        Schema,
        ["--foo", "True"],
        prompt=True,
    )

    mock.assert_called_once()
    assert isinstance(parsed_config, Schema)
    assert parsed_config.foo is True


def test_parse_optional_pydantic_field_is_none_without_prompting():
    class NestedConfig(BaseModel):
        """Nested configuration."""

        a: int = 3

    class Schema(BaseModel):
        """Test schema."""

        b: bool

        c: Optional[NestedConfig] = None

    parsed_config = parse_config_from_args(
        Schema,
        ["--b", "false"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.c is None
    assert parsed_config.b is False


def test_parse_optional_pydantic_field_with_some_args():
    """Test that parsing args overrides default values."""

    class NestedConfig(BaseModel):
        """Nested configuration."""

        a: int = 3

        d: float = 3.14

    class Schema(BaseModel):
        """Test schema."""

        c: Optional[NestedConfig] = None

    parsed_config = parse_config_from_args(
        Schema,
        ["--c.d", "2.71"],
        prompt=False,
    )

    assert isinstance(parsed_config, Schema)
    assert parsed_config.c is not None
    assert parsed_config.c.a == 3
    assert parsed_config.c.d == 2.71


def test_parse_optional_pydantic_field_user_objection(monkeypatch):
    class NestedConfig(BaseModel):
        """Nested configuration."""

        a: int = 3

    class Schema(BaseModel):
        """Test schema."""

        c: Optional[NestedConfig] = None

    mock = Mock(return_value=False)
    monkeypatch.setattr(click, "confirm", mock)

    parsed_config = parse_config_from_args(
        Schema,
        [],
        prompt=True,
    )

    mock.assert_called_once()

    assert isinstance(parsed_config, Schema)
    assert parsed_config.c is None


def test_parse_optional_pydantic_field_with_user_input(monkeypatch):
    class NestedConfig(BaseModel):
        """Nested configuration."""

        a: bool = False
        b: float = 3.14

    class Schema(BaseModel):
        """Test schema."""

        c: Optional[NestedConfig] = None

    mock = Mock(return_value=True)
    monkeypatch.setattr(click, "confirm", mock)

    parsed_config = parse_config_from_args(
        Schema,
        [],
        prompt=True,
    )

    mock.assert_called()

    assert isinstance(parsed_config, Schema)
    assert parsed_config.c is not None
    assert parsed_config.c.a is False
    assert parsed_config.c.b == 3.14
