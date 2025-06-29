from data.conn.event import ServerEvent


async def multicast(target_conns: list[str], event: ServerEvent.Base):
    # TODO: event broker가 아닌 connection에 직접 쏴 줄 수 있도록 바꾸기
    pass
    # if len(target_conns) == 0:
    #     return

    # await EventBroker.publish(
    #     message=Message(
    #         event="multicast",
    #         header={
    #             "target_conns": target_conns,
    #             "origin_event": message.event
    #         },
    #         payload=message.payload
    #     )
    # )


async def broadcast(event: ServerEvent.Base):
    # TODO: 위와 같음.
    pass
    # await EventBroker.publish(
    #     message=Message(
    #         event="broadcast",
    #         header={
    #             "origin_event": message.event
    #         },
    #         payload=message.payload
    #     )
    # )
