##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for AI functionality
##

import pytest

from src.game import Board, Evaluator, MinMaxAI


class TestMinMaxAI:
    """Test MinMaxAI class."""

    def test_ai_initialization(self):
        """Test AI creation."""
        ai = MinMaxAI(max_depth=3, time_limit=1.0)
        assert ai.max_depth == 3
        assert ai.time_limit == 1.0

    def test_find_winning_move(self):
        """Test AI finds winning moves."""
        board = Board(20, 20)
        ai = MinMaxAI(max_depth=2, time_limit=5.0)
        
        # Create a winning opportunity (4 in a row)
        for x in range(10, 14):
            board.place_stone(x, 10, Board.PLAYER)
        
        # AI should find the winning move
        move = ai.get_best_move(board, Board.PLAYER)
        assert move is not None
        assert move in [(14, 10), (9, 10)]  # Either end completes the five

    def test_block_opponent_win(self):
        """Test AI blocks opponent winning moves."""
        board = Board(20, 20)
        ai = MinMaxAI(max_depth=2, time_limit=5.0)
        
        # Opponent has 4 in a row
        for x in range(10, 14):
            board.place_stone(x, 10, Board.OPPONENT)
        
        # AI should block
        move = ai.get_best_move(board, Board.PLAYER)
        assert move is not None
        assert move in [(14, 10), (9, 10)]  # Block either end

    def test_opening_move(self):
        """Test AI makes reasonable opening move."""
        board = Board(20, 20)
        ai = MinMaxAI(max_depth=2, time_limit=5.0)
        
        move = ai.get_best_move(board, Board.PLAYER)
        assert move is not None
        # Should play near center
        x, y = move
        assert 8 <= x <= 12
        assert 8 <= y <= 12


class TestEvaluator:
    """Test Evaluator class."""

    def test_evaluator_initialization(self):
        """Test evaluator creation."""
        evaluator = Evaluator()
        assert evaluator is not None

    def test_evaluate_line(self):
        """Test line evaluation."""
        evaluator = Evaluator()
        
        # Five in a row
        score = evaluator.evaluate_line(5, True, True)
        assert score == Evaluator.FIVE
        
        # Four in a row (open)
        score = evaluator.evaluate_line(4, True, False)
        assert score == Evaluator.FOUR
        
        # Open three
        score = evaluator.evaluate_line(3, True, True)
        assert score == Evaluator.OPEN_THREE

    def test_position_evaluation(self):
        """Test position evaluation."""
        board = Board(20, 20)
        evaluator = Evaluator()
        
        # Place some stones
        board.place_stone(10, 10, Board.PLAYER)
        board.place_stone(11, 10, Board.PLAYER)
        
        # Evaluate extending the line
        score = evaluator.evaluate_position(board, 12, 10, Board.PLAYER)
        assert score > 0  # Should be positive for extending line

    def test_move_ordering(self):
        """Test move ordering."""
        board = Board(20, 20)
        evaluator = Evaluator()
        
        # Create a strong position
        for x in range(10, 13):
            board.place_stone(x, 10, Board.PLAYER)
        
        moves = [(9, 10), (13, 10), (15, 15)]
        ordered = evaluator.order_moves(board, moves, Board.PLAYER)
        
        # Moves extending the line should be prioritized
        assert ordered[0] in [(9, 10), (13, 10)]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
