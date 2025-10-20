"""
테스트 유틸리티 함수들
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, Optional
import tempfile
import os


class MockDatabase:
    """데이터베이스 모킹을 위한 클래스"""

    def __init__(self):
        self.is_closed = False
        self.data = {}

    async def execute(self, sql: str, params: tuple = ()):
        """SQL 실행 시뮬레이션"""
        return MockCursor()

    async def executemany(self, sql: str, params_list):
        """여러 SQL 실행 시뮬레이션"""
        return MockCursor()

    async def fetchall(self):
        """모든 행 가져오기 시뮬레이션"""
        return []

    async def fetchone(self):
        """한 행 가져오기 시뮬레이션"""
        return None

    async def commit(self):
        """커밋 시뮬레이션"""
        pass

    async def close(self):
        """연결 종료 시뮬레이션"""
        self.is_closed = True


class MockCursor:
    """데이터베이스 커서 모킹을 위한 클래스"""

    def __init__(self):
        self.rowcount = 0
        self.lastrowid = 1


class TestDatabaseManager:
    """테스트용 데이터베이스 매니저"""

    _instance = None
    _mock_db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_mock_db(cls) -> MockDatabase:
        """모킹된 데이터베이스 인스턴스 반환"""
        if cls._mock_db is None:
            cls._mock_db = MockDatabase()
        return cls._mock_db

    @classmethod
    def reset_mock_db(cls):
        """모킹된 데이터베이스 리셋"""
        cls._mock_db = None


def patch_database():
    """데이터베이스를 모킹하는 데코레이터"""
    def decorator(func):
        return patch('db.get_db')(patch('db.use_db')(func))
    return decorator


def create_test_temp_file() -> str:
    """테스트용 임시 파일 생성"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return path


def cleanup_test_temp_file(path: str):
    """테스트용 임시 파일 정리"""
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


class AsyncContextManagerMock:
    """비동기 컨텍스트 매니저 모킹"""

    def __init__(self, return_value=None):
        self.return_value = return_value or MockDatabase()

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


def mock_websocket_connection():
    """WebSocket 연결 모킹"""
    mock_ws = MagicMock()
    mock_ws.accept = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


class EventBrokerTestHelper:
    """EventBroker 테스트 도우미"""

    @staticmethod
    def mock_event_broker():
        """EventBroker 모킹"""
        return patch('event.broker.EventBroker.publish', new_callable=AsyncMock)

    @staticmethod
    def verify_event_published(mock_publish: AsyncMock, event_name: str) -> bool:
        """특정 이벤트가 발행되었는지 확인"""
        for call in mock_publish.call_args_list:
            if call[0] and hasattr(call[0][0], 'event') and call[0][0].event == event_name:
                return True
        return False


class GameStateTestHelper:
    """게임 상태 테스트 도우미"""

    @staticmethod
    def create_mock_board(width: int = 10, height: int = 10):
        """모킹된 게임 보드 생성"""
        board = {}
        for x in range(width):
            for y in range(height):
                board[(x, y)] = {
                    'is_mine': False,
                    'is_open': False,
                    'is_flag': False,
                    'mine_count': 0
                }
        return board

    @staticmethod
    def create_mock_cursor(cursor_id: str, x: int = 0, y: int = 0):
        """모킹된 커서 생성"""
        return {
            'id': cursor_id,
            'position': {'x': x, 'y': y},
            'color': 'red',
            'score': 0,
            'revive_at': None
        }


def integration_test_setup():
    """통합 테스트 설정"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 데이터베이스 모킹
            TestDatabaseManager.reset_mock_db()

            # 이벤트 브로커 모킹
            with EventBrokerTestHelper.mock_event_broker():
                return await func(*args, **kwargs)
        return wrapper
    return decorator