from event.broker import EventBroker
from event.message import Message
from event.payload import IdDataPayload

from data.cursor import Cursor
from data.board import Tiles, PointRange
from data.conn.event import ServerEvent, Empty

from handler.cursor import CursorEvent, CursorHandler
from handler.board import BoardHandler
from handler.score import ScoreHandler
from handler.conn import ConnectionHandler


class NotifyCursorStateChangedReceiver():
    @EventBroker.add_receiver(CursorEvent.POINTING)
    @EventBroker.add_receiver(CursorEvent.DEATH)
    @EventBroker.add_receiver(CursorEvent.MOVED)
    @EventBroker.add_receiver(CursorEvent.REVIVE)
    @staticmethod
    async def notify_cursor_state_changed(message: Message[IdDataPayload[str, Cursor]]):
        cur_id = message.payload.id

        cur = await CursorHandler.get(cur_id)

        event = ServerEvent.CursorsState(
            cursors=[
                ServerEvent.CursorsState.Elem(
                    id=cur.id,
                    position=cur.position,
                    pointer=cur.pointer,
                    color=cur.color,
                    revive_at=cur.revive_at,
                    score=(await ScoreHandler.get(cur.id)).value
                )
            ]
        )

        cur_watchers = await CursorHandler.get_watchers(cur)

        await ConnectionHandler.multicast(target_ids=[c.id for c in cur_watchers], external_event=event)
