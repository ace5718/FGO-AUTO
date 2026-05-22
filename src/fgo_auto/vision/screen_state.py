from enum import Enum


class ScreenState(str, Enum):
    UNKNOWN = "unknown"
    MAIN = "main"
    TERMINAL = "terminal"
    BATTLE = "battle"
    RESULT = "result"
