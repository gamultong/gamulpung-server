from dataclasses import dataclass, Field
from unittest.mock import MagicMock
from unittest import TestCase
from .utils import MockSet, override, Wrapper as Wp

from .nothing import example_wrapper


class ExampleMockSet(MockSet):
    __path__ = "tests.nothing"

    foo: Wp[MagicMock] = override(name="example", return_value=2)


class MockSet_TestCase(TestCase):
    @ExampleMockSet.patch()
    def test_patched(self, mock_set: ExampleMockSet):
        value = example_wrapper()
        self.assertEqual(value, 2)

    @ExampleMockSet.patch(
        override("foo", return_value=3)
    )
    def test_patched_override(self, mock_set: ExampleMockSet):
        value = example_wrapper()
        self.assertEqual(value, 3)


if __name__ == "__main__":
    from unittest import main
    main()
