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
RESPONSE_DEADLINE = 4.50  # Return move at this time (500ms safety margin)
MIN_THINKING_TIME = 0.1   # Always think at least this long
TT_WARMUP_DEPTH = 8       # Depth for warming TT during time bank (increased for productive warming)
TT_WARMUP_POSITIONS = 5   # Number of opponent responses to explore during warming

# Pondering - calculate during opponent's turn
PONDER_ENABLED = True
PONDER_PREDICTIONS = 5    # Top N opponent moves to explore
PONDER_MAX_DEPTH = 6      # Max depth during pondering
PONDER_POLL_INTERVAL = 0.1  # Poll interval in seconds

# Aspiration Windows - narrow initial search window
ASPIRATION_DELTA = 50       # Initial window size around previous score
ASPIRATION_MIN_DEPTH = 4    # Start using aspiration at depth 4

# LMR - Late Move Reductions
LMR_FULL_MOVES = 3          # First N moves at full depth
LMR_MIN_DEPTH = 3           # Minimum depth to apply LMR
LMR_REDUCTION = 2           # Depth reduction amount

# Quiescence Search - extend search on tactical moves at depth 0
QUIESCENCE_MAX_DEPTH = 4    # Maximum plies to search in quiescence (reduced to avoid timeout)
QUIESCENCE_MAX_MOVES = 6    # Maximum moves to explore per quiescence level
QUIESCENCE_DELTA = 50_000   # Delta pruning margin

# History Heuristic - track successful moves across depths
HISTORY_MAX_VALUE = 10_000  # Cap history scores to prevent overflow
HISTORY_DECAY_FACTOR = 0.9  # Multiply all history by this each age
HISTORY_BONUS_DEPTH = True  # Scale bonus by depth (deeper = more valuable)

# Opening Book - pre-computed moves for early game
OPENING_BOOK_MAX_MOVES = 6  # Use book for first N moves
OPENING_BOOK_ENABLED = True # Toggle opening book

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
MOVE_BLOCK_OPEN_FOUR = 200_000_000  # Open four = immediate loss, must block
MOVE_DOUBLE_FOUR = 150_000_000
MOVE_BLOCK_DOUBLE_FOUR = 140_000_000
MOVE_FOUR_THREE = 120_000_000
MOVE_BLOCK_FOUR_THREE = 110_000_000
MOVE_FORK = 100_000_000
MOVE_OPEN_FOUR = 50_000_000
MOVE_BLOCK_PRE_OPEN_FOUR = 45_000_000  # Block 3-in-row that becomes open four
MOVE_BLOCK_SPLIT_THREE = 40_000_000    # Split three → open four next move
MOVE_OPEN_THREE = 10_000_000
MOVE_SPLIT_THREE = 8_000_000
MOVE_BLOCK_OPEN_THREE = 5_000_000
MOVE_BLOCK_BUILDING_TWO = 2_000_000  # Proactive defense - stop .XX. from becoming .XXX.

# Threshold for immediate move (triggers time banking)
# Lower than MOVE_BLOCK_OPEN_FOUR to include split_three blocks
IMMEDIATE_MOVE_THRESHOLD = 40_000_000  # MOVE_BLOCK_SPLIT_THREE level

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
                        f"{player_str * 2}.{player_str}",   # XX.X - 1 gap, urgent
                        f"{player_str}.{player_str * 2}",   # X.XX - 1 gap, urgent
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
