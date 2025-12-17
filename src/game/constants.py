##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Constants for scoring and priorities
##

# Winning/Losing conditions
WIN_SCORE = 1_000_000_000
LOSE_SCORE = -WIN_SCORE

# Pattern scores
FIVE_IN_ROW = WIN_SCORE

# Four in a row patterns
OPEN_FOUR = 500_000      # Can win next move
CLOSED_FOUR = 10_000     # One end blocked

# Three in a row patterns
OPEN_THREE = 5_000       # Can become open four
DOUBLE_OPEN_THREE = 50_000  # Two open threes = guaranteed win
CLOSED_THREE = 500       # One end blocked

# Two in a row patterns
OPEN_TWO = 100           # Can become open three
CLOSED_TWO = 10          # One end blocked

# Single stone
SINGLE = 1

# Defense multiplier for opponent score evaluation
# Defense is CRITICAL - we prioritize blocking over attacking
DEFENSE_MULTIPLIER = 2.0

# Threat levels for move ordering
THREAT_LEVEL_WIN = 5         # Five in a row
THREAT_LEVEL_OPEN_FOUR = 4   # Open four
THREAT_LEVEL_CLOSED_FOUR = 3 # Closed four or open three
THREAT_LEVEL_OPEN_THREE = 2  # Open three or closed four
THREAT_LEVEL_NORMAL = 1      # Other patterns

# Search configuration
MAX_CANDIDATE_MOVES = 20
TOP_MOVES_PARALLEL = 10
MAX_MOVES_PER_DEPTH = 15
NEIGHBOR_SEARCH_DISTANCE = 2
CENTER_SEARCH_RADIUS = 2

# Time management
DEFAULT_TIME_LIMIT = 4.75
DEFAULT_MAX_DEPTH = 8
PARALLEL_WORKERS = 2
PARALLEL_TIMEOUT = 1.0

# Transposition table
TT_MAX_SIZE = 50_000
MAX_KILLER_MOVES = 2
