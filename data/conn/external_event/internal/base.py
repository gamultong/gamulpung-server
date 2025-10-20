from core.event.frame import ExternalPayload


class Validate_Protocol:
    # TODO : 구현 및 util로 이동
    def validate(self):
        pass


class ServerPayload(ExternalPayload, Validate_Protocol):
    pass


class ClientPayload(ExternalPayload, Validate_Protocol):
    pass


class ValidationException(Exception):
    # TODO : 구현
    def __init__(self, event, msg) -> None:
        pass
