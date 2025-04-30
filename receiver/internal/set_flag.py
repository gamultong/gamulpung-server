from event.broker import EventBroker
from event.message import Message
from data.payload import (
    EventCollection, SetFlagPayload,FlagSetPayload
)

from handler.board import BoardHandler
from handler.cursor import CursorHandler
from handler.score import ScoreHandler

from data.board import Point, Tile
from data.cursor import Cursor

from .utils import multicast

from config import SET_FLAG_SCORE


class SetFlagReceiver():
    @EventBroker.add_receiver(EventCollection.SET_FLAG)
    @staticmethod
    async def receive_set_flag(message: Message[SetFlagPayload]):
        cursor = CursorHandler.get_cursor(message.header["sender"])

        if not (tile := await get_tile_if_flaggable(cursor)):
            return
        
        tile.is_flag = not tile.is_flag
        tile.color = cursor.color if tile.is_flag else None

        await BoardHandler.set_flag_state(
            p=cursor.pointer, 
            state=tile.is_flag, color=tile.color
        )

        await give_reward(cursor)

        # 변경된 타일을 보고있는 커서들에게 전달
        view_cursors = CursorHandler.view_includes_point(p=cursor.pointer)
        await multicast_flag_set(
            target_conns=view_cursors,
            tile=tile, position=cursor.pointer
        )

async def give_reward(cursor:Cursor):
    await ScoreHandler.increase(cursor.id, SET_FLAG_SCORE)

async def multicast_flag_set(target_conns: list[Cursor], tile: Tile, position: Point):
    await multicast(
            target_conns=[c.id for c in target_conns],
            message=Message(
                event=EventCollection.FLAG_SET,
                payload=FlagSetPayload(
                    position=position,
                    is_set=tile.is_flag,
                    color=tile.color
                )
            )
        )
    

async def get_tile_if_flaggable(cursor:Cursor):
    if not cursor.check_interactable(cursor.pointer):
        return None

    # 보드 상태 가져오기 ~ 업데이트하기
    tiles = await BoardHandler.fetch(start=cursor.pointer, end=cursor.pointer)
    tile = Tile.from_int(tiles.data[0])

    if tile.is_open:
        return None

    return tile