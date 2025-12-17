##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Heuristic evaluator for board positions
##

from .board import Board
from .constants import (
    FIVE, OPPONENT_FIVE, OPEN_FOUR, BLOCK_OPEN_FOUR, OPEN_THREE,
    DOUBLE_OPEN_THREE, CLOSED_FOUR, OPEN_TWO, CLOSED_TWO, SINGLE,
    DEFENSE_MULTIPLIER, WIN_PRIORITY, BLOCK_WIN_PRIORITY,
    BLOCK_OPEN4_PRIORITY, OPEN4_PRIORITY, BLOCK_OPEN3_PRIORITY, OPEN3_PRIORITY
)

class Evaluator:

    def evaluate_line(
        self, count: int, open_start: bool, open_end: bool
    ) -> int:
        both_open = open_start and open_end
        one_open = open_start or open_end

        if count >= 5:
            return FIVE
        elif count == 4:
            if both_open:
                return OPEN_FOUR
            elif one_open:
                return CLOSED_FOUR
            return 0
        elif count == 3:
            if both_open:
                return OPEN_THREE
            elif one_open:
                return 100
            return 0
        elif count == 2:
            if both_open:
                return OPEN_TWO
            elif one_open:
                return CLOSED_TWO
            return 0
        elif count == 1:
            if both_open:
                return SINGLE
            return 0
        return 0

    def evaluate_position(self, board: Board, x: int, y: int, player: int) -> int:
        if not board.is_empty(x, y):
            return 0

        score = 0
        board.place_stone(x, y, player)

        for dx, dy in Board.DIRECTIONS:
            count, open_start, open_end = board.count_consecutive(
                x, y, dx, dy, player
            )
            score += self.evaluate_line(count, open_start, open_end)

        board.remove_stone(x, y)
        return score

    def evaluate_board(self, board: Board, player: int) -> int:
        opponent = 3 - player
        player_score = 0
        opponent_score = 0
        player_open_threes = 0
        opponent_open_threes = 0

        if board.find_winning_move(player):
            return FIVE

        if board.find_winning_move(opponent):
            return OPPONENT_FIVE

        for y in range(board.height):
            for x in range(board.width):
                stone = board.get_stone(x, y)
                if stone == Board.EMPTY:
                    continue

                for dx, dy in Board.DIRECTIONS:
                    count, open_start, open_end = board.count_consecutive(
                        x, y, dx, dy, stone
                    )
                    line_score = self.evaluate_line(count, open_start, open_end)

                    if stone == player:
                        player_score += line_score
                        if count == 3 and open_start and open_end:
                            player_open_threes += 1
                    else:
                        opponent_score += line_score
                        if count == 3 and open_start and open_end:
                            opponent_open_threes += 1

        if player_open_threes >= 2:
            player_score += DOUBLE_OPEN_THREE
        if opponent_open_threes >= 2:
            opponent_score += DOUBLE_OPEN_THREE

        return player_score - int(opponent_score * DEFENSE_MULTIPLIER)

    def order_moves(
        self, board: Board, moves: list[tuple[int, int]], player: int
    ) -> list[tuple[int, int]]:
        opponent = 3 - player
        move_scores = []
        critical_moves = []
        high_priority_moves = []

        for x, y in moves:
            player_threat = board.get_threat_level(x, y, player)
            opponent_threat = board.get_threat_level(x, y, opponent)

            if player_threat >= 5:
                return [(x, y)]
            if opponent_threat >= 5:
                critical_moves.append((BLOCK_WIN_PRIORITY, (x, y)))
                continue
            if opponent_threat >= 4:
                high_priority_moves.append((BLOCK_OPEN4_PRIORITY, (x, y)))
                continue
            if player_threat >= 4:
                high_priority_moves.append((OPEN4_PRIORITY, (x, y)))
                continue
            if opponent_threat >= 3:
                score = BLOCK_OPEN3_PRIORITY
            elif player_threat >= 3:
                score = OPEN3_PRIORITY
            else:
                player_score = self.evaluate_position(board, x, y, player)
                opponent_score = self.evaluate_position(board, x, y, opponent)
                score = player_score + opponent_score * 1.2

            move_scores.append((score, (x, y)))

        if critical_moves:
            critical_moves.sort(key=lambda x: x[0], reverse=True)
            return [move for _, move in critical_moves]
        if high_priority_moves:
            high_priority_moves.sort(key=lambda x: x[0], reverse=True)
            move_scores.sort(key=lambda x: x[0], reverse=True)
            return [move for _, move in high_priority_moves] + [move for _, move in move_scores]

        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in move_scores]

    def get_strategic_moves(
        self, board: Board, player: int, max_moves: int = 15
    ) -> list[tuple[int, int]]:
        opponent = 3 - player

        win_move = board.find_winning_move(player)
        if win_move:
            return [win_move]

        block_move = board.find_winning_move(opponent)
        if block_move:
            return [block_move]

        candidates = []
        for y in range(board.height):
            for x in range(board.width):
                if board.is_empty(x, y) and board.has_neighbor(x, y, distance=1):
                    candidates.append((x, y))

        if not candidates:
            center_x = board.width // 2
            center_y = board.height // 2
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    x, y = center_x + dx, center_y + dy
                    if board.is_empty(x, y):
                        candidates.append((x, y))

        ordered = self.order_moves(board, candidates, player)
        return ordered[:max_moves]
