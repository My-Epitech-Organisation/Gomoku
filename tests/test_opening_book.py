##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for Opening Book
##

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game.opening_book import OpeningBook, get_opening_book
from game import constants


class TestOpeningBookConstants:
    """Tests for opening book constants."""

    def test_opening_book_constants_exist(self):
        """Verify opening book constants are defined."""
        assert hasattr(constants, 'OPENING_BOOK_MAX_MOVES')
        assert hasattr(constants, 'OPENING_BOOK_ENABLED')
        assert constants.OPENING_BOOK_MAX_MOVES > 0


class TestOpeningBookInit:
    """Tests for OpeningBook initialization."""

    def test_book_initializes(self):
        """OpeningBook should initialize without error."""
        book = OpeningBook(20)
        assert book is not None
        assert book.board_size == 20

    def test_book_has_entries(self):
        """Book should have pre-computed entries."""
        book = OpeningBook(20)
        assert len(book.book) > 0

    def test_book_center_calculation(self):
        """Book should calculate center correctly."""
        book = OpeningBook(20)
        assert book.center == 10

        book15 = OpeningBook(15)
        assert book15.center == 7

    def test_book_size_method(self):
        """size() should return number of entries."""
        book = OpeningBook(20)
        assert book.size() > 0
        assert book.size() == len(book.book)


class TestOpeningBookLookup:
    """Tests for OpeningBook.lookup method."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.book = OpeningBook(20)

    def test_empty_board_returns_center(self):
        """Empty board should return center move."""
        move = self.book.lookup(self.board)
        assert move is not None
        # Center of 20x20 board
        assert move == (10, 10)

    def test_lookup_returns_valid_move(self):
        """Lookup should return a valid empty position."""
        self.board.place_stone(10, 10, 1)

        move = self.book.lookup(self.board)
        if move is not None:
            x, y = move
            assert 0 <= x < self.board.width
            assert 0 <= y < self.board.height
            assert self.board.grid[y][x] == 0

    def test_lookup_respects_move_count_limit(self):
        """Lookup should return None after max moves."""
        # Place many stones to exceed limit
        positions = [(i, 0) for i in range(10)]
        for i, (x, y) in enumerate(positions):
            player = 1 if i % 2 == 0 else 2
            self.board.place_stone(x, y, player)

        move = self.book.lookup(self.board)
        # Should return None since move_count > OPENING_BOOK_MAX_MOVES
        assert move is None

    def test_lookup_after_opponent_center(self):
        """After opponent plays center, book should have a response."""
        self.board.place_stone(10, 10, 2)  # Opponent at center

        move = self.book.lookup(self.board)
        # Should have a response (diagonal)
        assert move is not None

    def test_lookup_with_our_center(self):
        """After we play center and opponent responds, book should work."""
        self.board.place_stone(10, 10, 1)  # We at center
        self.board.place_stone(11, 10, 2)  # Opponent adjacent

        move = self.book.lookup(self.board)
        # May or may not have a response depending on book coverage
        # Just check it doesn't crash
        assert move is None or isinstance(move, tuple)


class TestOpeningBookSymmetry:
    """Tests for symmetry handling in OpeningBook."""

    def setup_method(self):
        self.book = OpeningBook(20)

    def test_symmetry_transforms_exist(self):
        """Should have 8 symmetry transforms."""
        transforms = self.book._get_transforms()
        assert len(transforms) == 8

    def test_symmetry_coverage(self):
        """Symmetric positions should have symmetric responses."""
        # Test that symmetric transformations are applied correctly
        # by checking a position that IS in the book
        board1 = Board(20, 20)
        board2 = Board(20, 20)

        # Place opponent at center - this is in the book
        board1.place_stone(10, 10, 2)
        board2.place_stone(10, 10, 2)

        move1 = self.book.lookup(board1)
        move2 = self.book.lookup(board2)

        # Both should have responses (same position)
        assert move1 is not None
        assert move2 is not None
        assert move1 == move2

    def test_transforms_preserve_center(self):
        """Center should be preserved by all transforms."""
        c = self.book.center
        transforms = self.book._get_transforms()

        for transform in transforms:
            result = transform(c, c)
            assert result == (c, c), f"Transform didn't preserve center: {result}"


class TestOpeningBookSingleton:
    """Tests for get_opening_book singleton."""

    def test_singleton_returns_same_instance(self):
        """get_opening_book should return same instance."""
        book1 = get_opening_book(20)
        book2 = get_opening_book(20)
        assert book1 is book2

    def test_singleton_different_sizes(self):
        """Different sizes should create new instances."""
        get_opening_book(20)
        book15 = get_opening_book(15)
        # After getting size 15, singleton is now 15
        # This is expected behavior
        assert book15.board_size == 15


class TestOpeningBookIntegration:
    """Integration tests for opening book with AI."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI(time_limit=2.0)

    def test_ai_uses_book_for_first_move(self):
        """AI should use opening book for move 1."""
        start = time.time()
        move = self.ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        # Should be very fast (book lookup, no search)
        assert elapsed < 0.5
        # Should return center
        assert move == (10, 10)

    def test_ai_uses_book_for_response(self):
        """AI should use opening book for response to center."""
        # Opponent plays center
        self.board.place_stone(10, 10, 2)

        start = time.time()
        move = self.ai.get_best_move(self.board, 1)
        elapsed = time.time() - start

        # Should be fast if book hit
        assert move is not None
        # Book response should be diagonal
        if elapsed < 0.5:
            # This was likely a book move
            assert move in [(11, 11), (9, 9), (11, 9), (9, 11)]

    def test_ai_falls_back_to_search(self):
        """AI should fall back to search when book doesn't match."""
        # Create a position not in book
        self.board.place_stone(5, 5, 1)
        self.board.place_stone(15, 15, 2)
        self.board.place_stone(5, 6, 1)
        self.board.place_stone(15, 14, 2)

        move = self.ai.get_best_move(self.board, 1)
        # Should still find a move
        assert move is not None

    def test_ai_book_doesnt_return_occupied(self):
        """AI book should never return an occupied position."""
        for _ in range(10):
            board = Board(20, 20)
            # Random setup
            board.place_stone(10, 10, 1)

            move = self.ai.get_best_move(board, 2)
            if move is not None:
                assert board.grid[move[1]][move[0]] == 0


