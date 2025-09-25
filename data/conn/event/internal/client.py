from .base import ClientEvent, ValidationException
from dataclasses import dataclass
from utils.config import Config
from data.board import Point


@dataclass
class SetWindowSize(ClientEvent):
    event_name = "SET_WINDOW_SIZE"

    width: int
    height: int

    def assert_valid(self):
        size_limit = (Config.WINDOW_SIZE_LIMIT - 1) / 2

        if self.width > size_limit:
            raise ValidationException(
                event=self,
                msg=f"width의 최대길이는 {size_limit}입니다."
            )
        if self.height > size_limit:
            raise ValidationException(
                event=self,
                msg=f"height의 최대길이는 {size_limit}입니다."
            )


@dataclass
class OpenTile(ClientEvent):
    event_name = "open-tile"

    position: Point


@dataclass
class SetFlag(ClientEvent):
    event_name = "set-flag"

    position: Point


@dataclass
class Move(ClientEvent):
    event_name = "move"

    position: Point


@dataclass
class Pointing(ClientEvent):
    event_name = "pointing"

    position: Point


@dataclass
class Chat(ClientEvent):
    event_name = "chat"

    content: str

    def assert_valid(self):
        if len(self.content) > Config.CHAT_MAX_LENGTH:
            raise ValidationException(
                event=self,
                msg=f"content의 최대길이는 {Config.CHAT_MAX_LENGTH}입니다."
            )


if __name__ == "__main__":
    print(SetWindowSize.__annotations__)
