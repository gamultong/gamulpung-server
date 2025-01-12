from event.payload import Payload, InvalidFieldException, MissingFieldException
from dataclasses import dataclass
from enum import Enum


class ExampleEnum(str, Enum):
    Hi = "hi"


@dataclass
class ExamplePayload(Payload):
    foo: str
    bar: str
    enum: ExampleEnum


@dataclass
class ExampleWrapperPayload(Payload):
    a: int
    b: str
    wrapped: ExamplePayload


EXAMPLE_PAYLOAD_DICT = {
    "foo": "foo",
    "bar": "bar",
    "enum": "hi"
}

EXAMPLE_PAYLOAD_DICT_MISSING_KEY = {
    "bar": "bar",
    "enum": "hi"
}

EXAMPLE_PAYLOAD_DICT_INVALID_KEY = {
    "foo": "foo",
    "bar": "bar",
    "enum": "hi",
    "baz": "baz"
}

EXAMPLE_PAYLOAD_DICT_INVALID_VALUE_TYPE = {
    "foo": "foo",
    "enum": "hi",
    "bar": 1,
}

EXAMPLE_PAYLOAD_DICT_INVALID_ENUM = {
    "foo": "foo",
    "bar": "bar",
    "enum": "hey",
}

EXAMPLE_PAYLOAD_WRAPPED_DICT = {
    "a": 1,
    "b": "b",
    "wrapped": EXAMPLE_PAYLOAD_DICT
}

EXAMPLE_PAYLOAD_WRAPPED_DICT_MISSING_KEY = {
    "a": 1,
    "b": "b",
    "wrapped": EXAMPLE_PAYLOAD_DICT_MISSING_KEY
}

EXAMPLE_PAYLOAD_WRAPPED_DICT_INVALID_KEY = {
    "a": 1,
    "b": "b",
    "wrapped": EXAMPLE_PAYLOAD_DICT_INVALID_KEY
}

EXAMPLE_PAYLOAD_WRAPPED_DICT_INVALID_VALUE_TYPE = {
    "a": 1,
    "b": "b",
    "wrapped": EXAMPLE_PAYLOAD_DICT_INVALID_VALUE_TYPE
}

EXAMPLE_PAYLOAD_WRAPPED_DICT_INVALID_ENUM = {
    "a": 1,
    "b": "b",
    "wrapped": EXAMPLE_PAYLOAD_DICT_INVALID_ENUM
}

EXCEPTION_TEST_CASES = \
    [
        {
            "dict": EXAMPLE_PAYLOAD_DICT_MISSING_KEY,
            "payload": ExamplePayload,
            "exp": MissingFieldException,
            "msg": "missing 1 keys: foo"
        },
        {
            "dict": EXAMPLE_PAYLOAD_DICT_INVALID_VALUE_TYPE,
            "payload": ExamplePayload,
            "exp": InvalidFieldException,
            "msg": "invaild field: bar -> 1"
        },
        {
            "dict": EXAMPLE_PAYLOAD_DICT_INVALID_ENUM,
            "payload": ExamplePayload,
            "exp": InvalidFieldException,
            "msg": "invaild field: enum -> hey"
        },
        {
            "dict": EXAMPLE_PAYLOAD_DICT_INVALID_KEY,
            "payload": ExamplePayload,
            "exp": InvalidFieldException,
            "msg": "invaild field: baz -> baz"
        },
        {
            "dict": EXAMPLE_PAYLOAD_WRAPPED_DICT_MISSING_KEY,
            "payload": ExampleWrapperPayload,
            "exp": MissingFieldException,
            "msg": "missing 1 keys: wrapped.foo"
        },
        {
            "dict": EXAMPLE_PAYLOAD_WRAPPED_DICT_INVALID_VALUE_TYPE,
            "payload": ExampleWrapperPayload,
            "exp": InvalidFieldException,
            "msg": "invaild field: wrapped.bar -> 1"
        },
        {
            "dict": EXAMPLE_PAYLOAD_WRAPPED_DICT_INVALID_ENUM,
            "payload": ExampleWrapperPayload,
            "exp": InvalidFieldException,
            "msg": "invaild field: wrapped.enum -> hey"
        },
        {
            "dict": EXAMPLE_PAYLOAD_WRAPPED_DICT_INVALID_KEY,
            "payload": ExampleWrapperPayload,
            "exp": InvalidFieldException,
            "msg": "invaild field: wrapped.baz -> baz"
        },
    ]
