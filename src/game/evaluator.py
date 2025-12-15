##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Heuristic evaluator for board positions
##

from .board import Board


class Evaluator:
    FIVE = 100000000        # Win - absolute priority
    FOUR = 10000000         # Four in a row (immediate threat)
    OPEN_THREE = 500000     # Open three (strong position)
    THREE = 10000           # Closed three
    OPEN_TWO = 1000         # Open two
    TWO = 200               # Closed two
    ONE = 10                # Single stone

    def evaluate_line(
        self, count: int, open_start: bool, open_end: bool
    ) -> int:
        both_open = open_start and open_end
        one_open = open_start or open_end

        if count >= 5:
            return self.FIVE
        elif count == 4:
            if one_open:
                return self.FOUR
            return 0
        elif count == 3:
            if both_open:
                return self.OPEN_THREE
            elif one_open:
                return self.THREE
            return 0
        elif count == 2:
            if both_open:
                return self.OPEN_TWO
            elif one_open:
                return self.TWO
            return 0
        elif count == 1:
            if both_open:
                return self.ONE
            else:
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

        if board.find_winning_move(player):
            return self.FIVE

        if board.find_winning_move(opponent):
            return -self.FIVE

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
                    else:
                        opponent_score += line_score

        return player_score - opponent_score * 1.5

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
                critical_moves.append((10000000, (x, y)))
                continue
            if opponent_threat >= 4:
                high_priority_moves.append((9000000, (x, y)))
                continue
            if player_threat >= 4:
                high_priority_moves.append((8000000, (x, y)))
                continue
            if opponent_threat >= 3:
                score = 1000000
            if player_threat >= 3:
                score = 500000
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
