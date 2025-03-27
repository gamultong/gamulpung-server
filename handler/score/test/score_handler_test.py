from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from tests.utils import PathPatch
from handler.storage.dict import DictSpace
from handler.storage.list.array import ArrayListSpace
from event.message import Message

from data.payload import DataPayload, IdPayload

patch = PathPatch("handler.score.internal.score_handler")
from handler.score import ScoreHandler, ScoreEvent, ScoreNotFoundException, RankOutOfRangeException
from data.score import Score

class ScoreHandler_TestCase(AsyncTestCase):
    def setUp(self):
        self.score_a = Score("A", 100, 2)
        self.score_b = Score("B", 200, 1)

        self.score_storage = DictSpace[str, Score](
            "score", {
            "A":self.score_a,
            "B": self.score_b
        })
        self.rank_index = ArrayListSpace[str](
            "rank", [self.score_b.id, self.score_a.id]
        )

        ScoreHandler.score_storage = self.score_storage
        ScoreHandler.rank_index = self.rank_index

    async def test_length(self):
        self.assertEqual(
            2,
            await ScoreHandler.length()
        )

    async def test_get_by_id_normal(self):
        score_a = await ScoreHandler.get_by_id("A")
        
        self.assertEqual(score_a, self.score_a)

    async def test_get_by_id_not_found(self):
        with self.assertRaises(ScoreNotFoundException):
            await ScoreHandler.get_by_id("C")        

    async def test_get_by_rank_single(self):
        score, *_ = await ScoreHandler.get_by_rank(1)
        self.assertEqual(score, self.score_b)

    async def test_get_by_rank_range(self):
        score_1, score_2 = await ScoreHandler.get_by_rank(1, 2)
        self.assertEqual(score_1, self.score_b)
        self.assertEqual(score_2, self.score_a)

    async def test_get_by_rank_out_of_range(self):
        with self.assertRaises(RankOutOfRangeException):
            await ScoreHandler.get_by_rank(0, 1)
        with self.assertRaises(RankOutOfRangeException):
            await ScoreHandler.get_by_rank(1, 3)

    async def test_get_by_rank_start_over_end(self):
        with self.assertRaises(RankOutOfRangeException):
            await ScoreHandler.get_by_rank(2, 1)

    @patch("EventBroker.publish")
    async def test_create(self, mock: AsyncMock):
        await ScoreHandler.create("C")
        mock.assert_called_once_with(
            message=Message(
                event=ScoreEvent.CREATED,
                payload=IdPayload(id="C")
            )
        )
        self.assertEqual(self.score_storage.data["C"], Score("C", 0, 3))

    @patch("EventBroker.publish")
    async def test_update(self, mock: AsyncMock):
        await ScoreHandler.update(Score("A", 300))
        
        mock.assert_called_once_with(
            message=Message(
                event=ScoreEvent.UPDATED,
                payload=DataPayload(
                    data=self.score_a,
                )
            )
        )

        self.assertNotEqual(self.score_storage.data["A"], self.score_a)
        self.assertEqual(self.score_storage.data["A"], Score("A", 300, 1))
        self.assertEqual(self.score_storage.data["B"], Score("B", 200, 2))

    @patch("EventBroker.publish")
    async def test_delete(self, mock: AsyncMock):
        await ScoreHandler.delete("B")
       
        mock.assert_called_once_with(
            message=Message(
                event=ScoreEvent.DELETED,
                payload=DataPayload(
                    data=self.score_b
                )
            ) 
        )
        
        self.assertNotIn("B", self.score_storage.data)
        self.assertEqual(self.score_storage.data["A"], Score("A", 100, 1))
    
    @patch("EventBroker.publish")
    async def test_delete_not_found(self, mock: AsyncMock):
        with self.assertRaises(ScoreNotFoundException):        
            await ScoreHandler.delete("C")