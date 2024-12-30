import asyncio
import random
from board.data import Point, Section, Tile, Tiles
from board.data.storage import SectionStorage
from cursor.data import Color


async def init_board():
    # 맵 초기화
    sec_0_0 = await SectionStorage.get(Point(0, 0))
    if sec_0_0 is None:
        section_0_0 = Section.create(Point(0, 0))

        tiles = section_0_0.fetch(Point(0, 0))
        t = Tile.from_int(tiles.data[0])
        t.is_open = True

        section_0_0.update(Tiles(data=[t.data]), Point(0, 0))

        await SectionStorage.set(section_0_0)


asyncio.run(init_board())


class BoardHandler:

    @staticmethod
    async def fetch(start: Point, end: Point) -> Tiles:
        # 반환할 데이터 공간 미리 할당
        out_width, out_height = (end.x - start.x + 1), (start.y - end.y + 1)
        out = bytearray(out_width * out_height)

        for sec_y in range(start.y // Section.LENGTH, end.y // Section.LENGTH - 1, - 1):
            for sec_x in range(start.x // Section.LENGTH, end.x // Section.LENGTH + 1):
                section = await BoardHandler._get_or_create_section(Point(sec_x, sec_y))

                inner_start = Point(
                    x=max(start.x, section.abs_x) - (section.abs_x),
                    y=min(start.y, section.abs_y + Section.LENGTH-1) - section.abs_y
                )
                inner_end = Point(
                    x=min(end.x, section.abs_x + Section.LENGTH-1) - section.abs_x,
                    y=max(end.y, section.abs_y) - section.abs_y
                )

                fetched = section.fetch(start=inner_start, end=inner_end)

                x_gap, y_gap = (inner_end.x - inner_start.x + 1), (inner_start.y - inner_end.y + 1)

                # start로부터 떨어진 거리
                out_x = (section.abs_x + inner_start.x) - start.x
                out_y = start.y - (section.abs_y + inner_start.y)

                for row_num in range(y_gap):
                    out_idx = (out_width * (out_y + row_num)) + out_x
                    data_idx = row_num * x_gap

                    data = fetched.data[data_idx:data_idx+x_gap]
                    out[out_idx:out_idx+x_gap] = data

        return Tiles(data=out)

    @staticmethod
    async def open_tile(p: Point) -> Tile:
        section, inner_p = await BoardHandler._get_section_from_abs_point(p)

        tiles = section.fetch(inner_p)

        tile = Tile.from_int(tiles.data[0])
        tile.is_open = True

        tiles.data[0] = tile.data

        section.update(data=tiles, start=inner_p)
        await BoardHandler._set_section(section)

        return tile

    @staticmethod
    async def open_tiles_cascade(p: Point) -> tuple[Point, Point, Tiles]:
        """
        지정된 타일부터 주변 타일들을 연쇄적으로 개방한다.
        빈칸들과 빈칸과 인접한숫자 타일까지 개방하며, 섹션 가장자리 데이터가 새로운 섹션으로 인해 중간에 수정되는 것을 방지하기 위해
        섹션을 사용할 때 인접 섹션이 존재하지 않으면 미리 만들어 놓는다.
        """
        # 탐색하며 발견한 섹션들
        sections: list[Section] = []

        async def get_section(p: Point) -> tuple[Section, Point]:
            sec_p = Point(
                x=p.x // Section.LENGTH,
                y=p.y // Section.LENGTH
            )

            section = None
            for sec in sections:
                # 이미 가지고 있으면 반환
                if sec.p == sec_p:
                    section = sec
                    break

            # 새로 가져오기
            if section is None:
                section = await BoardHandler._get_or_create_section(sec_p)
                sections.append(section)

            inner_p = Point(
                x=p.x - section.abs_x,
                y=p.y - section.abs_y
            )

            return section, inner_p

        queue = []
        queue.append(p)

        visited = set()
        visited.add((p.x, p.y))

        # 추후 fetch 범위
        min_x, min_y = p.x, p.y
        max_x, max_y = p.x, p.y

        while len(queue) > 0:
            p = queue.pop(0)

            # 범위 업데이트
            min_x, min_y = min(min_x, p.x), min(min_y, p.y)
            max_x, max_y = max(max_x, p.x), max(max_y, p.y)

            sec, inner_p = await get_section(p)

            # TODO: section.fetch_one(point) 같은거 만들어야 할 듯
            tile = Tile.from_int(sec.fetch(inner_p).data[0])

            # 타일 열어주기
            tile.is_open = True
            tile.is_flag = False
            tile.color = None

            sec.update(Tiles(data=bytearray([tile.data])), inner_p)

            if tile.number is not None:
                # 빈 타일 주변 number까지만 열어야 함.
                continue

            # (x, y) 순서
            delta = [
                (0, 1), (0, -1), (-1, 0), (1, 0),  # 상하좌우
                (-1, 1), (1, 1), (-1, -1), (1, -1),  # 좌상 우상 좌하 우하
            ]

            # 큐에 추가될 포인트 리스트
            temp_list = []

            for dx, dy in delta:
                np = Point(x=p.x+dx, y=p.y+dy)

                if (np.x, np.y) in visited:
                    continue
                visited.add((np.x, np.y))

                sec, inner_p = await get_section(np)

                nearby_tile = Tile.from_int(sec.fetch(inner_p).data[0])
                if nearby_tile.is_open:
                    # 이미 연 타일, 혹은 이전에 존재하던 열린 number 타일
                    continue

                temp_list.append(np)

            queue.extend(temp_list)

        # 섹션 변경사항 모두 저장
        await asyncio.gather(*[BoardHandler._set_section(section) for section in sections])

        start_p = Point(min_x, max_y)
        end_p = Point(max_x, min_y)
        tiles = await BoardHandler.fetch(start_p, end_p)

        return start_p, end_p, tiles

    @staticmethod
    async def set_flag_state(p: Point, state: bool, color: Color | None = None) -> Tile:
        section, inner_p = await BoardHandler._get_section_from_abs_point(p)

        tiles = section.fetch(inner_p)

        tile = Tile.from_int(tiles.data[0])
        tile.is_flag = state
        tile.color = color

        tiles.data[0] = tile.data

        section.update(data=tiles, start=inner_p)
        await BoardHandler._set_section(section)

        return tile

    async def _get_section_from_abs_point(abs_p: Point) -> tuple[Section, Point]:
        """
        절대 좌표 abs_p를 포함하는 섹션, 그리고 abs_p의 섹션 내부 좌표를 반환한다.
        """
        sec_p = Point(
            x=abs_p.x // Section.LENGTH,
            y=abs_p.y // Section.LENGTH
        )

        section = await BoardHandler._get_or_create_section(sec_p)

        inner_p = Point(
            x=abs_p.x - section.abs_x,
            y=abs_p.y - section.abs_y
        )

        return section, inner_p

    @staticmethod
    async def get_random_open_position() -> Point:
        """
        전체 맵에서 랜덤한 열린 타일 위치를 하나 찾는다.
        섹션이 하나 이상 존재해야한다.
        """
        # 이미 방문한 섹션들
        visited = set()

        while True:
            rand_p = await SectionStorage.get_random_sec_point()
            if (rand_p.x, rand_p.y) in visited:
                continue

            visited.add((rand_p.x, rand_p.y))

            chosen_section = await BoardHandler._get_section_or_none(rand_p)

            # 섹션 내부의 랜덤한 열린 타일 위치를 찾는다.
            inner_point = randomly_find_open_tile(chosen_section)
            if inner_point is None:
                continue

            open_point = Point(
                x=chosen_section.abs_x + inner_point.x,
                y=chosen_section.abs_y + inner_point.y
            )

            return open_point

    @staticmethod
    async def _get_or_create_section(p: Point) -> Section:
        """
        p에 해당하는 섹션을 가져온다. 만약 섹션이 존재하지 않으면 새로 만든다.
        완전한(주변 섹션과의 관계가 모두 적용된) 섹션을 반환한다.
        """
        section = await BoardHandler._get_section_or_none(p)

        is_complete_section = True

        if section is None:
            is_complete_section = False
            section = Section.create(p)

        # (x, y)
        delta = [
            (0, 1), (0, -1), (-1, 0), (1, 0),  # 상하좌우
            (-1, 1), (1, 1), (-1, -1), (1, -1),  # 좌상 우상 좌하 우하
        ]

        save_section_coroutines = []

        # 주변 섹션과 새로운 섹션의 인접 타일을 서로 적용시킨다.
        for dx, dy in delta:
            np = Point(p.x+dx, p.y+dy)
            neighbor = await BoardHandler._get_section_or_none(np)
            if neighbor is not None:
                continue

            # 주변 섹션이 존재하지 않으면 새로 생성 및 section에 적용.
            neighbor = Section.create(np)
            is_complete_section = False

            if dx != 0 and dy != 0:
                section.apply_neighbor_diagonal(neighbor)
            elif dx != 0:
                section.apply_neighbor_horizontal(neighbor)
            elif dy != 0:
                section.apply_neighbor_vertical(neighbor)

            save_section_coroutines.append(BoardHandler._set_section(neighbor))

        # 모서리 적용이 안 되어 있었다면 적용된 버전의 섹션을 저장
        if not is_complete_section:
            save_section_coroutines.append(BoardHandler._set_section(section))

        await asyncio.gather(*save_section_coroutines)

        return section

    @staticmethod
    async def explosion_count():
        sectios = await SectionStorage.get_all()
        if sectios is None:
            return 0

        total = 0
        for sec in sectios:
            total += sec.get_explosion_count()

        return total

    @staticmethod
    async def _get_section_or_none(p: Point) -> Section | None:
        return await SectionStorage.get(p)

    @staticmethod
    async def _set_section(sec: Section):
        await SectionStorage.set(sec)


def randomly_find_open_tile(section: Section) -> Point | None:
    """
    섹션 안에서 랜덤한 열린 타일 위치를 찾는다.
    시작 위치, 순회 방향의 순서를 무작위로 잡아 탐색한다.
    만약 열린 타일이 존재하지 않는다면 None.
    """

    # (증감값, 한계값)
    directions = [
        (1, Section.LENGTH - 1), (-1, 0)  # 순방향, 역방향
    ]
    random.shuffle(directions)

    x_start = random.randint(0, Section.LENGTH - 1)
    y_start = random.randint(0, Section.LENGTH - 1)

    pointers = [0, 0]  # first, second
    start_values = [0, 0]

    x_first = random.choice([True, False])
    x_pointer = 0 if x_first else 1
    y_pointer = 1 if x_first else 0

    start_values[x_pointer] = x_start
    start_values[y_pointer] = y_start

    # second 양방향 탐색
    for num, limit in directions:
        for second in range(start_values[1], limit + num, num):
            pointers[1] = second

            # first 양방향 탐색
            for num, limit in directions:
                for first in range(start_values[0], limit + num, num):
                    pointers[0] = first

                    x = pointers[x_pointer]
                    y = pointers[y_pointer]

                    idx = y * Section.LENGTH + x

                    tile = Tile.from_int(section.data[idx])
                    if tile.is_open:
                        # 좌표계에 맞게 y 반전
                        y = Section.LENGTH - y - 1
                        return Point(x, y)
