##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Split Three Detection and Blocking
##

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestSplitThreeDetection:
    """Tests for detecting split three patterns (XX.X, X.XX, X.X.X)."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_count_split_three_horizontal_xx_x(self):
        """Detect XX.X pattern horizontally."""
        # XX.X at row 10: stones at (10,10), (11,10), gap at (12,10), stone at (13,10)
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        # gap at 12,10
        self.board.place_stone(13, 10, 2)

        # Count threats at the gap position (where blocking would occur)
        self.board.place_stone(12, 10, 2)
        threats = self.ai._count_threats(self.board, 12, 10, 2)
        self.board.undo_stone(12, 10, 2)

        # Should detect this creates a four (closed_fours > 0 when gap is filled)
        assert threats["closed_fours"] >= 1 or threats["open_fours"] >= 1

    def test_count_split_three_vertical(self):
        """Detect XX.X pattern vertically - reproducing the losing game scenario."""
        # XX.X on column 12 (like the losing game)
        # Stones at (12,10), (12,11), gap at (12,12), stone at (12,13)
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(12, 11, 2)
        # gap at 12,12
        self.board.place_stone(12, 13, 2)

        # Check that placing at (12,12) would create a threat for opponent
        self.board.place_stone(12, 12, 2)
        threats = self.ai._count_threats(self.board, 12, 12, 2)
        self.board.undo_stone(12, 12, 2)

        # Filling the gap creates a four (4 in a row)
        assert threats["closed_fours"] >= 1 or threats["open_fours"] >= 1

    def test_count_split_three_x_x_x(self):
        """Detect X.X.X pattern."""
        # X.X.X at row 10
        self.board.place_stone(10, 10, 2)
        # gap at 11,10
        self.board.place_stone(12, 10, 2)
        # gap at 13,10
        self.board.place_stone(14, 10, 2)

        # When we place at one of the gaps
        self.board.place_stone(11, 10, 2)
        threats = self.ai._count_threats(self.board, 11, 10, 2)
        self.board.undo_stone(11, 10, 2)

        # Should have a split_three pattern
        assert threats["split_threes"] >= 1 or threats["closed_fours"] >= 1

    def test_split_three_detection_at_gap_position(self):
        """Test that split_threes count works when checking the gap position."""
        # Create XX.X pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        # gap at 12,10
        self.board.place_stone(13, 10, 2)

        # Check what opponent would get by playing at (12,10) - the gap
        self.board.place_stone(12, 10, 2)
        threats = self.ai._count_threats(self.board, 12, 10, 2)
        self.board.undo_stone(12, 10, 2)

        # Should detect this as creating a four
        total_fours = threats["open_fours"] + threats["closed_fours"]
        assert total_fours >= 1, f"Expected four creation, got {threats}"


class TestBlockSplitThree:
    """Tests for blocking opponent's split three patterns."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_block_split_three_horizontal(self):
        """AI should prioritize blocking XX.X pattern."""
        # Opponent (player 2) has XX.X pattern horizontally
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        # gap at 12,10
        self.board.place_stone(13, 10, 2)

        # Add some of our stones (not critical)
        self.board.place_stone(5, 5, 1)

        # Score for blocking the gap
        block_score = self.ai._move_heuristic(self.board, (12, 10), 1)

        # Score for a random move
        random_score = self.ai._move_heuristic(self.board, (0, 0), 1)

        # Blocking should have higher score
        assert block_score > random_score

    def test_block_split_three_critical_vertical(self):
        """AI must block XX.X on column 12 to prevent open four - losing game scenario."""
        # Reproduce losing game position at move 24
        # Opponent (player 2) has XX.X on column 12
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(12, 11, 2)
        # Gap at 12,12
        self.board.place_stone(12, 13, 2)

        # Add some of our stones (from the actual game)
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 11, 1)

        # Get best move - should block at (12, 12)
        move = self.ai.get_best_move(self.board, 1)

        # Must block at (12, 12) to prevent XXXX
        assert move == (12, 12), f"Expected (12,12) to block split three, got {move}"

    def test_move_heuristic_block_split_three_value(self):
        """Block split three should return MOVE_BLOCK_SPLIT_THREE score."""
        # XX.X pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(13, 10, 2)

        # Score for blocking move at the gap
        block_score = self.ai._move_heuristic(self.board, (12, 10), 1)

        # Should be at least MOVE_BLOCK_SPLIT_THREE
        # Note: might be higher if it also creates our threats
        assert block_score >= constants.MOVE_BLOCK_SPLIT_THREE, \
            f"Expected >= {constants.MOVE_BLOCK_SPLIT_THREE}, got {block_score}"


class TestSplitThreeCreation:
    """Tests for creating our own split three patterns."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_create_split_three_bonus(self):
        """Creating our own split three should get bonus."""
        # We have XX at (10,10) and (11,10)
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)

        # Playing at (13,10) creates XX.X pattern
        score = self.ai._move_heuristic(self.board, (13, 10), 1)

        # Should have MOVE_SPLIT_THREE bonus
        assert score >= constants.MOVE_SPLIT_THREE, \
            f"Expected >= {constants.MOVE_SPLIT_THREE}, got {score}"

    def test_create_x_x_x_pattern(self):
        """Creating X.X.X pattern should be valued."""
        # We have X at (10,10)
        self.board.place_stone(10, 10, 1)
        # Another X at (12,10) with gap
        self.board.place_stone(12, 10, 1)

        # Playing at (14,10) creates X.X.X pattern
        score = self.ai._move_heuristic(self.board, (14, 10), 1)

        # Should have significant bonus
        assert score >= constants.SCORE_SPLIT_THREE


class TestCriticalLosingPosition:
    """Test the exact position from the losing game."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_losing_game_move_24_position(self):
        """
        Reproduce the exact position where we lost.
        After move 24, opponent has XX.X on column 12.
        We should block at (12,12) but played (13,14) instead.
        """
        # Opponent stones on column 12 (simplified position)
        self.board.place_stone(12, 10, 2)  # Move 14
        self.board.place_stone(12, 11, 2)  # Move 16
        self.board.place_stone(12, 13, 2)  # Move 24 - creates XX.X

        # Some of our stones in the area
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)

        # The critical move should be to block at (12, 12)
        move = self.ai.get_best_move(self.board, 1)

        assert move == (12, 12), \
            f"CRITICAL: Must block at (12,12) to prevent XXXX, got {move}"

    def test_split_three_heuristic_higher_than_random(self):
        """Blocking split three should always score higher than random moves."""
        # Opponent has XX.X
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(12, 11, 2)
        self.board.place_stone(12, 13, 2)

        block_score = self.ai._move_heuristic(self.board, (12, 12), 1)

        # Test against various random positions
        random_positions = [(5, 5), (15, 15), (3, 3), (17, 17)]
        for pos in random_positions:
            random_score = self.ai._move_heuristic(self.board, pos, 1)
            assert block_score > random_score, \
                f"Block ({12},{12}) score {block_score} should be > random {pos} score {random_score}"
