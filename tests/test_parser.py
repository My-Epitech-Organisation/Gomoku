##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for protocol parser
##

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communication.protocol.parser import ProtocolParser
from communication.protocol.commands import CommandType, StartCommand, TurnCommand, BoardCommand


class TestProtocolParser:
    def setup_method(self):
        self.parser = ProtocolParser()

    def test_parse_start_valid(self):
        command = self.parser.parse_line("START 20")
        assert isinstance(command, StartCommand)
        assert command.params["size"] == 20

    def test_parse_start_invalid_size(self):
        with pytest.raises(ValueError, match="Invalid START"):
            self.parser.parse_line("START abc")

    def test_parse_turn_valid(self):
        command = self.parser.parse_line("TURN 10,15")
        assert isinstance(command, TurnCommand)
        assert command.params["x"] == 10
        assert command.params["y"] == 15

    def test_parse_turn_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid TURN"):
            self.parser.parse_line("TURN 10 15")

    def test_parse_turn_invalid_coords(self):
        with pytest.raises(ValueError, match="Invalid TURN"):
            self.parser.parse_line("TURN abc,def")

    def test_parse_begin(self):
        command = self.parser.parse_line("BEGIN")
        assert command.type == CommandType.BEGIN

    def test_parse_board(self):
        command = self.parser.parse_line("BOARD")
        assert isinstance(command, BoardCommand)
        assert command.moves() == []

    def test_parse_about(self):
        command = self.parser.parse_line("ABOUT")
        assert command.type == CommandType.ABOUT

    def test_parse_end(self):
        command = self.parser.parse_line("END")
        assert command.type == CommandType.END

    def test_parse_unknown_command(self):
        command = self.parser.parse_line("INVALID_COMMAND")
        assert command.type == CommandType.UNKNOWN

    def test_parse_empty_line(self):
        command = self.parser.parse_line("")
        assert command is None

    def test_parse_whitespace_line(self):
        command = self.parser.parse_line("   ")
        assert command is None

    def test_parse_board_line_valid(self):
        result = self.parser.parse_board_line("10,15,1")
        assert result == (10, 15, 1)

    def test_parse_board_line_done(self):
        result = self.parser.parse_board_line("DONE")
        assert result is None

    def test_parse_board_line_done_case_insensitive(self):
        result = self.parser.parse_board_line("done")
        assert result is None

    def test_parse_board_line_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid board line"):
            self.parser.parse_board_line("10,15")

    def test_parse_board_line_invalid_coords(self):
        with pytest.raises(ValueError, match="Invalid board line"):
            self.parser.parse_board_line("abc,def,1")

    def test_parse_board_line_invalid_stone_type(self):
        with pytest.raises(ValueError, match="Invalid board line"):
            self.parser.parse_board_line("10,15,3")