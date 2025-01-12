class NoMatchingReceiverException(Exception):
    def __init__(self, event: str):
        self.event = event

    def __str__(self):
        return f"no matching receiver for '{self.event}'"
