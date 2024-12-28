class InvalidEventTypeException(Exception):
    def __init__(self, event: str):
        self.event = event

    def __str__(self):
        return f"invalid event type: '{self.event}'"
