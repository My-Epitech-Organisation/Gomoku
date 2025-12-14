##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for board functionality
##

import pytest

from src.game import Board


class TestBoard:
    """Test Board class."""

    def test_board_initialization(self):
        """Test board creation."""
        board = Board(20, 20)
        assert board.width == 20
        assert board.height == 20
        assert board.move_count == 0

    def test_place_stone(self):
        """Test placing stones."""
        board = Board(20, 20)
        assert board.place_stone(10, 10, Board.PLAYER)
        assert board.get_stone(10, 10) == Board.PLAYER
        assert board.move_count == 1

    def test_invalid_placement(self):
        """Test invalid stone placement."""
        board = Board(20, 20)
        board.place_stone(10, 10, Board.PLAYER)
        # Can't place on occupied position
        assert not board.place_stone(10, 10, Board.OPPONENT)

    def test_winning_detection(self):
        """Test winning move detection."""
        board = Board(20, 20)
        # Place 4 in a row
        for x in range(10, 14):
            board.place_stone(x, 10, Board.PLAYER)
        # 5th should be winning
        assert board.is_winning_move(14, 10, Board.PLAYER)

    def test_threat_level(self):
        """Test threat level detection."""
        board = Board(20, 20)
        # Place 3 in a row
        for x in range(10, 13):
            board.place_stone(x, 10, Board.PLAYER)
        # Should detect threat
        threat = board.get_threat_level(13, 10, Board.PLAYER)
        assert threat >= 2

    def test_board_copy(self):
        """Test board copying."""
        board = Board(20, 20)
        board.place_stone(10, 10, Board.PLAYER)
        
        copy = board.copy()
        assert copy.get_stone(10, 10) == Board.PLAYER
        assert copy.move_count == board.move_count
        
        # Modify copy shouldn't affect original
        copy.place_stone(11, 11, Board.OPPONENT)
        assert board.get_stone(11, 11) == Board.EMPTY
        
        # Modify original shouldn't affect copy
        board.place_stone(12, 12, Board.PLAYER)
        assert copy.get_stone(12, 12) == Board.EMPTY

    def test_valid_moves(self):
        """Test getting valid moves."""
        board = Board(5, 5)
        moves = board.get_valid_moves(use_region=False)
        assert len(moves) == 25  # All positions empty
        
        board.place_stone(2, 2, Board.PLAYER)
        moves = board.get_valid_moves(use_region=False)
        assert len(moves) == 24  # One occupied

    def test_occupied_region(self):
        """Test occupied region calculation."""
        board = Board(20, 20)
        board.place_stone(10, 10, Board.PLAYER)
        board.place_stone(12, 12, Board.OPPONENT)
        
        min_x, min_y, max_x, max_y = board.get_occupied_region(margin=2)
        assert min_x <= 10
        assert max_x >= 12
        assert min_y <= 10
        assert max_y >= 12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
