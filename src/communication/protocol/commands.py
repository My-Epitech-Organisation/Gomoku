##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## commands
##

from enum import Enum
from typing import Any


class CommandType(Enum):
    START = "START"
    TURN = "TURN"
    BEGIN = "BEGIN"
    BOARD = "BOARD"
    END = "END"
    ABOUT = "ABOUT"
    DONE = "DONE"
    UNKNOWN = "UNKNOWN"


class Command:
    def __init__(self, type: CommandType, params: dict[str, Any] | None = None):
        self.type = type
        self.params = params

    def __str__(self) -> str:
        if self.params is None:
            return self.type.value
        return f"{self.type.value} {self.params}"


class StartCommand(Command):
    def __init__(self, size: int):
        super().__init__(CommandType.START, {"size": size})

    def size(self) -> int:
        return self.params["size"]


class TurnCommand(Command):
    def __init__(self, x: int, y: int):
        super().__init__(CommandType.TURN, {"x": x, "y": y})

    def x(self) -> int:
        return self.params["x"]

    def y(self) -> int:
        return self.params["y"]


class BoardMove:
    def __init__(self, x: int, y: int, stone_type: int):
        self.x = x
        self.y = y
        self.stone_type = stone_type

    def __str__(self) -> str:
        return f"{self.x},{self.y},{self.stone_type}"


class BoardCommand(Command):
    def __init__(self, moves: list[BoardMove] | None = None):
        super().__init__(
            CommandType.BOARD, {"moves": moves if moves is not None else []}
        )

    def moves(self) -> list[BoardMove]:
        return self.params["moves"]

    def add_move(self, x: int, y: int, stone_type: int) -> None:
        self.params["moves"].append(BoardMove(x, y, stone_type))

    def num_stones(self) -> int:
        return len(self.params["moves"])