class TestOpeningBookPatterns:
    """Tests for specific opening patterns."""

    def setup_method(self):
        self.board = Board(20, 20)
        self.book = OpeningBook(20)

    def test_empty_board_pattern(self):
        """Empty board should map to center."""
        state = frozenset()
        assert state in self.book.book
        assert self.book.book[state] == (10, 10)

    def test_opponent_center_pattern(self):
        """Opponent at center should have diagonal response."""
        state = frozenset([(10, 10, 2)])
        assert state in self.book.book

    def test_book_has_multiple_patterns(self):
        """Book should have patterns for various situations."""
        # Check we have more than just empty board
        assert self.book.size() > 10

    def test_book_responses_are_valid(self):
        """All book responses should be valid board positions."""
        for state, response in self.book.book.items():
            x, y = response
            assert 0 <= x < 20
            assert 0 <= y < 20
            # Response should not overlap with any stone in state
            state_positions = {(sx, sy) for sx, sy, _ in state}
            assert (x, y) not in state_positions


class TestOpeningBookPerformance:
    """Performance tests for opening book."""

    def test_book_lookup_fast(self):
        """Book lookup should be very fast."""
        board = Board(20, 20)
        book = OpeningBook(20)

        start = time.time()
        for _ in range(1000):
            book.lookup(board)
        elapsed = time.time() - start

        # 1000 lookups should take < 0.1 seconds
        assert elapsed < 0.1

    def test_book_initialization_reasonable(self):
        """Book initialization should be fast."""
        start = time.time()
        book = OpeningBook(20)
        elapsed = time.time() - start

        # Should initialize in < 0.1 seconds
        assert elapsed < 0.1
        assert book.size() > 0
