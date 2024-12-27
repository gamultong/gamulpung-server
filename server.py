from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from conn.manager import ConnectionManager
from board.event.handler import BoardEventHandler
from cursor.event.handler import CursorEventHandler
from message import Message
from message.payload import ErrorEvent, ErrorPayload

app = FastAPI()


@app.websocket("/session")
async def session(ws: WebSocket):
    try:
        view_width = int(ws.query_params.get("view_width"))
        view_height = int(ws.query_params.get("view_height"))
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
            message = await conn.receive()
            message.header = {"sender": conn.id}
            await ConnectionManager.handle_message(message)
        except (WebSocketDisconnect, ConnectionClosed) as e:
            # 연결 종료됨
            break
        except Exception as e:
            msg = e.__repr__()
            if hasattr(e, "msg"):
                msg = e.msg

            await conn.send(Message(
                event=ErrorEvent.ERROR,
                payload=ErrorPayload(msg=msg)
            ))

            print(f"Unhandled error while handling message: \n{message.__dict__}\n{type(e)}: '{msg}'")
            break

    await ConnectionManager.close(conn)


@app.get("/")
def health_check():
    return Response()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
