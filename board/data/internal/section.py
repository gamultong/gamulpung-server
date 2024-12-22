from .point import Point
from .tile import Tile
from .tiles import Tiles
from .exceptions import InvalidDataLengthException
from random import randint
from typing import Callable

MINE_TILE = 0b01000000
NUM_MASK = 0b00000111


class Section:
    LENGTH = 100
    MINE_RATIO = 0.3

    def __init__(self, p: Point, data: bytearray):
        self.p = p
        self.data = data

    def fetch(self, start: Point, end: Point | None = None) -> Tiles:
        if end is None:
            end = start

        # row 당 가져올 원소 개수 + 1
        x_gap = end.x - start.x + 1

        result = bytearray()
        for y in range(start.y, end.y-1, -1):
            # (row 길이 * y의 실제 인덱스 위치) + x 오프셋
            idx_start = Section.LENGTH * (Section.LENGTH - y - 1) + start.x
            result += self.data[idx_start: idx_start+x_gap]

        return Tiles(data=result)

    def update(self, data: Tiles, start: Point, end: Point | None = None) -> None:
        if end is None:
            end = start

        expected_len = (end.x - start.x + 1) * (start.y - end.y + 1)
        if len(data.data) != expected_len:
            raise InvalidDataLengthException(expected=expected_len, actual=len(data.data))

        x_gap = end.x - start.x + 1

        for y in range(start.y, end.y-1, -1):
            idx_start = Section.LENGTH * (Section.LENGTH - y - 1) + start.x
            offset = (start.y - y) * x_gap
            self.data[idx_start: idx_start+x_gap] = data.data[offset: offset+x_gap]

    @property
    def abs_x(self):
        return self.p.x * Section.LENGTH

    @property
    def abs_y(self):
        return self.p.y * Section.LENGTH

    def apply_neighbor_diagonal(self, neighbor):
        """
        대각선 방향에서 인접한 섹션을 서로 적용.
        각 섹션의 꼭짓점 부분만 체크하면 된다.
        """
        if self.p.y > neighbor.p.y:
            self_y = Section.LENGTH - 1
            neighbor_y = 0
        else:
            self_y = 0
            neighbor_y = Section.LENGTH - 1

        if self.p.x > neighbor.p.x:
            self_x = 0
            neighbor_x = Section.LENGTH - 1
        else:
            self_x = Section.LENGTH - 1
            neighbor_x = 0

        self_idx = (self_y * Section.LENGTH) + self_x
        neighbor_idx = (neighbor_y * Section.LENGTH) + neighbor_x

        if self.data[self_idx] & MINE_TILE:
            affect_origin_mines_to_new(
                new_tiles=neighbor.data,
                x_range=(neighbor_x, neighbor_x),
                y_range=(neighbor_y, neighbor_y)
            )

        if neighbor.data[neighbor_idx] & MINE_TILE:
            affect_new_mines_to_origin(
                origin_tiles=self.data,
                new_tiles=neighbor.data,
                mine_p=Point(neighbor_x, neighbor_y),
                x_range=(self_x, self_x),
                y_range=(self_y, self_y)
            )

    def apply_neighbor_vertical(self, neighbor):
        """
        수직 방향에서 인접한 섹션을 서로 적용.
        상하 모서리를 수평 방향으로 적용시킨다.
        """
        if self.p.y > neighbor.p.y:
            self_y = Section.LENGTH - 1
            neighbor_y = 0
        else:
            self_y = 0
            neighbor_y = Section.LENGTH - 1

        for x in range(Section.LENGTH):
            self_idx = (self_y * Section.LENGTH) + x
            neighbor_idx = (neighbor_y * Section.LENGTH) + x

            # 현재 위치가 mine일 시 상대 섹션에 적용시킬 x 범위
            leftmost = max(0, x - 1)
            rightmost = min(x + 1, Section.LENGTH - 1)

            if self.data[self_idx] & MINE_TILE:
                affect_origin_mines_to_new(
                    new_tiles=neighbor.data,
                    x_range=(leftmost, rightmost),
                    y_range=(neighbor_y, neighbor_y)
                )

            if neighbor.data[neighbor_idx] & MINE_TILE:
                affect_new_mines_to_origin(
                    origin_tiles=self.data,
                    new_tiles=neighbor.data,
                    mine_p=Point(x, neighbor_y),
                    x_range=(leftmost, rightmost),
                    y_range=(self_y, self_y)
                )

    def apply_neighbor_horizontal(self, neighbor):
        """
        수평 방향에서 인접한 섹션을 서로 적용.
        좌우 모서리를 수직 방향으로 적용시킨다.
        """
        if self.p.x > neighbor.p.x:
            self_x = 0
            neighbor_x = Section.LENGTH - 1
        else:
            self_x = Section.LENGTH - 1
            neighbor_x = 0

        for y in range(Section.LENGTH):
            self_idx = (y * Section.LENGTH) + self_x
            neighbor_idx = (y * Section.LENGTH) + neighbor_x

            # 현재 위치가 mine일 시 상대 섹션에 적용시킬 y 범위
            top = min(y + 1, Section.LENGTH - 1)
            bottom = max(0, y - 1)

            if self.data[self_idx] & MINE_TILE:
                affect_origin_mines_to_new(
                    new_tiles=neighbor.data,
                    x_range=(neighbor_x, neighbor_x),
                    y_range=(bottom, top)
                )

            if neighbor.data[neighbor_idx] & MINE_TILE:
                affect_new_mines_to_origin(
                    origin_tiles=self.data,
                    new_tiles=neighbor.data,
                    mine_p=Point(neighbor_x, y),
                    x_range=(self_x, self_x),
                    y_range=(bottom, top)
                )

    @staticmethod
    def from_str(p: Point, data: str):
        """
        레거시, 관련 로직 바꿔야 함.
        """
        return Section(p, bytearray.fromhex(data))

    @staticmethod
    def create(p: Point):
        total = Section.LENGTH**2
        mine_cnt = int((total * Section.MINE_RATIO)//1)

        # zero-value로 초기화됨,
        data = bytearray(total)

        for _ in range(mine_cnt):
            # 랜덤 위치가 잘못된 경우 재시도
            while True:
                rand_p = Point(
                    x=randint(0, Section.LENGTH - 1),
                    y=randint(0, Section.LENGTH - 1)
                )

                rand_idx = (rand_p.y * Section.LENGTH) + rand_p.x
                cur_tile = data[rand_idx]

                # 이미 지뢰가 존재
                if cur_tile & MINE_TILE:
                    continue

                # 주변 타일 검사
                valid = check_neighbor_restrictions(tiles=data, p=rand_p)
                if not valid:
                    continue

                data[rand_idx] = MINE_TILE

                # 주변 타일 숫자 증가
                increase_number_around(tiles=data, p=rand_p)
                break

        return Section(p=p, data=data)


def affect_origin_mines_to_new(new_tiles: bytearray, x_range: tuple[int, int], y_range: tuple[int, int]):
    """
    기존 존재하는 섹션(origin)의 지뢰들을 새로 들어온 섹션(new)의 타일에 적용
    -> origin에 지뢰가 존재 -> new에 위치한 인접 타일들 num += 1
    만약 new의 인접 타일이 7이면, 그 타일 주변 지뢰를 하나 제거한다.

    x_range, y_range 범위에 위치한 new 타일을 1씩 더해준다.
    """
    for y in range(y_range[0], y_range[1] + 1):
        for x in range(x_range[0], x_range[1] + 1):
            idx = (y * Section.LENGTH) + x

            tile = new_tiles[idx]
            if tile & MINE_TILE:
                continue

            num = tile & NUM_MASK
            if num == 7:
                # new의 num이 7이라면 주변 지뢰 1개 제거하여 origin의 지뢰를 적용시킬 수 있도록 한다.
                remove_one_nearby_mine(new_tiles, Point(x, y))
            else:
                tile += 1
            new_tiles[idx] = tile


def affect_new_mines_to_origin(
    origin_tiles: bytearray, new_tiles: bytearray, mine_p: Point,
    x_range: tuple[int, int], y_range: tuple[int, int]
):
    """
    새로 들어온 섹션(new)의 지뢰들을 기존 존재하는 섹션(origin)의 타일에 적용
    -> new에 지뢰가 존재 -> origin에 위치한 인접 타일들 num += 1
    만약 origin의 인접 타일이 7이면, new의 지뢰를 삭제한다.

    x_range, y_range 범위에 위치한 origin 타일을 1씩 더해준다.
    """
    for y in range(y_range[0], y_range[1] + 1):
        for x in range(x_range[0], x_range[1] + 1):
            idx = (y * Section.LENGTH) + x

            tile = origin_tiles[idx]
            if tile & MINE_TILE:
                continue

            num = tile & NUM_MASK
            if num == 7:
                # origin의 num이 7이다.
                # 이 경우에는 new의 지뢰를 제거하고 숫자로 덮어씌워준다.
                cnt = decrease_number_around_and_count_mines(
                    tiles=new_tiles,
                    p=mine_p
                )

                new_tiles_idx = (mine_p.y * Section.LENGTH) + mine_p.x
                new_tiles[new_tiles_idx] = cnt
                continue

            origin_tiles[idx] = tile + 1


def decrease_number_around_and_count_mines(tiles: bytearray, p: Point) -> int:
    """
    주변 8칸 타일들의 num을 1씩 감소시킨다.
    만약 타일이 지뢰라면, cnt++ 해준다.
    """
    cnt = 0

    def do(t: int, p: Point) -> tuple[int | None, bool]:
        nonlocal cnt
        if t & MINE_TILE:
            cnt += 1
            return None, False

        t -= 1
        return t, False

    for_each_neighbor(tiles, p, do)

    return cnt


def remove_one_nearby_mine(tiles: bytearray, p: Point):
    """
    주변 타일 중 지뢰 타일 하나를 제거한다.
    지뢰 타일은 주변 지뢰 개수 숫자로 덮어씌워지며,
    그 주변 타일의 num은 1씩 감소한다.
    """
    def do(t: int, p: Point) -> tuple[int | None, bool]:
        if not (t & MINE_TILE):
            return None, False

        cnt = decrease_number_around_and_count_mines(tiles=tiles, p=p)
        return cnt, True

    for_each_neighbor(tiles, p, do)


def increase_number_around(tiles: bytearray, p: Point):
    """
    주변 타일의 num을 1씩 증가시킨다.
    """
    def do(t: int, p: Point) -> tuple[int | None, bool]:
        if t & MINE_TILE:
            return None, False

        t += 1

        return t, False

    for_each_neighbor(tiles, p, do)


def check_neighbor_restrictions(tiles: bytearray, p: Point) -> bool:
    """
    mine이 생길 타일 주변 타일의 제약사항을 검사하여 valid한지 반환한다.
    valid하면 True.

    1. num이 7인가? -> mine을 더 추가하면 8이 된다.
    """
    valid = True

    def do(t: int, p: Point) -> tuple[int | None, bool]:
        nonlocal valid
        # 주변 타일이 7을 넘지 않아야 함
        if t & NUM_MASK == 7:
            valid = False

        return None, not valid

    for_each_neighbor(tiles, p, do)

    return valid


# (x, y)
_delta = [
    (0, 1), (0, -1), (-1, 0), (1, 0),  # 상하좌우
    (-1, 1), (1, 1), (-1, -1), (1, -1),  # 좌상 우상 좌하 우하
]


def for_each_neighbor(tiles: bytearray, p: Point, func: Callable[[int, Point], tuple[int | None, bool]]):
    """
    p(section 내부 좌표)의 주변 8방향의 인접 타일을 돌며 func를 실행.
    만약 인접 타일이 section의 범위를 벗어난다면 무시함.

    [func 반환값]
    tile: None이 아니면 타일을 업데이트.
    stop: True면 반복 중지
    """

    # 주변 탐색
    for dx, dy in _delta:
        np = Point(p.x+dx, p.y+dy)
        if \
                np.x < 0 or np.x >= Section.LENGTH or \
                np.y < 0 or np.y >= Section.LENGTH:
            continue

        new_idx = (np.y * Section.LENGTH) + np.x
        nearby_tile = tiles[new_idx]

        tile, stop = func(nearby_tile, np)
        if tile is not None:
            tiles[new_idx] = tile

        if stop:
            break
