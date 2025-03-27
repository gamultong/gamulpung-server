from .space import DictSpace
from handler.storage.interface import (
    DuplicateSpaceException, SpaceNotFoundException, Storage
)

class DictStorage(Storage):
    @staticmethod
    def create_space(key: str):
        if key in DictStorage.spaces:
            raise DuplicateSpaceException

        space = DictSpace(name=key, data={})
        DictStorage.spaces[key] = space

        return space

    @staticmethod
    def get_space(key: str):
        if key not in DictStorage.spaces:
            raise SpaceNotFoundException

        return DictStorage.spaces[key]
