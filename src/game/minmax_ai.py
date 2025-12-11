##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Min-Max AI with Alpha-Beta pruning
##

import time
from typing import Optional

from .board import Board
from .evaluator import Evaluator


class TranspositionTable:
    """Cache for board evaluations."""

    def __init__(self, max_size: int = 100000):
        self.table = {}
        self.max_size = max_size

    def get_hash(self, board: Board) -> int:
        hash_val = 0
        for y in range(board.height):
            for x in range(board.width):
                stone = board.get_stone(x, y)
                if stone != Board.EMPTY:
                    hash_val ^= (stone << (y * board.width + x))
        return hash_val

    def store(
        self,
        board: Board,
        depth: int,
        score: float,
        best_move: Optional[tuple[int, int]] = None,
    ) -> None:
        if len(self.table) >= self.max_size:
            keys = list(self.table.keys())
            for key in keys[: len(keys) // 2]:
                del self.table[key]

        hash_val = self.get_hash(board)
        self.table[hash_val] = {
            "depth": depth,
            "score": score,
            "best_move": best_move,
        }

    def lookup(self, board: Board, depth: int) -> Optional[dict]:
        hash_val = self.get_hash(board)
        entry = self.table.get(hash_val)
        if entry and entry["depth"] >= depth:
            return entry
        return None

    def clear(self) -> None:
        self.table.clear()


class KillerMoves:
    """Track moves that cause cutoffs."""

    def __init__(self, max_depth: int = 10):
        self.moves = [[] for _ in range(max_depth)]
        self.max_killers = 2

    def add(self, depth: int, move: tuple[int, int]) -> None:
        if depth >= len(self.moves):
            return
        if move not in self.moves[depth]:
            self.moves[depth].insert(0, move)
            if len(self.moves[depth]) > self.max_killers:
                self.moves[depth].pop()

    def get(self, depth: int) -> list[tuple[int, int]]:
        if depth >= len(self.moves):
            return []
        return self.moves[depth]

    def clear(self) -> None:
        for moves_list in self.moves:
            moves_list.clear()


class MinMaxAI:
    def __init__(
        self,
        max_depth: int = 4,
        time_limit: float = 4.5,
        use_iterative_deepening: bool = True,
    ):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_iterative_deepening = use_iterative_deepening
        self.evaluator = Evaluator()
        self.nodes_searched = 0
        self.transposition_table = TranspositionTable()
        self.killer_moves = KillerMoves(max_depth)
        self.start_time = 0.0

    def is_time_up(self) -> bool:
        return time.time() - self.start_time >= self.time_limit

    def get_best_move(
        self, board: Board, player: int
    ) -> Optional[tuple[int, int]]:
        self.start_time = time.time()
        self.nodes_searched = 0
        self.transposition_table.clear()
        self.killer_moves.clear()

        win_move = board.find_winning_move(player)
        if win_move:
            return win_move

        opponent = 3 - player
        block_move = board.find_winning_move(opponent)
        if block_move:
            return block_move

        best_move = None

        if self.use_iterative_deepening:
            for depth in range(1, self.max_depth + 1):
                if self.is_time_up():
                    break

                try:
                    move, score = self._search_with_depth(board, player, depth)
                    if move:
                        best_move = move

                    if score >= Evaluator.FIVE:
                        break

                except TimeoutError:
                    break
        else:
            best_move, _ = self._search_with_depth(board, player, self.max_depth)

        return best_move

    def _search_with_depth(
        self, board: Board, player: int, depth: int
    ) -> tuple[Optional[tuple[int, int]], float]:
        best_move = None
        alpha = float("-inf")
        beta = float("inf")

        moves = self.evaluator.get_strategic_moves(board, player)

        if not moves:
            return None, 0

        for move in moves:
            if self.is_time_up():
                raise TimeoutError("Time limit exceeded")

            x, y = move
            board.place_stone(x, y, player)
            score = self._minimax(
                board, depth - 1, alpha, beta, False, player, 3 - player
            )
            board.remove_stone(x, y)

            if score > alpha:
                alpha = score
                best_move = move

        return best_move, alpha

    def _minimax(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool,
        player: int,
        current_player: int,
    ) -> float:
        self.nodes_searched += 1

        if self.is_time_up():
            raise TimeoutError("Time limit exceeded")

        # Check transposition table
        cached = self.transposition_table.lookup(board, depth)
        if cached:
            return cached["score"]

        if depth == 0:
            score = self.evaluator.evaluate_board(board, player)
            self.transposition_table.store(board, depth, score)
            return score

        if board.find_winning_move(current_player):
            if current_player == player:
                return Evaluator.FIVE + depth
            else:
                return -Evaluator.FIVE - depth

        moves = self.evaluator.get_strategic_moves(board, current_player, max_moves=12)

        if not moves:
            score = self.evaluator.evaluate_board(board, player)
            self.transposition_table.store(board, depth, score)
            return score

        # Prioritize killer moves
        killer_moves = self.killer_moves.get(depth)
        ordered_moves = []
        for move in killer_moves:
            if move in moves:
                ordered_moves.append(move)
        for move in moves:
            if move not in ordered_moves:
                ordered_moves.append(move)
        moves = ordered_moves

        opponent = 3 - current_player

        if is_maximizing:
            max_eval = float("-inf")
            for x, y in moves:
                board.place_stone(x, y, current_player)
                eval_score = self._minimax(
                    board, depth - 1, alpha, beta, False, player, opponent
                )
                board.remove_stone(x, y)

                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)

                if beta <= alpha:
                    self.killer_moves.add(depth, (x, y))
                    break

            self.transposition_table.store(board, depth, max_eval)
            return max_eval
        else:
            min_eval = float("inf")
            for x, y in moves:
                board.place_stone(x, y, current_player)
                eval_score = self._minimax(
                    board, depth - 1, alpha, beta, True, player, opponent
                )
                board.remove_stone(x, y)

                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)

                if beta <= alpha:
                    self.killer_moves.add(depth, (x, y))
                    break

            self.transposition_table.store(board, depth, min_eval)
            return min_eval

    def get_stats(self) -> dict:
        elapsed_time = time.time() - self.start_time
        nps = (
            int(self.nodes_searched / elapsed_time) if elapsed_time > 0 else 0
        )

        return {
            "nodes_searched": self.nodes_searched,
            "time_elapsed": elapsed_time,
            "nodes_per_second": nps,
        }
