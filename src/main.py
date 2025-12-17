#!/usr/bin/env python3

##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## main
##

import sys
from typing import Optional

import constants
from communication import CommunicationManager
from game import Board, NegaMaxAI


class GameContext:
    def __init__(self):
        self.board: Optional[Board] = None
        self.ai: Optional[NegaMaxAI] = None
        self.player_stone = 1
        self.opponent_stone = 2

    def initialize_board(self, width: int, height: int) -> None:
        self.board = Board(width, height)
        self.ai = NegaMaxAI(
            max_depth=4,
            time_limit=4.75,
            use_iterative_deepening=True,
        )

    def get_opening_move(self) -> tuple[int, int]:
        if self.board is None:
            return (0, 0)

        if self.board.move_count > 0:
            moves = self.board.get_valid_moves()
            if moves:
                x, y = moves[0]
                self.board.place_stone(x, y, self.player_stone)
                return (x, y)
            return (0, 0)

        x = self.board.width // 2
        y = self.board.height // 2
        if self.board.place_stone(x, y, self.player_stone):
            return (x, y)

        moves = self.board.get_valid_moves()
        if moves:
            x, y = moves[0]
            self.board.place_stone(x, y, self.player_stone)
            return (x, y)
        return (0, 0)

    def process_opponent_move(self, x: int, y: int) -> None:
        if self.board is not None:
            if not self.board.place_stone(x, y, self.opponent_stone):
                print(
                    f"[WARNING] Invalid opponent move at ({x}, {y}): "
                    "position already occupied or out of bounds.",
                    file=sys.stderr,
                )

    def get_best_move(self) -> tuple[int, int]:
        if self.board is None or self.ai is None:
            return (0, 0)

        try:
            move = self.ai.get_best_move(self.board, self.player_stone)

            if move is None:
                moves = self.board.get_valid_moves()
                if moves:
                    move = moves[0]
                else:
                    return (0, 0)

            x, y = move
            self.board.place_stone(x, y, self.player_stone)

            # Log stats to stderr for debugging
            stats = self.ai.get_stats()
            print(
                f"[AI] Nodes: {stats['nodes_searched']}, "
                f"Time: {stats['time_elapsed']:.2f}s, "
                f"NPS: {stats['nodes_per_second']}",
                file=sys.stderr,
            )

            return (x, y)

        except Exception as e:
            print(f"[ERROR] AI failed: {e}", file=sys.stderr)
            moves = self.board.get_valid_moves()
            if moves:
                x, y = moves[0]
                self.board.place_stone(x, y, self.player_stone)
                return (x, y)
            return (0, 0)

    def process_board(self, moves: list) -> None:
        if self.board is None:
            return

        self.board = Board(self.board.width, self.board.height)

        for move in moves:
            x, y = move.x, move.y
            stone_type = move.stone_type
            if self.board.is_valid_position(x, y):
                self.board.place_stone(x, y, stone_type)

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
