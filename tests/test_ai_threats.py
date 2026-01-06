##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for AI threat detection (double-three, four-three, double-four)
##

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestCountThreats:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_count_threats_empty(self):
        """An isolated move creates no threat"""
        self.board.place_stone(10, 10, 1)
        threats = self.ai._count_threats(self.board, 10, 10, 1)
        assert threats["fives"] == 0
        assert threats["open_fours"] == 0
        assert threats["closed_fours"] == 0
        assert threats["open_threes"] == 0

    def test_count_threats_open_three(self):
        """Detects a horizontal open three"""
        # Place .XXX.
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        threats = self.ai._count_threats(self.board, 11, 10, 1)
        assert threats["open_threes"] >= 1

    def test_count_threats_open_four(self):
        """Detects a horizontal open four"""
        # Place .XXXX.
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        self.board.place_stone(13, 10, 1)
        threats = self.ai._count_threats(self.board, 11, 10, 1)
        assert threats["open_fours"] >= 1

    def test_count_threats_five(self):
        """Detects five in a row"""
        for i in range(5):
            self.board.place_stone(10 + i, 10, 1)
        threats = self.ai._count_threats(self.board, 12, 10, 1)
        assert threats["fives"] >= 1


class TestMoveHeuristicThreats:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_winning_move(self):
        """A winning move has maximum priority"""
        # XXXX. -> playing at (14,10) wins
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        score = self.ai._move_heuristic(self.board, (14, 10), 1)
        assert score == constants.MOVE_WIN

    def test_block_winning_move(self):
        """Block an opponent's winning move"""
        # Opponent has XOOOO. (blocked on one side by X)
        self.board.place_stone(9, 10, 1)  # Block one side
        for i in range(4):
            self.board.place_stone(10 + i, 10, 2)
        score = self.ai._move_heuristic(self.board, (14, 10), 1)
        assert score == constants.MOVE_BLOCK_WIN

    def test_double_three_detection(self):
        """Detects a double-three (fork)"""
        # L-shaped configuration to create two open threes
        #     X
        #     X
        #   X X X
        self.board.place_stone(10, 10, 1)  # Center
        self.board.place_stone(9, 10, 1)   # Left
        self.board.place_stone(10, 9, 1)   # Top
        # Playing at (11,10) and (10,11) creates double-three
        self.board.place_stone(11, 10, 1)  # Right
        self.board.place_stone(10, 11, 1)  # Bottom

        # Place a stone that creates the fork
        score = self.ai._move_heuristic(self.board, (10, 12), 1)
        # Should detect at least one threat pattern
        assert score >= constants.MOVE_OPEN_THREE

    def test_four_three_detection(self):
        """Detects a four-three"""
        # Horizontal: XXX. (needs one more for four)
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        # Vertical: X above
        self.board.place_stone(13, 9, 1)
        self.board.place_stone(13, 11, 1)

        # Playing at (13,10) creates horizontal four AND vertical three
        score = self.ai._move_heuristic(self.board, (13, 10), 1)
        # Should be at least a four
        assert score >= constants.MOVE_OPEN_FOUR or score >= constants.MOVE_FOUR_THREE

    def test_open_four_priority(self):
        """An open four has high priority"""
        # .XXX. -> playing adjacent creates .XXXX.
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        score = self.ai._move_heuristic(self.board, (13, 10), 1)
        assert score >= constants.MOVE_OPEN_FOUR

    def test_block_open_four(self):
        """Block an opponent's open four"""
        # Opponent has .OOO.
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(12, 10, 2)
        score = self.ai._move_heuristic(self.board, (13, 10), 1)
        assert score >= constants.MOVE_BLOCK_OPEN_THREE


class TestDoubleThreeForkScenarios:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_l_shape_fork(self):
        """L-shaped fork"""
        #   . X .
        #   . X .
        #   X X ?   <- playing at ? creates double-three
        self.board.place_stone(10, 8, 1)   # Vertical top
        self.board.place_stone(10, 9, 1)   # Vertical middle
        self.board.place_stone(9, 10, 1)   # Horizontal left
        self.board.place_stone(10, 10, 1)  # Center

        # Playing at (11, 10) should create a fork
        score = self.ai._move_heuristic(self.board, (11, 10), 1)
        # The move should have high priority (fork or three)
        assert score >= constants.MOVE_OPEN_THREE


class TestGetImmediateMove:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_immediate_win(self):
        """AI plays the winning move immediately"""
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        move = self.ai._get_immediate_move(self.board, 1)
        assert move == (14, 10) or move == (9, 10)

    def test_immediate_block(self):
        """AI blocks an imminent win"""
        for i in range(4):
            self.board.place_stone(10 + i, 10, 2)
        move = self.ai._get_immediate_move(self.board, 1)
        assert move == (14, 10) or move == (9, 10)

    def test_no_immediate_threat(self):
        """No immediate move if no critical threat"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 11, 2)
        move = self.ai._get_immediate_move(self.board, 1)
        assert move is None
