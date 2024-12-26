from board.data import Point, Section
import lmdb
import random

env = lmdb.Environment(path="./database", max_dbs=1)


class SectionStorage:
    def get_random_sec_point() -> Point:
        """
        주의: 한개 이상의 섹션이 존재해야 함
        TODO: 전체 key를 불러오고 있음.
        """
        with env.begin() as tx:
            with tx.cursor() as cursor:
                keys = list(cursor.iternext(keys=True, values=False))
                rand_key = random.choice(keys)

                return Point.unmarshal_bytes(rand_key)

    def get(p: Point) -> Section | None:
        with env.begin() as tx:
            p_key = p.marshal_bytes()

            data = tx.get(p_key)
            if data is not None:
                return Section(p=p, data=bytearray(data))

            return None

    def set(section: Section):
        with env.begin(write=True) as tx:
            p_key = section.p.marshal_bytes()

            tx.put(key=p_key, value=section.data)
