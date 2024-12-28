class InvalidTileException(Exception):
    def __init__(self, tile: dict):
        self.tile = tile

    def __str__(self):
        return f"invalid tile: {self.tile}"


class InvalidDataLengthException(Exception):
    def __init__(self, expected: int, actual: int):
        self.expected = expected
        self.actual = actual

    def __str__(self):
        return f"invalid data length. expected: {self.expected}, actual: {self.actual}"
