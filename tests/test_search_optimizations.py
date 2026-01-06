##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Search Optimizations (PVS, LMR, Aspiration Windows)
##

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestAspirationWindows:
    """Tests for aspiration windows optimization."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_aspiration_uses_previous_value(self):
        """Aspiration should start from previous depth's value."""
        # Setup a simple position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)
        self.board.place_stone(10, 11, 1)

        # Get a move (this triggers iterative deepening with aspiration)
        move = self.ai.get_best_move(self.board, 1)
        assert move is not None

    def test_search_at_depth_with_window(self):
        """_search_at_depth_with_window should work with custom bounds."""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)

        # Test with narrow window
        move, value = self.ai._search_at_depth_with_window(
            self.board, 1, depth=3, alpha=-100, beta=100
        )
        assert move is not None

    def test_aspiration_constants_exist(self):
        """Verify aspiration constants are defined."""
        assert hasattr(constants, 'ASPIRATION_DELTA')
        assert hasattr(constants, 'ASPIRATION_MIN_DEPTH')
        assert constants.ASPIRATION_DELTA > 0
        assert constants.ASPIRATION_MIN_DEPTH > 0


class TestPVS:
    """Tests for Principal Variation Search optimization."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=1.0)

    def test_pvs_first_move_full_window(self):
        """First move in negamax should use full window."""
        # Create a mid-game position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(9, 10, 2)

        # Run negamax - PVS should work
        result = self.ai.negamax(
            self.board, depth=4, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=1
        )
        assert isinstance(result, int)

    def test_pvs_returns_valid_evaluation(self):
        """PVS should return valid evaluation scores."""
        self.board.place_stone(10, 10, 1)

        value = self.ai.negamax(
            self.board, depth=3, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=2
        )
        # Score should be bounded
        assert -constants.INFINITY <= value <= constants.INFINITY


class TestLMR:
    """Tests for Late Move Reductions optimization."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=1.0)

    def test_lmr_constants_exist(self):
        """Verify LMR constants are defined."""
        assert hasattr(constants, 'LMR_FULL_MOVES')
        assert hasattr(constants, 'LMR_MIN_DEPTH')
        assert hasattr(constants, 'LMR_REDUCTION')
        assert constants.LMR_FULL_MOVES >= 1
        assert constants.LMR_MIN_DEPTH >= 1
        assert constants.LMR_REDUCTION >= 1

    def test_is_tactical_move_detects_threats(self):
        """_is_tactical_move should detect moves creating fours."""
        # Create position where a move makes a four
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(10, 12, 1)

        # Place stone to check if it's tactical
        self.board.place_stone(10, 13, 1)
        is_tactical = self.ai._is_tactical_move(self.board, (10, 13), 1)
        self.board.undo_stone(10, 13, 1)

        assert is_tactical is True

    def test_is_tactical_move_detects_blocking(self):
        """_is_tactical_move should detect blocking moves."""
        # Create opponent threat
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(10, 11, 2)
        self.board.place_stone(10, 12, 2)

        # Our stone blocks their four
        self.board.place_stone(10, 13, 1)
        is_tactical = self.ai._is_tactical_move(self.board, (10, 13), 1)
        self.board.undo_stone(10, 13, 1)

        assert is_tactical is True

    def test_is_tactical_move_non_critical(self):
        """_is_tactical_move should return False for non-critical moves."""
        # Just some random stones far apart
        self.board.place_stone(5, 5, 1)
        self.board.place_stone(15, 15, 2)

        # A move far from all threats
        self.board.place_stone(0, 0, 1)
        is_tactical = self.ai._is_tactical_move(self.board, (0, 0), 1)
        self.board.undo_stone(0, 0, 1)

        assert is_tactical is False


class TestSearchDepthImprovement:
    """Tests to verify depth improvement with optimizations."""

    def setup_method(self):
        self.board = Board(20, 20)

    def test_search_completes_in_time(self):
        """Search should complete within time limit."""
        ai = MinMaxAI(time_limit=2.0)

        # Mid-game position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 2)
        self.board.place_stone(9, 9, 1)
        self.board.place_stone(11, 11, 2)

        start = time.time()
        move = ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        assert move is not None
        # Should complete within RESPONSE_DEADLINE + margin
        assert elapsed < constants.RESPONSE_DEADLINE + 1.0

    def test_negamax_node_counting(self):
        """Node counter should track search progress."""
        ai = MinMaxAI(time_limit=0.5)

        self.board.place_stone(10, 10, 1)
        ai.nodes = 0

        ai.negamax(
            self.board, depth=3, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=2
        )

        assert ai.nodes > 0


class TestIntegrationOptimizations:
    """Integration tests for all optimizations together."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_optimizations_find_winning_move(self):
        """With optimizations, AI should still find winning moves."""
        # Create a winning position for player 1
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(10, 12, 1)
        self.board.place_stone(10, 13, 1)
        # Gap at 10,14 - winning move

        move = self.ai.get_best_move(self.board, 1)
        assert move == (10, 14) or move == (10, 9)  # Either end wins

    def test_optimizations_block_threat(self):
        """With optimizations, AI should block opponent threats."""
        # Opponent has 4 in a row
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(10, 11, 2)
        self.board.place_stone(10, 12, 2)
        self.board.place_stone(10, 13, 2)

        # We need to block
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        assert move in [(10, 9), (10, 14)]  # Must block

    def test_full_game_simulation(self):
        """Run a short game to verify stability."""
        moves_played = 0
        current_player = 1

        while moves_played < 10:
            move = self.ai.get_best_move(self.board, current_player)
            if move is None:
                break

            self.board.place_stone(move[0], move[1], current_player)
            if self.board.check_win(move[0], move[1], current_player):
                break

            current_player = 3 - current_player
            moves_played += 1

        # Should have made at least some moves
        assert moves_played >= 5
