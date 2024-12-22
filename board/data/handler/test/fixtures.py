from board.data import Section, Point
from board.data.handler import BoardHandler


def setup_board():
    """
    /docs/example-map-state.png
    """

    Section.LENGTH = 4

    tile_state_1 = bytearray([
        0b00000000, 0b00000000, 0b00000000, 0b00000000,
        0b00000001, 0b00000001, 0b00000001, 0b00000000,
        0b10000001, 0b01110000, 0b00000001, 0b00000000,
        0b10000001, 0b00000001, 0b00000001, 0b00000000
    ])
    tile_state_2 = bytearray([
        0b00000001, 0b00000010, 0b00000010, 0b00000001,
        0b00000001, 0b01000000, 0b01000000, 0b00000001,
        0b00000001, 0b00000010, 0b10000010, 0b10000001,
        0b00000001, 0b00100001, 0b10000001, 0b10000000
    ])
    tile_state_3 = bytearray([
        0b00000001, 0b01000000, 0b10000010, 0b10000001,
        0b10000001, 0b10000001, 0b10000011, 0b01101000,
        0b10000000, 0b10000000, 0b10000010, 0b01000000,
        0b11000000, 0b10000000, 0b10000001, 0b00000001
    ])
    tile_state_4 = bytearray([
        0b10000001, 0b00111001, 0b00000001, 0b00000001,
        0b00000011, 0b00000010, 0b01000000, 0b00000001,
        0b00000011, 0b01000000, 0b00000010, 0b00000001,
        0b00000010, 0b00000001, 0b00000001, 0b00000000
    ])

    BoardHandler.sections = \
        {
            0: {
                0: Section(Point(0, 0), tile_state_1),
                -1: Section(Point(-1, 0), tile_state_2)
            },
            -1: {
                0: Section(Point(0, -1), tile_state_4),
                -1: Section(Point(-1, -1), tile_state_3)
            }
        }
    BoardHandler.max_x = 0
    BoardHandler.min_x = -1
    BoardHandler.max_y = 0
    BoardHandler.min_y = -1
