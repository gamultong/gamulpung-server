from handler.score import ScoreHandler
from data.payload import DataPayload
from data.cursor import Cursor
from event.message import Message


class DeleteCursorReceiver:
    @staticmethod
    async def cursor_delete(message: Message[DataPayload[Cursor]]):
        assert message.payload.data
        cursor = message.payload.data

        # 1. Score 삭제
        await ScoreHandler.delete(
            id=cursor.id
        )
        # 2. cursor-delete publish
        await multicast_cursor_delete(
            target_conns=[cursor]
        )


async def multicast_cursor_delete(target_conns: list[Cursor]):
    pass
