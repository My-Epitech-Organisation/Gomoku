##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for diagonal threat detection - fixes for Game 2 loss
##

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI


class TestDiagonalFourDetection:
    """Test diagonal four detection - the Game 2 losing scenario."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_diagonal_four_backslash(self):
        """AI must block diagonal \\ four."""
        # Opponent builds diagonal: (10,10), (11,11), (12,12), (13,13)
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        self.board.place_stone(12, 12, 2)
        self.board.place_stone(13, 13, 2)
        # Player stone
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Must block at (9,9) or (14,14)
        assert move in [(9, 9), (14, 14)], \
            f"Must block diagonal \\ four, got {move}"

    def test_diagonal_four_slash(self):
        """AI must block diagonal / four."""
        # Opponent builds diagonal: (13,10), (12,11), (11,12), (10,13)
        self.board.place_stone(13, 10, 2)
        self.board.place_stone(12, 11, 2)
        self.board.place_stone(11, 12, 2)
        self.board.place_stone(10, 13, 2)
        # Player stone
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Must block at (14,9) or (9,14)
        assert move in [(14, 9), (9, 14)], \
            f"Must block diagonal / four, got {move}"

    def test_game2_critical_position(self):
        """Reproduce Game 2 Move 43 - diagonal XXXX not blocked."""
        # Marin's diagonal from replay: (13,13), (14,12), (15,11), (16,10)
        # Note: This is diagonal / direction
        self.board.place_stone(13, 13, 2)
        self.board.place_stone(14, 12, 2)
        self.board.place_stone(15, 11, 2)
        self.board.place_stone(16, 10, 2)
        # Add some player stones
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Must block at (12,14) or (17,9)
        assert move in [(12, 14), (17, 9)], \
            f"CRITICAL: Must block Game 2 diagonal at (12,14) or (17,9), got {move}"


class TestDiagonalSplitThreeDetection:
    """Test split three detection on diagonals."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_diagonal_split_three_backslash(self):
        """AI must detect XX.X on diagonal \\."""
        # XX.X diagonal: (10,10), (11,11), gap, (13,13)
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        # gap at (12,12)
        self.board.place_stone(13, 13, 2)
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        assert move == (12, 12), \
            f"Must block diagonal split three at (12,12), got {move}"

    def test_diagonal_split_three_slash(self):
        """AI must detect XX.X on diagonal /."""
        # XX.X diagonal: (13,10), (12,11), gap, (10,13)
        self.board.place_stone(13, 10, 2)
        self.board.place_stone(12, 11, 2)
        # gap at (11,12)
        self.board.place_stone(10, 13, 2)
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        assert move == (11, 12), \
            f"Must block diagonal split three at (11,12), got {move}"


