from enum import IntEnum

PROTOCOL_VERSION = "2.0"
BOARD_SIZE = 20


class StoneType(IntEnum):
    EMPTY = 0
    OWN = 1
    OPPONENT = 2
