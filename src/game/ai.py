##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## ai
##

import time
import sys
import threading
from typing import Tuple, Optional
from . import constants


class MinMaxAI:
    def __init__(self, max_depth: int = constants.MAX_DEPTH, time_limit: float = constants.TIME_LIMIT, use_iterative_deepening: bool = True):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_iterative_deepening = use_iterative_deepening
        self.stop_search = False
        self.aggressive = True
        self.nodes = 0

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        self.aggressive = (board.move_count == 0)
        self.stop_search = False
        self.nodes = 0
        best_move = [None]  # Use list to modify in thread

        def search_thread():
            start_time = time.time()
            current_best = None
            current_value = -constants.INFINITY

            moves = board.get_valid_moves()
            if not moves:
                return

            current_depth = 1

            while not self.stop_search:
                move, value = self._search_at_depth(board, player, current_depth)
                if move is not None:
                    current_best = move
                    current_value = value
                    best_move[0] = current_best
                current_depth += 1

            elapsed = time.time() - start_time
            print(f"[AI] Stats: depth {current_depth-1}, nodes {self.nodes}, time {elapsed:.2f}s, aggressive {self.aggressive}", file=sys.stderr)

        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()
        time.sleep(self.time_limit)
        self.stop_search = True
        return best_move[0]

    def _get_best_move_fixed_depth(self, board, player: int) -> Optional[Tuple[int, int]]:
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
            value = -self.negamax(board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent)
            if value > best_value:
                best_value = value
                best_move = move

        return best_move

    def _search_at_depth(self, board, player: int, depth: int) -> Tuple[Optional[Tuple[int, int]], int]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent)
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

    def negamax(self, board, depth: int, alpha: int, beta: int, current_player: int) -> int:
        if self.stop_search:
            return 0
        self.nodes += 1
        if depth == 0 or board.is_full():
            return self.evaluate(board) * (1 if current_player == 1 else -1)

        max_eval = -constants.INFINITY
        moves = board.get_valid_moves()
        opponent = 3 - current_player

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], current_player)
            eval = -self.negamax(board_copy, depth - 1, -beta, -alpha, opponent)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if alpha >= beta:
                break

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
        if self.aggressive:
            return int(constants.ATTACK_MULTIPLIER_AGGRESSIVE * player_total - constants.DEFENSE_MULTIPLIER_AGGRESSIVE * opponent_total)
        else:
            return int(constants.ATTACK_MULTIPLIER_DEFENSIVE * player_total - constants.DEFENSE_MULTIPLIER_DEFENSIVE * opponent_total)

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
                line.append(str(stone) if stone != 0 else '.')
            else:
                line.append('#')  # Wall
        return ''.join(line)

    def _evaluate_line(self, line: str, player: int) -> int:
        player_str = str(player)
        opponent_str = str(3 - player)

        # Patterns for the player
        patterns = {
            'five': player_str * 5,
            'open_four': f'.{player_str * 4}.',
            'closed_four': [f'{player_str * 4}.', f'.{player_str * 4}', f'{player_str * 3}.{player_str}', f'{player_str * 2}.{player_str * 2}'],
            'open_three': f'.{player_str * 3}.',
            'closed_three': [f'{player_str * 3}.', f'.{player_str * 3}', f'{player_str * 2}.{player_str}', f'{player_str}.{player_str * 2}'],
            'open_two': f'.{player_str * 2}.',
            'closed_two': [f'{player_str * 2}.', f'.{player_str * 2}', f'{player_str}.{player_str}']
        }

        score = 0
        if patterns['five'] in line:
            score += constants.SCORE_FIVE
        if patterns['open_four'] in line:
            score += constants.SCORE_OPEN_FOUR
        for pat in patterns['closed_four']:
            if pat in line:
                score += constants.SCORE_CLOSED_FOUR
                break
        if patterns['open_three'] in line:
            score += constants.SCORE_OPEN_THREE
        for pat in patterns['closed_three']:
            if pat in line:
                score += constants.SCORE_CLOSED_THREE
                break
        if patterns['open_two'] in line:
            score += constants.SCORE_OPEN_TWO
        for pat in patterns['closed_two']:
            if pat in line:
                score += constants.SCORE_CLOSED_TWO
                break

        return score

    def _search_at_depth(self, board, player: int, depth: int) -> Tuple[Optional[Tuple[int, int]], int]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()
        # Move ordering: sort by heuristic score
        moves = sorted(moves, key=lambda m: -self._move_heuristic(board, m, player))[:20]  # Top 20

        for move in moves:
            board_copy = board.copy()
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent)
            if value > best_value:
                best_value = value
                best_move = move

        return best_move, best_value

    def _move_heuristic(self, board, move, player: int) -> int:
        board_copy = board.copy()
        board_copy.place_stone(move[0], move[1], player)
        return self.evaluate(board_copy)