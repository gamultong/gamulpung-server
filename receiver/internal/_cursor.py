# from event.broker import EventBroker
# from event.message import Message
# from event.payload import Empty

# from data.payload import DataPayload
# from data.cursor import Cursor
# from data.board import Tiles
# from data.conn.event import ServerEvent

# from handler.cursor import CursorEvent, CursorHandler, CursorException
# from handler.board import BoardHandler
# from handler.score import ScoreHandler

# from .utils import multicast

# Message[DataPayload[Cursor[Cursor.Targets]]]

# def validate(old: Cursor, new: Cursor):
#     if old.position != new.position:
#         return True
#     if old.width < new.width:
#         return True
#     if old.height < new.height:
#         return True
#     return False

# class CursorReceiver():
#     @EventBroker.add_receiver(CursorEvent.WINDOW_SIZE_SET)
#     @EventBroker.add_receiver(CursorEvent.MOVED)
#     @staticmethod
#     async def notify_window_changed(message: Message[DataPayload[Cursor[Cursor.Targets]]]):
#         cur_id = message.payload.id

#         old_cur = message.payload.data
#         assert old_cur is not None
#         old_targets = old_cur.sub[Cursor.Targets]

#         new_cur = await CursorHandler.get(cur_id)
#         if not validate(old_cur, new_cur):
#             return

#         # 변경해야함
#         new_targets = await CursorHandler.get_targets(new_cur)

#         new_targets = Cursor.Targets(
#             _id=cur_id,
#             relations=[cur.id for cur in new_targets]
#         )

#         tl = new_cur.view_range.top_left
#         br = new_cur.view_range.bottom_right
#         tiles = await BoardHandler.fetch(tl, br)

#         tiles_state_event = make_tiles_state_event(new_cur, tiles)

#         await multicast(
#             target_conns=[cur_id],
#             event=tiles_state_event
#         )

#         filtering_targets = filter_new_targets(old_targets, new_targets)
#         if len(filtering_targets) == 0:
#             return

#         filtering_targets = [
#             await CursorHandler.get(_cur_id)
#             for _cur_id in filtering_targets
#         ]

#         event = await make_cursor_state_event(filtering_targets)
#         await multicast(
#             target_conns=[cur_id],
#             event=event
#         )

#     @EventBroker.add_receiver(CursorEvent.POINTING)
#     @EventBroker.add_receiver(CursorEvent.DEATH)
#     @EventBroker.add_receiver(CursorEvent.MOVED)
#     @EventBroker.add_receiver(CursorEvent.REVIVE)
#     @EventBroker.add_receiver(CursorEvent.DELETE)
#     @EventBroker.add_receiver(CursorEvent.CREATED)
#     @staticmethod
#     async def notify_cursor_state_changed(message: Message[DataPayload[Cursor[Cursor.Watchers]]]):
#         cur_id = message.payload.id
#         new_cur = await CursorHandler.get(cur_id)

#         old_cur = message.payload.data
#         if old_cur is None:
#             old_cur = make_empty_cursor()

#         watchers = await CursorHandler.get_watchers(new_cur)
#         event = ServerEvent.CursorsState(
#             cursors=[make_cursor_to_elem(old_cur, new_cur)]
#         )

#         await multicast(target_conns=[cur.id for cur in watchers], event=event)

# def make_empty_cursor():
#     return Cursor(
#         conn_id=Empty,
#         position=Empty,
#         pointer=Empty,
#         color=Empty,
#         width=Empty,
#         height=Empty,
#         revive_at=Empty,
#     )

# def make_cursor_to_elem(old: Cursor, new: Cursor):
#     position = Empty if old.position == new.position else new.position
#     pointer = Empty if old.pointer == new.pointer else new.pointer
#     color = Empty if old.color == new.color else new.color
#     revive_at = Empty if old.revive_at == new.revive_at else new.revive_at

#     return ServerEvent.CursorsState.Elem(
#         id=new.id,
#         position=position,
#         pointer=pointer,
#         color=color,
#         revive_at=revive_at,
#     )


# async def make_cursor_state_event(targets: list[Cursor]):
#     event_elem_li = [
#         ServerEvent.CursorsState.Elem(
#             id=cur.id,
#             position=cur.position,
#             pointer=cur.pointer,
#             color=cur.color,
#             revive_at=cur.revive_at,
#             score=(await ScoreHandler.get(cur.id)).value
#         )
#         for cur in targets
#     ]

#     event = ServerEvent.CursorsState(
#         cursors=event_elem_li
#     )

#     return event


# def filter_new_targets(old_targets: Cursor.Targets, new_targets: Cursor.Targets):
#     def func(id): return id not in old_targets

#     return Cursor.Targets(
#         _id=new_targets.id,
#         relations=[cur_id for cur_id in filter(func, new_targets)]
#     )


# def make_tiles_state_event(cursor: Cursor, tiles: Tiles):
#     event_elem = ServerEvent.TilesState.Elem(
#         range=cursor.view_range,
#         data=tiles.to_str()
#     )

#     event = ServerEvent.TilesState(
#         tiles=[event_elem]
#     )

#     return event
