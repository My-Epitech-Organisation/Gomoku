##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## board
##

import random
from typing import List, Tuple

from . import constants


class Board:
    zobrist_table = None

    def __init__(self, width: int, height: int):
        if Board.zobrist_table is None:
            Board._init_zobrist(width, height)
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.move_count = 0
        self.current_hash = 0

    def _init_zobrist(cls, width: int, height: int):
        random.seed(42)
        cls.zobrist_table = [[[random.getrandbits(64) for _ in range(2)] for _ in range(width)] for _ in range(height)]

    def place_stone(self, x: int, y: int, player: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == 0:
            self.grid[y][x] = player
            self.move_count += 1
            self.current_hash ^= self.zobrist_table[y][x][player - 1]
            return True
        return False

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        if self.move_count == 0:
            center_x, center_y = self.width // 2, self.height // 2
            return [(center_x, center_y)]

        occupied = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != 0:
                    occupied.add((x, y))

        candidates = set()
        for x, y in occupied:
            for dy in range(-constants.MOVE_RADIUS, constants.MOVE_RADIUS + 1):
                for dx in range(-constants.MOVE_RADIUS, constants.MOVE_RADIUS + 1):
                    nx, ny = x + dx, y + dy
                    if (
                        0 <= nx < self.width
                        and 0 <= ny < self.height
                        and self.grid[ny][nx] == 0
                    ):
                        candidates.add((nx, ny))

        return list(candidates)

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == 0

    def is_full(self) -> bool:
        return self.move_count == self.width * self.height

    def check_win(self, x: int, y: int, player: int) -> bool:
        for dx, dy in constants.DIRECTIONS:
            count = 1

            nx, ny = x + dx, y + dy
            while (
                0 <= nx < self.width
                and 0 <= ny < self.height
                and self.grid[ny][nx] == player
            ):
                count += 1
                nx += dx
                ny += dy

            nx, ny = x - dx, y - dy
            while (
                0 <= nx < self.width
                and 0 <= ny < self.height
                and self.grid[ny][nx] == player
            ):
                count += 1
                nx -= dx
                ny -= dy
            if count >= constants.WIN_LENGTH:
                return True
        return False

    def copy(self) -> "Board":
        new_board = Board(self.width, self.height)
        new_board.grid = [row[:] for row in self.grid]
        new_board.move_count = self.move_count
        new_board.current_hash = self.current_hash
        return new_board
