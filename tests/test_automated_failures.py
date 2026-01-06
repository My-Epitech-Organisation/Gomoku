##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests reproducing automated test failures - Fight 3 & 4 from tests 05, 06, 07
##

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI


def visualize_board(board, highlight=None):
    """Print board state for debugging."""
    print("\n    ", end="")
    for x in range(min(15, board.width)):
        print(f"{x:2}", end=" ")
    print()
    for y in range(min(15, board.height)):
        print(f"{y:2}  ", end="")
        for x in range(min(15, board.width)):
            cell = board.grid[y][x]
            if highlight and (x, y) == highlight:
                print(f"[{cell}]", end="")
            elif cell == 0:
                print(" . ", end="")
            elif cell == 1:
                print(" X ", end="")  # Player 1
            else:
                print(" O ", end="")  # Player 2
        print()
    print()


class TestFight3Sequence:
    """
    Reproduce Fight 3 from tests 05/07 (ab_4_scd_v2/ab_4_pdy).
    Our AI is Player 2. Player 1 wins with diagonal (5,5)→(6,4)→(7,3)→(8,2)→(9,1).

    Full sequence:
    6,3,1 -> 4,3,2 -> 7,2,1 -> 5,4,2 -> 7,3,1 -> 3,2,2 -> 6,5,1 -> 3,4,2 ->
    2,1,1 -> 3,3,2 -> 3,5,1 -> 3,1,2 -> 3,0,1 -> 5,2,2 -> 6,1,1 -> 1,6,2 ->
    2,5,1 -> 5,3,2 -> 5,5,1 -> 4,5,2 -> 6,4,1 -> 6,2,2 -> 8,2,1 -> 4,6,2 ->
    9,1,1 -> Player 1 WIN
    """

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()
        # Full move sequence: (x, y, player)
        self.moves = [
            (6, 3, 1), (4, 3, 2), (7, 2, 1), (5, 4, 2), (7, 3, 1), (3, 2, 2),
            (6, 5, 1), (3, 4, 2), (2, 1, 1), (3, 3, 2), (3, 5, 1), (3, 1, 2),
            (3, 0, 1), (5, 2, 2), (6, 1, 1), (1, 6, 2), (2, 5, 1), (5, 3, 2),
            (5, 5, 1), (4, 5, 2), (6, 4, 1), (6, 2, 2), (8, 2, 1), (4, 6, 2),
            (9, 1, 1),  # Winning move
        ]

    def _play_moves_until(self, move_index):
        """Play moves from 0 to move_index (exclusive)."""
        for i in range(move_index):
            x, y, player = self.moves[i]
            self.board.place_stone(x, y, player)

    def debug_visualize_final_position(self):
        """Visualize the final losing position (debug utility, not a test)."""
        self._play_moves_until(len(self.moves))
        print("\n=== FINAL POSITION (Player 1 wins) ===")
        print("Winning diagonal: (5,5)→(6,4)→(7,3)→(8,2)→(9,1)")
        visualize_board(self.board)

    def test_move22_should_block_split_four(self):
        """
        After move 21 (6,4,1), Player 1 has:
        - (5,5), (6,4), (7,3) on diagonal = 3 in a row
        - BUT column 6 has split-four: (6,1), (6,3), (6,4), (6,5) with gap at (6,2)!

        Move 22 is Player 2's turn. MUST block split-four at (6,2).
        The split-four is more urgent than the diagonal three.
        """
        self._play_moves_until(21)  # Up to move 21 (6,4,1)

        print("\n=== After Move 21: Player 1 played (6,4) ===")
        print("Player 1 diagonal threat: (5,5)→(6,4)→(7,3)")
        print("Player 1 split-four on col 6: (6,1)-(6,3)-(6,4)-(6,5) gap at (6,2)")
        visualize_board(self.board)

        # Player 2's turn - must block split-four (more urgent than diagonal)
        move = self.ai.get_best_move(self.board, 2)
        print(f"AI suggests: {move}")
        print(f"Actual game played: (6, 2)")

        # Must block split-four at (6,2) - this is forced!
        assert move == (6, 2), \
            f"Move 22: Must block split-four at (6,2), got {move}"

    def test_move24_must_block_four(self):
        """
        After move 23 (8,2,1), Player 1 has an open four on the diagonal:
        (5,5)→(6,4)→(7,3)→(8,2), extendable to five at (9,1) or (4,6).

        Move 24: Player 2 must block at one of these endpoints.
        """
        self._play_moves_until(23)  # Up to move 23 (8,2,1)

        print("\n=== After Move 23: Player 1 played (8,2) - OPEN FOUR! ===")
        print("Player 1 has OPEN FOUR: (5,5)→(6,4)→(7,3)→(8,2)")
        print("Can extend to (9,1) or (4,6)")
        visualize_board(self.board)

        # At this point it's already too late - open four means certain loss
        # But AI should still try to block
        move = self.ai.get_best_move(self.board, 2)
        print(f"AI suggests: {move}")
        print(f"Actual game played: (4, 6)")

        assert move in [(9, 1), (4, 6)], \
            f"Move 24: Must block OPEN FOUR at (9,1) or (4,6), got {move}"

    def debug_critical_move19_analysis(self):
        """Debug utility: Analyze board state before Move 19 (5,5,1)."""
        self._play_moves_until(18)  # Up to move 18 (5,3,2)

        print("\n=== After Move 18: Before P1 plays (5,5) ===")
        print("P1 stones so far: (6,3), (7,2), (7,3), (6,5), (2,1), (3,5), (3,0), (6,1), (2,5)")
        visualize_board(self.board)

    def test_move20_should_see_diagonal_start(self):
        """
        After move 19 (5,5,1), Player 1 has (5,5) and (7,3) on same diagonal.
        Not yet 3 in a row, but building.

        After move 20 (4,5,2), then move 21 (6,4,1) creates 3 in a row.
        """
        self._play_moves_until(19)  # Up to move 19 (5,5,1)

        print("\n=== After Move 19: P1 played (5,5) ===")
        print("P1 diagonal stones: (7,3) and (5,5) - 2 stones with gap at (6,4)")
        visualize_board(self.board)

        # Check if AI sees the diagonal building
        move = self.ai.get_best_move(self.board, 2)
        print(f"AI Move 20 suggestion: {move}")
        print(f"Actual game: (4, 5)")

        # Ideally should block at (6,4) but might not be urgent yet
        if move == (6, 4):
            print("GOOD: AI would prevent the diagonal!")


