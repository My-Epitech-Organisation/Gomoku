##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Board representation and pattern detection
##

from typing import Optional


class Board:
    EMPTY = 0
    PLAYER = 1
    OPPONENT = 2
    DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[self.EMPTY] * width for _ in range(height)]
        self.move_count = 0

    def copy(self) -> "Board":
        new_board = Board(self.width, self.height)
        new_board.grid = [row[:] for row in self.grid]
        new_board.move_count = self.move_count
        return new_board

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_empty(self, x: int, y: int) -> bool:
        return self.is_valid_position(x, y) and self.grid[y][x] == self.EMPTY

    def place_stone(self, x: int, y: int, player: int) -> bool:
        if not self.is_empty(x, y):
            return False
        self.grid[y][x] = player
        self.move_count += 1
        return True

    def remove_stone(self, x: int, y: int) -> None:
        if self.is_valid_position(x, y):
            self.grid[y][x] = self.EMPTY
            self.move_count -= 1

    def get_stone(self, x: int, y: int) -> int:
        if self.is_valid_position(x, y):
            return self.grid[y][x]
        return -1

    def count_consecutive(
        self, x: int, y: int, dx: int, dy: int, player: int
    ) -> tuple[int, bool, bool]:

        count = 1
        nx, ny = x + dx, y + dy

        while self.is_valid_position(nx, ny) and self.grid[ny][nx] == player:
            count += 1
            nx += dx
            ny += dy
        open_end = self.is_valid_position(nx, ny) and self.grid[ny][nx] == self.EMPTY

        nx, ny = x - dx, y - dy
        while self.is_valid_position(nx, ny) and self.grid[ny][nx] == player:
            count += 1
            nx -= dx
            ny -= dy
        open_start = self.is_valid_position(nx, ny) and self.grid[ny][nx] == self.EMPTY

        return count, open_start, open_end

    def check_line(self, x: int, y: int, player: int) -> tuple[int, bool]:
        max_length = 0
        is_open = False

        for dx, dy in self.DIRECTIONS:
            count, open_start, open_end = self.count_consecutive(x, y, dx, dy, player)
            if count > max_length:
                max_length = count
                is_open = open_start or open_end

        return max_length, is_open

    def is_winning_move(self, x: int, y: int, player: int) -> bool:
        if not self.is_empty(x, y):
            return False

        self.place_stone(x, y, player)
        length, _ = self.check_line(x, y, player)
        self.remove_stone(x, y)

        return length >= 5

    def find_winning_move(self, player: int) -> Optional[tuple[int, int]]:
        for y in range(self.height):
            for x in range(self.width):
                if self.is_winning_move(x, y, player):
                    return (x, y)
        return None

    def get_threat_level(self, x: int, y: int, player: int) -> int:
        if not self.is_empty(x, y):
            return 0

        self.place_stone(x, y, player)
        max_threat = 0

        for dx, dy in self.DIRECTIONS:
            count, open_start, open_end = self.count_consecutive(x, y, dx, dy, player)

            if count >= 5:
                threat = 5
            elif count == 4:
                threat = 4
            elif count == 3 and (open_start and open_end):
                threat = 3
            elif count == 3:
                threat = 2
            elif count == 2:
                threat = 1
            else:
                threat = 0

            max_threat = max(max_threat, threat)

        self.remove_stone(x, y)
        return max_threat

    def get_occupied_region(self, margin: int = 2) -> tuple[int, int, int, int]:
        min_x, min_y = self.width, self.height
        max_x, max_y = -1, -1

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] != self.EMPTY:
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if max_x == -1:
            center = self.width // 2
            return (center - 1, center - 1, center + 1, center + 1)

        min_x = max(0, min_x - margin)
        min_y = max(0, min_y - margin)
        max_x = min(self.width - 1, max_x + margin)
        max_y = min(self.height - 1, max_y + margin)

        return (min_x, min_y, max_x, max_y)

    def get_valid_moves(self, use_region: bool = True) -> list[tuple[int, int]]:
        moves = []

        if use_region and self.move_count > 0:
            min_x, min_y, max_x, max_y = self.get_occupied_region()
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    if self.is_empty(x, y):
                        moves.append((x, y))
        else:
            for y in range(self.height):
                for x in range(self.width):
                    if self.is_empty(x, y):
                        moves.append((x, y))

        return moves

    def has_neighbor(self, x: int, y: int, distance: int = 1) -> bool:
        for dy in range(-distance, distance + 1):
            for dx in range(-distance, distance + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if (
                    self.is_valid_position(nx, ny)
                    and self.grid[ny][nx] != self.EMPTY
                ):
                    return True
        return False

    def __str__(self) -> str:
        lines = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                stone = self.grid[y][x]
                if stone == self.EMPTY:
                    row.append(".")
                elif stone == self.PLAYER:
                    row.append("X")
                else:
                    row.append("O")
            lines.append(" ".join(row))
        return "\n".join(lines)
