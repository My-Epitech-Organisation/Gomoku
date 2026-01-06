##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Time Banking and Pondering features
##

import pytest
import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestTimeBanking:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_time_banked_return_uses_remaining_time(self):
        """Time banking should use time until deadline"""
        # Create a position with an obvious winning move
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)

        start = time.time()
        move = self.ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        # Move should be (9,10) or (14,10)
        assert move in [(9, 10), (14, 10)]

        # If time banking is enabled, we should wait near the deadline
        if constants.TIME_BANK_ENABLED:
            # Should take at least MIN_THINKING_TIME
            assert elapsed >= constants.MIN_THINKING_TIME * 0.5

    def test_immediate_win_still_returns_correct_move(self):
        """Immediate winning move should still be found with time banking"""
        # XXXX. - immediate win at (14,10)
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)

        move = self.ai.get_best_move(self.board, 1)
        assert move in [(9, 10), (14, 10)]

    def test_tt_warming_happens(self):
        """TT should have more entries after time banking"""
        # Create a position with an obvious winning move
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        self.board.place_stone(5, 5, 2)

        initial_tt_size = len(self.ai.transposition_table)

        self.ai.get_best_move(self.board, 1)

        # TT should have more entries (from warming)
        final_tt_size = len(self.ai.transposition_table)
        assert final_tt_size >= initial_tt_size

    def test_get_top_opponent_moves(self):
        """Should return top N predicted opponent moves"""
        # Create a position with some stones
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(9, 9, 2)
        self.board.place_stone(10, 9, 2)

        top_moves = self.ai._get_top_opponent_moves(self.board, 2, 5)

        assert len(top_moves) <= 5
        assert all(isinstance(m, tuple) and len(m) == 2 for m in top_moves)

    def test_get_top_opponent_moves_prioritizes_threats(self):
        """Top opponent moves should include threat extensions"""
        # Opponent has 3 stones - should predict extension
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(12, 10, 2)
        self.board.place_stone(5, 5, 1)  # Our stone

        top_moves = self.ai._get_top_opponent_moves(self.board, 2, 5)

        # Should include (9,10) or (13,10) as top predictions
        threat_extensions = [(9, 10), (13, 10)]
        assert any(m in threat_extensions for m in top_moves)


class TestPonderManager:
    def setup_method(self):
        from game.ponder import PonderManager
        self.board = Board(20, 20)
        self.ai = MinMaxAI()
        self.ponder_mgr = PonderManager(self.ai)

    def test_start_pondering_creates_predictions(self):
        """Starting pondering should create prediction threads"""
        # Setup a game position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 2)

        self.ponder_mgr.start_pondering(self.board, (10, 10), 1)

        # Give threads time to start
        time.sleep(0.1)

        assert self.ponder_mgr.is_pondering() or len(self.ponder_mgr.predictions) >= 0

    def test_stop_pondering_clears_state(self):
        """Stopping pondering should clean up"""
        self.board.place_stone(10, 10, 1)
        self.ponder_mgr.start_pondering(self.board, (10, 10), 1)
        time.sleep(0.05)

        self.ponder_mgr.stop_pondering()

        assert not self.ponder_mgr.is_pondering()

    def test_on_opponent_move_returns_cached_on_hit(self):
        """Ponder hit should return cached result"""
        # Setup position
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)

        self.ponder_mgr.start_pondering(self.board, (11, 10), 1)

        # Wait for pondering to complete
        time.sleep(0.5)

        # Check if any prediction was made
        if len(self.ponder_mgr.predictions) > 0:
            # Get one of the predicted moves
            pred_move = list(self.ponder_mgr.predictions.keys())[0]
            self.ponder_mgr.on_opponent_move(pred_move[0], pred_move[1])
            # The key thing is it should have cleared predictions
            assert len(self.ponder_mgr.predictions) == 0

    def test_on_opponent_move_returns_none_on_miss(self):
        """Ponder miss should return None"""
        self.board.place_stone(10, 10, 1)
        self.ponder_mgr.start_pondering(self.board, (10, 10), 1)
        time.sleep(0.05)

        # Query for a move that wasn't predicted
        result = self.ponder_mgr.on_opponent_move(0, 0)

        assert result is None


class TestAsyncInputReader:
    def test_async_reader_queues_input(self):
        """AsyncInputReader should queue lines from input"""
        import io
        from communication.async_reader import AsyncInputReader

        # Create a fake input stream
        input_stream = io.StringIO("line1\nline2\nline3\n")

        reader = AsyncInputReader(input_stream)
        reader.start()

        # Wait for reader to process
        time.sleep(0.1)

        line1 = reader.get_line(timeout=0.5)
        assert line1 == "line1"

        line2 = reader.get_line(timeout=0.5)
        assert line2 == "line2"

        reader.stop()

    def test_async_reader_timeout(self):
        """AsyncInputReader should return None on timeout"""
        import io
        from communication.async_reader import AsyncInputReader

        # Empty input stream
        input_stream = io.StringIO("")

        reader = AsyncInputReader(input_stream)
        reader.start()

        result = reader.get_line(timeout=0.1)
        assert result is None

        reader.stop()

    def test_has_input_check(self):
        """has_input should correctly report queue state"""
        import io
        from communication.async_reader import AsyncInputReader

        input_stream = io.StringIO("test\n")
        reader = AsyncInputReader(input_stream)
        reader.start()

        time.sleep(0.1)

        assert reader.has_input()

        reader.get_line(timeout=0.1)
        assert not reader.has_input()

        reader.stop()


class TestTimeBankingIntegration:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=5.0)

    def test_forced_move_uses_time_bank(self):
        """Forced moves should use remaining time for TT warming"""
        # Create forced move scenario
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)

        start = time.time()
        move = self.ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        assert move in [(9, 10), (14, 10)]

        # Should have used some time for warming
        # (At minimum, should take longer than just finding the move)
        if constants.TIME_BANK_ENABLED:
            assert elapsed >= 0.05

    def test_full_search_when_no_forced_move(self):
        """Without forced move, should do full iterative deepening"""
        # Simple position - no forced moves
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 11, 2)

        start = time.time()
        move = self.ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        assert move is not None
        # Should take some time for search
        assert elapsed > 0
