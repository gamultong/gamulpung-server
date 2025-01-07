from enum import Enum
from random import randint


class Color(str, Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    PURPLE = "PURPLE"
    BLUE = "BLUE"

    @staticmethod
    def get_random():
        rand_idx = randint(0, len(Color._member_names_) - 1)
        color = Color._member_names_[rand_idx]
        return Color._member_map_[color]
