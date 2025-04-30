from data.conn.event import (
    to_message, from_message, Event, ValidationException, event,
    InvalidEventFormat
)
from data.base import DataObj
from dataclasses import dataclass
from tests.utils import cases
from unittest import TestCase

@event
class ExampleEvent(Event):
    event_name = "example"

    @dataclass
    class Elem(DataObj):
        field:int

    field: list[Elem]
    
    def assert_valid(self):
        raise ValidationException(self, "example")
    
class Event_TestCase(TestCase):
    def test_to_message(self):
        example = ExampleEvent(field=[ExampleEvent.Elem(field=1)])

        msg = to_message(example)

        self.assertEqual(
            msg,
            {
                "header": {
                    "event": example.event_name,
                },
                "content": example.to_dict(),
            }
        )
        
    def test_assert_vaild(self):
        event = ExampleEvent(field=[ExampleEvent.Elem(field=5)])

        with self.assertRaises(ValidationException):
            event.assert_valid()

    def test_from_message(self):
        raw = {
            "header": {
                "event": ExampleEvent.event_name
            },
            "content": {
                "field": [
                    {"field": 1},
                    {"field": 2},
                ]
            }
        }

        event: ExampleEvent = from_message(raw)
        event.field

        self.assertEqual(event.event_name, ExampleEvent.event_name)
        self.assertEqual(event.field, [
            ExampleEvent.Elem(field=1),
            ExampleEvent.Elem(field=2),
        ])

    @cases([
        {
            "data": {
                "header": {
                    "event": ExampleEvent.event_name
                },
                "content": {
                    "non-field": [
                        {"field": 1},
                        {"field": 2},
                    ]
                }
            }
        },
        {
            "data": {
                "header": {
                    "event": ExampleEvent.event_name
                },
                "content": {}
            }
        },
        {
            "data": {
                "header": {
                    "event": "이건절대못찾을걸?"
                },
                "content": {}
            }
        },
        {
            "data": {}
        }
    ])
    def test_from_message_invalid(self, data: dict):
        with self.assertRaises(InvalidEventFormat):
            from_message(data)
        