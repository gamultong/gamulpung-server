from dataclasses import dataclass


@dataclass
class Point:
    x: int
    y: int

    def copy(self):
        return Point(self.x, self.y)

    def marshal_bytes(self) -> bytes:
        x_b = self.x.to_bytes(length=8, signed=True)
        y_b = self.y.to_bytes(length=8, signed=True)
        return x_b + y_b

    @staticmethod
    def unmarshal_bytes(b: bytes):
        x = int.from_bytes(bytes=b[:8], signed=True)
        y = int.from_bytes(bytes=b[8:], signed=True)
        return Point(x, y)
