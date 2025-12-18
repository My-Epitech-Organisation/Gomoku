##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## ai
##

import sys
import threading
import time
from typing import Optional, Tuple

from . import constants


class MinMaxAI:
    def __init__(
        self,
        max_depth: int = constants.MAX_DEPTH,
        time_limit: float = constants.TIME_LIMIT,
        use_iterative_deepening: bool = True,
    ):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_iterative_deepening = use_iterative_deepening
        self.stop_search = False
        self.nodes = 0
        self.transposition_table = {}
        self.age = 0

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        self.stop_search = False
        self.nodes = 0
        self.age += 1
        best_move = [None]

        # Check for immediate threats before search
        immediate_move = self._get_immediate_move(board, player)
        if immediate_move is not None:
            return immediate_move

        def search_thread():
            start_time = time.time()
            current_best = None

            moves = board.get_valid_moves()
            if not moves:
                return

            current_depth = 1

            while not self.stop_search:
                move, value = self._search_at_depth(board, player, current_depth)
                if move is not None:
                    current_best = move
                    best_move[0] = current_best
                current_depth += 1

            elapsed = time.time() - start_time
            print(
                f"[AI] Stats: depth {current_depth-1}, nodes {self.nodes}, "
                f"time {elapsed:.2f}s",
                file=sys.stderr,
            )

        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()
        time.sleep(self.time_limit)
        self.stop_search = True
        return best_move[0]

    def _get_best_move_fixed_depth(
        self, board, player: int
    ) -> Optional[Tuple[int, int]]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()
        if not moves:
            return None

        depth = self._get_depth(board.move_count)

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
            )
            if value > best_value:
                best_value = value
                best_move = move

        return best_move

    def _search_at_depth(
        self, board, player: int, depth: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
            )
            if value > best_value:
                best_value = value
                best_move = move

        return best_move, best_value

    def _get_depth(self, move_count: int) -> int:
        if move_count < 10:
            return constants.DEPTH_EARLY
        elif move_count < 30:
            return constants.DEPTH_MID
        else:
            return constants.DEPTH_LATE

    def negamax(
        self, board, depth: int, alpha: int, beta: int, current_player: int
    ) -> int:
        if self.stop_search:
            return 0
        self.nodes += 1

        hash_key = board.current_hash
        if hash_key in self.transposition_table:
            entry = self.transposition_table[hash_key]
            if entry['age'] == self.age and entry['depth'] >= depth:
                if entry['flag'] == constants.EXACT:
                    return entry['value']
                elif entry['flag'] == constants.LOWER and entry['value'] >= beta:
                    return entry['value']
                elif entry['flag'] == constants.UPPER and entry['value'] <= alpha:
                    return entry['value']

        if depth == 0 or board.is_full():
            return self.evaluate(board) * (1 if current_player == 1 else -1)

        max_eval = -constants.INFINITY
        moves = board.get_valid_moves()
        opponent = 3 - current_player
        original_alpha = alpha

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], current_player)
            eval = -self.negamax(board_copy, depth - 1, -beta, -alpha, opponent)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if alpha >= beta:
                break

        if max_eval <= original_alpha:
            flag = constants.UPPER
        elif max_eval >= beta:
            flag = constants.LOWER
        else:
            flag = constants.EXACT
        self.transposition_table[hash_key] = {
            'value': max_eval,
            'depth': depth,
            'flag': flag,
            'age': self.age
        }

        return max_eval

    def evaluate(self, board) -> int:
        player_total = 0
        opponent_total = 0
        for y in range(board.height):
            for x in range(board.width):
                if board.grid[y][x] == 1:
                    player_total += self._evaluate_position(board, x, y, 1)
                elif board.grid[y][x] == 2:
                    opponent_total += self._evaluate_position(board, x, y, 2)
        return int(
            constants.ATTACK_MULTIPLIER * player_total
            - constants.DEFENSE_MULTIPLIER * opponent_total
        )

    def _evaluate_position(self, board, x: int, y: int, player: int) -> int:
        score = 0
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)
            score += self._evaluate_line(line, player)
        return score

    def _get_line(self, board, x: int, y: int, dx: int, dy: int) -> str:
        line = []
        for i in range(-4, 5):
            nx, ny = x + i * dx, y + i * dy
            if 0 <= nx < board.width and 0 <= ny < board.height:
                stone = board.grid[ny][nx]
                line.append(str(stone) if stone != 0 else ".")
            else:
                line.append("#")
        return "".join(line)

    def _evaluate_line(self, line: str, player: int) -> int:
        player_str = str(player)

        patterns = constants.get_patterns(player)

        score = 0

        if patterns["winning"]["five"] in line:
            score += constants.SCORE_FIVE
        if patterns["winning"]["open_four"] in line:
            score += constants.SCORE_OPEN_FOUR
        for pat in patterns["winning"]["closed_four"]:
            if pat in line:
                score += constants.SCORE_CLOSED_FOUR
                break
        for pat in patterns["winning"]["split_four"]:
            if pat in line:
                score += constants.SCORE_SPLIT_FOUR
                break

        if patterns["threat"]["open_three"] in line:
            score += constants.SCORE_OPEN_THREE
        for pat in patterns["threat"]["closed_three"]:
            if pat in line:
                score += constants.SCORE_CLOSED_THREE
                break
        for pat in patterns["threat"]["split_three"]:
            if pat in line:
                score += constants.SCORE_SPLIT_THREE
                break
        for pat in patterns["threat"]["broken_open_three"]:
            if pat in line:
                score += constants.SCORE_BROKEN_THREE
                break

        if patterns["development"]["open_two"] in line:
            score += constants.SCORE_OPEN_TWO
        for pat in patterns["development"]["closed_two"]:
            if pat in line:
                score += constants.SCORE_CLOSED_TWO
                break

        return score

    def _search_at_depth(
        self, board, player: int, depth: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()
        moves = sorted(moves, key=lambda m: -self._move_heuristic(board, m, player))[
            :12
        ]

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
            )
            if value > best_value:
                best_value = value
                best_move = move

        return best_move, best_value

    def _move_heuristic(self, board, move, player: int) -> int:
        x, y = move
        opponent = 3 - player

        board_copy = board.copy()
        board_copy.place_stone(x, y, player)
        if board_copy.check_win(x, y, player):
            return constants.MOVE_WIN

        board_opp = board.copy()
        board_opp.place_stone(x, y, opponent)
        if board_opp.check_win(x, y, opponent):
            return constants.MOVE_BLOCK_WIN

        score = self._evaluate_position(board_copy, x, y, player)
        if score >= constants.SCORE_OPEN_FOUR:
            return constants.MOVE_OPEN_FOUR

        if score >= constants.SCORE_OPEN_THREE:
            return constants.MOVE_OPEN_THREE

        threat_count = 0
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board_copy, x, y, dx, dy)
            patterns = constants.get_patterns(player)
            if patterns["threat"]["open_three"] in line:
                threat_count += 1
        if threat_count >= 2:
            return constants.MOVE_FORK

        return self.evaluate(board_copy)

    def _get_immediate_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        opponent = 3 - player
        moves = board.get_valid_moves()

        for move in moves:
            x, y = move
            board_copy = board.copy()
            board_copy.place_stone(x, y, player)
            if board_copy.check_win(x, y, player):
                return move

        for move in moves:
            x, y = move
            board_opp = board.copy()
            board_opp.place_stone(x, y, opponent)
            if board_opp.check_win(x, y, opponent):
                return move

        return None
