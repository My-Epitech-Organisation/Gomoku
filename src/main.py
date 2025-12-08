#!/usr/bin/env python3

import constants
from communication import CommunicationManager


class GameContext:
    def __init__(self):
        self.board = None
        self.board_width = 0
        self.board_height = 0

    def initialize_board(self, width: int, height: int) -> None:
        self.board_width = width
        self.board_height = height
        self.board = [[0] * width for _ in range(height)]

    def get_opening_move(self) -> tuple[int, int]:
        x = self.board_width // 2
        y = self.board_height // 2
        self.board[y][x] = 1
        return (x, y)

    def process_opponent_move(self, x: int, y: int) -> None:
        if 0 <= x < self.board_width and 0 <= y < self.board_height:
            self.board[y][x] = 2

    def get_best_move(self) -> tuple[int, int]:
        for y in range(self.board_height):
            for x in range(self.board_width):
                if self.board[y][x] == 0:
                    self.board[y][x] = 1
                    return (x, y)
        return (0, 0)

    def process_board(self, moves: list) -> None:
        self.board = [[0] * self.board_width for _ in range(self.board_height)]
        for move in moves:
            x, y = move.x, move.y
            if 0 <= x < self.board_width and 0 <= y < self.board_height:
                self.board[y][x] = move.stone_type

    def get_about_info(self) -> dict:
        return {
            "name": constants.BRAIN_NAME,
            "version": constants.BRAIN_VERSION,
            "author": constants.BRAIN_AUTHOR,
            "country": constants.BRAIN_COUNTRY,
        }


if __name__ == "__main__":
    context = GameContext()
    manager = CommunicationManager(context)
    manager.run()
