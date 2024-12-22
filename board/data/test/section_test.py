from tests.utils import cases
from board.data import Section, Point, Tile, Tiles
from board.data.internal.section import for_each_neighbor

import unittest


# 테스트를 위해 Section.LENGTH를 4로 설정
Section.LENGTH = 4

# hex는 문자 2개 사용하기 때문에 2번 반복
EXAPMLE_SECTION_DATA = "11223344556677889900aabbccddeeff"
DATA_LENGTH = (Section.LENGTH ** 2) * 2

EXAMPLE_POINT = Point(x=0, y=Section.LENGTH - 1)

FETCH_TEST_CASES = [
    {
        "desc": "fetch all",
        "range": {
            "start_point": EXAMPLE_POINT,
            "end_point": Point(
                x=Section.LENGTH-1,
                y=0
            )
        },
        "expect": EXAPMLE_SECTION_DATA
    },
    {
        "desc": "fetch start",
        "range": {
            "start_point": EXAMPLE_POINT
        },
        "expect": EXAPMLE_SECTION_DATA[0: 2]
    },
    {
        "desc": "fetch end",
        "range": {
            "start_point": Point(
                x=Section.LENGTH - 1,
                y=0
            )
        },
        "expect": EXAPMLE_SECTION_DATA[DATA_LENGTH - 2:]
    }
]


