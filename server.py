from fastapi import FastAPI, WebSocket, Response, WebSocketDisconnect
from websockets.exceptions import ConnectionClosed
from handler.conn import ConnectionHandler, Conn

app = FastAPI()


@app.websocket("/session")
async def session(ws: WebSocket):
    conn = await Conn.create(ws)

    await ConnectionHandler.join(conn)

    while True:
        try:
            client_event = await conn.receive()
            await ConnectionHandler.publish_client_event(conn, client_event)
        except (WebSocketDisconnect, ConnectionClosed) as e:
            # 연결 종료됨
            break

    await ConnectionHandler.quit(conn)


@app.get("/")
def health_check():
    return Response()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
