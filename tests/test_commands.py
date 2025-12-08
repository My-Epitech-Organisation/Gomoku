##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for protocol commands
##

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from communication.protocol.commands import (
    CommandType,
    Command,
    StartCommand,
    TurnCommand,
    BoardCommand,
    BoardMove,
)


class TestCommands:
    def test_command_creation(self):
        command = Command(CommandType.START, {"size": 20})
        assert command.type == CommandType.START
        assert command.params["size"] == 20

    def test_command_str_representation(self):
        command = Command(CommandType.START, {"size": 20})
        assert str(command) == "START {'size': 20}"

    def test_start_command(self):
        start_cmd = StartCommand(20)
        assert start_cmd.type == CommandType.START
        assert start_cmd.params["size"] == 20
        assert start_cmd.size() == 20

    def test_turn_command(self):
        turn_cmd = TurnCommand(10, 15)
        assert turn_cmd.type == CommandType.TURN
        assert turn_cmd.params["x"] == 10
        assert turn_cmd.params["y"] == 15
        assert turn_cmd.x() == 10
        assert turn_cmd.y() == 15

    def test_board_command_empty(self):
        board_cmd = BoardCommand()
        assert board_cmd.type == CommandType.BOARD
        assert board_cmd.moves() == []

    def test_board_command_with_moves(self):
        moves = [BoardMove(10, 15, 1), BoardMove(11, 16, 2)]
        board_cmd = BoardCommand(moves)
        assert board_cmd.moves() == moves
        assert board_cmd.num_stones() == 2

    def test_board_command_add_move(self):
        board_cmd = BoardCommand()
        board_cmd.add_move(10, 15, 1)
        assert len(board_cmd.moves()) == 1
        move = board_cmd.moves()[0]
        assert move.x == 10
        assert move.y == 15
        assert move.stone_type == 1

    def test_board_move_creation(self):
        move = BoardMove(5, 8, 2)
        assert move.x == 5
        assert move.y == 8
        assert move.stone_type == 2

    def test_board_move_str_representation(self):
        move = BoardMove(5, 8, 2)
        assert str(move) == "5,8,2"

    def test_command_type_enum_values(self):
        assert CommandType.START.value == "START"
        assert CommandType.TURN.value == "TURN"
        assert CommandType.BEGIN.value == "BEGIN"
        assert CommandType.BOARD.value == "BOARD"
        assert CommandType.END.value == "END"
        assert CommandType.ABOUT.value == "ABOUT"
        assert CommandType.DONE.value == "DONE"
        assert CommandType.UNKNOWN.value == "UNKNOWN"