class SectionTestCase(unittest.TestCase):
    def setUp(self):
        self.section = Section.from_str(
            p=EXAMPLE_POINT,
            data=EXAPMLE_SECTION_DATA
        )

    def test_from_str(self):
        self.section = Section.from_str(
            p=EXAMPLE_POINT,
            data=EXAPMLE_SECTION_DATA
        )

        self.assertEqual(self.section.p, EXAMPLE_POINT)

        data_length = len(self.section.data)
        self.assertEqual(data_length, Section.LENGTH ** 2)

    @cases(FETCH_TEST_CASES)
    def test_fetch(self, desc, range, expect):
        start = range["start_point"]
        end = range["end_point"] if "end_point" in range else None

        data = self.section.fetch(start=start, end=end)

        self.assertEqual(data.to_str(), expect, desc)

    def test_fetch_out_of_range(self):
        pass
        # TODO:
        # {
        #     "desc": "fetch out of range",
        #     "range": {
        #         "start_point": Point(
        #             x=EXAMPLE_POINT.x + Section.LENGTH + 1,
        #             y=EXAMPLE_POINT.y
        #             )
        #     },
        #     "expect": IndexError()
        # },

    def test_update_one(self):
        value = Tiles(data=b'A')

        self.section.update(data=value, start=EXAMPLE_POINT)

        got = self.section.fetch(start=EXAMPLE_POINT)
        self.assertEqual(got, value)

    def test_update_range(self):
        rows = 3
        cols = 3

        # 업데이트용 row * col 크기의 2D bytearray 생성
        data = bytearray().join([bytearray.fromhex(f"{i}{i}")*cols for i in range(rows)])
        value = Tiles(data)
        start = EXAMPLE_POINT
        end = Point(2, 1)

        self.section.update(data=value, start=start, end=end)

        got = self.section.fetch(start=start, end=end)
        self.assertEqual(got.data, value.data)

    def test_create(self):
        mine = Tile.create(
            is_open=False,
            is_mine=True,
            is_flag=False,
            color=None,
            number=None,
        )

        sec = Section.create(Point(0, 0))

        total = Section.LENGTH ** 2
        mine_cnt = int((total * Section.MINE_RATIO)//1)

        self.assertEqual(len(sec.data), total)
        self.assertEqual(sec.data.count(mine.data), mine_cnt)

        num_mask = 0b00000111
        mine_tile = 0b01000000

        for y in range(Section.LENGTH):
            for x in range(Section.LENGTH):
                idx = (y * Section.LENGTH) + x
                tile = sec.data[idx]
                if tile == mine.data:
                    continue

                result = 0

                # 숫자가 제대로 기록되어 있는가
                def count_num(t: int, p: Point) -> tuple[int | None, bool]:
                    nonlocal result
                    if t == mine_tile:
                        result += 1

                    return None, False

                for_each_neighbor(sec.data, Point(x, y), func=count_num)

                got = tile & num_mask

                self.assertEqual(got, result)

                # 숫자가 7을 넘지 않는가
                def check_number_restriction(t: int, p: Point) -> tuple[int | None, bool]:
                    self.assertLessEqual(t & num_mask,  7)
                    return None, False

                for_each_neighbor(sec.data, Point(x, y), func=check_number_restriction)


class SectionApplyNeighborTestCase(unittest.TestCase):
    def setUp(self):
        # 왼쪽 위 섹션: 오른쪽 끝을 감싸는 지뢰들
        self.left_top_section = Section(Point(-1, 1), data=bytearray([
            MINES_OF(0), MINES_OF(1), MINES_OF(2), MINES_OF(2),
            MINES_OF(0), MINES_OF(2), MINE_TILE__, OPEN_MINE__,
            MINES_OF(0), MINES_OF(3), MINE_TILE__, MINES_OF(5),
            MINES_OF(0), MINES_OF(2), MINE_TILE__, MINE_TILE__
        ]))
        # 오른쪽 위 섹션: 왼쪽 아래 끝단 2개 지뢰
        self.right_top_section = Section(Point(0, 1), data=bytearray([
            MINES_OF(1), MINES_OF(1), MINES_OF(0), MINES_OF(0),
            MINE_TILE__, MINES_OF(2), MINES_OF(0), MINES_OF(0),
            OPEN_MINE__, MINES_OF(4), MINES_OF(1), MINES_OF(0),
            OPEN_MINE__, MINE_TILE__, MINES_OF(1), MINES_OF(0)
        ]))
        # 왼쪽 아래 섹션: 오른쪽 아래 끝단 2개 지뢰
        self.left_bottom_section = Section(Point(-1, 0), data=bytearray([
            MINES_OF(0), MINES_OF(0), MINES_OF(0), MINES_OF(0),
            MINES_OF(0), MINES_OF(0), MINES_OF(1), MINES_OF(1),
            MINES_OF(0), MINES_OF(0), MINES_OF(2), MINE_TILE__,
            MINES_OF(0), MINES_OF(0), MINES_OF(2), OPEN_MINE__
        ]))
        # 오른쪽 아래 섹션: 왼쪽 위 끝단을 감싸는 지뢰들
        self.right_bottom_section = Section(Point(0, 0), data=bytearray([
            MINES_OF(3), OPEN_MINE__, MINES_OF(2), MINES_OF(0),
            MINE_TILE__, MINE_TILE__, MINES_OF(2), MINES_OF(0),
            MINES_OF(2), MINES_OF(2), MINES_OF(1), MINES_OF(0),
            MINES_OF(0), MINES_OF(0), MINES_OF(0), MINES_OF(0)
        ]))

    def test_apply_neighbor_vertical(self):
        self.right_bottom_section.apply_neighbor_vertical(
            neighbor=self.right_top_section
        )
        # right_top_section
        self.assertEqual(self.right_top_section.data[14], MINES_OF(2))  # x=2, y=0
        # right_bottom_section
        self.assertEqual(self.right_bottom_section.data[0], MINES_OF(5))  # x=0, y=3
        self.assertEqual(self.right_bottom_section.data[2], MINES_OF(3))  # x=2, y=3

    def test_apply_neighbor_down(self):
        self.right_top_section.apply_neighbor_vertical(
            neighbor=self.right_bottom_section
        )
        # right_top_section
        self.assertEqual(self.right_top_section.data[14], MINES_OF(2))  # x=2, y=0
        # right_bottom_section
        self.assertEqual(self.right_bottom_section.data[0], MINES_OF(5))  # x=0, y=3
        self.assertEqual(self.right_bottom_section.data[2], MINES_OF(3))  # x=2, y=3

    def test_apply_neighbor_right(self):
        self.left_bottom_section.apply_neighbor_horizontal(
            neighbor=self.right_bottom_section
        )
        # left_bottom_section
        self.assertEqual(self.left_bottom_section.data[3], MINES_OF(1))  # x=3, y=3
        self.assertEqual(self.left_bottom_section.data[7], MINES_OF(2))  # x=3, y=2
        # below_section
        self.assertEqual(self.right_bottom_section.data[8], MINES_OF(4))  # x=0, y=1
        self.assertEqual(self.right_bottom_section.data[12], MINES_OF(2))  # x=0, y=0

    def test_apply_neighbor_left(self):
        self.right_bottom_section.apply_neighbor_horizontal(
            neighbor=self.left_bottom_section
        )
        # left_bottom_section
        self.assertEqual(self.left_bottom_section.data[3], MINES_OF(1))  # x=3, y=3
        self.assertEqual(self.left_bottom_section.data[7], MINES_OF(2))  # x=3, y=2
        # below_section
        self.assertEqual(self.right_bottom_section.data[8], MINES_OF(4))  # x=0, y=1
        self.assertEqual(self.right_bottom_section.data[12], MINES_OF(2))  # x=0, y=0

    def test_apply_neighbor_diagnoal_left_top_right_bottom(self):
        self.left_top_section.apply_neighbor_diagonal(
            neighbor=self.right_bottom_section
        )
        # right_bottom_section
        self.assertEqual(self.right_bottom_section.data[0], MINES_OF(4))  # x=0, y=3

    def test_apply_neighbor_diagnoal_right_bottom_left_top(self):
        self.right_bottom_section.apply_neighbor_diagonal(
            neighbor=self.left_top_section
        )
        # right_bottom_section
        self.assertEqual(self.right_bottom_section.data[0], MINES_OF(4))  # x=0, y=3

    def test_apply_neighbor_diagnoal_left_bottom_right_top(self):
        self.left_bottom_section.apply_neighbor_diagonal(
            neighbor=self.right_top_section
        )
        # left_bottom_section
        self.assertEqual(self.left_bottom_section.data[3], MINES_OF(1))  # x=3, y=3

    def test_apply_neighbor_diagnoal_right_top_left_bottom(self):
        self.right_top_section.apply_neighbor_diagonal(
            neighbor=self.left_bottom_section
        )
        # left_bottom_section
        self.assertEqual(self.left_bottom_section.data[3], MINES_OF(1))  # x=3, y=3

    def test_apply_neighbor_num_overflow_left_right(self):
        self.left_top_section.apply_neighbor_horizontal(
            neighbor=self.right_top_section
        )

        # left_top_section
        self.assertEqual(self.left_top_section.data[11], MINES_OF(7))  # x=3, y=1

        # right_top_section
        l = [
            self.right_top_section.data[4],  # x=0, y=2
            self.right_top_section.data[8],  # x=0, y=1
            self.right_top_section.data[12],  # x=0, y=0
        ]
        self.assertEqual(l.count(MINE_TILE__) + l.count(OPEN_MINE__), 2)

    def test_apply_neighbor_num_overflow_right_left(self):
        self.right_top_section.apply_neighbor_horizontal(
            neighbor=self.left_top_section
        )

        # left_top_section
        self.assertEqual(self.left_top_section.data[11], MINES_OF(7))  # x=3, y=1
        l = [
            self.left_top_section.data[6],  # x=2, y=2
            self.left_top_section.data[7],  # x=3, y=2
            self.left_top_section.data[10],  # x=2, y=1
            self.left_top_section.data[14],  # x=2, y=0
            self.left_top_section.data[15],  # x=3, y=0

        ]
        self.assertEqual(l.count(MINE_TILE__) + l.count(OPEN_MINE__), 4)


MINE_TILE__ = 0b01000000
OPEN_MINE__ = 0b11000000


def MINES_OF(n: int) -> int:
    if n > 7:
        raise "invalid mine count"
    return n


if __name__ == "__main__":
    unittest.main()
