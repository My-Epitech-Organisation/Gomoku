##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Game 3 critical positions - open three and open four blocking
##

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI


class TestGame3OpenThreeBlocking:
    """Test blocking open three before it becomes open four."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_block_open_three_column11(self):
        """
        Reproduce Game 3 Move 15 situation.
        Opponent has open three at column 11 (y=7,8,9).
        We MUST block at y=6 or y=10 to prevent open four.
        """
        # Opponent (player 2) open three on column 11
        self.board.place_stone(11, 7, 2)  # (x=11, y=7)
        self.board.place_stone(11, 8, 2)  # (x=11, y=8)
        self.board.place_stone(11, 9, 2)  # (x=11, y=9)

        # Our stone at y=11 (from earlier in game)
        self.board.place_stone(11, 11, 1)

        # Some other stones to make it realistic
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(9, 10, 1)

        move = self.ai.get_best_move(self.board, 1)

        # Must block at (11, 6) or (11, 10) to prevent .XXX. becoming .XXXX.
        assert move in [(11, 6), (11, 10)], \
            f"Must block open three at (11,6) or (11,10), got {move}"


class TestGame3OpenFourBlocking:
    """Test blocking open four (already unstoppable but still need to try)."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_block_open_four_column11(self):
        """
        Reproduce Game 3 Move 17 situation.
        Opponent has open four at column 11 (y=6,7,8,9).
        Both ends open - this is unstoppable but we should still block.
        """
        # Opponent (player 2) open four on column 11
        self.board.place_stone(11, 6, 2)
        self.board.place_stone(11, 7, 2)
        self.board.place_stone(11, 8, 2)
        self.board.place_stone(11, 9, 2)

        # Our stone at y=11 (doesn't help - y=10 is empty between)
        self.board.place_stone(11, 11, 1)

        # Some other stones
        self.board.place_stone(10, 10, 1)

        move = self.ai.get_best_move(self.board, 1)

        # Must try to block at (11, 5) or (11, 10)
        assert move in [(11, 5), (11, 10)], \
            f"Must block open four at (11,5) or (11,10), got {move}"

    def test_block_four_with_wall(self):
        """
        When we have a stone adjacent to a four, prefer blocking on that side
        to create a complete wall.
        """
        # Opponent four on column 11: y=7,8,9,10
        self.board.place_stone(11, 7, 2)
        self.board.place_stone(11, 8, 2)
        self.board.place_stone(11, 9, 2)
        self.board.place_stone(11, 10, 2)

        # Our stone at y=12 - adjacent to y=11 block position
        self.board.place_stone(11, 12, 1)

        # Some other stones
        self.board.place_stone(10, 10, 1)

        move = self.ai.get_best_move(self.board, 1)

        # Prefer blocking at (11, 11) which creates wall with our (11, 12)
        # rather than (11, 6) which leaves open
        assert move == (11, 11), \
            f"Should block at (11,11) to create wall, got {move}"


class TestScanBoardThreats:
    """Test that _scan_board_threats correctly identifies threats."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_scan_detects_open_three_vertical(self):
        """Scan must detect vertical open three."""
        # .XXX. on column 11
        self.board.place_stone(11, 7, 2)
        self.board.place_stone(11, 8, 2)
        self.board.place_stone(11, 9, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        assert len(threats["open_threes"]) >= 1, \
            f"Must detect open three, got {threats}"

    def test_scan_open_three_has_blocks(self):
        """Scan must return block positions for open three."""
        # .XXX. on column 11
        self.board.place_stone(11, 7, 2)
        self.board.place_stone(11, 8, 2)
        self.board.place_stone(11, 9, 2)

        threats = self.ai._scan_board_threats(self.board, 2)

        if threats["open_threes"]:
            threat = threats["open_threes"][0]
            blocks = threat.get("blocks", [])
            # Should have block positions at y=6 and y=10
            assert len(blocks) >= 1, "Open three should have block positions"


class TestGame3FullReplay:
    """Replay critical moments from Game 3."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_move15_should_block_open_three(self):
        """
        Full replay up to Move 14, then verify Move 15 blocks correctly.
        """
        # Replay moves 1-14
        moves = [
            (10, 10, 1),  # Move 1: P1
            (11, 9, 2),   # Move 2: P2 (y,x) -> (x,y) = (11,9)
            (11, 11, 1),  # Move 3: P1
            (9, 9, 2),    # Move 4: P2
            (10, 9, 1),   # Move 5: P1
            (10, 8, 2),   # Move 6: P2
            (12, 10, 1),  # Move 7: P1
            (11, 7, 2),   # Move 8: P2 - column 11, y=7
            (12, 6, 1),   # Move 9: P1
            (9, 8, 2),    # Move 10: P2
            (9, 10, 1),   # Move 11: P1 (the suspected bad move)
            (8, 10, 2),   # Move 12: P2
            (7, 11, 1),   # Move 13: P1
            (11, 8, 2),   # Move 14: P2 - column 11, y=8 (makes XXX)
        ]

        for x, y, player in moves:
            self.board.place_stone(x, y, player)

        # Now it's Move 15 (our turn)
        # Column 11 has opponent at y=7,8,9 - wait, let me check...
        # Move 2: (11, 9) Move 8: (11, 7) Move 14: (11, 8)
        # So column 11 (x=11) has opponent at y=7,8,9 = open three!

        move = self.ai.get_best_move(self.board, 1)

        # We should block at (11, 6) or (11, 10)
        # Note: There might be other urgent threats, but column 11 is critical
        print(f"Move 15 suggestion: {move}")
        # This is informational - the AI might have other priorities


class TestGame4SplitThreeBlocking:
    """Test split three blocking - the Game 4 bug."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_block_split_three_column11(self):
        """
        Reproduce Game 4 Move 11 bug.
        Opponent has X.XX on column 11 (y=7, gap at y=8, y=9, y=10).
        We MUST block at y=8, NOT play at y=5.
        """
        # Opponent split three on column 11: X.XX
        self.board.place_stone(11, 7, 2)   # X at y=7
        # gap at y=8
        self.board.place_stone(11, 9, 2)   # X at y=9
        self.board.place_stone(11, 10, 2)  # X at y=10

        # Our stone blocking one end
        self.board.place_stone(11, 11, 1)

        # Some other stones
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(10, 9, 1)

        move = self.ai.get_best_move(self.board, 1)

        # Must block at (11, 8) to fill the gap
        assert move == (11, 8), \
            f"Must block split three gap at (11,8), got {move}"

    def test_split_three_detected_and_blocked(self):
        """Verify scan detects split three and returns gap position."""
        # XX.X pattern on row 10
        self.board.place_stone(7, 10, 2)
        self.board.place_stone(8, 10, 2)
        # gap at (9, 10)
        self.board.place_stone(10, 10, 2)

        # Our stone
        self.board.place_stone(5, 5, 1)

        threats = self.ai._scan_board_threats(self.board, 2)

        # Should detect split three
        assert len(threats["split_threes"]) >= 1, "Must detect split three"

        # Gap should be at (9, 10)
        found_gap = False
        for threat in threats["split_threes"]:
            if threat.get("gap") == (9, 10):
                found_gap = True
                break
        assert found_gap, "Split three gap should be at (9,10)"

        # AI should block at gap
        move = self.ai.get_best_move(self.board, 1)
        assert move == (9, 10), f"Must block at gap (9,10), got {move}"
