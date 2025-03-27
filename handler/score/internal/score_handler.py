from data.score import Score
from data.payload import EventEnum, DataPayload

from handler.storage.interface import KeyValueInterface, ListInterface
from handler.storage.dict import DictStorage
from handler.storage.list.array import ArrayListStorage
from data.payload import DataPayload, IdPayload
from event.broker import EventBroker
from event.message import Message

class ScoreEvent(EventEnum):
    CREATED = "Score.created"
    UPDATED = "Score.updated"
    DELETED = "Score.deleted"

# 숙제
# publishable -> 권한 부여, 메서드 주입
# identify.Event 자동

class ScoreNotFoundException(Exception):
    pass
class RankOutOfRangeException(Exception):
    pass
class ScoreAlreadyExistsException(Exception):
    pass

# @publishable 
class ScoreHandler:
    __identify__:str = "Score"
    __event__: ScoreEvent

    score_storage:KeyValueInterface[str, Score] = DictStorage.create_space(
        key=__identify__ + ".score"
    )
    rank_index:ListInterface[str] = ArrayListStorage.create_space(
        key=__identify__ + ".rank"
    )

    @classmethod
    async def get_by_id(cls, id: str) -> Score:
        score = await cls.score_storage.get(id)
        if score is None:
            raise ScoreNotFoundException()

        return score

    @classmethod
    async def get_by_rank(cls, start:int, end:int|None=None) -> tuple[Score]:
        if end is None:
            end = start

        if not (1 <= start <= end <= await cls.rank_index.length()):
            raise RankOutOfRangeException()
        
        async def get_score_by_idx(idx: int):
            key = await cls.rank_index.get(idx)
            score = await cls.score_storage.get(key)
            return score

        result = [
            await get_score_by_idx(idx)
            for idx in range(start-1, end) # 1,2,3 -> 0,1,2
        ]
            
        return tuple(result)

    @classmethod
    async def update(cls, score: Score):
        current = await cls.score_storage.get(score.id)
        if current is None:
            raise ScoreNotFoundException()

        score.rank = current.rank
        score = await cls.__move_rank(score)
        message = Message(
            event=ScoreEvent.UPDATED,
            payload=DataPayload(data=current)
        )
        
        await cls.score_storage.set(score.id, score)
        await EventBroker.publish(message=message)

    @classmethod
    async def create(cls, id: str):
        current = await cls.score_storage.get(id)
        if current is not None:
            raise ScoreAlreadyExistsException()

        await cls.rank_index.append(id)
        
        score = Score(id, 0, await cls.rank_index.length())
        message = Message(
            event=ScoreEvent.CREATED,
            payload=IdPayload(id=id)
        )

        await cls.score_storage.set(score.id, score)
        await EventBroker.publish(message=message)

    @classmethod
    async def length(cls):
        return await cls.rank_index.length()

    @classmethod
    async def delete(cls, id: str):
        score = await cls.score_storage.get(id)
        if score is None:
            raise ScoreNotFoundException()

        await cls.score_storage.delete(id)
        await cls.__delete_rank(score)
        
        await EventBroker.publish(
            message=Message(
                event=ScoreEvent.DELETED,
                payload=DataPayload(data=score)
            )
        )

    @classmethod
    async def __delete_rank(cls, score:Score):
        for i in range(score.rank, await cls.rank_index.length()):
            id = await cls.rank_index.get(i)
            other_score = await cls.score_storage.get(id)
            other_score.rank -= 1
            await cls.score_storage.set(id, other_score)

        await cls.rank_index.pop(score.rank - 1)
        
    @classmethod
    async def __move_rank(cls, score:Score):
        # score 인자 -> score 변경 O | rank 변경 X
        # score minus 없다는 기준 

        # 기존 rank 위치 제거
        # 지금 스코어의 rank 찾기 = O(log N) (지금은 O(N))
        # 지금 스코어의 rank에 score id 넣기
        # 이전 rank와 현재 rank 사이에 있는 스코어들에게 rank + 1 = O(N)
        # 범위: 현재 rank < n <= 이전 rank 
        
        prev_rank = score.rank
        await cls.rank_index.pop(score.rank - 1)
        
        for i in range(prev_rank - 1):
            id = await cls.rank_index.get(i)
            other_score = await cls.score_storage.get(id)

            if other_score.score < score.score:
                score.rank = other_score.rank
                await cls.rank_index.insert(other_score.rank - 1, score.id)
                break
            
        for i in range(score.rank, prev_rank):
            id = await cls.rank_index.get(i)
            other_score = await cls.score_storage.get(id)
            other_score.rank += 1 
            await cls.score_storage.set(id, other_score)

        return score


"""
기능 정리

set
given score
when 기존 score X
then score_storage에 추가 & rank_index에 append & created event 발행
when 기존 score O
then rank_index에 변경 범위 모두 rank 수정 후 socre 모두 updated event 발행 

delete
"""