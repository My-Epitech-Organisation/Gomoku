##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## File-based logger for game analysis and debugging
##

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional


class GameLogger:
    """File-based logger for game analysis and debugging."""

    LOG_DIR = Path("logs")

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.log_file = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        if enabled:
            self._setup_log_file()

    def _setup_log_file(self):
        """Create log directory and file."""
        try:
            self.LOG_DIR.mkdir(exist_ok=True)
            log_path = self.LOG_DIR / f"game_{self.session_id}.log"
            self.log_file = open(log_path, "w", buffering=1)  # Line buffered
            self.info(f"Session started: {self.session_id}")
        except (OSError, IOError) as e:
            # If we can't create log file, continue without file logging
            print(f"[WARN] Could not create log file: {e}", file=sys.stderr)
            self.log_file = None

    def _write(self, level: str, message: str):
        """Write to both file and stderr."""
        if not self.enabled:
            return

        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}][{level}] {message}"

        if self.log_file:
            try:
                self.log_file.write(formatted + "\n")
            except (OSError, IOError):
                pass  # Ignore file write errors

        # Also print to stderr for real-time monitoring
        print(formatted, file=sys.stderr)

    def info(self, message: str):
        """Log info message."""
        self._write("INFO", message)

    def debug(self, message: str):
        """Log debug message."""
        self._write("DEBUG", message)

    def warn(self, message: str):
        """Log warning message."""
        self._write("WARN", message)

    def error(self, message: str):
        """Log error message."""
        self._write("ERROR", message)

    def move(
        self,
        move_num: int,
        player: int,
        x: int,
        y: int,
        time_ms: int,
        info: str = ""
    ):
        """Log a move with timing info."""
        self._write("MOVE", f"#{move_num} P{player}: ({x},{y}) {time_ms}ms {info}")

    def threat(self, threat_type: str, positions: list, direction: str):
        """Log detected threat."""
        pos_str = ", ".join(f"({x},{y})" for x, y in positions)
        self._write("THREAT", f"{threat_type} at [{pos_str}] dir={direction}")

    def search(
        self,
        depth: int,
        nodes: int,
        time_s: float,
        best_move: Optional[tuple]
    ):
        """Log search stats."""
        move_str = f"({best_move[0]},{best_move[1]})" if best_move else "None"
        self._write(
            "SEARCH",
            f"depth={depth} nodes={nodes} time={time_s:.2f}s best={move_str}"
        )

    def board_scan(self, threats: dict):
        """Log global board scan results."""
        fours = len(threats.get("fours", []))
        open_threes = len(threats.get("open_threes", []))
        split_threes = len(threats.get("split_threes", []))

        if fours > 0 or open_threes > 0 or split_threes > 0:
            self._write(
                "SCAN",
                f"Threats: fours={fours}, open_threes={open_threes}, "
                f"split_threes={split_threes}"
            )

    def close(self):
        """Close log file."""
        if self.log_file:
            self.info("Session ended")
            try:
                self.log_file.close()
            except (OSError, IOError):
                pass
            self.log_file = None


# Global logger instance
_logger: Optional[GameLogger] = None


def get_logger() -> GameLogger:
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = GameLogger(enabled=True)
    return _logger


def close_logger():
    """Close the global logger."""
    global _logger
    if _logger is not None:
        _logger.close()
        _logger = None
