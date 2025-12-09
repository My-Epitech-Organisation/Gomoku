#!/usr/bin/env python3
##
## EPITECH PROJECT, 2025
## Gomoku Visualizer
## File description:
## PySide6 visualizer launcher
##

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from gomoku_visualizer_pyside import main

if __name__ == "__main__":
    main()
