##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Tests for AI threat detection (double-three, four-three, double-four)
##

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from game.board import Board
from game.ai import MinMaxAI
from game import constants


class TestCountThreats:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_count_threats_empty(self):
        """Un coup isolé ne crée aucune menace"""
        self.board.place_stone(10, 10, 1)
        threats = self.ai._count_threats(self.board, 10, 10, 1)
        assert threats["fives"] == 0
        assert threats["open_fours"] == 0
        assert threats["closed_fours"] == 0
        assert threats["open_threes"] == 0

    def test_count_threats_open_three(self):
        """Détecte un trois ouvert horizontal"""
        # Place .XXX.
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        threats = self.ai._count_threats(self.board, 11, 10, 1)
        assert threats["open_threes"] >= 1

    def test_count_threats_open_four(self):
        """Détecte un quatre ouvert horizontal"""
        # Place .XXXX.
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        self.board.place_stone(13, 10, 1)
        threats = self.ai._count_threats(self.board, 11, 10, 1)
        assert threats["open_fours"] >= 1

    def test_count_threats_five(self):
        """Détecte cinq en ligne"""
        for i in range(5):
            self.board.place_stone(10 + i, 10, 1)
        threats = self.ai._count_threats(self.board, 12, 10, 1)
        assert threats["fives"] >= 1


class TestMoveHeuristicThreats:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_winning_move(self):
        """Un coup gagnant a la priorité maximale"""
        # XXXX. -> jouer en (14,10) gagne
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        score = self.ai._move_heuristic(self.board, (14, 10), 1)
        assert score == constants.MOVE_WIN

    def test_block_winning_move(self):
        """Bloquer une victoire adverse"""
        # Adversaire a OOOO.
        for i in range(4):
            self.board.place_stone(10 + i, 10, 2)
        score = self.ai._move_heuristic(self.board, (14, 10), 1)
        assert score == constants.MOVE_BLOCK_WIN

    def test_double_three_detection(self):
        """Détecte un double-three (fork)"""
        # Configuration en L pour créer deux trois ouverts
        #     X
        #     X
        #   X X X
        self.board.place_stone(10, 10, 1)  # Centre
        self.board.place_stone(9, 10, 1)   # Gauche
        self.board.place_stone(10, 9, 1)   # Haut
        # Jouer en (11,10) et (10,11) crée double-three
        self.board.place_stone(11, 10, 1)  # Droite
        self.board.place_stone(10, 11, 1)  # Bas

        # Placer une pierre qui crée le fork
        score = self.ai._move_heuristic(self.board, (10, 12), 1)
        # Devrait détecter au moins un pattern de menace
        assert score >= constants.MOVE_OPEN_THREE

    def test_four_three_detection(self):
        """Détecte un four-three"""
        # Horizontal: XXX. (besoin d'un de plus pour four)
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        # Vertical: X au-dessus
        self.board.place_stone(13, 9, 1)
        self.board.place_stone(13, 11, 1)

        # Jouer en (13,10) crée four horizontal ET trois vertical
        score = self.ai._move_heuristic(self.board, (13, 10), 1)
        # Devrait être au moins un four
        assert score >= constants.MOVE_OPEN_FOUR or score >= constants.MOVE_FOUR_THREE

    def test_open_four_priority(self):
        """Un quatre ouvert a haute priorité"""
        # .XXX. -> jouer adjacent crée .XXXX.
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 10, 1)
        self.board.place_stone(12, 10, 1)
        score = self.ai._move_heuristic(self.board, (13, 10), 1)
        assert score >= constants.MOVE_OPEN_FOUR

    def test_block_open_four(self):
        """Bloquer un quatre ouvert adverse"""
        # Adversaire a .OOO.
        self.board.place_stone(10, 10, 2)
        self.board.place_stone(11, 10, 2)
        self.board.place_stone(12, 10, 2)
        score = self.ai._move_heuristic(self.board, (13, 10), 1)
        assert score >= constants.MOVE_BLOCK_OPEN_THREE


class TestDoubleThreeForkScenarios:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_l_shape_fork(self):
        """Fork en forme de L"""
        #   . X .
        #   . X .
        #   X X ?   <- jouer en ? crée double-three
        self.board.place_stone(10, 8, 1)   # Vertical haut
        self.board.place_stone(10, 9, 1)   # Vertical milieu
        self.board.place_stone(9, 10, 1)   # Horizontal gauche
        self.board.place_stone(10, 10, 1)  # Centre

        # Jouer en (11, 10) devrait créer un fork
        score = self.ai._move_heuristic(self.board, (11, 10), 1)
        # Le coup devrait avoir une priorité élevée (fork ou three)
        assert score >= constants.MOVE_OPEN_THREE


class TestGetImmediateMove:
    def setup_method(self):
        self.board = Board(20, 20)
        self.ai = MinMaxAI()

    def test_immediate_win(self):
        """L'IA joue le coup gagnant immédiatement"""
        for i in range(4):
            self.board.place_stone(10 + i, 10, 1)
        move = self.ai._get_immediate_move(self.board, 1)
        assert move == (14, 10) or move == (9, 10)

    def test_immediate_block(self):
        """L'IA bloque une victoire imminente"""
        for i in range(4):
            self.board.place_stone(10 + i, 10, 2)
        move = self.ai._get_immediate_move(self.board, 1)
        assert move == (14, 10) or move == (9, 10)

    def test_no_immediate_threat(self):
        """Pas de coup immédiat si pas de menace critique"""
        self.board.place_stone(10, 10, 1)
        self.board.place_stone(11, 11, 2)
        move = self.ai._get_immediate_move(self.board, 1)
        assert move is None
