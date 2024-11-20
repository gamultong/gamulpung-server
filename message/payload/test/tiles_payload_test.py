import unittest

from board.handler import Point
from message.payload import FetchTilesPayload, TilesPayload
from .testdata.tiles_payload_testdata import EXAPLE_FETCH_TILES_DICT, EXAPLE_TILES_DICT

class FetchTilesPayloadTestCase(unittest.TestCase):
    def setUp(self):
        self.payload = FetchTilesPayload._from_dict(EXAPLE_FETCH_TILES_DICT)

    def test_payload_vaild_data(self):
        assert self.payload.start_x == 0
        assert self.payload.start_y == 0
        assert self.payload.end_x == 0
        assert self.payload.end_y == 0

    def test_payload_vaild_property(self):
        assert type(self.payload.start_p) == Point
        assert self.payload.start_p.x == 0
        assert self.payload.start_p.y == 0
        
        assert type(self.payload.end_p) == Point
        assert self.payload.end_p.x == 0
        assert self.payload.end_p.y == 0

class TilesPayloadTestCase(unittest.TestCase):
    def setUp(self):
        self.payload = TilesPayload._from_dict(EXAPLE_TILES_DICT)

    def test_payload_vaild_data(self):
        assert self.payload.start_x == 0
        assert self.payload.start_y == 0
        assert self.payload.end_x == 4
        assert self.payload.end_y == 4
        assert self.payload.tiles == "CCCCCCCCCCC111CC1F1CC111C"

    def test_payload_vaild_property(self):
        assert type(self.payload.start_p) == Point
        assert self.payload.start_p.x == 0
        assert self.payload.start_p.y == 0

        assert type(self.payload.end_p) == Point
        assert self.payload.end_p.x == 4
        assert self.payload.end_p.y == 4


if __name__ == "__main__":
    unittest.main()