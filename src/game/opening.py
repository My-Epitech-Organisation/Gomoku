##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## opening
##

import random
import sys
from typing import Optional, Tuple


def get_first_move(board, player: int) -> Optional[Tuple[int, int]]:
    if player != 1:
        return None

    # Random position not too close to border
    min_pos = 3
    max_pos = board.width - 3
    candidates = [(x, y) for x in range(min_pos, max_pos) for y in range(min_pos, max_pos)]
    random.shuffle(candidates)
    for x, y in candidates:
        if board.is_valid_position(x, y):
            return (x, y)
    return None


def get_opening_move(board, player: int) -> Optional[Tuple[int, int]]:
    # For future strategies, for now return None
    return None
