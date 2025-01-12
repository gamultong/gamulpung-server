import unittest
from event.payload import Payload, ParsablePayload
from dataclasses import dataclass


@dataclass
class ExampleData:
    exp_str: str
    exp_int: int


@dataclass
class ExamplePayload(Payload):
    example_data: ParsablePayload[ExampleData]


EXAMPLE_JSON = {
    "example_data": {
        "exp_str": "example",
        "exp_int": 5
    }
}


class ParserblePayloadTestCase(unittest.TestCase):
    def test_parsing(self):
        payload = ExamplePayload._from_dict(EXAMPLE_JSON)

        self.assertEqual(type(payload), ExamplePayload)
        self.assertEqual(type(payload.example_data), ExampleData)
        self.assertEqual(payload.example_data.exp_str, "example")
        self.assertEqual(payload.example_data.exp_int, 5)


if __name__ == "__main__":
    unittest.main()