class TestFight3Move06Sequence:
    """
    Reproduce Fight 3 from test 06 (ab_4_mc_v2).
    Different game sequence, Player 1 also wins.

    Full sequence:
    6,6,1 -> 4,6,2 -> 6,4,1 -> 6,7,2 -> 6,5,1 -> 6,3,2 -> 5,6,1 -> 4,7,2 ->
    7,4,1 -> 5,7,2 -> 7,7,1 -> 8,3,2 -> 2,7,1 -> 7,3,2 -> 9,3,1 -> 4,3,2 ->
    5,3,1 -> 5,4,2 -> 4,4,1 -> 5,5,2 -> 8,6,1 -> 7,5,2 -> 7,6,1 -> 9,6,2 ->
    6,8,1 -> 9,5,2 -> 4,10,1 -> 5,9,2 -> 4,9,1 -> 4,5,2 -> 7,2,1 -> 9,7,2 ->
    9,8,1 -> 10,9,2 -> 5,10,1 -> 3,8,2 -> 7,10,1 -> 6,10,2 -> 7,8,1 -> 7,9,2 ->
    8,8,1 -> 10,8,2 -> 5,8,1 -> Player 1 WIN
    """

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()
        self.moves = [
            (6, 6, 1), (4, 6, 2), (6, 4, 1), (6, 7, 2), (6, 5, 1), (6, 3, 2),
            (5, 6, 1), (4, 7, 2), (7, 4, 1), (5, 7, 2), (7, 7, 1), (8, 3, 2),
            (2, 7, 1), (7, 3, 2), (9, 3, 1), (4, 3, 2), (5, 3, 1), (5, 4, 2),
            (4, 4, 1), (5, 5, 2), (8, 6, 1), (7, 5, 2), (7, 6, 1), (9, 6, 2),
            (6, 8, 1), (9, 5, 2), (4, 10, 1), (5, 9, 2), (4, 9, 1), (4, 5, 2),
            (7, 2, 1), (9, 7, 2), (9, 8, 1), (10, 9, 2), (5, 10, 1), (3, 8, 2),
            (7, 10, 1), (6, 10, 2), (7, 8, 1), (7, 9, 2), (8, 8, 1), (10, 8, 2),
            (5, 8, 1),  # Winning move
        ]

    def _play_moves_until(self, move_index):
        for i in range(move_index):
            x, y, player = self.moves[i]
            self.board.place_stone(x, y, player)

    def debug_visualize_final_position(self):
        """Debug utility: Visualize final position to identify winning pattern."""
        self._play_moves_until(len(self.moves))
        print("\n=== TEST 06 FINAL POSITION (Player 1 wins at 5,8) ===")
        visualize_board(self.board)

        # Find Player 1's winning line through (5,8)
        print("Player 1 stones to analyze for 5-in-row through (5,8):")
        p1_stones = []
        for i, (x, y, p) in enumerate(self.moves):
            if p == 1:
                p1_stones.append((x, y, i+1))
        for x, y, move_num in p1_stones:
            print(f"  Move {move_num}: ({x}, {y})")

    def debug_find_winning_pattern(self):
        """Find the exact winning 5-in-a-row pattern."""
        self._play_moves_until(len(self.moves))

        # Check all directions from (5,8)
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        win_x, win_y = 5, 8

        for dx, dy in directions:
            line = [(win_x, win_y)]
            # Check positive direction
            for i in range(1, 5):
                nx, ny = win_x + i*dx, win_y + i*dy
                if 0 <= nx < 20 and 0 <= ny < 20 and self.board.grid[ny][nx] == 1:
                    line.append((nx, ny))
                else:
                    break
            # Check negative direction
            for i in range(1, 5):
                nx, ny = win_x - i*dx, win_y - i*dy
                if 0 <= nx < 20 and 0 <= ny < 20 and self.board.grid[ny][nx] == 1:
                    line.append((nx, ny))
                else:
                    break

            if len(line) >= 5:
                print(f"WINNING LINE (dir {dx},{dy}): {sorted(line)}")


