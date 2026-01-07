##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## manager
##

import sys
from typing import Any, Optional, TextIO

import constants
from game import constants as game_constants

from .async_reader import AsyncInputReader
from .protocol.commands import (
    BoardCommand,
    Command,
    CommandType,
)
from .protocol.parser import ProtocolParser
from .protocol.responses import (
    AboutResponse,
    ErrorResponse,
    MoveResponse,
    OkResponse,
    Response,
)


class CommunicationManager:
    def __init__(
        self,
        context: Any,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ):
        self.context = context
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stdout
        self.parser = ProtocolParser()
        self.running = False
        self.async_reader: Optional[AsyncInputReader] = None
        self.ponder_manager = None  # Set by context if pondering enabled
        self.use_async = game_constants.PONDER_ENABLED

    def send_response(self, response: Response) -> None:
        output = response.to_output()
        self.output_stream.write(output + "\n")
        self.output_stream.flush()

    def read_line(self) -> str | None:
        try:
            line = self.input_stream.readline()
            if not line:
                return None
            return line.strip()
        except EOFError:
            return None

    def process_command(self, command: Command) -> list[Response]:
        if command.type == CommandType.END:
            self.running = False
            return []
        elif command.type == CommandType.ABOUT:
            return [self._handle_about()]
        elif command.type == CommandType.START:
            return [self._handle_start(command)]
        elif command.type == CommandType.BEGIN:
            return [self._handle_begin(command)]
        elif command.type == CommandType.TURN:
            return [self._handle_turn(command)]
        elif command.type == CommandType.BOARD:
            return [self._handle_board(command)]
        return []

    def _handle_about(self) -> Response:
        if hasattr(self.context, constants.METHOD_GET_ABOUT_INFO):
            info = self.context.get_about_info()
            return AboutResponse(**info)
        return AboutResponse()

    def _handle_start(self, command: Command) -> Response:
        try:
            size = command.params[constants.PARAM_SIZE]
            if size <= 0:
                return ErrorResponse("Invalid board size")
            if hasattr(self.context, constants.METHOD_INITIALIZE_BOARD):
                self.context.initialize_board(size, size)
                return OkResponse()
            return ErrorResponse(constants.CONTEXT_NO_INIT)
        except Exception as e:
            return ErrorResponse(f"{constants.INITIALIZATION_FAILED}: {str(e)}")

    def _handle_begin(self, command: Command) -> Response:
        try:
            if hasattr(self.context, constants.METHOD_GET_OPENING_MOVE):
                x, y = self.context.get_opening_move()
                return MoveResponse(x, y)
            return ErrorResponse(constants.CONTEXT_NO_OPENING)
        except Exception as e:
            return ErrorResponse(f"{constants.OPENING_MOVE_FAILED}: {str(e)}")

    def _handle_turn(self, command: Command) -> Response:
        try:
            x = command.params[constants.PARAM_X]
            y = command.params[constants.PARAM_Y]

            # Check for ponder hit before processing
            ponder_result = None
            if self.ponder_manager is not None:
                ponder_result = self.ponder_manager.on_opponent_move(x, y)

            if hasattr(self.context, constants.METHOD_PROCESS_OPPONENT_MOVE):
                self.context.process_opponent_move(x, y)

            if ponder_result is not None:
                # Ponder hit - use cached result but wait until deadline for consistency
                import time
                ponder_start = time.time()
                move_x, move_y = ponder_result
                if hasattr(self.context, "board") and self.context.board is not None:
                    self.context.board.place_stone(move_x, move_y, self.context.player_stone)
                    # Use remaining time for TT warming (BLOCKING until deadline)
                    if self.context.ai is not None and game_constants.TIME_BANK_ENABLED:
                        import threading
                        board_copy = self.context.board.copy()
                        player = self.context.player_stone

                        def blocking_warm():
                            self.context.ai._warm_tt_background(board_copy, player)

                        thread = threading.Thread(target=blocking_warm, daemon=True)
                        thread.start()

                        # Wait until deadline (use full time like normal moves)
                        elapsed = time.time() - ponder_start
                        remaining = game_constants.RESPONSE_DEADLINE - elapsed - 0.1
                        if remaining > 0:
                            time.sleep(remaining)

                        # Stop the warming thread
                        self.context.ai.stop_search = True
                        thread.join(timeout=0.05)
            elif hasattr(self.context, constants.METHOD_GET_BEST_MOVE):
                move_x, move_y = self.context.get_best_move()
            else:
                return ErrorResponse(constants.CONTEXT_NO_MOVE_GEN)

            # Start pondering for next turn
            if self.ponder_manager is not None and hasattr(self.context, "board"):
                self.ponder_manager.start_pondering(
                    self.context.board,
                    (move_x, move_y),
                    self.context.player_stone
                )

            return MoveResponse(move_x, move_y)
        except Exception as e:
            return ErrorResponse(f"{constants.MOVE_GENERATION_FAILED}: {str(e)}")

    def _handle_board(self, command: Command) -> Response:
        try:
            if hasattr(self.context, constants.METHOD_PROCESS_BOARD):
                self.context.process_board(command.moves())
            if hasattr(self.context, constants.METHOD_GET_BEST_MOVE):
                move_x, move_y = self.context.get_best_move()
                return MoveResponse(move_x, move_y)
            return ErrorResponse(constants.CONTEXT_NO_MOVE_GEN)
        except Exception as e:
            return ErrorResponse(f"{constants.BOARD_PROCESSING_FAILED}: {str(e)}")

    def read_board_command(self, board_cmd: BoardCommand) -> BoardCommand:
        while True:
            line = self.read_line()
            if line is None:
                break
            result = self.parser.parse_board_line(line)
            if result is None:
                break
            x, y, stone_type = result
            board_cmd.add_move(x, y, stone_type)
        return board_cmd

    def run(self) -> None:
        self.running = True

        # Initialize async reader if pondering is enabled
        if self.use_async:
            self.async_reader = AsyncInputReader(self.input_stream)
            self.async_reader.start()

        while self.running:
            line = self._get_next_line()
            if line is None:
                break
            try:
                command = self.parser.parse_line(line)
                if command is None:
                    continue
                if command.type == CommandType.BOARD:
                    command = self.read_board_command(command)
                responses = self.process_command(command)
                for response in responses:
                    self.send_response(response)
            except ValueError as e:
                self.send_response(ErrorResponse(f"{constants.PARSE_ERROR}: {str(e)}"))
            except Exception as e:
                self.send_response(
                    ErrorResponse(f"{constants.UNEXPECTED_ERROR}: {str(e)}")
                )

        # Cleanup
        if self.async_reader is not None:
            self.async_reader.stop()

    def _get_next_line(self) -> Optional[str]:
        """Get next line, using async reader if enabled."""
        if self.use_async and self.async_reader is not None:
            # Poll with timeout to allow pondering to continue
            while self.running:
                line = self.async_reader.get_line(
                    timeout=game_constants.PONDER_POLL_INTERVAL
                )
                if line is not None:
                    return line
                # No input yet - pondering continues in background
            return None
        else:
            return self.read_line()
