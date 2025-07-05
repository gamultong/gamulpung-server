from event.broker import EventBroker
from event.message import Message
from event.payload import Empty

from data.conn.event import ServerEvent

from data.cursor import Cursor
from data.score import Score

from data.payload import DataPayload

from handler.score import ScoreEvent

from unittest import TestCase, IsolatedAsyncioTestCase as AsyncTestCase
from unittest.mock import AsyncMock, MagicMock, call
from ..test_tools import get_cur_set, assertMulticast
from tests.utils import PathPatch, cases, override, MockSet, Wrapper as Wp
from config import SCOREBOARD_SIZE

from receiver.internal.score.save_deleted_score import (
    SaveDeletedScoreReceiver
)


MOCK_PATH = "receiver.internal.score.save_deleted_score"
patch = PathPatch(MOCK_PATH)


class SaveDeletedScoreReceiver_TestCase(AsyncTestCase):
    pass
