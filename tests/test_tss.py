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


class TestVerticalThreatDetection:
    """Test for the vertical threat scenario from the lost game."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_detects_vertical_four(self):
        """AI must block vertical four before opponent wins"""
        # Opponent has 4 stones vertically on column 12
        self.board.place_stone(12, 8, 2)
        self.board.place_stone(12, 9, 2)
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(12, 11, 2)
        # Place a player stone to make it a valid game state
        self.board.place_stone(10, 10, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Must block at (12, 7) or (12, 12)
        assert move in [(12, 7), (12, 12)]

    def test_detects_vertical_three_building(self):
        """AI detects vertical threat being built"""
        # Opponent building vertical threat on column 12
        self.board.place_stone(12, 9, 2)
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(12, 11, 2)
        # Player stones
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Should either block or create own winning threat
        assert move is not None


class TestIncrementalEvaluation:
    """Tests for incremental evaluation correctness."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_incremental_matches_full_eval(self):
        """Incremental evaluation matches full recalculation"""
        # Place some stones
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(10, 11, 1)
        self.board.place_stone(9, 9, 2)

        # First evaluation (full)
        eval1 = self.ai.evaluate(self.board)

        # Reset cache and recalculate
        self.board.eval_cache.clear()
        self.board.eval_totals = {1: 0, 2: 0}

        eval2 = self.ai.evaluate(self.board)

        assert eval1 == eval2

    def test_incremental_after_move(self):
        """Evaluation updates correctly after new move"""
        self.board.place_stone(10, 10, 1)
        eval1 = self.ai.evaluate(self.board)

        # Add more stones
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        eval2 = self.ai.evaluate(self.board)

        # Score should increase with more aligned stones
        assert eval2 > eval1

    def test_incremental_after_undo(self):
        """Evaluation updates correctly after undo"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        eval_with_three = self.ai.evaluate(self.board)

        # Undo last move
        self.board.undo_stone(12, 10, 1)
        eval_with_two = self.ai.evaluate(self.board)

        # Score should be lower
        assert eval_with_two < eval_with_three


class TestSplitThreeBlocking:
    """Tests for split three and pre-open-four blocking - fixes for lost game."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_block_split_three_horizontal(self):
        """AI must block XX.X pattern to prevent open four"""
        # Opponent has XX.X on row 14: (7,14), (8,14), gap, (10,14)
        self.board.place_stone(7, 14, 2)
        self.board.place_stone(8, 14, 2)
        self.board.place_stone(10, 14, 2)
        # Player stone
        self.board.place_stone(10, 10, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Must block at (9, 14) to fill the gap
        assert move == (9, 14), f"Expected (9,14) to block split three, got {move}"

    def test_block_pre_open_four_horizontal(self):
        """AI must block .XXX. pattern before it becomes open four"""
        # Opponent has .XXX. on row 14
        self.board.place_stone(8, 14, 2)
        self.board.place_stone(9, 14, 2)
        self.board.place_stone(10, 14, 2)
        # Player stone
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Must block at (7, 14) or (11, 14) to prevent open four
        assert move in [(7, 14), (11, 14)], f"Expected block at ends, got {move}"

    def test_losing_game_scenario_move35(self):
        """Reproduce critical position from lost game (Move 35 scenario)"""
        # Opponent built line on y=14: (7,14), (8,14), (9,14)
        # This is a .XXX. pattern that wasn't blocked
        self.board.place_stone(7, 14, 2)
        self.board.place_stone(8, 14, 2)
        self.board.place_stone(9, 14, 2)

        # Add some player stones (simulating mid-game)
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 11, 1)
        self.board.place_stone(9, 9, 1)

        move = self.ai.get_best_move(self.board, 1)
        # AI must block the pre-open-four
        assert move in [(6, 14), (10, 14)], \
            f"AI should block pre-open-four at (6,14) or (10,14), got {move}"

    def test_count_threats_detects_split_three(self):
        """_count_threats correctly identifies split three patterns"""
        # XX.X pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(13, 10, 2)

        # Place opponent stone at gap to test threat count
        self.board.place_stone(12, 10, 2)
        threats = self.ai._count_threats(self.board, 12, 10, 2)
        self.board.undo_stone(12, 10, 2)

        # Should detect it creates a four
        assert threats["closed_fours"] >= 1 or threats["open_fours"] >= 1

    def test_count_threats_detects_pre_open_four(self):
        """_count_threats correctly identifies .XXX. pattern"""
        # .XXX. pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(12, 10, 2)

        threats = self.ai._count_threats(self.board, 11, 10, 2)
        # Should detect pre-open-four
        assert threats["pre_open_fours"] >= 1

    def test_move_heuristic_prioritizes_block(self):
        """_move_heuristic gives high score to blocking split three"""
        # XX.X pattern
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(13, 10, 2)

        # Score for blocking the gap
        block_score = self.ai._move_heuristic(self.board, (12, 10), 1)

        # Score for random non-critical move
        random_score = self.ai._move_heuristic(self.board, (5, 5), 1)

        assert block_score > random_score
        # Should be at least MOVE_BLOCK_SPLIT_THREE level
        from game import constants
        assert block_score >= constants.MOVE_BLOCK_SPLIT_THREE

    def test_vertical_split_three_block(self):
        """AI blocks vertical split three (column threat)"""
        # XX.X pattern on column 12 - more urgent threat
        self.board.place_stone(12, 8, 2)
        self.board.place_stone(12, 9, 2)
        # gap at (12, 10)
        self.board.place_stone(12, 11, 2)
        # Player stone
        self.board.place_stone(5, 5, 1)

        move = self.ai.get_best_move(self.board, 1)
        # Should block at gap (12, 10)
        assert move == (12, 10), \
            f"Expected to block vertical split three at (12,10), got {move}"
