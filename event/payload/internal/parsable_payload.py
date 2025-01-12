from typing import TypeVar, Generic

DATA_TYPE = TypeVar("DATA_TYPE")


class ParsablePayload(Generic[DATA_TYPE]):
    pass