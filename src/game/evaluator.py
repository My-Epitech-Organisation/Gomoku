##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Heuristic evaluator for board positions
##

from .board import Board
from .constants import (
    FIVE_IN_ROW, OPEN_FOUR, CLOSED_FOUR,
    OPEN_THREE, DOUBLE_OPEN_THREE, CLOSED_THREE,
    OPEN_TWO, CLOSED_TWO, SINGLE,
    DEFENSE_MULTIPLIER, THREAT_LEVEL_WIN, THREAT_LEVEL_OPEN_FOUR,
    THREAT_LEVEL_CLOSED_FOUR, THREAT_LEVEL_OPEN_THREE,
    MAX_CANDIDATE_MOVES
)

class Evaluator:

    def evaluate_line(
        self, count: int, open_start: bool, open_end: bool
    ) -> int:
        both_open = open_start and open_end
        one_open = open_start or open_end

        if count >= 5:
            return FIVE_IN_ROW
        elif count == 4:
            return OPEN_FOUR if both_open else (CLOSED_FOUR if one_open else 0)
        elif count == 3:
            return OPEN_THREE if both_open else (CLOSED_THREE if one_open else 0)
        elif count == 2:
            return OPEN_TWO if both_open else (CLOSED_TWO if one_open else 0)
        elif count == 1:
            return SINGLE if both_open else 0
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
        player_open_fours = 0
        opponent_open_fours = 0

        if board.find_winning_move(player):
            return FIVE_IN_ROW

        if board.find_winning_move(opponent):
            return -FIVE_IN_ROW

        for y in range(board.height):
            for x in range(board.width):
                stone = board.get_stone(x, y)
                if stone == Board.EMPTY:
                    continue

                for dx, dy in Board.DIRECTIONS:
                    count, open_start, open_end = board.count_consecutive(
                        x, y, dx, dy, stone
                    )
                    both_open = open_start and open_end
                    line_score = self.evaluate_line(count, open_start, open_end)

                    if stone == player:
                        player_score += line_score
                        if count == 4 and both_open:
                            player_open_fours += 1
                        elif count == 3 and both_open:
                            player_open_threes += 1
                    else:
                        opponent_score += line_score
                        if count == 4 and both_open:
                            opponent_open_fours += 1
                        elif count == 3 and both_open:
                            opponent_open_threes += 1

        if player_open_threes >= 2:
            player_score += DOUBLE_OPEN_THREE
        if opponent_open_threes >= 2:
            opponent_score += DOUBLE_OPEN_THREE

        if opponent_open_fours > 0:
            opponent_score += OPEN_FOUR * 3

        if opponent_open_threes > 0:
            opponent_score += OPEN_THREE * 10

        return player_score - int(opponent_score * DEFENSE_MULTIPLIER)

    def order_moves(
        self, board: Board, moves: list[tuple[int, int]], player: int
    ) -> list[tuple[int, int]]:
        opponent = 3 - player
        move_scores = []

        for x, y in moves:
            player_threat = board.get_threat_level(x, y, player)
            opponent_threat = board.get_threat_level(x, y, opponent)

            if player_threat >= THREAT_LEVEL_WIN:
                return [(x, y)]

            score = self._calculate_move_score(
                board, x, y, player, opponent, player_threat, opponent_threat
            )
            move_scores.append((score, (x, y)))

        move_scores.sort(key=lambda x: x[0], reverse=True)
        return [move for _, move in move_scores]

    def _calculate_move_score(
        self,
        board: Board,
        x: int,
        y: int,
        player: int,
        opponent: int,
        player_threat: int,
        opponent_threat: int
    ) -> float:
        if player_threat >= THREAT_LEVEL_WIN:
            return 10_000_000_000

        if opponent_threat >= THREAT_LEVEL_WIN:
            return 9_000_000_000

        if opponent_threat >= THREAT_LEVEL_OPEN_FOUR:
            return 5_000_000_000

        if player_threat >= THREAT_LEVEL_OPEN_FOUR:
            return 4_000_000_000

        if opponent_threat >= THREAT_LEVEL_OPEN_THREE:
            return 1_000_000_000

        if player_threat >= THREAT_LEVEL_OPEN_THREE:
            return 500_000_000

        if opponent_threat >= THREAT_LEVEL_CLOSED_FOUR:
            return 100_000_000

        if player_threat >= THREAT_LEVEL_CLOSED_FOUR:
            return 50_000_000

        player_score = self.evaluate_position(board, x, y, player)
        opponent_score = self.evaluate_position(board, x, y, opponent)

        return player_score + opponent_score * DEFENSE_MULTIPLIER

    def get_strategic_moves(
        self, board: Board, player: int, max_moves: int = MAX_CANDIDATE_MOVES
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
