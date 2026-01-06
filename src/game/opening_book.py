##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Opening book for pre-computed moves
##

from typing import Dict, List, Optional, Tuple, Set, Callable


class OpeningBook:
    """
    Pre-computed opening moves for Gomoku.

    Uses normalized board representation to handle symmetry.
    Board states are represented as frozensets of (x, y, player) tuples.
    """

    def __init__(self, board_size: int = 20):
        self.board_size = board_size
        self.center = board_size // 2
        self.book: Dict[frozenset, Tuple[int, int]] = {}
        self._build_book()

    def _build_book(self) -> None:
        """Build the opening book with common patterns."""
        c = self.center  # Shorthand for center coordinate

        # === Move 1: Empty board -> play center ===
        self.book[frozenset()] = (c, c)

        # === Move 2: Opponent at center -> adjacent diagonal ===
        self._add_with_symmetry(
            [(c, c, 2)],  # Opponent at center
            (c + 1, c + 1)  # Our response: diagonal
        )

        # === Move 3: We have center, opponent adjacent ===
        # Standard: extend opposite direction for strong formation
        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            self._add_with_symmetry(
                [(c, c, 1), (c + dx, c + dy, 2)],
                (c - dx, c - dy)
            )

        # === Move 3: We have center, opponent far ===
        # If opponent plays far, extend toward center influence
        for dist in [2, 3]:
            for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                self._add_with_symmetry(
                    [(c, c, 1), (c + dx * dist, c + dy * dist, 2)],
                    (c + dx, c + dy)  # Extend toward opponent
                )

        # === Move 4: Building a line ===
        # If we have two in a row, extend to three
        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            # We: center + one direction, Opp: somewhere else
            self._add_with_symmetry(
                [(c, c, 1), (c + dx, c + dy, 1), (c - dx, c - dy, 2)],
                (c + 2*dx, c + 2*dy)  # Extend our line
            )
            self._add_with_symmetry(
                [(c, c, 1), (c + dx, c + dy, 1), (c + 2*dx, c + 2*dy, 2)],
                (c - dx, c - dy)  # Extend other direction
            )

        # === Move 4: Block opponent's development ===
        # If opponent has two adjacent, place between us and them
        for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
            self._add_with_symmetry(
                [(c, c, 1), (c + 2*dx, c + 2*dy, 2), (c + 3*dx, c + 3*dy, 2)],
                (c + dx, c + dy)  # Block between us and them
            )

        # === Additional patterns for robustness ===
        # Diagonal response to knight's move
        self._add_with_symmetry(
            [(c, c, 1), (c + 2, c + 1, 2)],
            (c + 1, c + 1)
        )
        self._add_with_symmetry(
            [(c, c, 1), (c + 1, c + 2, 2)],
            (c + 1, c + 1)
        )

    def _add_with_symmetry(
        self,
        stones: List[Tuple[int, int, int]],
        response: Tuple[int, int]
    ) -> None:
        """
        Add a position and all its symmetric variants to the book.

        Symmetries considered:
        - 4 rotations (0, 90, 180, 270 degrees)
        - 4 reflections (horizontal, vertical, both diagonals)
        """
        for transform in self._get_transforms():
            transformed_stones = frozenset(
                (transform(x, y)[0], transform(x, y)[1], p)
                for x, y, p in stones
            )
            transformed_response = transform(response[0], response[1])

            # Only add if response is valid
            rx, ry = transformed_response
            if 0 <= rx < self.board_size and 0 <= ry < self.board_size:
                self.book[transformed_stones] = transformed_response

    def _get_transforms(self) -> List[Callable[[int, int], Tuple[int, int]]]:
        """Get all 8 symmetry transformations."""
        c = self.center

        transforms = [
            # Identity
            lambda x, y: (x, y),
            # Rotate 90 degrees clockwise around center
            lambda x, y, c=c: (c + (y - c), c - (x - c)),
            # Rotate 180 degrees
            lambda x, y, c=c: (2*c - x, 2*c - y),
            # Rotate 270 degrees clockwise
            lambda x, y, c=c: (c - (y - c), c + (x - c)),
            # Reflect horizontal (mirror left-right)
            lambda x, y, c=c: (2*c - x, y),
            # Reflect vertical (mirror top-bottom)
            lambda x, y, c=c: (x, 2*c - y),
            # Reflect main diagonal
            lambda x, y, c=c: (c + (y - c), c + (x - c)),
            # Reflect anti-diagonal
            lambda x, y, c=c: (c - (y - c), c - (x - c)),
        ]
        return transforms

    def lookup(self, board) -> Optional[Tuple[int, int]]:
        """
        Look up a board position in the opening book.

        Args:
            board: Board object with grid and move_count

        Returns:
            Best move (x, y) if found, None otherwise
        """
        from . import constants

        # Only use book for first N moves
        if not constants.OPENING_BOOK_ENABLED:
            return None

        if board.move_count > constants.OPENING_BOOK_MAX_MOVES:
            return None

        # Convert board to normalized representation
        stones = set()
        for y in range(board.height):
            for x in range(board.width):
                if board.grid[y][x] != 0:
                    stones.add((x, y, board.grid[y][x]))

        state = frozenset(stones)

        # Direct lookup
        if state in self.book:
            move = self.book[state]
            # Verify move is valid (empty square)
            if board.grid[move[1]][move[0]] == 0:
                return move

        return None

    def size(self) -> int:
        """Return the number of positions in the book."""
        return len(self.book)


# Singleton instance
_opening_book: Optional[OpeningBook] = None


def get_opening_book(board_size: int = 20) -> OpeningBook:
    """Get the singleton opening book instance."""
    global _opening_book
    if _opening_book is None or _opening_book.board_size != board_size:
        _opening_book = OpeningBook(board_size)
    return _opening_book
