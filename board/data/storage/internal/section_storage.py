from board.data import Point, Section
import lmdb

env = lmdb.Environment(path="./database", max_dbs=1)


class SectionStorage:
    def get(p: Point) -> Section | None:
        with env.begin() as tx:
            p_key = p.marshal_bytes()

            data = tx.get(p_key)
            if data is not None:
                return Section(p=p, data=bytearray(data))

            return None

    def create(section: Section):
        with env.begin(write=True) as tx:
            p_key = section.p.marshal_bytes()

            tx.put(key=p_key, value=section.data, overwrite=False)

    def update(section: Section):  
        with env.begin(write=True) as tx:
            p_key = section.p.marshal_bytes()

            tx.put(key=p_key, value=section.data, overwrite=True)