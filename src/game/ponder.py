##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Ponder Manager - Background calculation during opponent's turn
##

import threading
from typing import TYPE_CHECKING, Dict, Optional, Tuple

from . import constants

if TYPE_CHECKING:
    from .ai import MinMaxAI
    from .board import Board


class PonderManager:
    """
    Manages pondering (thinking during opponent's turn).

    After we make a move, we predict the opponent's likely responses
    and search those positions in background threads. When the opponent
    makes their move, if it matches one of our predictions (ponder hit),
    we can return the cached result immediately.
    """

    def __init__(self, ai: "MinMaxAI"):
        self.ai = ai
        self.predictions: Dict[Tuple[int, int], Tuple[int, int]] = {}
        self.lock = threading.Lock()
        self.pondering = False
        self.stop_flag = False
        self.threads: list[threading.Thread] = []

    def start_pondering(
        self,
        board: "Board",
        our_move: Tuple[int, int],
        player: int
    ) -> None:
        """
        Start pondering after we play our move.

        Args:
            board: Current board state (after our move is placed)
            our_move: The move we just played
            player: Our player number (1 or 2)
        """
        if not constants.PONDER_ENABLED:
            return

        self.stop_pondering()

        with self.lock:
            self.predictions.clear()
            self.pondering = True
            self.stop_flag = False

        opponent = 3 - player

        # Get top predicted opponent moves
        predicted_moves = self.ai._get_top_opponent_moves(
            board, opponent, constants.PONDER_PREDICTIONS
        )

        # Start background search for each prediction
        self.threads = []
        for pred_move in predicted_moves:
            thread = threading.Thread(
                target=self._ponder_position,
                args=(board.copy(), pred_move, opponent, player),
                daemon=True
            )
            self.threads.append(thread)
            thread.start()

    def _ponder_position(
        self,
        board: "Board",
        opponent_move: Tuple[int, int],
        opponent: int,
        player: int
    ) -> None:
        """
        Search a predicted position in background.

        Args:
            board: Board copy to work on
            opponent_move: Predicted opponent move
            opponent: Opponent player number
            player: Our player number
        """
        try:
            if self.stop_flag:
                return

            # Place predicted opponent move
            x, y = opponent_move
            if not board.place_stone(x, y, opponent):
                return

            if self.stop_flag:
                return

            # Search for our best response
            # Use shallow depth for speed, but with TT warming
            original_depth = self.ai.max_depth
            self.ai.max_depth = constants.PONDER_MAX_DEPTH

            best_move = self.ai.get_best_move(board, player)

            self.ai.max_depth = original_depth

            if self.stop_flag:
                return

            # Store result
            if best_move is not None:
                with self.lock:
                    if self.pondering:
                        self.predictions[opponent_move] = best_move

        except Exception:
            pass  # Silently ignore errors in background thread

    def on_opponent_move(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        Called when opponent makes their move.

        Args:
            x, y: Opponent's move coordinates

        Returns:
            Our cached response if ponder hit, None otherwise
        """
        self.stop_pondering()

        with self.lock:
            result = self.predictions.get((x, y))
            self.predictions.clear()
            return result

    def stop_pondering(self) -> None:
        """Stop all pondering threads."""
        self.stop_flag = True

        with self.lock:
            self.pondering = False

        # Signal AI to stop search
        if hasattr(self.ai, 'stop_search'):
            self.ai.stop_search = True

        # Wait briefly for threads to finish
        for thread in self.threads:
            thread.join(timeout=0.05)

        self.threads = []

    def is_pondering(self) -> bool:
        """Check if currently pondering."""
        with self.lock:
            return self.pondering
