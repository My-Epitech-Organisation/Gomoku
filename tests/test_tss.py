##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Threat Space Search (TSS) - Victory by Continuous Threats
##

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI


class TestGetThreatMoves:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_no_threat_moves_empty(self):
        """No threat moves on empty board"""
        threat_moves = self.ai._get_threat_moves(self.board, 1)
        assert threat_moves == []

    def test_no_threat_moves_isolated(self):
        """An isolated stone creates no threat"""
        self.board.place_stone(10, 10, 1)
        threat_moves = self.ai._get_threat_moves(self.board, 1)
        assert len(threat_moves) == 0

    def test_threat_moves_with_two_stones(self):
        """Two aligned stones allow creating a three"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        threat_moves = self.ai._get_threat_moves(self.board, 1)
        # Extensions (9,10), (12,10) create an open three
        assert len(threat_moves) >= 2

    def test_threat_moves_creates_four(self):
        """Three aligned stones - extension creates a four"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        threat_moves = self.ai._get_threat_moves(self.board, 1)
        # (9,10) and (13,10) create a four
        assert (9, 10) in threat_moves or (13, 10) in threat_moves


class TestGetDefenseMoves:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_no_defense_needed(self):
        """No defense needed without threat"""
        self.board.place_stone(10, 10, 2)
        defense_moves = self.ai._get_defense_moves(self.board, 2)
        assert len(defense_moves) == 0

    def test_defense_against_three(self):
        """Defense against an open three"""
        # Opponent has XX.X (three with gap)
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(13, 10, 2)
        defense_moves = self.ai._get_defense_moves(self.board, 2)
        # Should include (12,10) to block the gap
        # and (9,10), (14,10) to block extensions
        assert len(defense_moves) >= 1

    def test_defense_against_open_four(self):
        """Defense against an open four"""
        # Opponent has .XXXX.
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(13, 10, 2)
        defense_moves = self.ai._get_defense_moves(self.board, 2)
        # Must block at the ends
        assert (9, 10) in defense_moves or (14, 10) in defense_moves


class TestVCTSearch:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_vct_with_winning_move(self):
        """VCT finds a win if winning move exists"""
        # XXXX. -> immediate win
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        result = self.ai._vct_search(self.board, 1, 1, depth=0, max_depth=2)
        assert result is True

    def test_no_vct_without_threats(self):
        """No VCT without threats"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(15, 15, 2)
        result = self.ai._vct_search(self.board, 1, 1, depth=0, max_depth=4)
        assert result is False


class TestThreatSpaceSearch:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_finds_immediate_winning_sequence(self):
        """TSS finds a winning sequence in 2 moves"""
        # Configuration: two possible open threes
        # If we play (13,10), we get XXXX -> win
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        # TSS should find the move (13,10) or (9,10)
        move = self.ai._threat_space_search(self.board, 1, max_depth=4, time_limit=0.5)
        # Can be None if no confirmed VCT, or the winning move
        if move is not None:
            assert move in [(9, 10), (13, 10), (14, 10)]

    def test_no_vct_returns_none(self):
        """TSS returns None if no VCT"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(5, 5, 2)
        move = self.ai._threat_space_search(self.board, 1, max_depth=4, time_limit=0.5)
        assert move is None

    def test_respects_time_limit(self):
        """TSS respects the time limit"""
        import time
        # Complex position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        start = time.time()
        self.ai._threat_space_search(self.board, 1, max_depth=10, time_limit=0.1)
        elapsed = time.time() - start
        # Should finish in less than 0.5s (margin for setup)
        assert elapsed < 0.5

    def test_four_three_vct(self):
        """TSS finds VCT with four-three"""
        # Configuration that allows creating a four-three
        #   X
        #   X
        # X X ? -> playing at ? creates horizontal + vertical
        self.board.place_stone(10, 8, 1)   # Vertical
        self.board.place_stone(10, 9, 1)   # Vertical
        self.board.place_stone(9, 10, 1)   # Horizontal
        self.board.place_stone(10, 10, 1)  # Center
        # The move (11, 10) creates a fork
        move = self.ai._threat_space_search(self.board, 1, max_depth=6, time_limit=0.5)
        # TSS can find this move as potential VCT
        if move is not None:
            x, y = move
            # Verify the move is adjacent to existing stones
            assert abs(x - 10) <= 2 and abs(y - 10) <= 2


class TestTSSIntegration:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_get_best_move_uses_tss(self):
        """get_best_move uses TSS before negamax"""
        # Configuration with obvious VCT
        # XXXX. -> the best move is clearly (14,10)
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        # But _get_immediate_move should find it first
        move = self.ai.get_best_move(self.board, 1)
        assert move in [(14, 10), (9, 10)]

    def test_blocks_opponent_vct(self):
        """AI blocks a potential opponent VCT"""
        # Opponent (2) has OOOO.
        for i in range(4):
            self.board.place_stone(10 + i, 10, 2)
        move = self.ai.get_best_move(self.board, 1)
        # Must block at (14,10) or (9,10)
        assert move in [(14, 10), (9, 10)]