class TestDiagonalThreatBuilding:
    """Test early detection of diagonal threats being built."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_blocks_diagonal_three_early(self):
        """AI should block diagonal three before it becomes four."""
        # Opponent has diagonal three: (10,10), (11,11), (12,12)
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        self.board.place_stone(12, 12, 2)
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Should block at (9,9) or (13,13) to prevent XXXX
        assert move in [(9, 9), (13, 13)], \
            f"Should block diagonal three extension, got {move}"


class TestGlobalThreatScan:
    """Test global threat scanning functionality."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_scan_detects_diagonal_four(self):
        """Global scan must detect diagonal four."""
        # Create diagonal four
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        self.board.place_stone(12, 12, 2)
        self.board.place_stone(13, 13, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        # Should detect four on diagonal
        assert len(threats["fours"]) >= 1, \
            "Global scan must detect diagonal four"

    def test_scan_detects_diagonal_open_three(self):
        """Global scan must detect diagonal open three."""
        # Create diagonal three with spaces on both sides
        # .XXX. pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        self.board.place_stone(12, 12, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        # Should detect open three on diagonal
        assert len(threats["open_threes"]) >= 1, \
            "Global scan must detect diagonal open three"

    def test_scan_detects_diagonal_split_three(self):
        """Global scan must detect diagonal split three."""
        # Create XX.X pattern on diagonal
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        # gap at (12,12)
        self.board.place_stone(13, 13, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        # Should detect split three on diagonal
        assert len(threats["split_threes"]) >= 1, \
            "Global scan must detect diagonal split three"

    def test_scan_returns_gap_position(self):
        """Global scan should return the gap position for split patterns."""
        # Create XX.X pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        # gap at (12,12)
        self.board.place_stone(13, 13, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        # Find the split three and check gap position
        found_gap = False
        for threat in threats["split_threes"]:
            if threat["gap"] == (12, 12):
                found_gap = True
                break

        assert found_gap, \
            "Global scan should identify gap at (12,12)"


class TestGame5DiagonalThree:
    """Test Game 5 scenario - diagonal three not detected."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_game5_diagonal_three_detection(self):
        """
        Game 5 loss: diagonal (5,7)-(6,8)-(7,9)-(8,10)-(9,11) won.
        At move 17, opponent had 3 stones but we didn't block.
        """
        # Opponent has diagonal /: (7,9)-(8,10)-(9,11) - 3 consecutive
        self.board.place_stone(7, 9, 2)
        self.board.place_stone(8, 10, 2)
        self.board.place_stone(9, 11, 2)
        # Our stone somewhere
        self.board.place_stone(10, 10, 1)

        # Should detect open three and force block
        threats = self.ai._scan_board_threats(self.board, 2)

        # Must detect this as open_three since both ends are extensible
        assert len(threats["open_threes"]) >= 1, \
            f"Must detect diagonal open three, got {threats}"

    def test_game5_blocks_diagonal_three(self):
        """AI must block diagonal three before it becomes four."""
        # Opponent has diagonal /: (7,9)-(8,10)-(9,11)
        self.board.place_stone(7, 9, 2)
        self.board.place_stone(8, 10, 2)
        self.board.place_stone(9, 11, 2)
        # Our stone
        self.board.place_stone(10, 10, 1)

        move = self.ai.get_best_move(self.board, 1)

        # Must block at (6,8) or (10,12) to prevent extension
        assert move in [(6, 8), (10, 12)], \
            f"Must block diagonal three at (6,8) or (10,12), got {move}"

    def test_detects_extensible_diagonal_three(self):
        """Test that XXX with both ends open is detected as open_three."""
        # Diagonal \: (8,8)-(9,9)-(10,10) with both ends clear
        self.board.place_stone(8, 8, 2)
        self.board.place_stone(9, 9, 2)
        self.board.place_stone(10, 10, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        # Check for open_three detection
        found_open_three = False
        for t in threats["open_threes"]:
            if t["direction"] in ["diagonal_\\", "diagonal_/"]:
                found_open_three = True
                break

        assert found_open_three, \
            f"Must detect diagonal open three (.XXX.), got {threats}"


class TestScanAllDirections:
    """Test that scan covers all 4 directions."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_horizontal_detection(self):
        """Scan detects horizontal threats."""
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(13, 10, 2)

        threats = self.ai._scan_board_threats(self.board, 2)
        assert len(threats["fours"]) >= 1
        assert any(t["direction"] == "horizontal" for t in threats["fours"])

    def test_vertical_detection(self):
        """Scan detects vertical threats."""
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(10, 11, 2)
        self.board.place_stone(10, 12, 2)
        self.board.place_stone(10, 13, 2)

        threats = self.ai._scan_board_threats(self.board, 2)
        assert len(threats["fours"]) >= 1
        assert any(t["direction"] == "vertical" for t in threats["fours"])

    def test_diagonal_backslash_detection(self):
        """Scan detects diagonal \\ threats."""
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 11, 2)
        self.board.place_stone(12, 12, 2)
        self.board.place_stone(13, 13, 2)

        threats = self.ai._scan_board_threats(self.board, 2)
        assert len(threats["fours"]) >= 1
        assert any(t["direction"] == "diagonal_\\" for t in threats["fours"])

    def test_diagonal_slash_detection(self):
        """Scan detects diagonal / threats."""
        self.board.place_stone(13, 10, 2)
        self.board.place_stone(12, 11, 2)
        self.board.place_stone(11, 12, 2)
        self.board.place_stone(10, 13, 2)

        threats = self.ai._scan_board_threats(self.board, 2)
        assert len(threats["fours"]) >= 1
        assert any(t["direction"] == "diagonal_/" for t in threats["fours"])
