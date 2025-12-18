##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## constants
##

WIN_LENGTH = 5
INFINITY = 1_000_000_000

DEPTH_EARLY = 3
DEPTH_MID = 4
DEPTH_LATE = 6

DIRECTIONS = [
    (1, 0),  # horizontal
    (0, 1),  # vertical
    (1, 1),  # diagonal \
    (1, -1),  # diagonal /
]


ATTACK_MULTIPLIER_AGGRESSIVE = 0.9
DEFENSE_MULTIPLIER_AGGRESSIVE = 1.1
ATTACK_MULTIPLIER_DEFENSIVE = 1.1
DEFENSE_MULTIPLIER_DEFENSIVE = 0.9

TIME_LIMIT = 4.75
MAX_DEPTH = 10

DOUBLE_THREE_BONUS = 20_000
DOUBLE_FOUR_BONUS = 50_000
CENTER_CONTROL = 10

ATTACK_MULTIPLIER = 1.0
DEFENSE_MULTIPLIER = 0.9

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

def get_patterns(player: int) -> dict:
    """Get the pattern dictionary for a given player, organized by category."""
    player_str = str(player)
    return {
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
