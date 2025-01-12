class InvalidFieldException(Exception):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return f"invaild field: {self.get_key()} -> {self.get_value()}"

    def get_key(self):
        if type(self.value) == self.__class__:
            return f"{self.key}.{self.value.get_key()}"
        return self.key

    def get_value(self):
        if type(self.value) == self.__class__:
            return self.value.get_value()
        return self.value


class MissingFieldException(Exception):
    def __init__(self, key, value=None):
        self.key = key
        self.value = value

    def __str__(self):
        return f"missing {len(tuple(self.get_keys()))} keys: {", ".join(self.get_keys())}"

    def get_keys(self):
        if type(self.value) == self.__class__:
            return map(lambda key: f"{self.key}.{key}", self.value.get_keys())
        return self.key


class DumbHumanException(Exception):
    def __str__(self):
        return "worng use. what have you done"
