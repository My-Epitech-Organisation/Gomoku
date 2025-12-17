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
DEPTH_LATE = 3

DIRECTIONS = [
    (1, 0), # horizontal
    (0, 1), # vertical
    (1, 1), # diagonal \
    (1, -1) # diagonal /
]


# XXXXX
SCORE_FIVE = 1_000_000

# _XXXX_
SCORE_OPEN_FOUR = 100_000

# XXXX_
# _XXXX
# XXX_X
# XX_XX
SCORE_CLOSED_FOUR = 10_000

# _XXX_
SCORE_OPEN_THREE = 5_000

# XXX_
# _XXX
# XX_X
# X_XX
SCORE_CLOSED_THREE = 1000

# _XX_
SCORE_OPEN_TWO = 300

# XX_
# _XX
# X_X
SCORE_CLOSED_TWO = 50

DOUBLE_THREE_BONUS = 20_000
DOUBLE_FOUR_BONUS = 50_000
CENTER_CONTROL = 10

## Priorities for move ordering
# 5. Priorités de coup (Move Ordering)

# Ordre strict recommandé :

# Coup gagnant immédiat

# Blocage d’un coup gagnant adverse

# Création d’un open four

# Blocage d’un open four adverse

# Création d’un open three

# Blocage d’un open three adverse

# Autres patterns décroissants

ATTACK_MULTIPLIER = 1.0
DEFENSE_MULTIPLIER = 0.9

## Evaluation method
# eval =
# ATTACK_MULTIPLIER * score(player)
# - DEFENSE_MULTIPLIER * score(opponent)


# 8. Masques de patterns (optimisation)

# Chaque ligne analysée est transformée en chaîne :

# 0 = bord
# 1 = joueur
# 2 = adversaire
# 3 = vide

# Exemple :

# 0333310

# Permet :

# Hash rapide

# Pattern matching

# Tables pré-calculées


MOVE_RADIUS = 2

## Terminal values
# if win(player): return +INFINITY - depth
# if win(opponent): return -INFINITY + depth