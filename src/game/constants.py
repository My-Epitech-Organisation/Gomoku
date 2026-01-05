##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## constants
##

WIN_LENGTH = 5
INFINITY = 1_000_000_000

DEPTH_EARLY = 5
DEPTH_MID = 7
DEPTH_LATE = 9

DIRECTIONS = [
    (1, 0),  # horizontal
    (0, 1),  # vertical
    (1, 1),  # diagonal \
    (1, -1),  # diagonal /
]


ATTACK_MULTIPLIER = 0.9
DEFENSE_MULTIPLIER = 1.1

TIME_LIMIT = 4.75
MAX_DEPTH = 12

# Time Banking - use remaining time to warm TT
TIME_BANK_ENABLED = True
RESPONSE_DEADLINE = 4.70  # Return move at this time (300ms safety margin)
MIN_THINKING_TIME = 0.1   # Always think at least this long
TT_WARMUP_DEPTH = 4       # Depth for warming TT during time bank

# Pondering - calculate during opponent's turn
PONDER_ENABLED = True
PONDER_PREDICTIONS = 5    # Top N opponent moves to explore
PONDER_MAX_DEPTH = 6      # Max depth during pondering
PONDER_POLL_INTERVAL = 0.1  # Poll interval in seconds

DOUBLE_THREE_BONUS = 20_000
DOUBLE_FOUR_BONUS = 50_000
CENTER_CONTROL = 10

MOVE_RADIUS = 2

SCORE_FIVE = 1_000_000
SCORE_OPEN_FOUR = 100_000
SCORE_CLOSED_FOUR = 10_000
SCORE_OPEN_THREE = 5_000
SCORE_CLOSED_THREE = 1000
SCORE_OPEN_TWO = 300
SCORE_CLOSED_TWO = 50

SCORE_SPLIT_FOUR = 15_000
SCORE_SPLIT_THREE = 3_000
SCORE_BROKEN_THREE = 4_000

DOUBLE_OPEN_THREE = 20_000
THREAT_THREE_COMBO = 15_000
DOUBLE_FOUR = INFINITY // 2

EXACT = 0
LOWER = 1
UPPER = 2

MOVE_WIN = 1_000_000_000
MOVE_BLOCK_WIN = 500_000_000
MOVE_DOUBLE_FOUR = 150_000_000
MOVE_BLOCK_DOUBLE_FOUR = 140_000_000
MOVE_FOUR_THREE = 120_000_000
MOVE_BLOCK_FOUR_THREE = 110_000_000
MOVE_FORK = 100_000_000
MOVE_OPEN_FOUR = 50_000_000
MOVE_BLOCK_OPEN_FOUR = 25_000_000
MOVE_OPEN_THREE = 10_000_000
MOVE_BLOCK_OPEN_THREE = 5_000_000

PATTERNS = {1: None, 2: None}


def _init_patterns():
    if PATTERNS[1] is None:
        for player in [1, 2]:
            player_str = str(player)
            PATTERNS[player] = {
                "winning": {
                    "five": player_str * 5,
                    "open_four": f".{player_str * 4}.",
                    "closed_four": [
                        f"{player_str * 4}.",
                        f".{player_str * 4}",
                        f"{player_str * 3}.{player_str}",
                        f"{player_str * 2}.{player_str * 2}",
                    ],
                    "split_four": [
                        f"{player_str * 2}.{player_str * 2}",
                        f"{player_str}.{player_str * 3}",
                        f"{player_str * 3}.{player_str}",
                    ],
                },
                "threat": {
                    "open_three": f".{player_str * 3}.",
                    "closed_three": [
                        f"{player_str * 3}.",
                        f".{player_str * 3}",
                        f"{player_str * 2}.{player_str}",
                        f"{player_str}.{player_str * 2}",
                    ],
                    "split_three": [
                        f"{player_str}.{player_str}.{player_str}",
                        f"{player_str * 2}..{player_str}",
                        f"{player_str}..{player_str * 2}",
                    ],
                    "broken_open_three": [
                        f".{player_str * 2}.{player_str}.",
                        f".{player_str}.{player_str * 2}.",
                    ],
                },
                "development": {
                    "open_two": f".{player_str * 2}.",
                    "closed_two": [
                        f"{player_str * 2}.",
                        f".{player_str * 2}",
                        f"{player_str}.{player_str}",
                    ],
                },
            }


_init_patterns()
