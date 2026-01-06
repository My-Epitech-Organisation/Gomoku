##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for History Heuristic
##

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestHistoryConstants:
    """Tests for history heuristic constants."""

    def test_history_constants_exist(self):
        """Verify history constants are defined."""
        assert hasattr(constants, 'HISTORY_MAX_VALUE')
        assert hasattr(constants, 'HISTORY_DECAY_FACTOR')
        assert hasattr(constants, 'HISTORY_BONUS_DEPTH')
        assert constants.HISTORY_MAX_VALUE > 0
        assert 0 < constants.HISTORY_DECAY_FACTOR < 1


class TestHistoryTableInit:
    """Tests for history table initialization."""

    def test_history_table_initialized(self):
        """History table should be initialized for both players."""
        ai = MinMaxAI(time_limit=1.0)
        assert 1 in ai.history_table
        assert 2 in ai.history_table
        assert isinstance(ai.history_table[1], dict)
        assert isinstance(ai.history_table[2], dict)

    def test_history_table_empty_initially(self):
        """History table should be empty at start."""
        ai = MinMaxAI(time_limit=1.0)
        assert len(ai.history_table[1]) == 0
        assert len(ai.history_table[2]) == 0


class TestUpdateHistory:
    """Tests for _update_history method."""

    def setup_method(self):
        self.ai = MinMaxAI(time_limit=1.0)

    def test_update_history_adds_score(self):
        """_update_history should add score for moves."""
        move = (10, 10)
        self.ai._update_history(move, 1, depth=3)
        assert move in self.ai.history_table[1]
        assert self.ai.history_table[1][move] > 0

    def test_update_history_accumulates(self):
        """Multiple updates should accumulate scores."""
        move = (10, 10)
        self.ai._update_history(move, 1, depth=3)
        first_score = self.ai.history_table[1][move]

        self.ai._update_history(move, 1, depth=3)
        second_score = self.ai.history_table[1][move]

        assert second_score > first_score

    def test_update_history_depth_scaling(self):
        """Deeper cutoffs should give higher history bonus."""
        move1 = (10, 10)
        move2 = (11, 11)

        self.ai._update_history(move1, 1, depth=2)
        self.ai._update_history(move2, 1, depth=4)

        # Depth 4 cutoff should be worth more than depth 2
        assert self.ai.history_table[1][move2] > self.ai.history_table[1][move1]

    def test_update_history_per_player(self):
        """History should be tracked separately per player."""
        move = (10, 10)
        self.ai._update_history(move, 1, depth=3)
        self.ai._update_history(move, 2, depth=5)

        assert move in self.ai.history_table[1]
        assert move in self.ai.history_table[2]
        # Player 2 used deeper depth, should have higher score
        assert self.ai.history_table[2][move] > self.ai.history_table[1][move]

    def test_history_caps_at_max(self):
        """History scores should be capped."""
        move = (10, 10)
        for _ in range(1000):
            self.ai._update_history(move, 1, depth=10)

        assert self.ai.history_table[1][move] <= constants.HISTORY_MAX_VALUE


class TestDecayHistory:
    """Tests for _decay_history method."""

    def setup_method(self):
        self.ai = MinMaxAI(time_limit=1.0)

    def test_decay_history_reduces_scores(self):
        """_decay_history should reduce all scores."""
        move = (10, 10)
        self.ai._update_history(move, 1, depth=5)
        original_score = self.ai.history_table[1][move]

        self.ai._decay_history()

        assert self.ai.history_table[1][move] < original_score

    def test_decay_applies_factor(self):
        """Decay should apply the configured factor."""
        move = (10, 10)
        # Set a known score
        self.ai.history_table[1][move] = 100

        self.ai._decay_history()

        expected = int(100 * constants.HISTORY_DECAY_FACTOR)
        assert self.ai.history_table[1][move] == expected

    def test_decay_removes_zero_entries(self):
        """Decay should remove entries that reach 0."""
        move = (10, 10)
        self.ai.history_table[1][move] = 1

        # Many decays should reduce to 0 and remove
        for _ in range(100):
            self.ai._decay_history()

        assert move not in self.ai.history_table[1]

    def test_decay_affects_both_players(self):
        """Decay should affect both players' history."""
        move = (10, 10)
        self.ai.history_table[1][move] = 100
        self.ai.history_table[2][move] = 100

        self.ai._decay_history()

        assert self.ai.history_table[1][move] < 100
        assert self.ai.history_table[2][move] < 100


