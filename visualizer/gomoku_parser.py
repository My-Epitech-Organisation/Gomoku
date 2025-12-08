##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## gomoku_parser
##

from typing import List, Tuple, Optional


class ReplayParser:
    def __init__(self):
        self.moves = []
        self.board_size = 20

    def parse_file(self, filename: str) -> List[Tuple[int, int, int]]:
        self.moves = []

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                move = self._parse_replay_log_line(line)
                if move:
                    self.moves.append(move)

        except FileNotFoundError:
            print(f"File {filename} not found")
        except Exception as e:
            print(f"Error parsing file: {e}")

        return self.moves

    def _parse_replay_log_line(self, line: str) -> Optional[Tuple[int, int, int]]:
        try:
            if ':' not in line:
                return None

            parts = line.split(':')
            if len(parts) < 3:
                return None

            timestamp = int(parts[0])
            player = int(parts[1])

            coords_time = parts[2].split()
            if len(coords_time) < 2:
                return None

            y = int(coords_time[0])
            x = int(coords_time[1])

            return (x, y, player)

        except (ValueError, IndexError):
            return None
