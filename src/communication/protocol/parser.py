##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## parser
##

import re

import constants

from .commands import (
    BoardCommand,
    Command,
    CommandType,
    StartCommand,
    TurnCommand,
)


class ProtocolParser:
    COORDINATE_PATTERN = re.compile(r"^(\d+),(\d+)$")
    BOARD_LINE_PATTERN = re.compile(r"^(\d+),(\d+),([12])$")

    def parse_line(self, line: str) -> Command | None:
        line = line.strip()
        if not line:
            return None
        parts = line.split(maxsplit=1)
        command_str = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""
        try:
            cmd_type = CommandType(command_str)
        except ValueError:
            return Command(CommandType.UNKNOWN, {"raw": line})
        return self._parse_command(cmd_type, args)

    def _parse_command(self, cmd_type: CommandType, args: str) -> Command:
        if cmd_type == CommandType.START:
            return self._parse_start(args)
        elif cmd_type == CommandType.TURN:
            return self._parse_turn(args)
        elif cmd_type == CommandType.BEGIN:
            return Command(CommandType.BEGIN)
        elif cmd_type == CommandType.BOARD:
            return BoardCommand()
        elif cmd_type == CommandType.END:
            return Command(CommandType.END)
        elif cmd_type == CommandType.ABOUT:
            return Command(CommandType.ABOUT)
        elif cmd_type == CommandType.DONE:
            return Command(CommandType.DONE)
        else:
            return Command(CommandType.UNKNOWN, {"raw": f"{cmd_type.value} {args}"})

    def _parse_start(self, args: str) -> StartCommand:
        try:
            size = int(args.strip())
            return StartCommand(size)
        except ValueError as e:
            raise ValueError(f"{constants.INVALID_START_CMD}: {args}") from e

    def _parse_turn(self, args: str) -> TurnCommand:
        match = ProtocolParser.COORDINATE_PATTERN.match(args.strip())
        if not match:
            raise ValueError(f"{constants.INVALID_TURN_CMD}: {args}")
        x = int(match.group(1))
        y = int(match.group(2))
        return TurnCommand(x, y)

    def parse_board_line(self, line: str) -> tuple[int, int, int] | None:
        line = line.strip()
        if line.upper() == constants.DONE_KEYWORD:
            return None
        match = ProtocolParser.BOARD_LINE_PATTERN.match(line)
        if not match:
            raise ValueError(f"{constants.INVALID_BOARD_LINE}: {line}")
        x = int(match.group(1))
        y = int(match.group(2))
        stone_type = int(match.group(3))
        return (x, y, stone_type)
