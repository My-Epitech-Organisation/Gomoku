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
from .constants import (
    FIVE_IN_ROW, THREAT_LEVEL_OPEN_FOUR, THREAT_LEVEL_OPEN_THREE, THREAT_LEVEL_OPEN_TWO,
    DEFAULT_TIME_LIMIT, DEFAULT_MAX_DEPTH, TT_MAX_SIZE,
    MAX_KILLER_MOVES, TOP_MOVES_PARALLEL, MAX_MOVES_PER_DEPTH,
    PARALLEL_WORKERS, PARALLEL_TIMEOUT
)


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
    def __init__(self, max_size: int = TT_MAX_SIZE):
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
    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH):
        self.moves = [[] for _ in range(max_depth)]
        self.max_killers = MAX_KILLER_MOVES

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
        max_depth: int = DEFAULT_MAX_DEPTH,
        time_limit: float = DEFAULT_TIME_LIMIT,
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

        opponent = 3 - player

        win_move = board.find_winning_move(player)
        if win_move:
            return win_move

        block_win = board.find_winning_move(opponent)
        if block_win:
            return block_win

        for y in range(board.height):
            for x in range(board.width):
                if board.is_empty(x, y):
                    opp_threat = board.get_threat_level(x, y, opponent)
                    if opp_threat >= THREAT_LEVEL_OPEN_THREE:
                        our_threat = board.get_threat_level(x, y, player)
                        if our_threat >= THREAT_LEVEL_OPEN_FOUR:
                            continue

                        if opp_threat >= THREAT_LEVEL_OPEN_FOUR:
                            return (x, y)

        for y in range(board.height):
            for x in range(board.width):
                if board.is_empty(x, y):
                    our_threat = board.get_threat_level(x, y, player)
                    if our_threat >= THREAT_LEVEL_OPEN_FOUR:
                        return (x, y)

        opponent_crosses = board.find_cross_patterns(opponent)
        if opponent_crosses:
            strongest_cross = opponent_crosses[0]
            if strongest_cross[2] >= 2:
                return (strongest_cross[0], strongest_cross[1])

        opponent_t_patterns = board.find_t_patterns(opponent)
        if opponent_t_patterns:
            return opponent_t_patterns[0]

        best_defense = None
        highest_opp_threat = 0
        for y in range(board.height):
            for x in range(board.width):
                if board.is_empty(x, y):
                    opp_threat = board.get_threat_level(x, y, opponent)
                    if opp_threat > highest_opp_threat:
                        highest_opp_threat = opp_threat
                        best_defense = (x, y)

        if highest_opp_threat >= THREAT_LEVEL_OPEN_THREE:
            return best_defense

        if board.is_defensive_mode() and highest_opp_threat >= THREAT_LEVEL_OPEN_TWO:
            return best_defense

        best_move = None
        best_score = float('-inf')

        if self.use_iterative_deepening:
            for depth in range(1, self.max_depth + 1):
                if self.is_time_up():
                    break

                try:
                    move, score = self._search_with_depth(board, player, depth)
                    if move:
                        best_move = move
                        best_score = score

                    if score >= FIVE_IN_ROW - 100:
                        break

                except TimeoutError:
                    break
        else:
            best_move, best_score = self._search_with_depth(board, player, self.max_depth)

        return best_move

    def _search_with_depth(
        self, board: Board, player: int, depth: int
    ) -> tuple[Optional[tuple[int, int]], float]:
        ordered_moves = self.evaluator.get_strategic_moves(board, player)

        num_moves = min(len(ordered_moves), TOP_MOVES_PARALLEL + depth)
        top_moves = ordered_moves[:num_moves]

        with concurrent.futures.ProcessPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            futures = [
                executor.submit(evaluate_move, board, move, depth, player, 3 - player)
                for move in top_moves
            ]

            results = []
            for future in concurrent.futures.as_completed(futures):
                if self.is_time_up():
                    break
                try:
                    move, score = future.result(timeout=PARALLEL_TIMEOUT)
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
            score = FIVE_IN_ROW + depth if current_player == player else -FIVE_IN_ROW - depth
            self.transposition_table.store(board, depth, score)
            return score

        moves = self.evaluator.get_strategic_moves(board, current_player, max_moves=MAX_MOVES_PER_DEPTH)

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
