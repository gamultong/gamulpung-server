"""
해당 문서 참조 
- API/WebSocket/client
"""
from .base import ClientPayload, ValidationException
from utils.config import Config
from data.board import Point


class SetWindowSize(ClientPayload):
    width: int
    height: int

    def validate(self):
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


class OpenTile(ClientPayload):
    position: Point


class SetFlag(ClientPayload):
    position: Point


class Move(ClientPayload):
    position: Point


class Pointing(ClientPayload):
    position: Point


class Chat(ClientPayload):
    message: str

    def validate(self):
        if len(self.message) > Config.CHAT_MAX_LENGTH:
            raise ValidationException(
                event=self,
                msg=f"message의 최대길이는 {Config.CHAT_MAX_LENGTH}입니다."
            )


if __name__ == "__main__":
    print(SetWindowSize.__annotations__)
