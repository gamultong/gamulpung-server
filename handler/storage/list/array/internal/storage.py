from .space import ArrayListSpace
from handler.storage.interface import (
    DuplicateSpaceException, SpaceNotFoundException, Storage
)

class ArrayListStorage(Storage):
    @staticmethod
    def create_space(key: str):
        if key in ArrayListStorage.spaces:
            raise DuplicateSpaceException

        space = ArrayListSpace(name=key, data=[])
        ArrayListStorage.spaces[key] = space

        return space

    @staticmethod
    def get_space(key: str):
        if key not in ArrayListStorage.spaces:
            raise SpaceNotFoundException

        return ArrayListStorage.spaces[key]