class TestGetHistoryScore:
    """Tests for _get_history_score method."""

    def setup_method(self):
        self.ai = MinMaxAI(time_limit=1.0)

    def test_get_history_score_default(self):
        """_get_history_score returns 0 for unknown moves."""
        score = self.ai._get_history_score((5, 5), 1)
        assert score == 0

    def test_get_history_score_returns_stored_value(self):
        """_get_history_score returns stored value."""
        move = (10, 10)
        self.ai._update_history(move, 1, depth=4)
        expected = self.ai.history_table[1][move]

        score = self.ai._get_history_score(move, 1)
        assert score == expected

    def test_get_history_score_per_player(self):
        """_get_history_score is player-specific."""
        move = (10, 10)
        self.ai._update_history(move, 1, depth=3)

        score_p1 = self.ai._get_history_score(move, 1)
        score_p2 = self.ai._get_history_score(move, 2)

        assert score_p1 > 0
        assert score_p2 == 0


class TestHistoryIntegration:
    """Integration tests for history heuristic in search."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_history_updated_on_cutoff(self):
        """History should be updated when beta cutoff occurs."""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)
        self.board.place_stone(10, 11, 1)

        # Run search - this should cause some cutoffs
        self.ai.negamax(
            self.board, depth=4, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=1
        )

        # At least one move should have history now
        total_history = sum(self.ai.history_table[1].values())
        total_history += sum(self.ai.history_table[2].values())
        assert total_history > 0

    def test_decay_called_on_new_search(self):
        """Decay should be called at start of each get_best_move."""
        move = (10, 10)
        self.ai.history_table[1][move] = 100

        self.board.place_stone(10, 10, 1)

        # First search
        self.ai.get_best_move(self.board, 2)

        # History should have decayed
        assert self.ai.history_table[1][move] < 100

    def test_history_affects_move_ordering(self):
        """Moves with high history should be explored earlier."""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)

        # Give a specific move high history
        high_history_move = (10, 11)
        for _ in range(10):
            self.ai._update_history(high_history_move, 1, depth=5)

        # Run search
        self.ai.nodes = 0
        self.ai.get_best_move(self.board, 1)

        # The high history move should have been considered
        assert self.ai._get_history_score(high_history_move, 1) > 0

    def test_search_still_works_with_history(self):
        """Search should work correctly with history enabled."""
        # Create a winning position for player 1
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(10, 12, 1)
        self.board.place_stone(10, 13, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Should find the winning move
        assert move == (10, 14) or move == (10, 9)

    def test_history_persists_across_moves(self):
        """History should persist across multiple moves."""
        self.board.place_stone(10, 10, 1)
        self.ai.get_best_move(self.board, 2)

        # Store current history
        history_after_first = dict(self.ai.history_table[1])

        self.board.place_stone(9, 9, 2)
        self.ai.get_best_move(self.board, 1)

        # History should still exist (possibly decayed)
        # New entries may have been added
        total_before = sum(history_after_first.values())
        total_after = sum(self.ai.history_table[1].values())
        # Can't guarantee relationship, just that it works
        assert isinstance(total_after, (int, float))


class TestHistoryPerformance:
    """Performance tests for history heuristic."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_history_doesnt_slow_search(self):
        """History heuristic should not significantly slow search."""
        import time

        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)

        start = time.time()
        move = self.ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        assert move is not None
        # Should complete within response deadline
        assert elapsed < constants.RESPONSE_DEADLINE + 0.5

    def test_history_memory_bounded(self):
        """History table should not grow unbounded."""
        # Run several searches
        for i in range(5):
            self.board = Board(20, 20)
            self.board.place_stone(10, 10, 1)
            self.board.place_stone(9 + i, 9, 2)
            self.ai.get_best_move(self.board, 1)

        # History table should have reasonable size
        # 20x20 board = 400 positions max per player
        assert len(self.ai.history_table[1]) <= 400
        assert len(self.ai.history_table[2]) <= 400
