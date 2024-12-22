from fastapi.websockets import WebSocket
from websockets.exceptions import ConnectionClosed
from message import Message
from dataclasses import dataclass


@dataclass
class Conn:
    id: str
    conn: WebSocket

    @staticmethod
    def create(id: str, ws: WebSocket):
        return Conn(id=id, conn=ws)

    async def accept(self):
        await self.conn.accept()

    async def close(self):
        await self.conn.close()

    async def receive(self):
        return Message.from_str(await self.conn.receive_text())

    async def send(self, msg: Message):
        try:
            await self.conn.send_text(msg.to_str())
        except ConnectionClosed:
            # 커넥션이 종료되었는데도 타이밍 문제로 인해 커넥션을 가져왔을 수 있음.
            return
