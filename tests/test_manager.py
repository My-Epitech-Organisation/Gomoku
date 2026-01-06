##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for communication manager
##

import sys
import os
from io import StringIO

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communication import CommunicationManager
from communication.protocol.commands import CommandType, Command
from communication.protocol.responses import ResponseType


class MockGameContext:
    def __init__(self):
        self.board = None
        self.initialized = False
        self.opponent_moves = []
        self.best_moves = [(5, 5), (6, 6), (7, 7)]
        self.move_index = 0

    def initialize_board(self, width: int, height: int) -> None:
        self.board = [[0] * width for _ in range(height)]
        self.initialized = True

    def get_opening_move(self) -> tuple[int, int]:
        return (10, 10)

    def process_opponent_move(self, x: int, y: int) -> None:
        self.opponent_moves.append((x, y))

    def get_best_move(self) -> tuple[int, int]:
        move = self.best_moves[self.move_index % len(self.best_moves)]
        self.move_index += 1
        return move

    def process_board(self, moves: list) -> None:
        self.board_moves = moves

    def get_about_info(self) -> dict:
        return {
            "name": "TestBrain",
            "version": "1.0",
            "author": "TestAuthor",
            "country": "FR",
        }


class TestCommunicationManager:
    def setup_method(self):
        self.context = MockGameContext()
        self.input_stream = StringIO()
        self.output_stream = StringIO()
        self.manager = CommunicationManager(
            self.context,
            input_stream=self.input_stream,
            output_stream=self.output_stream
        )

    def test_initialization(self):
        assert self.manager.context == self.context
        assert self.manager.input_stream == self.input_stream
        assert self.manager.output_stream == self.output_stream
        assert not self.manager.running

    def test_send_response(self):
        from communication.protocol.responses import OkResponse
        response = OkResponse()
        self.manager.send_response(response)
        output = self.output_stream.getvalue()
        assert output == "OK\n"

    def test_read_line_valid(self):
        self.input_stream.write("START 20\n")
        self.input_stream.seek(0)
        line = self.manager.read_line()
        assert line == "START 20"

    def test_read_line_empty(self):
        self.input_stream.write("\n")
        self.input_stream.seek(0)
        line = self.manager.read_line()
        assert line == ""

    def test_read_line_eof(self):
        self.input_stream.seek(0)
        line = self.manager.read_line()
        assert line is None

    def test_process_command_end(self):
        command = Command(CommandType.END)
        responses = self.manager.process_command(command)
        assert responses == []
        assert not self.manager.running

    def test_process_command_about(self):
        command = Command(CommandType.ABOUT)
        responses = self.manager.process_command(command)
        assert len(responses) == 1
        response = responses[0]
        assert response.type == ResponseType.OK
        assert 'name="TestBrain"' in response.to_output()

    def test_process_command_start_success(self):
        command = Command(CommandType.START, {"size": 20})
        responses = self.manager.process_command(command)
        assert len(responses) == 1
        assert responses[0].type == ResponseType.OK
        assert self.context.initialized

    def test_process_command_start_no_context_method(self):
        # Create a context without the method to test error handling
        class MockContextNoInit:
            pass
        self.manager.context = MockContextNoInit()
        command = Command(CommandType.START, {"size": 20})
        responses = self.manager.process_command(command)
        assert len(responses) == 1
        assert responses[0].type == ResponseType.ERROR

    def test_process_command_begin_success(self):
        command = Command(CommandType.BEGIN)
        responses = self.manager.process_command(command)
        assert len(responses) == 1
        assert responses[0].type == ResponseType.MOVE
        assert responses[0].data == "10,10"

    def test_process_command_turn_success(self):
        command = Command(CommandType.TURN, {"x": 5, "y": 5})
        responses = self.manager.process_command(command)
        assert len(responses) == 1
        assert responses[0].type == ResponseType.MOVE
        assert responses[0].data == "5,5"
        assert (5, 5) in self.context.opponent_moves

    def test_process_command_board_success(self):
        from communication.protocol.commands import BoardMove, BoardCommand
        moves = [BoardMove(1, 1, 1), BoardMove(2, 2, 2)]
        command = BoardCommand(moves)
        responses = self.manager.process_command(command)
        assert len(responses) == 1
        assert responses[0].type == ResponseType.MOVE
        assert hasattr(self.context, 'board_moves')

    def test_process_command_unknown(self):
        command = Command(CommandType.UNKNOWN)
        responses = self.manager.process_command(command)
        # Unknown commands are now ignored (no response sent)
        assert len(responses) == 0

    def test_read_board_command(self):
        from communication.protocol.commands import BoardCommand
        board_cmd = BoardCommand()

        # Simulate BOARD command input
        input_lines = ["10,10,1", "11,11,2", "DONE"]
        for line in input_lines:
            self.input_stream.write(line + "\n")
        self.input_stream.seek(0)

        result = self.manager.read_board_command(board_cmd)
        assert result == board_cmd
        assert len(board_cmd.moves()) == 2
        assert board_cmd.moves()[0].x == 10
        assert board_cmd.moves()[0].y == 10
        assert board_cmd.moves()[0].stone_type == 1