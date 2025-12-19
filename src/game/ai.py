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
        self.root_player = 1

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        self.stop_search = False
        self.nodes = 0
        self.age += 1
        self.root_player = player
        best_move = [None]

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
            board.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board, depth - 1, -constants.INFINITY, constants.INFINITY, opponent, move, player
            )
            board.undo_stone(move[0], move[1], player)
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
            board.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board, depth - 1, -constants.INFINITY, constants.INFINITY, opponent, move, player
            )
            board.undo_stone(move[0], move[1], player)
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
        self, board, depth: int, alpha: int, beta: int, current_player: int, last_move: Optional[Tuple[int, int]] = None, root_player: int = 1
    ) -> int:
        if self.stop_search:
            return 0
        self.nodes += 1

        hash_key = board.current_hash
        if hash_key in self.transposition_table:
            entry = self.transposition_table[hash_key]
            if entry["age"] == self.age and entry["depth"] >= depth:
                if entry["flag"] == constants.EXACT:
                    return entry["value"]
                elif entry["flag"] == constants.LOWER and entry["value"] >= beta:
                    return entry["value"]
                elif entry["flag"] == constants.UPPER and entry["value"] <= alpha:
                    return entry["value"]

        if depth == 0 or board.is_full():
            return self.evaluate(board, last_move, root_player)

        max_eval = -constants.INFINITY
        moves = board.get_valid_moves()
        opponent = 3 - current_player
        original_alpha = alpha

        for move in moves:
            board.place_stone(move[0], move[1], current_player)
            eval = -self.negamax(board, depth - 1, -beta, -alpha, opponent, move, root_player)
            board.undo_stone(move[0], move[1], current_player)
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
            "value": max_eval,
            "depth": depth,
            "flag": flag,
            "age": self.age,
        }

        return max_eval

    def evaluate(self, board, last_move: Optional[Tuple[int, int]] = None, root_player: int = 1) -> int:
        if last_move is None:
            center_x, center_y = board.width // 2, board.height // 2
            positions = set()
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    x, y = center_x + dx, center_y + dy
                    if 0 <= x < board.width and 0 <= y < board.height:
                        positions.add((x, y))
        else:
            x, y = last_move
            positions = set()
            for dx in range(-4, 5):
                for dy in range(-4, 5):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < board.width and 0 <= ny < board.height:
                        positions.add((nx, ny))

        player_total = 0
        opponent_total = 0
        for x, y in positions:
            if board.grid[y][x] == 1:
                player_total += self._evaluate_position(board, x, y, 1)
            elif board.grid[y][x] == 2:
                opponent_total += self._evaluate_position(board, x, y, 2)

        opponent_player = 3 - root_player
        danger_forced = False
        for x, y in positions:
            if board.grid[y][x] == 0:
                board.place_stone(x, y, opponent_player)
                threat_count = 0
                for dx, dy in constants.DIRECTIONS:
                    line = self._get_line(board, x, y, dx, dy)
                    if self._has_open_three(line, opponent_player):
                        threat_count += 1
                board.undo_stone(x, y, opponent_player)
                if threat_count >= 2:
                    danger_forced = True
                    break

        opponent_split_two_count = 0
        for x, y in positions:
            if board.grid[y][x] == opponent_player:
                count = 0
                for dx, dy in constants.DIRECTIONS:
                    line = self._get_line(board, x, y, dx, dy)
                    if self._has_split_two(line, opponent_player):
                        count += 1
                if count >= 2:
                    opponent_split_two_count += 1

        if danger_forced or opponent_split_two_count > 0:
            return -constants.INFINITY
        else:
            if root_player == 1:
                score = int(
                    constants.ATTACK_MULTIPLIER * player_total
                    - constants.DEFENSE_MULTIPLIER * opponent_total
                )
            else:
                score = int(
                    constants.ATTACK_MULTIPLIER * opponent_total
                    - constants.DEFENSE_MULTIPLIER * player_total
                )
            return score

    def _evaluate_position(self, board, x: int, y: int, player: int) -> int:
        score = 0
        threat_count = 0
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)
            score += self._evaluate_line(line, player)
            if self._has_split_three(line, player):
                threat_count += 1
        if threat_count >= 2:
            score -= 100_000
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

        patterns = constants.PATTERNS[player]

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

    def _has_split_three(self, line: str, player: int) -> bool:
        patterns = constants.PATTERNS[player]["threat"]["split_three"]
        for pat in patterns:
            if pat in line:
                return True
        return False

    def _has_open_three(self, line: str, player: int) -> bool:
        pattern = constants.PATTERNS[player]["threat"]["open_three"]
        return pattern in line

    def _has_split_two(self, line: str, player: int) -> bool:
        p = str(player)
        patterns = [f"{p}.{p}", f"{p}..{p}"]
        return any(pat in line for pat in patterns)

    def _creates_double_open_three(self, board, x, y, player):
        threat_count = 0
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)
            if self._has_open_three(line, player):
                threat_count += 1
        return threat_count >= 2

    def _is_losing_move(self, board, move, player):
        opponent = 3 - player
        board.place_stone(move[0], move[1], player)
        opp_moves = board.get_valid_moves()
        for opp_move in opp_moves:
            board.place_stone(opp_move[0], opp_move[1], opponent)
            if self._creates_double_open_three(board, opp_move[0], opp_move[1], opponent):
                board.undo_stone(opp_move[0], opp_move[1], opponent)
                board.undo_stone(move[0], move[1], player)
                return True
            board.undo_stone(opp_move[0], opp_move[1], opponent)
        board.undo_stone(move[0], move[1], player)
        return False

    def _search_at_depth(
        self, board, player: int, depth: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        board_copy = board.copy()
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board_copy.get_valid_moves()
        if depth <= 2:
            max_moves = 12
        elif depth <= 4:
            max_moves = 8
        else:
            max_moves = 6
        moves = sorted(
            moves, key=lambda m: -self._move_heuristic(board_copy, m, player)
        )[:max_moves]

        moves = [m for m in moves if not self._is_losing_move(board_copy, m, player)]

        for move in moves:
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent, move, self.root_player
            )
            board_copy.undo_stone(move[0], move[1], player)
            if value > best_value:
                best_value = value
                best_move = move

        return best_move, best_value

    def _move_heuristic(self, board, move, player: int) -> int:
        x, y = move
        opponent = 3 - player

        board.place_stone(x, y, player)
        if board.check_win(x, y, player):
            board.undo_stone(x, y, player)
            return constants.MOVE_WIN

        board.undo_stone(x, y, player)
        board.place_stone(x, y, opponent)
        if board.check_win(x, y, opponent):
            board.undo_stone(x, y, opponent)
            return constants.MOVE_BLOCK_WIN

        opp_score = self._evaluate_position(board, x, y, opponent)
        board.undo_stone(x, y, opponent)
        if opp_score >= constants.SCORE_OPEN_FOUR:
            return constants.MOVE_BLOCK_OPEN_FOUR
        elif opp_score >= constants.SCORE_OPEN_THREE:
            return constants.MOVE_BLOCK_OPEN_THREE

        board.place_stone(x, y, player)
        score = self._evaluate_position(board, x, y, player)
        if score >= constants.SCORE_OPEN_FOUR:
            board.undo_stone(x, y, player)
            return constants.MOVE_OPEN_FOUR

        if score >= constants.SCORE_OPEN_THREE:
            board.undo_stone(x, y, player)
            return constants.MOVE_OPEN_THREE

        threat_count = 0
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)
            patterns = constants.PATTERNS[player]
            if patterns["threat"]["open_three"] in line:
                threat_count += 1
        board.undo_stone(x, y, player)
        if threat_count >= 2:
            return constants.MOVE_FORK

        return 0

    def _get_immediate_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        moves = board.get_valid_moves()
        best_move = None
        best_score = -1

        for move in moves:
            score = self._move_heuristic(board, move, player)
            if score > best_score:
                best_score = score
                best_move = move

        if best_score >= constants.MOVE_BLOCK_OPEN_FOUR:
            return best_move

        return None
