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


class OpeningBook:
    def __init__(self):
        self.sequences = []
        self._build_book()

    def _add_sequence(self, seq):
        self.sequences.append(seq)

    def _build_book(self):
        sequences = [
            [(-2,9), (-2,8), (0,9), (0,8), (-1,5), (-1,4)],
            [(-9,7), (-7,8), (-8,6), (-6,4), (-8,5)],
            [(0,-3), (0,-4), (0,-7), (1,-4), (-1,-4), (-2,-5), (0,-5), (1,-6), (1,-5)],
            [(7,-10), (9,-8), (6,-10), (9,-7), (5,-10), (9,-6), (9,-5), (4,-10), (7,-8), (5,-6), (7,-6), (5,-5)],
            [(9,-8), (9,-7), (8,-8), (8,-7), (7,-8), (7,-7), (9,-2), (9,-3), (8,-2), (8,-3), (7,-2), (7,-3)],
            [(-8,-8), (-7,-8), (-6,-7), (-6,-6), (-6,-8), (-5,-8)],
            [(-8,-8), (-7,-8), (-5,-7), (-5,-8), (-5,-9), (-4,-5)],
            [(-8,-8), (-7,-8), (-5,-8), (-7,-9), (-7,-10), (-7,-6)],
            [(-9,-9), (-8,-8), (-6,-8), (-7,-7), (-8,-7), (-7,-5)],
            [(-9,-9), (-8,-9), (-6,-8), (-6,-6), (-7,-7), (-5,-7)],
            [(-9,-9), (-8,-10), (-7,-9), (-7,-8), (-6,-8), (-6,-6)],
            [(-9,-9), (-7,-10), (-7,-9), (-8,-8), (-8,-10), (-6,-9)],
        ]
        symmetries = [
            lambda dx, dy: (dy, -dx),      # rotate 90
            lambda dx, dy: (-dx, -dy),     # rotate 180
            lambda dx, dy: (-dy, dx),      # rotate 270
            lambda dx, dy: (dx, -dy),      # mirror horizontal
            lambda dx, dy: (-dx, dy),      # mirror vertical
            lambda dx, dy: (dy, dx),       # mirror diagonal
            lambda dx, dy: (-dy, -dx),     # mirror anti-diagonal
        ]
        for seq in sequences:
            if not seq:
                continue
            relative_seq = [seq[0]]
            for i in range(1, len(seq)):
                dx = seq[i][0] - seq[i-1][0]
                dy = seq[i][1] - seq[i-1][1]
                relative_seq.append((dx, dy))
            self._add_sequence(relative_seq)
            for sym in symmetries:
                sym_seq = [sym(*delta) for delta in relative_seq]
                self._add_sequence(sym_seq)

    def _matches(self, seq, current_moves, tx, ty):
        if len(current_moves) > len(seq):
            return False
        current_x = 10 + tx
        current_y = 10 + ty
        for i, delta in enumerate(seq):
            expected_x = current_x + delta[0]
            expected_y = current_y + delta[1]
            if i < len(current_moves):
                if current_moves[i] != (expected_x, expected_y):
                    return False
            current_x = expected_x
            current_y = expected_y
        return True

    def get_best_move(self, board):
        current_moves = board.moves
        if not current_moves:
            first_moves = {}
            for seq in self.sequences:
                if seq:
                    delta = seq[0]
                    x = 10 + delta[0]
                    y = 10 + delta[1]
                    if 0 <= x < 20 and 0 <= y < 20:
                        key = (x, y)
                        first_moves[key] = first_moves.get(key, 0) + 1
            if first_moves:
                return max(first_moves, key=first_moves.get)
            return None

        next_moves = {}
        for seq in self.sequences:
            for tx in range(-10, 11):
                for ty in range(-10, 11):
                    if self._matches(seq, current_moves, tx, ty):
                        next_index = len(current_moves)
                        if next_index < len(seq):
                            current_x = 10 + tx
                            current_y = 10 + ty
                            for i in range(next_index + 1):
                                delta = seq[i]
                                current_x += delta[0]
                                current_y += delta[1]
                            next_x = current_x
                            next_y = current_y
                            if 0 <= next_x < 20 and 0 <= next_y < 20:
                                key = (next_x, next_y)
                                next_moves[key] = next_moves.get(key, 0) + 1
        if next_moves:
            return max(next_moves, key=next_moves.get)
        return None


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
        self.opening_book = OpeningBook()

    def get_opening_move(self, board) -> Optional[Tuple[int, int]]:
        move = self.opening_book.get_best_move(board)
        if move is not None:
            print(
                f"[AI] Using opening book move: {move[0]},{move[1]}",
                file=sys.stderr,
            )
        return move

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        self.stop_search = False
        self.nodes = 0
        self.age += 1
        best_move = [None]

        opening_move = self.opening_book.get_best_move(board)
        if opening_move is not None:
            print(
                f"[AI] Using opening book move: {opening_move[0]},{opening_move[1]}",
                file=sys.stderr,
            )
            return opening_move

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
                board, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
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
                board, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
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
        self, board, depth: int, alpha: int, beta: int, current_player: int
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
            return self.evaluate(board) * (1 if current_player == 1 else -1)

        max_eval = -constants.INFINITY
        moves = board.get_valid_moves()
        opponent = 3 - current_player
        original_alpha = alpha

        for move in moves:
            board.place_stone(move[0], move[1], current_player)
            eval = -self.negamax(board, depth - 1, -beta, -alpha, opponent)
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

    def _search_at_depth(
        self, board, player: int, depth: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        board_copy = board.copy()
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board_copy.get_valid_moves()
        moves = sorted(
            moves, key=lambda m: -self._move_heuristic(board_copy, m, player)
        )[:12]

        for move in moves:
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
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
