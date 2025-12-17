##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Board representation and pattern detection
##

from typing import Optional
from .constants import (
    THREAT_LEVEL_WIN, THREAT_LEVEL_OPEN_FOUR,
    THREAT_LEVEL_CLOSED_FOUR, THREAT_LEVEL_OPEN_THREE,
    THREAT_LEVEL_OPEN_TWO, THREAT_LEVEL_NORMAL,
    NEIGHBOR_SEARCH_DISTANCE, CENTER_SEARCH_RADIUS
)


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
        if self.is_valid_position(x, y) and self.grid[y][x] != self.EMPTY:
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
            both_open = open_start and open_end

            if count >= 5:
                threat = THREAT_LEVEL_WIN
            elif count == 4:
                threat = THREAT_LEVEL_OPEN_FOUR if both_open else THREAT_LEVEL_CLOSED_FOUR
            elif count == 3:
                threat = THREAT_LEVEL_OPEN_THREE if both_open else THREAT_LEVEL_NORMAL
            elif count == 2:
                threat = THREAT_LEVEL_OPEN_TWO if both_open else 0
            else:
                threat = 0

            max_threat = max(max_threat, threat)

        self.remove_stone(x, y)
        return max_threat

    def get_occupied_region(self, margin: int = NEIGHBOR_SEARCH_DISTANCE) -> tuple[int, int, int, int]:
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

    def has_neighbor(self, x: int, y: int, distance: int = NEIGHBOR_SEARCH_DISTANCE) -> bool:
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

    def detect_cross_pattern(self, x: int, y: int, player: int) -> int:
        if not self.is_empty(x, y):
            return 0

        self.place_stone(x, y, player)

        threats_count = 0
        has_open_line = False

        for dx, dy in self.DIRECTIONS:
            count, open_start, open_end = self.count_consecutive(x, y, dx, dy, player)
            both_open = open_start and open_end

            if count >= 2:
                if both_open:
                    threats_count += 2
                    has_open_line = True
                elif open_start or open_end:
                    threats_count += 1

        self.remove_stone(x, y)

        if threats_count >= 4 and has_open_line:
            return 3
        elif threats_count >= 3:
            return 2
        elif threats_count >= 2:
            return 1

        return 0

    def find_cross_patterns(self, player: int) -> list[tuple[int, int, int]]:
        cross_positions = []

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == player:
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            nx, ny = x + dx, y + dy
                            if self.is_empty(nx, ny):
                                strength = self.detect_cross_pattern(nx, ny, player)
                                if strength > 0:
                                    cross_positions.append((nx, ny, strength))

        unique_crosses = {}
        for x, y, strength in cross_positions:
            if (x, y) not in unique_crosses or unique_crosses[(x, y)] < strength:
                unique_crosses[(x, y)] = strength

        result = [(x, y, s) for (x, y), s in unique_crosses.items()]
        result.sort(key=lambda t: t[2], reverse=True)

        return result

    def detect_t_pattern(self, x: int, y: int, player: int) -> bool:
        if not self.is_empty(x, y):
            return False

        self.place_stone(x, y, player)

        has_horizontal = False
        has_vertical = False

        h_count, h_open_start, h_open_end = self.count_consecutive(x, y, 1, 0, player)
        if h_count >= 2 and (h_open_start or h_open_end):
            has_horizontal = True

        v_count, v_open_start, v_open_end = self.count_consecutive(x, y, 0, 1, player)
        if v_count >= 2 and (v_open_start or v_open_end):
            has_vertical = True

        self.remove_stone(x, y)

        return has_horizontal and has_vertical

    def find_t_patterns(self, player: int) -> list[tuple[int, int]]:
        t_positions = []

        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == player:
                    for dy in range(-2, 3):
                        for dx in range(-2, 3):
                            nx, ny = x + dx, y + dy
                            if self.is_empty(nx, ny) and self.detect_t_pattern(nx, ny, player):
                                if (nx, ny) not in t_positions:
                                    t_positions.append((nx, ny))

        return t_positions

    def find_open_two_threats(self, player: int) -> list[tuple[int, int]]:
        threats = []

        for y in range(self.height):
            for x in range(self.width):
                if not self.is_empty(x, y):
                    continue

                self.place_stone(x, y, player)

                for dx, dy in self.DIRECTIONS:
                    count, open_start, open_end = self.count_consecutive(x, y, dx, dy, player)

                    if count == 2 and open_start and open_end:
                        if (x, y) not in threats:
                            threats.append((x, y))
                        break

                self.remove_stone(x, y)

        return threats

    def is_defensive_mode(self) -> bool:
        from .constants import DEFENSIVE_MODE_MOVE_THRESHOLD
        return self.move_count % 2 == 1 and self.move_count <= DEFENSIVE_MODE_MOVE_THRESHOLD * 2 + 1

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
