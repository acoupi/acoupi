"""Test suite for the acoupi system config module."""

import datetime
from typing import List, Tuple

import pytest
from pydantic import BaseModel, ValidationError

from acoupi.system.config import get_config_field, set_config_field


def test_get_simple_config_field_value():
    """It should return the value of a simple field."""

    class Config(BaseModel):
        a: int
        b: str

    config = Config(a=1, b="2")

    assert get_config_field(config, "a") == 1


def test_get_nested_field():
    """It should return the value of a nested field."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        c: NestedConfig

    config = Config(c=NestedConfig(a=3, b="4"))

    assert get_config_field(config, "c.a") == 3


def test_get_field_from_list_type():
    """It should return the value of a field from a list."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    assert get_config_field(config, "a.0") == 1


def test_get_field_from_list_fails_if_index_is_too_large():
    """It should raise an error if the index is too large."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    with pytest.raises(IndexError):
        get_config_field(config, "a.3")


def test_get_field_from_complex_list_item():
    """It should return the value of a field from a complex list item."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        a: List[NestedConfig]

    config = Config(a=[NestedConfig(a=1, b="2")])

    assert get_config_field(config, "a.0.a") == 1


def test_get_list_field():
    """It should return the value of a list field."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    assert get_config_field(config, "a") == [1, 2, 3]


def test_get_field_from_complex_tuple_item():
    """It should return the value of a field from a complex tuple item."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        a: Tuple[NestedConfig, NestedConfig]

    config = Config(a=(NestedConfig(a=1, b="2"), NestedConfig(a=3, b="4")))
    assert get_config_field(config, "a.1.a") == 3


def test_get_field_from_config_fails_if_field_does_not_exist():
    """It should raise an error if the field does not exist."""

    class Config(BaseModel):
        a: int

    config = Config(a=1)

    with pytest.raises(AttributeError):
        get_config_field(config, "b")


def test_set_config_field_by_passing_the_full_config_in_json_format():
    """It should set the value of a field by passing the full field."""

    class Config(BaseModel):
        a: int
        b: str

    config = Config(a=1, b="2")

    new_config = set_config_field(
        config,
        "",
        '{"a": 3, "b": "4"}',
        is_json=True,
    )

    assert new_config.a == 3
    assert new_config.b == "4"


def test_set_simple_config_field_value():
    """It should set the value of a simple field."""

    class Config(BaseModel):
        a: int
        b: str

    config = Config(a=1, b="2")

    new_config = set_config_field(config, "a", 3)

    assert new_config.a == 3
    assert new_config.b == "2"


def test_set_field_should_fail_if_validation_fails():
    """It should raise an error if the value is invalid."""

    class Config(BaseModel):
        a: int
        b: str

    config = Config(a=1, b="2")

    with pytest.raises(ValidationError):
        set_config_field(config, "a", "foo")


def test_set_field_in_nested_config():
    """It should set the value of a field in a nested config."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        c: NestedConfig

    config = Config(c=NestedConfig(a=3, b="4"))

    new_config = set_config_field(config, "c.a", 5)

    assert new_config.c.a == 5
    assert new_config.c.b == "4"


def test_set_nested_config_with_json_string():
    """It should set the value of a nested config with a json string."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        c: NestedConfig

    config = Config(c=NestedConfig(a=3, b="4"))

    new_config = set_config_field(
        config,
        "c",
        '{"a": 5, "b": "6"}',
        is_json=True,
    )

    assert new_config.c.a == 5
    assert new_config.c.b == "6"


def test_set_nested_config_with_json_string_and_complex_types():
    """It should raise an error if the json string is invalid."""

    class NestedConfig(BaseModel):
        a: int
        b: datetime.datetime

    class Config(BaseModel):
        c: NestedConfig
        d: bool

    config = Config(c=NestedConfig(a=3, b=datetime.datetime.now()), d=True)

    new_config = set_config_field(
        config,
        "c",
        '{"a": "5", "b": "2024-08-10T19:10:02"}',
        is_json=True,
    )

    assert new_config.c.a == 5
    assert new_config.c.b == datetime.datetime(2024, 8, 10, 19, 10, 2)


def test_set_nested_config_with_invalid_json_fails():
    """It should raise an error if the json string is invalid."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        c: NestedConfig

    config = Config(c=NestedConfig(a=3, b="4"))

    with pytest.raises(ValidationError):
        set_config_field(
            config,
            "c",
            '{"a": 5, "b": 6}',
            is_json=True,
        )


def test_set_list_field():
    """It should set the value of a list field."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    new_config = set_config_field(config, "a", [4, 5])

    assert new_config.a == [4, 5]


def test_set_list_field_fails_if_types_do_not_match():
    """It should raise an error if the types do not match."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    with pytest.raises(ValidationError):
        set_config_field(config, "a", [4, "a"])


def test_set_field_item_in_list():
    """It should set the value of an item in a list."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    new_config = set_config_field(config, "a.1", 4)

    assert new_config.a == [1, 4, 3]


def test_set_field_item_fails_if_validation_fails():
    """It should raise an error if the value is invalid."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    with pytest.raises(ValidationError):
        set_config_field(config, "a.1", "foo")


def test_set_field_item_fails_if_index_is_too_large():
    """It should raise an error if the index is too large."""

    class Config(BaseModel):
        a: List[int]

    config = Config(a=[1, 2, 3])

    with pytest.raises(IndexError):
        set_config_field(config, "a.3", 4)


def test_set_field_item_in_complex_list_item():
    """It should set the value of a field in a complex list item."""

    class NestedConfig(BaseModel):
        a: int
        b: str

    class Config(BaseModel):
        a: List[NestedConfig]

    config = Config(a=[NestedConfig(a=1, b="2")])

    new_config = set_config_field(config, "a.0.a", 3)

    assert new_config.a[0].a == 3


def test_set_field_should_fail_if_not_in_schema():
    """It should raise an error if the field is not in the schema."""

    class Config(BaseModel):
        a: int

    config = Config(a=1)

    with pytest.raises(AttributeError):
        set_config_field(config, "b", 3)
