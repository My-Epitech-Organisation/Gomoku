##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## NegaMax AI with Alpha-Beta pruning and multithreading
##

import time
import concurrent.futures
import copy
from typing import Optional

from .board import Board
from .evaluator import Evaluator
from .constants import FIVE


def evaluate_move(board, move, depth, player, current_player):
    try:
        board = copy.deepcopy(board)
        board.place_stone(move[0], move[1], player)

        ai = NegaMaxAI(max_depth=depth, time_limit=10, use_iterative_deepening=False)
        score = -ai._negamax(board, depth - 1, float('-inf'), float('inf'), player, current_player)

        return move, score
    except Exception as e:
        return move, float('-inf')

class TranspositionTable:
    def __init__(self, max_size: int = 50000):
        self.table = {}
        self.max_size = max_size

    def get_hash(self, board: Board) -> int:
        stones = tuple(
            board.get_stone(x, y)
            for y in range(board.height)
            for x in range(board.width)
        )
        return hash(stones)

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
    def __init__(self, max_depth: int = 5):
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


class NegaMaxAI:
    def __init__(
        self,
        max_depth: int = 5,
        time_limit: float = 4.75,
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

    def find_block_strong_threat(self, board: Board, opponent: int) -> Optional[tuple[int, int]]:
        """Find a move that blocks opponent's strong threats (open 4 or open 3)."""
        threats = []
        for y in range(board.height):
            for x in range(board.width):
                if board.is_empty(x, y):
                    threat = board.get_threat_level(x, y, opponent)
                    if threat >= 3:  # Block open 4 and open 3
                        threats.append((threat, (x, y)))

        if threats:
            threats.sort(reverse=True)
            return threats[0][1]
        return None

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

        block_threat = self.find_block_strong_threat(board, opponent)
        if block_threat:
            return block_threat

        if self.use_iterative_deepening:
            for depth in range(1, self.max_depth + 1):
                if self.is_time_up():
                    break

                try:
                    move, score = self._search_with_depth(board, player, depth)
                    if move:
                        best_move = move

                    if score >= FIVE:
                        break

                except TimeoutError:
                    break
        else:
            best_move, _ = self._search_with_depth(board, player, self.max_depth)

        return best_move

    def _search_with_depth(
        self, board: Board, player: int, depth: int
    ) -> tuple[Optional[tuple[int, int]], float]:
        ordered_moves = self.evaluator.get_strategic_moves(board, player)
        top_moves = ordered_moves[:8]

        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(evaluate_move, board, move, depth, player, 3 - player)
                for move in top_moves
            ]

            results = []
            for future in concurrent.futures.as_completed(futures):
                if self.is_time_up():
                    break
                try:
                    move, score = future.result(timeout=1)
                    results.append((score, move))
                except concurrent.futures.TimeoutError:
                    continue

        if results:
            results.sort(reverse=True)
            return results[0][1], results[0][0]
        else:
            return None, 0

    def _negamax(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        player: int,
        current_player: int,
    ) -> float:

        if self.is_time_up():
            raise TimeoutError("Time limit exceeded")

        cached = self.transposition_table.lookup(board, depth)
        if cached:
            return cached["score"]

        if depth == 0:
            score = self.evaluator.evaluate_board(board, player)
            self.transposition_table.store(board, depth, score)
            return score

        if board.find_winning_move(current_player):
            score = FIVE + depth if current_player == player else -FIVE - depth
            self.transposition_table.store(board, depth, score)
            return score

        moves = self.evaluator.get_strategic_moves(board, current_player, max_moves=12)

        if not moves:
            score = self.evaluator.evaluate_board(board, player)
            self.transposition_table.store(board, depth, score)
            return score

        killer_moves = self.killer_moves.get(depth)
        ordered_moves = []
        for move in killer_moves:
            if move in moves:
                ordered_moves.append(move)
        for move in moves:
            if move not in ordered_moves:
                ordered_moves.append(move)
        moves = ordered_moves

        max_eval = float("-inf")
        for x, y in moves:
            board.place_stone(x, y, current_player)
            eval_score = -self._negamax(
                board, depth - 1, -beta, -alpha, player, 3 - current_player
            )
            board.remove_stone(x, y)

            if eval_score > max_eval:
                max_eval = eval_score

            alpha = max(alpha, eval_score)

            if alpha >= beta:
                self.killer_moves.add(depth, (x, y))
                break

        self.transposition_table.store(board, depth, max_eval)
        return max_eval

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
