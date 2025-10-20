"""
Payload 모듈 테스트

테스트 범위:
- ExternalPayload.create() 정상 동작
- IdPayload 생성
- IdDataPayload 생성
"""

from core.data import DataObj
from frame import Payload, ExternalPayload, IdPayload, IdDataPayload
import unittest
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================
# Test Data
# ============================================================

class ExamplePayload(ExternalPayload):
    """Example External Payload"""
    field1: str
    field2: str


class ExampleData(DataObj):
    """Example Data Object"""
    name: str
    value: int


# ============================================================
# Tests
# ============================================================

class Payload_TestCase(unittest.TestCase):
    """Payload 모듈 테스트"""

    def test_payload_base(self):
        """Payload 기본 클래스 테스트"""
        # Payload는 DataObj를 상속하므로 dataclass로 동작
        self.assertTrue(issubclass(Payload, DataObj))

    def test_external_payload_create(self):
        """ExternalPayload.create() 테스트"""
        # dict에서 Payload 객체 생성
        data = {"field1": "value1", "field2": "value2"}
        payload = ExamplePayload.create(data)

        self.assertEqual(payload.field1, "value1")
        self.assertEqual(payload.field2, "value2")

    def test_external_payload_to_dict(self):
        """ExternalPayload.to_dict() 테스트"""
        payload = ExamplePayload(field1="test1", field2="test2")
        payload_dict = payload.to_dict()

        self.assertEqual(payload_dict["field1"], "test1")
        self.assertEqual(payload_dict["field2"], "test2")

    def test_id_payload_str(self):
        """IdPayload[str] 생성 테스트"""
        id_payload = IdPayload[str](id="example-123")
        self.assertEqual(id_payload.id, "example-123")

    def test_id_payload_int(self):
        """IdPayload[int] 생성 테스트"""
        id_payload = IdPayload[int](id=42)
        self.assertEqual(id_payload.id, 42)

    def test_id_data_payload(self):
        """IdDataPayload 생성 테스트"""
        # 변경 전 데이터
        old_data = ExampleData(name="test", value=100)

        # IdDataPayload 생성
        payload = IdDataPayload[str, ExampleData](
            id="example-123",
            data=old_data
        )

        self.assertEqual(payload.id, "example-123")
        self.assertEqual(payload.data.name, "test")
        self.assertEqual(payload.data.value, 100)

    def test_id_data_payload_to_dict(self):
        """IdDataPayload.to_dict() 테스트"""
        old_data = ExampleData(name="test", value=100)
        payload = IdDataPayload[str, ExampleData](
            id="example-123",
            data=old_data
        )

        payload_dict = payload.to_dict()

        self.assertEqual(payload_dict["id"], "example-123")
        self.assertEqual(payload_dict["data"]["name"], "test")
        self.assertEqual(payload_dict["data"]["value"], 100)

    def test_payload_copy(self):
        """Payload.copy() 테스트"""
        original = ExamplePayload(field1="value1", field2="value2")
        copied = original.copy()

        self.assertEqual(copied.field1, original.field1)
        self.assertEqual(copied.field2, original.field2)
        self.assertIsNot(copied, original)  # 다른 객체


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    unittest.main()
