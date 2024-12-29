from board.data import Section, Point
from board.data.storage import SectionStorage

from db import db


async def setup_board():
    """
    /docs/example-map-state.png
    """
    await teardown_board()

    Section.LENGTH = 4

    sections = [
        Section(Point(0, 0), bytearray([
            0b00000000, 0b00000000, 0b00000000, 0b00000000,
            0b00000001, 0b00000001, 0b00000001, 0b00000000,
            0b10000001, 0b01110000, 0b00000001, 0b00000000,
            0b10000001, 0b00000001, 0b00000001, 0b00000000
        ])),
        Section(Point(-1, 0), bytearray([
            0b00000001, 0b00000010, 0b00000010, 0b00000001,
            0b00000001, 0b01000000, 0b01000000, 0b00000001,
            0b00000001, 0b00000010, 0b10000010, 0b10000001,
            0b00000001, 0b00100001, 0b10000001, 0b10000000
        ])),
        Section(Point(-1, -1),  bytearray([
            0b00000001, 0b01000000, 0b10000010, 0b10000001,
            0b10000001, 0b10000001, 0b10000011, 0b01101000,
            0b10000000, 0b10000000, 0b10000010, 0b01000000,
            0b11000000, 0b10000000, 0b10000001, 0b00000001
        ])),
        Section(Point(0, -1),  bytearray([
            0b10000001, 0b00111001, 0b00000001, 0b00000001,
            0b00000011, 0b00000010, 0b01000000, 0b00000001,
            0b00000011, 0b01000000, 0b00000010, 0b00000001,
            0b00000010, 0b00000001, 0b00000001, 0b00000000
        ]))
    ]

    for section in sections:
        await SectionStorage.set(section)


async def teardown_board():
    await db.execute("DELETE FROM sections")
