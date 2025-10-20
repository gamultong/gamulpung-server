"""
Event & EventSet 모듈 테스트

테스트 범위:
- EventSet 정의 및 Event 생성
- set_scope() 적용
- event.name 확인
- Event payload 타입 확인
"""

from core.data import DataObj
from frame import Payload, IdPayload, IdDataPayload
from frame import Event, EventSet, set_scope
from dataclasses import dataclass
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# Test Data
# ============================================================

@dataclass
class ExampleData(DataObj):
    """Example Data Object"""
    name: str
    value: int


# ============================================================
# Tests
# ============================================================

class Event_TestCase(unittest.TestCase):
    """Event & EventSet 모듈 테스트"""

    def test_eventset_basic(self):
        """EventSet 기본 정의 테스트"""
        class ExampleEventSet(EventSet):
            EVENT_1 = Event[str]
            EVENT_2 = Event[int]

        # EventSet이 Event 타입들을 포함하는지 확인
        self.assertTrue(hasattr(ExampleEventSet, "EVENT_1"))
        self.assertTrue(hasattr(ExampleEventSet, "EVENT_2"))

    def test_event_creation(self):
        """Event 생성 테스트"""
        class ExampleEventSet(EventSet):
            STRING_EVENT = Event[str]
            INT_EVENT = Event[int]

        # Event 객체 생성
        str_event = ExampleEventSet.STRING_EVENT(payload="hello")
        int_event = ExampleEventSet.INT_EVENT(payload=42)

        self.assertEqual(str_event.payload, "hello")
        self.assertEqual(int_event.payload, 42)

    def test_set_scope_decorator(self):
        """set_scope() 데코레이터 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            CREATE = Event[IdPayload[str]]
            UPDATE = Event[IdDataPayload[str, ExampleData]]
            DELETE = Event[IdPayload[str]]

        # scope_name 확인
        self.assertEqual(ExampleEventSet.scope_name, "Example")

        # Event name에 scope가 포함되는지 확인
        self.assertEqual(ExampleEventSet.CREATE.name, "Example.CREATE")
        self.assertEqual(ExampleEventSet.UPDATE.name, "Example.UPDATE")
        self.assertEqual(ExampleEventSet.DELETE.name, "Example.DELETE")

    def test_event_name_without_scope(self):
        """scope 없는 Event name 테스트"""
        class ExampleEventSet(EventSet):
            EVENT_1 = Event[str]

        # scope가 설정되지 않았으므로 scope 없는 이름
        self.assertEqual(ExampleEventSet.EVENT_1.name, "EVENT_1")

    def test_event_payload_type(self):
        """Event payload_type 확인 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            STRING_EVENT = Event[str]
            ID_EVENT = Event[IdPayload[int]]

        # payload_type 확인
        self.assertIs(ExampleEventSet.STRING_EVENT.payload_type, str)
        self.assertEqual(ExampleEventSet.ID_EVENT.payload_type, IdPayload[int])

    def test_eventset_events_method(self):
        """EventSet.events() 메서드 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            EVENT_1 = Event[IdPayload[str]]
            EVENT_2 = Event[IdPayload[str]]

        events_dict = ExampleEventSet.events()

        # dict 형태로 반환되는지 확인
        self.assertIsInstance(events_dict, dict)
        self.assertIn("Example.EVENT_1", events_dict)
        self.assertIn("Example.EVENT_2", events_dict)

    def test_event_scope_reference(self):
        """Event에서 EventSet 역참조 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            CREATE = Event[IdPayload[str]]

        # Event가 자신이 속한 EventSet을 참조하는지 확인
        self.assertEqual(ExampleEventSet.CREATE.scope, ExampleEventSet)

    def test_multiple_eventsets(self):
        """여러 EventSet 정의 테스트"""
        @set_scope("Example1")
        class Example1EventSet(EventSet):
            CREATE = Event[IdPayload[str]]

        @set_scope("Example2")
        class Example2EventSet(EventSet):
            CREATE = Event[IdPayload[str]]

        # 서로 다른 scope를 가지므로 이름이 다름
        self.assertEqual(Example1EventSet.CREATE.name, "Example1.CREATE")
        self.assertEqual(Example2EventSet.CREATE.name, "Example2.CREATE")
        self.assertNotEqual(Example1EventSet.CREATE.name, Example2EventSet.CREATE.name)

    def test_event_with_complex_payload(self):
        """복잡한 Payload를 가진 Event 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            UPDATE = Event[IdDataPayload[str, ExampleData]]

        # 복잡한 Payload로 Event 생성
        old_data = ExampleData(name="test", value=100)
        payload = IdDataPayload[str, ExampleData](
            id="example-123",
            data=old_data
        )
        event = ExampleEventSet.UPDATE(payload=payload)

        self.assertEqual(event.name, "Example.UPDATE")
        self.assertEqual(event.payload.id, "example-123")
        self.assertEqual(event.payload.data.name, "test")
        self.assertEqual(event.payload.data.value, 100)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    unittest.main()
