from board.data import Section, Point
from board.data.storage.internal.section_storage import env
from board.data.storage import SectionStorage


def setup_board():
    """
    /docs/example-map-state.png
    """
    teardown_board()

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
        SectionStorage.set(section)


def teardown_board():
    with env.begin(write=True) as txn:
        db = env.open_db()
        txn.drop(db)
