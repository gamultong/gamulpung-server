"""
Message 모듈 테스트

테스트 범위:
- Message 생성 및 to_dict()
- from_str() 역직렬화
- external_scope() 등록
- parsing 함수들
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
import json
from dataclasses import dataclass
from frame import Message
from frame.internal.message import EXTERNAL_SCOPE
from frame import Event, EventSet, set_scope
from frame import ExternalPayload, IdPayload


# ============================================================
# Test Data
# ============================================================

@dataclass
class ExamplePayload(ExternalPayload):
    """Example Payload"""
    data: dict[str, int]


@dataclass
class Example1Payload(ExternalPayload):
    """Example Payload 1"""
    field1: str
    field2: int


# ============================================================
# Tests
# ============================================================

class Message_TestCase(unittest.TestCase):
    """Message 모듈 테스트"""

    def test_message_creation(self):
        """Message 생성 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            SIMPLE = Event[str]

        event = ExampleEventSet.SIMPLE(payload="hello")
        message = Message(event=event)

        self.assertEqual(message.event, event)
        self.assertEqual(message.event.payload, "hello")

    def test_message_to_dict(self):
        """Message.to_dict() 테스트"""
        @set_scope("Example")
        class ExampleEventSet(EventSet):
            ACTION = Event[IdPayload[str]]

        payload = IdPayload[str](id="example-123")
        event = ExampleEventSet.ACTION(payload=payload)
        message = Message(event=event)

        message_dict = message.to_dict()

        self.assertIn("header", message_dict)
        self.assertIn("payload", message_dict)
        self.assertEqual(message_dict["header"]["event"], "Example.ACTION")

    def test_parsing_external_to_internal(self):
        """parsing_external_to_interanl() 테스트"""
        # kebab-case → snake_case + External scope
        result = Message.parsing_external_to_interanl("example-action")
        self.assertEqual(result, "External.example_action")

        result = Message.parsing_external_to_interanl("test-event")
        self.assertEqual(result, "External.test_event")

    def test_parsing_internal_to_external(self):
        """parsing_interanl_to_external() 테스트"""
        # snake_case + External scope → kebab-case
        result = Message.parsing_interanl_to_external("External.example_action")
        self.assertEqual(result, "example-action")

        result = Message.parsing_interanl_to_external("External.test_event")
        self.assertEqual(result, "test-event")

    def test_external_scope_registration(self):
        """external_scope() 등록 테스트"""
        # 새로운 Message 클래스 생성 (기존 것과 충돌 방지)
        class TestMessageClass(Message):
            _external_event_sets = []
            _external_events_dict = {}

        @TestMessageClass.external_scope
        class ExampleEventSet(EventSet):
            EVENT_1 = Event[ExamplePayload]
            EVENT_2 = Event[Example1Payload]

        # EventSet이 External scope로 등록되었는지 확인
        self.assertIn(ExampleEventSet, TestMessageClass._external_event_sets)
        self.assertEqual(ExampleEventSet.scope_name, EXTERNAL_SCOPE)

        # Event가 dict에 등록되었는지 확인
        self.assertIn("External.EVENT_1", TestMessageClass._external_events_dict)
        self.assertIn("External.EVENT_2", TestMessageClass._external_events_dict)

    def test_message_from_str(self):
        """Message.from_str() 역직렬화 테스트"""
        # 새로운 Message 클래스 생성
        class TestMessageClass(Message):
            _external_event_sets = []
            _external_events_dict = {}

        @TestMessageClass.external_scope
        class ExampleEventSet(EventSet):
            ACTION = Event[ExamplePayload]

        # JSON 문자열 → Message
        json_str = json.dumps({
            "header": {"event": "action"},
            "payload": {"data": {"x": 10, "y": 20}}
        })

        message = TestMessageClass.from_str(json_str)

        self.assertEqual(message.event.name, "External.ACTION")
        self.assertEqual(message.event.payload.data["x"], 10)
        self.assertEqual(message.event.payload.data["y"], 20)

    def test_message_roundtrip(self):
        """Message 생성 → dict → JSON → from_str 라운드트립 테스트"""
        # 새로운 Message 클래스 생성
        class TestMessageClass(Message):
            _external_event_sets = []
            _external_events_dict = {}

        @TestMessageClass.external_scope
        class ExampleEventSet(EventSet):
            UPDATE = Event[Example1Payload]

        # 1. Message 생성
        payload = Example1Payload(field1="test", field2=42)
        event = ExampleEventSet.UPDATE(payload=payload)
        original_message = TestMessageClass(event=event)

        # 2. Message → dict
        message_dict = original_message.to_dict()

        # 3. dict → JSON (external naming 변환)
        external_dict = {
            "header": {
                "event": TestMessageClass.parsing_interanl_to_external(message_dict["header"]["event"])
            },
            "payload": message_dict["payload"].to_dict()
        }
        json_str = json.dumps(external_dict)

        # 4. JSON → Message
        reconstructed_message = TestMessageClass.from_str(json_str)

        # 5. 검증
        self.assertEqual(reconstructed_message.event.name, original_message.event.name)
        self.assertEqual(reconstructed_message.event.payload.field1, original_message.event.payload.field1)
        self.assertEqual(reconstructed_message.event.payload.field2, original_message.event.payload.field2)

    def test_multiple_external_eventsets(self):
        """여러 External EventSet 등록 테스트"""
        class TestMessageClass(Message):
            _external_event_sets = []
            _external_events_dict = {}

        @TestMessageClass.external_scope
        class Example1EventSet(EventSet):
            EVENT_1 = Event[ExamplePayload]

        @TestMessageClass.external_scope
        class Example2EventSet(EventSet):
            EVENT_2 = Event[ExamplePayload]

        # 두 EventSet 모두 등록되었는지 확인
        self.assertEqual(len(TestMessageClass._external_event_sets), 2)
        self.assertIn(Example1EventSet, TestMessageClass._external_event_sets)
        self.assertIn(Example2EventSet, TestMessageClass._external_event_sets)

        # Event가 모두 dict에 등록되었는지 확인
        self.assertIn("External.EVENT_1", TestMessageClass._external_events_dict)
        self.assertIn("External.EVENT_2", TestMessageClass._external_events_dict)


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    unittest.main()
