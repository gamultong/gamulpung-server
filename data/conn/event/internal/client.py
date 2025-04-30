from .base import event, ClientEvent, ValidationException

from config import WINDOW_SIZE_LIMIT, CHAT_MAX_LENGTH
from data.board import Point

@event
class SetWindowSize(ClientEvent):
    event_name = "set-window-size"

    width:int
    height:int

    def assert_valid(self):
        size_limit = (WINDOW_SIZE_LIMIT - 1) / 2
        
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

@event
class OpenTile(ClientEvent):
    event_name = "open-tile"

    position: Point

@event
class SetFlag(ClientEvent):
    event_name = "set-flag"

    position: Point

@event
class Move(ClientEvent):
    event_name = "move"

    position: Point

@event
class Chat(ClientEvent):
    event_name = "chat"

    content:str

    def assert_valid(self):
        if len(self.content) > CHAT_MAX_LENGTH:
            raise ValidationException(
                event=self,
                msg=f"content의 최대길이는 {CHAT_MAX_LENGTH}입니다."
            )
