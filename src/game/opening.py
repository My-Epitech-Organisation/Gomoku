##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## opening
##

from typing import Optional, Tuple


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