class TestReplayAndAnalyze:
    """Utility class to replay any game and find where AI diverges."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def debug_replay_fight3_find_divergence(self):
        """Debug utility: Replay Fight 3 and find where AI diverges."""
        moves = [
            (6, 3, 1), (4, 3, 2), (7, 2, 1), (5, 4, 2), (7, 3, 1), (3, 2, 2),
            (6, 5, 1), (3, 4, 2), (2, 1, 1), (3, 3, 2), (3, 5, 1), (3, 1, 2),
            (3, 0, 1), (5, 2, 2), (6, 1, 1), (1, 6, 2), (2, 5, 1), (5, 3, 2),
            (5, 5, 1), (4, 5, 2), (6, 4, 1), (6, 2, 2), (8, 2, 1), (4, 6, 2),
            (9, 1, 1),
        ]

        print("\n=== REPLAY ANALYSIS: Finding where AI would diverge ===\n")

        divergences = []
        for i, (x, y, player) in enumerate(moves):
            if player == 2:  # Our AI's turn
                ai_move = self.ai.get_best_move(self.board, 2)
                actual = (x, y)
                if ai_move != actual:
                    divergences.append({
                        'move_num': i + 1,
                        'ai_choice': ai_move,
                        'actual': actual,
                    })
                    status = f"DIVERGE: AI={ai_move}"
                else:
                    status = "MATCH"
                print(f"Move {i+1}: P2 played {actual}, AI suggests {ai_move} [{status}]")

            self.board.place_stone(x, y, player)

        print(f"\n=== Total divergences: {len(divergences)} ===")
        for d in divergences:
            print(f"  Move {d['move_num']}: AI would play {d['ai_choice']} instead of {d['actual']}")


class TestForkDetection:
    """Test fork detection - analyzing where the game was truly lost."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_move20_correctly_blocks_split_four(self):
        """At Move 20, blocking (4,5) is CORRECT - it's an immediate win threat."""
        moves = [
            (6, 3, 1), (4, 3, 2), (7, 2, 1), (5, 4, 2), (7, 3, 1), (3, 2, 2),
            (6, 5, 1), (3, 4, 2), (2, 1, 1), (3, 3, 2), (3, 5, 1), (3, 1, 2),
            (3, 0, 1), (5, 2, 2), (6, 1, 1), (1, 6, 2), (2, 5, 1), (5, 3, 2),
            (5, 5, 1),  # Move 19 creates XX.XX on row 5
        ]
        for x, y, player in moves:
            self.board.place_stone(x, y, player)

        print("\n=== Move 20: Row 5 has XX.XX - must block! ===")
        visualize_board(self.board)

        move = self.ai.get_best_move(self.board, 2)
        print(f"AI: {move}")

        # (4,5) is correct - blocks immediate win
        assert move == (4, 5), f"Should block split-four at (4,5), got {move}"

    def test_move18_should_take_5_5(self):
        """
        THE REAL BUG: At Move 18, P2 should play (5,5) to prevent:
        1. Row 5 split-four (P1 has (2,5), (3,5), (6,5))
        2. Diagonal threat through (5,5)-(6,4)-(7,3)

        P2 played (5,3) instead - this is the losing move!
        """
        moves = [
            (6, 3, 1), (4, 3, 2), (7, 2, 1), (5, 4, 2), (7, 3, 1), (3, 2, 2),
            (6, 5, 1), (3, 4, 2), (2, 1, 1), (3, 3, 2), (3, 5, 1), (3, 1, 2),
            (3, 0, 1), (5, 2, 2), (6, 1, 1), (1, 6, 2), (2, 5, 1),  # Move 17
            # Move 18 is P2's turn - what should AI play?
        ]
        for x, y, player in moves:
            self.board.place_stone(x, y, player)

        print("\n=== Move 18: Critical decision point ===")
        print("P1 has row 5: X(2,5), X(3,5), X(6,5) = X X . . X")
        print("(5,5) would block row 5 AND prevent diagonal!")
        visualize_board(self.board)

        move = self.ai.get_best_move(self.board, 2)
        print(f"AI suggests: {move}")
        print(f"Actual game: (5, 3)")
        print(f"Optimal move: (5, 5) or (4, 5)")

        # Should recognize (5,5) or (4,5) as critical
        assert move in [(5, 5), (4, 5)], \
            f"Should block row 5 development at (5,5) or (4,5), got {move}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
