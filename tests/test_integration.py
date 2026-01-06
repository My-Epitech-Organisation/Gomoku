##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Integration tests for the communication system
##

import sys
import os
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communication import CommunicationManager


class MockGameContext:
    """Mock context for integration testing"""
    def __init__(self):
        self.board = None
        self.board_width = 0
        self.board_height = 0
        self.move_count = 0

    def initialize_board(self, width: int, height: int) -> None:
        self.board_width = width
        self.board_height = height
        self.board = [[0] * width for _ in range(height)]

    def get_opening_move(self) -> tuple[int, int]:
        return (10, 10)

    def process_opponent_move(self, x: int, y: int) -> None:
        if 0 <= x < self.board_width and 0 <= y < self.board_height:
            self.board[y][x] = 2

    def get_best_move(self) -> tuple[int, int]:
        # Return sequential moves for testing
        moves = [(0, 0), (1, 0), (2, 0)]
        move = moves[self.move_count % len(moves)]
        self.move_count += 1
        return move

    def process_board(self, moves: list) -> None:
        self.board = [[0] * self.board_width for _ in range(self.board_height)]
        for move in moves:
            x, y = move.x, move.y
            if 0 <= x < self.board_width and 0 <= y < self.board_height:
                self.board[y][x] = move.stone_type

    def get_about_info(self) -> dict:
        return {
            "name": "Gomokucaracha",
            "version": "6.7",
            "author": "Santiago Eliott Paul-Antoine",
            "country": "FR",
        }


class TestIntegration:
    def test_full_protocol_flow(self):
        """Test a complete game flow from start to end"""
        context = MockGameContext()

        # Create input/output streams
        input_commands = [
            "START 20",
            "BEGIN",
            "TURN 11,10",
            "TURN 12,10",
            "ABOUT",
            "END"
        ]
        input_stream = StringIO("\n".join(input_commands) + "\n")
        output_stream = StringIO()

        # Create manager
        manager = CommunicationManager(
            context,
            input_stream=input_stream,
            output_stream=output_stream
        )

        # Run the protocol
        manager.run()

        # Check outputs
        output = output_stream.getvalue().strip().split('\n')

        # Should have responses for each command except END
        expected_responses = [
            "OK",           # START 20
            "10,10",        # BEGIN
            "0,0",          # TURN 11,10 -> first empty position
            "1,0",          # TURN 12,10 -> next empty position
            'name="Gomokucaracha", version="6.7", author="Santiago Eliott Paul-Antoine", country="FR"'  # ABOUT
        ]

        assert output == expected_responses

    def test_board_command_flow(self):
        """Test BOARD command with multi-line input"""
        context = MockGameContext()
        context.initialize_board(20, 20)

        input_commands = [
            "BOARD",
            "10,10,1",
            "11,11,2",
            "12,12,1",
            "DONE"
        ]
        input_stream = StringIO("\n".join(input_commands) + "\n")
        output_stream = StringIO()

        manager = CommunicationManager(
            context,
            input_stream=input_stream,
            output_stream=output_stream
        )

        # Process BOARD command
        manager.run()

        output = output_stream.getvalue().strip()
        # Should respond with a move
        assert "," in output  # format: "x,y"

    def test_error_handling(self):
        """Test error handling for invalid commands"""
        context = MockGameContext()

        input_commands = [
            "START invalid_size",
            "TURN invalid_coords",
            "UNKNOWN_COMMAND",
            "END"
        ]
        input_stream = StringIO("\n".join(input_commands) + "\n")
        output_stream = StringIO()

        manager = CommunicationManager(
            context,
            input_stream=input_stream,
            output_stream=output_stream
        )

        manager.run()

        output = output_stream.getvalue().strip().split('\n')

        # Should have error responses for invalid START and TURN, but UNKNOWN_COMMAND is ignored
        assert len(output) == 2
        assert any("ERROR" in line for line in output)
        # No UNKNOWN response since unknown commands are now ignored

    def test_context_integration(self):
        """Test that context methods are called correctly"""
        context = MockGameContext()

        input_commands = ["START 15", "BEGIN", "END"]
        input_stream = StringIO("\n".join(input_commands) + "\n")
        output_stream = StringIO()

        manager = CommunicationManager(
            context,
            input_stream=input_stream,
            output_stream=output_stream
        )

        manager.run()

        # Check that context was initialized
        assert context.board_width == 15
        assert context.board_height == 15
        assert context.board is not None