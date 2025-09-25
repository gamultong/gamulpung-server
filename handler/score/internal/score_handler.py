from data.score import Score
from event.payload import EventEnum, IdDataPayload

from handler.storage.interface import KeyValueInterface, ListInterface
from handler.storage.dict import DictStorage
from handler.storage.list.array import ArrayListStorage
from event.broker import EventBroker, publish_data_event
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
    __identify__: str = "Score"
    __event__: ScoreEvent

    score_storage: KeyValueInterface[str, Score] = DictStorage.create_space(
        key=__identify__ + ".score"
    )
    rank_index: ListInterface[str] = ArrayListStorage.create_space(
        key=__identify__ + ".rank"
    )

    # external_method start

    @classmethod
    async def get(cls, id: str) -> Score:
        score = await cls.score_storage.get(id)
        if score is None:
            raise ScoreNotFoundException()

        return score

    @classmethod
    async def get_by_rank(cls, start: int, end: int | None = None) -> tuple[Score]:
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
            for idx in range(start-1, end)  # 1,2,3 -> 0,1,2
        ]

        return tuple(result)

    @classmethod
    async def increase(cls, id: str, value: int):
        score = await cls.score_storage.get(id)
        if score is None:
            raise ScoreNotFoundException()

        score.value += value
        return await cls.update(score)

    @classmethod
    async def update(cls, score: Score):
        current = await cls.score_storage.get(score.id)
        if current is None:
            raise ScoreNotFoundException()

        score = await cls.__update(current, score.value)

        await publish_data_event(ScoreEvent.UPDATED, data=current)

        return score

    @classmethod
    async def create(cls, id: str):
        current = await cls.score_storage.get(id)
        if current is not None:
            raise ScoreAlreadyExistsException()

        score = Score(id, 0)
        score = await cls.__create(score=score)

        await publish_data_event(ScoreEvent.CREATED, id=id)

    @classmethod
    async def length(cls):
        return await cls.rank_index.length()

    @classmethod
    async def delete(cls, id: str):
        score = await cls.score_storage.get(id)
        if score is None:
            raise ScoreNotFoundException()

        await cls.__delete(score)

        await publish_data_event(ScoreEvent.DELETED, data=score)

    # external_method end

    @classmethod
    async def __delete(cls, score: Score):
        await cls.score_storage.delete(score.id)
        await cls.rank_index.pop(score.rank - 1)

        length = await cls.length()
        await cls.__adjust_rank_range(score.rank, length)

    @classmethod
    async def __create(cls, score: Score):
        score = score.copy()
        score.rank = await cls.rank_index.length() + 1

        await cls.rank_index.append(score.id)
        await cls.score_storage.set(score.id, score)
        return score

    @classmethod
    async def __update(cls, score: Score, new_value: int):
        """score가 증가한다고만 가정"""
        # 이전 score, 증가 new_socre:int
        score = score.copy()

        before_rank = score.rank
        score.rank = await cls.__find_rank(new_value)
        score.value = new_value

        await cls.rank_index.pop(before_rank - 1)
        await cls.rank_index.insert(score.rank - 1, score.id)
        await cls.score_storage.set(score.id, score)

        await cls.__adjust_rank_range(score.rank, before_rank)
        return score

    @classmethod
    async def __adjust_rank_range(cls, start_rank: int, before_rank: int):
        for idx in range(start_rank - 1, before_rank):
            id = await cls.rank_index.get(idx)
            score = await cls.score_storage.get(id)

            score.rank = idx + 1
            await cls.score_storage.set(score.id, score)

    @classmethod
    async def __find_rank(cls, value: int):
        length = await cls.rank_index.length()
        for i in range(length):
            id = await cls.rank_index.get(i)
            score = await cls.score_storage.get(id)

            if score.value < value:
                return score.rank

        return length
