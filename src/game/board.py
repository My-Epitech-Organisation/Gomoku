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
        # Incremental evaluation cache
        self.eval_cache = {}  # (x, y, player) -> score
        self.eval_totals = {1: 0, 2: 0}
        self.eval_dirty = set()  # positions needing recalculation

    @classmethod
    def _init_zobrist(cls, width: int, height: int):
        random.seed(42)
        cls.zobrist_table = [
            [[random.getrandbits(64) for _ in range(2)] for _ in range(width)]
            for _ in range(height)
        ]

    def place_stone(self, x: int, y: int, player: int) -> bool:
        if 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == 0:
            self.grid[y][x] = player
            self.move_count += 1
            self.current_hash ^= self.zobrist_table[y][x][player - 1]
            self._invalidate_eval_region(x, y)
            return True
        return False

    def undo_stone(self, x: int, y: int, player: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == player:
            self.grid[y][x] = 0
            self.move_count -= 1
            self.current_hash ^= self.zobrist_table[y][x][player - 1]
            self._invalidate_eval_region(x, y)

    def _invalidate_eval_region(self, x: int, y: int) -> None:
        """Mark positions in a radius of 4 as dirty for re-evaluation."""
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.eval_dirty.add((nx, ny))

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
        new_board.eval_cache = self.eval_cache.copy()
        new_board.eval_totals = self.eval_totals.copy()
        new_board.eval_dirty = self.eval_dirty.copy()
        return new_board
