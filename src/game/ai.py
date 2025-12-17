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
    def __init__(self, max_depth: int = 4, time_limit: float = 5.0, use_iterative_deepening: bool = True):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_iterative_deepening = use_iterative_deepening

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        print(f"Starting search for player {player}, moves: {len(board.get_valid_moves())}", file=sys.stderr)
        if not self.use_iterative_deepening:
            return self._get_best_move_fixed_depth(board, player)

        best_move = [None]  # Use list to modify in thread
        stop_event = threading.Event()

        def search_thread():
            start_time = time.time()
            current_best = None
            current_value = -constants.INFINITY

            moves = board.get_valid_moves()
            if not moves:
                return

            max_depth = self._get_depth(board.move_count)
            current_depth = 1

            while current_depth <= max_depth and not stop_event.is_set():
                print(f"Searching at depth {current_depth}", file=sys.stderr)
                move, value = self._search_at_depth(board, player, current_depth)
                if move is not None:
                    current_best = move
                    current_value = value
                    best_move[0] = current_best
                    print(f"Best move at depth {current_depth}: {current_best}, value: {current_value}", file=sys.stderr)
                current_depth += 1

            elapsed = time.time() - start_time
            print(f"Search thread finished in {elapsed:.2f}s", file=sys.stderr)

        thread = threading.Thread(target=search_thread)
        thread.start()
        thread.join(timeout=self.time_limit)
        stop_event.set()  # Signal to stop
        # Don't wait for thread to finish, return current best
        print(f"Final move: {best_move[0]}", file=sys.stderr)
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
        score = 0
        for y in range(board.height):
            for x in range(board.width):
                if board.grid[y][x] == 1:
                    score += self._evaluate_position(board, x, y, 1)
                elif board.grid[y][x] == 2:
                    score -= self._evaluate_position(board, x, y, 2)
        return score

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