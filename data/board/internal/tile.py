from data.base import DataObj

from dataclasses import dataclass
from data.cursor import Color
from .exceptions import InvalidTileException


@dataclass
class Tile(DataObj):
    is_open: bool
    is_mine: bool
    is_flag: bool
    color: Color | None
    number: int | None

    @property
    def data(self) -> int:
        d = 0b00000000

        d |= 0b10000000 if self.is_open else 0
        d |= 0b01000000 if self.is_mine else 0
        d |= 0b00100000 if self.is_flag else 0
        d |= self.number if self.number is not None else 0

        match self.color:
            case Color.RED | None:
                color_bits = 0
            case Color.YELLOW:
                color_bits = 1
            case Color.BLUE:
                color_bits = 2
            case Color.PURPLE:
                color_bits = 3

        d |= color_bits << 3

        return d

    def copy(self, hide_info: bool = False):
        t = Tile(
            is_open=self.is_open,
            is_mine=self.is_mine,
            is_flag=self.is_flag,
            color=self.color,
            number=self.number
        )
        if hide_info:
            t.is_mine = False
            t.number = None
        return t

    @staticmethod
    def create(
        is_open: bool,
        is_mine: bool,
        is_flag: bool,
        color: Color | None,
        number: int | None
    ):
        """
        __init__ 대신 이걸 쓰기를 권장.
        """
        t = Tile(
            is_open=is_open,
            is_mine=is_mine,
            is_flag=is_flag,
            color=color,
            number=number
        )

        if (t.number is not None) and (t.number >= 8 or t.number < 0):
            # 숫자는 음수이거나 8 이상일 수 없음
            raise InvalidTileException(t.__dict__)
        if t.is_mine and (t.number is not None):
            # 지뢰 타일은 숫자를 가지고있지 않음
            raise InvalidTileException(t.__dict__)
        if is_open and is_flag:
            # 열려있는 타일은 깃발이 꽂혀있을 수 없음
            raise InvalidTileException(t.__dict__)
        if is_flag and (color is None):
            # 색깔 없이 깃발이 꽂혀있을 수 없음
            raise InvalidTileException(t.__dict__)
        if (not is_flag) and (color is not None):
            # 깃발이 없는 채로 색깔이 존재할 수 없음
            raise InvalidTileException(t.__dict__)

        return t

    @staticmethod
    def from_int(b: int):
        is_open = bool(b & 0b10000000)
        is_mine = bool(b & 0b01000000)
        is_flag = bool(b & 0b00100000)

        color = extract_color(b) if is_flag else None
        number = extract_number(b) if not is_mine else None

        t = Tile(
            is_open=is_open,
            is_mine=is_mine,
            is_flag=is_flag,
            color=color,
            number=number
        )

        if t.is_open and t.is_flag:
            # 열려있는 타일은 깃발이 꽂혀있을 수 없음
            raise InvalidTileException(t.__dict__)

        return t


def extract_color(b: int) -> Color:
    mask = 0b00011000
    match (b & mask) >> 3:
        case 0:
            return Color.RED
        case 1:
            return Color.YELLOW
        case 2:
            return Color.BLUE
        case 3:
            return Color.PURPLE


def extract_number(i: int) -> int | None:
    result = i & 0b00000111
    if result == 0:
        # 0은 None으로 반환
        return None
    return result
