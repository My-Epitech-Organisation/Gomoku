
from typing import List


class Board:
    def __init__(self, size: int = 20):
        self.size = size
        self.grid = [[0 for _ in range(size)] for _ in range(size)]
        self.moves = []

    def set_stone(self, x: int, y: int, player: int) -> None:
        if 0 <= x < self.size and 0 <= y < self.size:
            self.grid[y][x] = player
            self.moves.append((x, y, player))

    def get_stone(self, x: int, y: int) -> int:
        if 0 <= x < self.size and 0 <= y < self.size:
            return self.grid[y][x]
        return 0

    def clear(self) -> None:
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.moves = []

    def copy(self) -> 'Board':
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        new_board.moves = self.moves[:]
        return new_board
