from board.data import Point, Section, Tile, Tiles
from cursor.data import Color


def init_first_section() -> dict[int, dict[int, Section]]:
    section_0_0 = Section.create(Point(0, 0))

    tiles = section_0_0.fetch(Point(0, 0))

    t = Tile.from_int(tiles.data[0])
    t.is_open = True

    section_0_0.update(Tiles(data=[t.data]), Point(0, 0))

    return {0: {0: section_0_0}}


class BoardHandler:
    # sections[y][x]
    sections: dict[int, dict[int, Section]] = init_first_section()

    @staticmethod
    def fetch(start: Point, end: Point) -> Tiles:
        # 반환할 데이터 공간 미리 할당
        out_width, out_height = (end.x - start.x + 1), (start.y - end.y + 1)
        out = bytearray(out_width * out_height)

        for sec_y in range(start.y // Section.LENGTH, end.y // Section.LENGTH - 1, - 1):
            for sec_x in range(start.x // Section.LENGTH, end.x // Section.LENGTH + 1):
                section = BoardHandler._get_or_create_section(sec_x, sec_y)

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
    def open_tile(p: Point) -> Tile:
        section, inner_p = BoardHandler._get_section_from_abs_point(p)

        tiles = section.fetch(inner_p)

        tile = Tile.from_int(tiles.data[0])
        tile.is_open = True

        tiles.data[0] = tile.data

        section.update(data=tiles, start=inner_p)
        BoardHandler._save_section(section)

        return tile

    @staticmethod
    def open_tiles_cascade(p: Point) -> tuple[Point, Point, Tiles]:
        # 탐색하며 발견한 섹션들
        sections: list[Section] = []

        def get_section(p: Point) -> tuple[Section, Point]:
            sec_p = Point(
                x=p.x // Section.LENGTH,
                y=p.y // Section.LENGTH
            )
            for section in sections:
                if section.p == sec_p:
                    inner_p = Point(
                        x=p.x - section.abs_x,
                        y=p.y - section.abs_y
                    )
                    return section, inner_p

            found_section, inner_p = BoardHandler._get_section_from_abs_point(p)
            sections.append(found_section)

            return found_section, inner_p

        queue = []
        queue.append(p)

        # 추후 fetch 범위
        min_x, min_y = p.x, p.y
        max_x, max_y = p.x, p.y

        while len(queue) > 0:
            p = queue.pop(0)

            min_x, min_y = min(min_x, p.x), min(min_y, p.y)
            max_x, max_y = max(max_x, p.x), max(max_y, p.y)

            sec, inner_p = get_section(p)

            # TODO: section.fetch_one(point) 같은거 만들어야 할 듯
            tile = Tile.from_int(sec.fetch(inner_p).data[0])

            # 열어주기
            tile.is_open = True
            tile.is_flag = False
            tile.color = None

            sec.update(Tiles(data=bytearray([tile.data])), inner_p)

            if tile.number is not None:
                continue

            # (x, y) 순서
            delta = [
                (0, 1), (0, -1), (-1, 0), (1, 0),  # 상하좌우
                (-1, 1), (1, 1), (-1, -1), (1, -1),  # 좌상 우상 좌하 우하
            ]

            for dx, dy in delta:
                np = Point(x=p.x+dx, y=p.y+dy)

                sec, inner_p = get_section(np)
                tile = Tile.from_int(sec.fetch(inner_p).data[0])
                if tile.is_open or tile.is_mine:
                    # is_mine이 True인 경우:
                    # cascading open으로 인해 생긴 새로운 섹션의 가장자리가 지뢰일 때.
                    continue

                queue.append(np)

        # 섹션 변경사항 모두 저장
        for section in sections:
            BoardHandler._save_section(section)

        start_p = Point(min_x, max_y)
        end_p = Point(max_x, min_y)
        tiles = BoardHandler.fetch(start_p, end_p)

        return start_p, end_p, tiles

    @staticmethod
    def set_flag_state(p: Point, state: bool, color: Color | None = None) -> Tile:
        section, inner_p = BoardHandler._get_section_from_abs_point(p)

        tiles = section.fetch(inner_p)

        tile = Tile.from_int(tiles.data[0])
        tile.is_flag = state
        tile.color = color

        tiles.data[0] = tile.data

        section.update(data=tiles, start=inner_p)
        BoardHandler._save_section(section)

        return tile

    def _get_section_from_abs_point(abs_p: Point) -> tuple[Section, Point]:
        """
        절대 좌표 abs_p를 포함하는 섹션, 그리고 abs_p의 섹션 내부 좌표를 반환한다.
        """
        sec_p = Point(
            x=abs_p.x // Section.LENGTH,
            y=abs_p.y // Section.LENGTH
        )

        section = BoardHandler._get_or_create_section(sec_p.x, sec_p.y)

        inner_p = Point(
            x=abs_p.x - section.abs_x,
            y=abs_p.y - section.abs_y
        )

        return section, inner_p

    def _save_section(section: Section):
        BoardHandler.sections[section.p.y][section.p.x] = section

    @staticmethod
    def _get_or_create_section(x: int, y: int) -> Section:
        if y not in BoardHandler.sections:
            BoardHandler.sections[y] = {}

        if x not in BoardHandler.sections[y]:
            new_section = Section.create(Point(x, y))

            # (x, y)
            delta = [
                (0, 1), (0, -1), (-1, 0), (1, 0),  # 상하좌우
                (-1, 1), (1, 1), (-1, -1), (1, -1),  # 좌상 우상 좌하 우하
            ]

            # 주변 섹션과 새로운 섹션의 인접 타일을 서로 적용시킨다.
            for dx, dy in delta:
                nx, ny = x+dx, y+dy
                neighbor = BoardHandler._get_section_or_none(nx, ny)
                # 주변 섹션이 없을 수 있음.
                if neighbor is None:
                    continue

                if dx != 0 and dy != 0:
                    neighbor.apply_neighbor_diagonal(new_section)
                elif dx != 0:
                    neighbor.apply_neighbor_horizontal(new_section)
                elif dy != 0:
                    neighbor.apply_neighbor_vertical(new_section)

                BoardHandler.sections[ny][nx] = neighbor

            BoardHandler.sections[y][x] = new_section

        return BoardHandler.sections[y][x]

    @staticmethod
    def _get_section_or_none(x: int, y: int) -> Section | None:
        if y in BoardHandler.sections and x in BoardHandler.sections[y]:
            return BoardHandler.sections[y][x]
