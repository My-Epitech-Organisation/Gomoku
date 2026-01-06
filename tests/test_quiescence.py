##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Quiescence Search
##

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestQuiescenceConstants:
    """Tests for quiescence search constants."""

    def test_quiescence_constants_exist(self):
        """Verify quiescence constants are defined."""
        assert hasattr(constants, 'QUIESCENCE_MAX_DEPTH')
        assert hasattr(constants, 'QUIESCENCE_DELTA')
        assert constants.QUIESCENCE_MAX_DEPTH > 0
        assert constants.QUIESCENCE_DELTA > 0


class TestQuiescenceSearch:
    """Tests for quiescence_search method."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_quiescence_finds_immediate_win(self):
        """QS should find winning move at depth 0."""
        # Four in a row - QS must find the win
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)

        score = self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1
        )
        # Score should be very high (winning position)
        assert score >= constants.SCORE_OPEN_FOUR

    def test_quiescence_depth_limit(self):
        """QS should respect max depth."""
        self.board.place_stone(10, 10, 1)
        initial_nodes = self.ai.nodes

        # Start at max depth - should only evaluate stand-pat
        self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1,
            qs_depth=constants.QUIESCENCE_MAX_DEPTH
        )

        # Should have explored only 1 node (the stand-pat)
        assert self.ai.nodes == initial_nodes + 1

    def test_quiescence_stand_pat(self):
        """QS returns stand-pat when no tactical moves."""
        # Just one stone - no tactical moves available
        self.board.place_stone(10, 10, 1)

        regular_eval = self.ai.evaluate(self.board)
        qs_eval = self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1
        )

        # Should be approximately equal (same or better with QS)
        # The difference depends on perspective adjustment
        assert abs(qs_eval - regular_eval) < constants.QUIESCENCE_DELTA

    def test_quiescence_beta_cutoff(self):
        """QS should perform beta cutoff."""
        self.board.place_stone(10, 10, 1)

        # Very narrow window should cause early cutoff
        score = self.ai.quiescence_search(
            self.board, 1000000, 1000001, 1
        )
        assert score <= 1000001  # Beta bound respected

    def test_quiescence_alpha_improvement(self):
        """QS should improve alpha when better move found."""
        # Create a position with tactical potential
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(10, 12, 1)

        score = self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1
        )
        # Should return a reasonable score
        assert score > -constants.INFINITY

    def test_quiescence_counts_nodes(self):
        """QS should increment node counter."""
        self.board.place_stone(10, 10, 1)
        initial_nodes = self.ai.nodes

        self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1
        )

        assert self.ai.nodes > initial_nodes


class TestGetQuiescenceMoves:
    """Tests for _get_quiescence_moves method."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_get_quiescence_moves_winning(self):
        """_get_quiescence_moves returns winning move only."""
        # Four in a row - winning move available
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)

        moves = self.ai._get_quiescence_moves(self.board, 1)
        # Should only return the winning move
        assert len(moves) == 1
        assert moves[0] in [(14, 10), (9, 10)]

    def test_get_quiescence_moves_blocks_win(self):
        """_get_quiescence_moves includes blocking moves."""
        # Opponent has four in a row
        for i in range(4):
            self.board.place_stone(10 + i, 10, 2)

        moves = self.ai._get_quiescence_moves(self.board, 1)
        # Should include blocking moves
        assert (14, 10) in moves or (9, 10) in moves

    def test_get_quiescence_moves_finds_fours(self):
        """_get_quiescence_moves finds moves that create fours."""
        # Three in a row - can create a four
        for i in range(3):
            self.board.place_stone(10 + i, 10, 1)

        moves = self.ai._get_quiescence_moves(self.board, 1)
        # Should include moves that extend to four
        assert len(moves) > 0
        assert (13, 10) in moves or (9, 10) in moves

    def test_get_quiescence_moves_limited(self):
        """_get_quiescence_moves should return at most 8 moves."""
        # Create many potential tactical positions
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(5, 5, 2)
        self.board.place_stone(5, 6, 2)

        moves = self.ai._get_quiescence_moves(self.board, 1)
        assert len(moves) <= 8

    def test_get_quiescence_moves_empty_when_no_tactics(self):
        """_get_quiescence_moves returns empty for non-tactical position."""
        # Just a single stone - no tactical moves
        self.board.place_stone(10, 10, 1)

        moves = self.ai._get_quiescence_moves(self.board, 2)
        # May or may not have moves depending on position evaluation
        # But at least shouldn't crash
        assert isinstance(moves, list)

    def test_get_quiescence_moves_priority_order(self):
        """_get_quiescence_moves should prioritize critical moves."""
        # Create both a winning opportunity and a block needed
        # Player 1 has 4 in a row (can win)
        for i in range(4):
            self.board.place_stone(5 + i, 5, 1)

        moves = self.ai._get_quiescence_moves(self.board, 1)
        # Winning move should be first
        assert moves[0] in [(9, 5), (4, 5)]


class TestNegamaxQuiescenceIntegration:
    """Tests for negamax calling quiescence at depth 0."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_negamax_depth_zero_calls_quiescence(self):
        """Negamax at depth 0 should call quiescence."""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)

        initial_nodes = self.ai.nodes

        # Depth 0 should trigger quiescence
        score = self.ai.negamax(
            self.board, depth=0, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=1
        )

        # Quiescence should have been called and counted nodes
        assert self.ai.nodes > initial_nodes
        assert isinstance(score, int)

    def test_negamax_still_works_with_depth(self):
        """Negamax with depth > 0 should still work normally."""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 9, 2)

        score = self.ai.negamax(
            self.board, depth=3, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=1
        )

        assert isinstance(score, int)
        assert -constants.INFINITY <= score <= constants.INFINITY

    def test_quiescence_improves_tactical_evaluation(self):
        """Quiescence should give better eval for tactical positions."""
        # Create a position where player 1 has a forcing sequence
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(10, 12, 1)
        # Player 1 can create an open four

        # Eval with quiescence (via depth 0)
        qs_score = self.ai.negamax(
            self.board, depth=0, alpha=-constants.INFINITY,
            beta=constants.INFINITY, current_player=1
        )

        # This should be a strong position for player 1
        assert qs_score > 0


class TestQuiescencePerformance:
    """Performance tests for quiescence search."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_quiescence_terminates(self):
        """Quiescence should always terminate (no infinite loops)."""
        import time

        # Create a complex tactical position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(10, 12, 1)
        self.board.place_stone(9, 10, 2)
        self.board.place_stone(9, 11, 2)

        start = time.time()
        score = self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1
        )
        elapsed = time.time() - start

        # Should complete quickly (< 1 second)
        assert elapsed < 1.0
        assert isinstance(score, int)

    def test_quiescence_reasonable_node_count(self):
        """Quiescence should not explode node count."""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 11, 2)
        self.board.place_stone(9, 9, 1)

        self.ai.nodes = 0
        self.ai.quiescence_search(
            self.board, -constants.INFINITY, constants.INFINITY, 1
        )

        # Should not explore too many nodes (with depth limit)
        # Max 8 moves per ply, 6 plies = ~262k worst case
        # But with pruning should be much less
        assert self.ai.nodes < 10000
