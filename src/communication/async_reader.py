##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## Async stdin reader for non-blocking input
##

import queue
import sys
import threading
from typing import Optional, TextIO


class AsyncInputReader:
    """
    Non-blocking stdin reader using a daemon thread.

    This allows the main loop to poll for input while doing
    background work (pondering, TT warming).
    """

    def __init__(self, input_stream: TextIO = None):
        self.input_stream = input_stream or sys.stdin
        self.queue: queue.Queue[str] = queue.Queue()
        self.running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the reader thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the reader thread."""
        self.running = False

    def _read_loop(self) -> None:
        """Background thread: reads stdin and queues lines."""
        while self.running:
            try:
                line = self.input_stream.readline()
                if not line:
                    self.running = False
                    break
                self.queue.put(line.strip())
            except Exception:
                self.running = False
                break

    def get_line(self, timeout: float = None) -> Optional[str]:
        """
        Get next line from queue.

        Args:
            timeout: Max seconds to wait. None = block forever.

        Returns:
            The next line, or None if timeout expired.
        """
        try:
            return self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def has_input(self) -> bool:
        """Check if input is available without blocking."""
        return not self.queue.empty()
