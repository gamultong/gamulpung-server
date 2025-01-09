from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from conn.manager import ConnectionManager
from data_layer.board import Section
from board.event.handler import BoardEventHandler
from cursor.event.handler import CursorEventHandler
from message import Message
from message.payload import ErrorEvent, ErrorPayload
from config import VIEW_SIZE_LIMIT

app = FastAPI()


@app.websocket("/session")
async def session(ws: WebSocket):
    try:
        view_width = int(ws.query_params.get("view_width"))
        view_height = int(ws.query_params.get("view_height"))

        if \
                view_width <= 0 or view_height <= 0 or \
                view_width > VIEW_SIZE_LIMIT or view_height > VIEW_SIZE_LIMIT:
            raise Exception({"msg": "don't play with view size"})

    except KeyError as e:
        print(f"WebSocket connection closed: {e}")
        await ws.close(code=1000, reason="Missing required data")
        return
    except TypeError as e:
        print(f"WebSocket connection closed: {e}")
        await ws.close(code=1000, reason="Data not properly typed")
        return
    except Exception as e:
        await ws.close(code=1006, reason=e.__repr__())
        return

    conn = await ConnectionManager.add(ws, width=view_width, height=view_height)

    while True:
        try:
            msg = await conn.receive()
            await ConnectionManager.publish_client_event(conn_id=conn.id, msg=msg)
        except (WebSocketDisconnect, ConnectionClosed) as e:
            # 연결 종료됨
            break
        except Exception as e:
            await conn.send(Message(
                event=ErrorEvent.ERROR,
                payload=ErrorPayload(msg=e)
            ))

            print(f"Unhandled error while handling message: \n{msg.__dict__}\n{type(e)}: '{e}'")
            break

    await ConnectionManager.close(conn)


@app.get("/")
def health_check():
    return Response()


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        import asyncio
        from db import db
        asyncio.run(db.close())
