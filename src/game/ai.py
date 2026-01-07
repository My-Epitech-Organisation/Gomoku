##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## ai
##

import threading
import time
from collections import OrderedDict
from typing import List, Optional, Tuple

from . import constants
from .opening_book import get_opening_book
from utils.logger import get_logger


class LRUTranspositionTable:
    """LRU-evicting transposition table with maximum size."""

    def __init__(self, max_size: int = 500_000):
        self.max_size = max_size
        self._cache = OrderedDict()

    def __contains__(self, key):
        return key in self._cache

    def __getitem__(self, key):
        self._cache.move_to_end(key)
        return self._cache[key]

    def __setitem__(self, key, value):
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)

    def get(self, key, default=None):
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return default

    def clear(self):
        self._cache.clear()

    def __len__(self):
        return len(self._cache)


class MinMaxAI:
    def __init__(
        self,
        max_depth: int = constants.MAX_DEPTH,
        time_limit: float = constants.TIME_LIMIT,
        use_iterative_deepening: bool = True,
    ):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.use_iterative_deepening = use_iterative_deepening
        self.stop_search = False
        self.nodes = 0
        self.transposition_table = LRUTranspositionTable(max_size=constants.TT_MAX_SIZE)
        self.killer_moves = {}
        self.history_table = {1: {}, 2: {}}  # player -> {(x,y): score}
        self.threat_cache = {}  # (board_hash, x, y, player) -> threats dict
        self.age = 0

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        self.stop_search = False
        self.nodes = 0
        self.age += 1
        self._decay_history()  # Decay history scores each search
        self.threat_cache.clear()  # Clear threat cache for new search
        start_time = time.time()
        logger = get_logger()
        opponent = 3 - player

        # Check opening book first (for early game moves)
        if board.move_count <= constants.OPENING_BOOK_MAX_MOVES:
            opening_book = get_opening_book(board.width)
            book_move = opening_book.lookup(board)
            if book_move is not None:
                logger.info(f"Opening book move: {book_move}")
                # Use time banking to warm TT instead of returning immediately
                return self._time_banked_return(board, player, book_move, start_time)

        # Ultra-fast critical check (< 1ms) - detects win/block moves
        # Don't return immediately - use time banking to warm TT
        critical_move = self._check_immediate_critical(board, player)
        if critical_move is not None:
            logger.info(f"Critical move (win/block5): {critical_move}")
            # Will be handled via time banking below

        # Phase 0: Global threat scan - find critical opponent threats
        board_threats = self._scan_board_threats(board, opponent)
        logger.board_scan(board_threats)

        # Collect force block move if any (don't return immediately - use time banking)
        force_block_move = None

        # Force block if opponent has a four (immediate loss otherwise)
        if board_threats["fours"] and force_block_move is None:
            for threat in board_threats["fours"]:
                if threat["gap"]:
                    logger.threat("FOUR", threat["positions"], threat["direction"])
                    logger.info(f"Force blocking four at {threat['gap']}")
                    force_block_move = threat["gap"]
                    break
            # Solid four with no gap - block at ends
            if force_block_move is None:
                for threat in board_threats["fours"]:
                    positions = threat["positions"]
                    # Find blocking positions at ends
                    first_pos = positions[0]
                    last_pos = positions[-1]
                    # Calculate direction
                    dx = 1 if positions[1][0] > positions[0][0] else (
                        -1 if positions[1][0] < positions[0][0] else 0
                    )
                    dy = 1 if positions[1][1] > positions[0][1] else (
                        -1 if positions[1][1] < positions[0][1] else 0
                    )
                    block1 = (first_pos[0] - dx, first_pos[1] - dy)
                    block2 = (last_pos[0] + dx, last_pos[1] + dy)

                    # Check validity of each block
                    b1_valid = (0 <= block1[0] < board.width and
                                0 <= block1[1] < board.height and
                                board.grid[block1[1]][block1[0]] == 0)
                    b2_valid = (0 <= block2[0] < board.width and
                                0 <= block2[1] < board.height and
                                board.grid[block2[1]][block2[0]] == 0)

                    # Check if our stone is adjacent to each block (creates wall)
                    # Position beyond block1 (even further before the four)
                    beyond1 = (block1[0] - dx, block1[1] - dy)
                    # Position beyond block2 (even further after the four)
                    beyond2 = (block2[0] + dx, block2[1] + dy)

                    b1_has_wall = (0 <= beyond1[0] < board.width and
                                   0 <= beyond1[1] < board.height and
                                   board.grid[beyond1[1]][beyond1[0]] == player)
                    b2_has_wall = (0 <= beyond2[0] < board.width and
                                   0 <= beyond2[1] < board.height and
                                   board.grid[beyond2[1]][beyond2[0]] == player)

                    # Prioritize block that creates a wall with our existing stone
                    if b1_valid and b1_has_wall:
                        logger.info(f"Force blocking solid four at {block1} (wall)")
                        force_block_move = block1
                        break
                    if b2_valid and b2_has_wall:
                        logger.info(f"Force blocking solid four at {block2} (wall)")
                        force_block_move = block2
                        break

                    # Check if both blocks are needed (open four = unstoppable)
                    if b1_valid and b2_valid:
                        logger.warn(f"OPEN FOUR detected - unstoppable! Blocking {block2}")
                        force_block_move = block2
                        break

                    # Fallback: any valid block
                    if b1_valid:
                        logger.info(f"Force blocking solid four at {block1}")
                        force_block_move = block1
                        break
                    if b2_valid:
                        logger.info(f"Force blocking solid four at {block2}")
                        force_block_move = block2
                        break

        # === HYBRID ATTACK/DEFENSE LOGIC (Sente) ===
        # If opponent has no four, check if we can create a stronger threat
        offensive_move = None
        our_threat = None
        if force_block_move is None:
            our_threat = self._find_our_best_threat(board, player)
            if our_threat is not None:
                threat_move, threat_type = our_threat
                if threat_type in ['win', 'fork', 'four']:
                    # Our threat is stronger - take initiative!
                    logger.info(f"Offensive move ({threat_type}): {threat_move}")
                    offensive_move = threat_move

        # Force block open threes before they become open fours
        # An open three (.XXX.) blocked now prevents unstoppable open four
        # BUT: skip if we have an offensive move (our four > their open three)
        if board_threats["open_threes"] and force_block_move is None and offensive_move is None:
            for threat in board_threats["open_threes"]:
                blocks = threat.get("blocks", [])
                if blocks:
                    # Prefer the block that's closer to our existing stones
                    best_block = None
                    best_score = -1
                    for block in blocks:
                        bx, by = block
                        if (0 <= bx < board.width and 0 <= by < board.height
                                and board.grid[by][bx] == 0):
                            # Score based on proximity to our stones
                            score = 0
                            for ddy in range(-2, 3):
                                for ddx in range(-2, 3):
                                    nx, ny = bx + ddx, by + ddy
                                    if (0 <= nx < board.width and 0 <= ny < board.height
                                            and board.grid[ny][nx] == player):
                                        score += 1
                            if score > best_score:
                                best_score = score
                                best_block = block
                    if best_block:
                        logger.info(f"Force blocking open three at {best_block} (prevent open four)")
                        force_block_move = best_block
                        break

        # Force block split threes (X.XX, XX.X) - fill the gap to prevent four
        # This was the Game 4 bug: split_three detected but not blocked
        # BUT: skip if we have an offensive move (our four > their split three)
        if board_threats["split_threes"] and force_block_move is None and offensive_move is None:
            for threat in board_threats["split_threes"]:
                gap = threat.get("gap")
                if gap:
                    gx, gy = gap
                    if (0 <= gx < board.width and 0 <= gy < board.height
                            and board.grid[gy][gx] == 0):
                        logger.info(f"Force blocking split three at {gap} (fill gap)")
                        force_block_move = gap
                        break

        # Phase 0.5: Early game - prefer connected moves near opponent
        if force_block_move is None and board.move_count <= 4:
            early_move = self._get_early_game_move(board, player, opponent)
            if early_move:
                logger.info(f"Early game move: {early_move}")
                force_block_move = early_move

        # Phase 1: Check for immediate/forced moves (if no force block)
        immediate_move = None
        if force_block_move is None:
            immediate_move = self._get_immediate_move(board, player)

            # If no immediate threat, try development move (open_three or building)
            if immediate_move is None and our_threat is not None:
                threat_move, threat_type = our_threat
                if threat_type in ['open_three', 'building']:
                    logger.info(f"Development move ({threat_type}): {threat_move}")
                    immediate_move = threat_move

        # Phase 2: Threat Space Search (VCT) if no immediate move
        vct_move = None
        if force_block_move is None and immediate_move is None:
            vct_move = self._threat_space_search(board, player, max_depth=14, time_limit=1.5)
            if vct_move is not None:
                logger.info(f"VCT found: {vct_move}")

        # Determine if we have a decided move
        # Priority: critical > offensive (four/fork) > force_block > immediate > vct
        decided_move = critical_move or offensive_move or force_block_move or immediate_move or vct_move

        # Is this a critical move that should NOT be overridden by VCT counter-attack?
        is_critical = (critical_move is not None) or (force_block_move is not None)

        # Phase 3: Time Banking on ALL decided moves, or Full Search
        result = None
        if decided_move is not None and constants.TIME_BANK_ENABLED:
            # We have a decided move - use remaining time to warm TT
            result = self._time_banked_return(board, player, decided_move, start_time, is_critical)
        elif decided_move is not None:
            # Time banking disabled - return immediately
            result = decided_move
        else:
            # No decided move - do full iterative deepening search
            result = self._full_iterative_search(board, player, start_time)

        # Final fallback: ensure we ALWAYS return a valid move (prevents timeout)
        if result is None:
            valid_moves = board.get_valid_moves()
            if valid_moves:
                result = valid_moves[0]
                logger.warning(f"Final fallback to first valid move: {result}")

        return result

    def _time_banked_return(
        self,
        board,
        player: int,
        decided_move: Tuple[int, int],
        start_time: float,
        is_critical: bool = False
    ) -> Tuple[int, int]:
        """
        Return decided move at deadline, using remaining time productively.

        Two phases:
        1. TT Warming (~60% of time): Deep search on predicted opponent responses
        2. Counter-attack Search (~35% of time): Look for better offensive moves

        This ensures we use the full 4.5s even when we found a fast move.
        """
        logger = get_logger()
        elapsed = time.time() - start_time
        remaining = constants.RESPONSE_DEADLINE - elapsed

        logger.debug(f"Time bank: elapsed={elapsed:.3f}s, remaining={remaining:.3f}s")

        if remaining < constants.MIN_THINKING_TIME:
            logger.debug(f"Skipping time bank (remaining < {constants.MIN_THINKING_TIME}s)")
            return decided_move

        # Create board with our decided move played
        future_board = board.copy()
        future_board.place_stone(decided_move[0], decided_move[1], player)

        # Predict opponent responses for TT warming
        opponent = 3 - player
        predicted_responses = self._get_top_opponent_moves(
            future_board, opponent, count=constants.TT_WARMUP_POSITIONS
        )

        # Storage for potential better move found during counter-attack search
        better_move = [None]

        def productive_thread():
            """Use time for TT warming AND counter-attack search."""
            nonlocal better_move

            # Phase 1: TT Warming (~60% of remaining time)
            warm_budget = remaining * 0.6
            warm_start = time.time()

            for pred_move in predicted_responses:
                if self.stop_search or (time.time() - warm_start) > warm_budget:
                    break

                pred_board = future_board.copy()
                pred_board.place_stone(pred_move[0], pred_move[1], opponent)

                # Iterative deepening on each position for deeper TT entries
                for d in range(2, constants.TT_WARMUP_DEPTH + 1, 2):
                    if self.stop_search or (time.time() - warm_start) > warm_budget:
                        break
                    self._search_at_depth(pred_board, player, depth=d)

            # Phase 2: Counter-attack search (~35% of remaining time)
            # SKIP if move is critical (must block) or if stopped
            # Critical moves are: win/block5 (critical_move) or blocking fours/open_threes (force_block_move)
            if self.stop_search or is_critical:
                return

            # Only search for counter-attack if we're defending (not winning)
            # This avoids wasting time when we already have a winning move
            attack_budget = remaining * 0.35

            # Quick VCT search to see if we have a winning sequence
            try:
                vct = self._threat_space_search(
                    board, player, max_depth=10, time_limit=attack_budget
                )
                if vct and vct != decided_move:
                    # Found a potentially better offensive move
                    better_move[0] = vct
                    logger.info(f"Counter-attack found: {vct} (was defending: {decided_move})")
            except Exception:
                # Ignore errors in counter-attack search
                pass

        # Spawn thread and reset stop flag
        self.stop_search = False
        thread = threading.Thread(target=productive_thread, daemon=True)
        thread.start()

        current_elapsed = time.time() - start_time
        actual_remaining = constants.RESPONSE_DEADLINE - current_elapsed
        sleep_time = max(0, actual_remaining - 0.30)
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Signal stop and wait for cleanup
        self.stop_search = True
        thread.join(timeout=0.03)

        # Return better move if found, otherwise decided move
        final_move = better_move[0] if better_move[0] else decided_move
        logger.debug(f"Time banked: returning {final_move} after {time.time() - start_time:.2f}s")

        return final_move

    def _quick_tt_warm(
        self,
        board,
        player: int,
        our_move: Tuple[int, int],
        time_budget: float
    ) -> None:
        """
        Quick TT warming after iterative search.
        Uses remaining time to pre-compute likely future positions.
        """
        logger = get_logger()

        # Skip if budget too small (avoid timeout)
        if time_budget < 0.15:
            return

        start = time.time()

        # Create board with our move played
        future_board = board.copy()
        future_board.place_stone(our_move[0], our_move[1], player)

        # Predict opponent responses (only 1-2 to stay fast)
        opponent = 3 - player
        predictions = self._get_top_opponent_moves(future_board, opponent, count=2)

        self.stop_search = False
        warmed = 0

        for pred_move in predictions:
            # Check time BEFORE starting search
            if time.time() - start > time_budget * 0.8:
                break

            pred_board = future_board.copy()
            pred_board.place_stone(pred_move[0], pred_move[1], opponent)

            # Very shallow search to stay fast (depth 2 instead of 4)
            self._search_at_depth(pred_board, player, depth=2)
            warmed += 1

        logger.debug(f"Quick TT warm: {warmed}/{len(predictions)} in {time.time()-start:.2f}s")

    def _warm_tt_background(self, board, player: int) -> None:
        """
        Non-blocking TT warming (runs in background after ponder hit).
        Continues until stop_search is set or work is done.
        Called from a daemon thread, so it won't block the response.
        """
        logger = get_logger()
        self.stop_search = False
        opponent = 3 - player

        # Predict opponent responses and search them
        predicted_responses = self._get_top_opponent_moves(board, opponent, count=5)

        warmed = 0
        for pred_move in predicted_responses:
            if self.stop_search:
                break
            pred_board = board.copy()
            pred_board.place_stone(pred_move[0], pred_move[1], opponent)
            self._search_at_depth(pred_board, player, depth=constants.TT_WARMUP_DEPTH)
            warmed += 1

        logger.debug(f"Background TT warm: {warmed}/{len(predicted_responses)} done")

    def _full_iterative_search(
        self,
        board,
        player: int,
        start_time: float
    ) -> Optional[Tuple[int, int]]:
        """Full iterative deepening search with time control and aspiration windows."""
        logger = get_logger()
        best_move = [None]
        final_depth = [1]
        search_finished = [False]

        def search_thread():
            current_depth = 1
            previous_value = 0  # Initial guess for aspiration windows

            while not self.stop_search and current_depth <= constants.MAX_DEPTH:
                # Use aspiration windows for depth >= ASPIRATION_MIN_DEPTH
                if current_depth >= constants.ASPIRATION_MIN_DEPTH:
                    alpha = previous_value - constants.ASPIRATION_DELTA
                    beta = previous_value + constants.ASPIRATION_DELTA

                    move, value = self._search_at_depth_with_window(
                        board, player, current_depth, alpha, beta
                    )

                    # Re-search with full window if outside aspiration bounds
                    if value <= alpha or value >= beta:
                        move, value = self._search_at_depth(board, player, current_depth)
                else:
                    move, value = self._search_at_depth(board, player, current_depth)

                if move is not None:
                    best_move[0] = move
                    previous_value = value

                final_depth[0] = current_depth
                current_depth += 1

            search_finished[0] = True

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

        # Wait for search time (leave 0.3s safety margin)
        search_time = constants.RESPONSE_DEADLINE - 0.3
        elapsed = time.time() - start_time
        time.sleep(max(0, search_time - elapsed))

        self.stop_search = True
        thread.join(timeout=0.1)

        total_elapsed = time.time() - start_time
        logger.search(final_depth[0], self.nodes, total_elapsed, best_move[0])

        # Time banking: use remaining time to warm TT for next turn (only if enough time)
        remaining = constants.RESPONSE_DEADLINE - (time.time() - start_time)
        if best_move[0] is not None and constants.TIME_BANK_ENABLED and remaining > 0.2:
            self._quick_tt_warm(board, player, best_move[0], remaining - 0.15)

        # Fallback: if no move found, return first valid move (prevents timeout/None)
        if best_move[0] is None:
            valid_moves = board.get_valid_moves()
            if valid_moves:
                best_move[0] = valid_moves[0]
                logger.warning(f"Fallback to first valid move in iterative search: {best_move[0]}")

        return best_move[0]

    def _get_top_opponent_moves(
        self,
        board,
        opponent: int,
        count: int = 5
    ) -> List[Tuple[int, int]]:
        """Get top N predicted opponent moves by heuristic."""
        moves = board.get_valid_moves()
        scored_moves = []
        for move in moves:
            score = self._move_heuristic(board, move, opponent)
            scored_moves.append((move, score))
        scored_moves.sort(key=lambda x: -x[1])
        return [m[0] for m in scored_moves[:count]]

    def _get_best_move_fixed_depth(
        self, board, player: int
    ) -> Optional[Tuple[int, int]]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()
        if not moves:
            return None

        depth = self._get_depth(board.move_count)

        for move in moves:
            board.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
            )
            board.undo_stone(move[0], move[1], player)
            if value > best_value:
                best_value = value
                best_move = move

        return best_move

    def _search_at_depth(
        self, board, player: int, depth: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board.get_valid_moves()

        for move in moves:
            board.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
            )
            board.undo_stone(move[0], move[1], player)
            if value > best_value:
                best_value = value
                best_move = move

        return best_move, best_value

    def _get_depth(self, move_count: int) -> int:
        if move_count < 10:
            return constants.DEPTH_EARLY
        elif move_count < 30:
            return constants.DEPTH_MID
        else:
            return constants.DEPTH_LATE

    def negamax(
        self, board, depth: int, alpha: int, beta: int, current_player: int
    ) -> int:
        if self.stop_search:
            return 0
        self.nodes += 1

        hash_key = board.current_hash
        tt_best_move = None

        if hash_key in self.transposition_table:
            entry = self.transposition_table[hash_key]
            tt_best_move = entry.get("best_move")
            if entry["age"] == self.age and entry["depth"] >= depth:
                if entry["flag"] == constants.EXACT:
                    return entry["value"]
                elif entry["flag"] == constants.LOWER and entry["value"] >= beta:
                    return entry["value"]
                elif entry["flag"] == constants.UPPER and entry["value"] <= alpha:
                    return entry["value"]

        if board.is_full():
            return self.evaluate(board) * (1 if current_player == 1 else -1)

        if depth == 0:
            return self.quiescence_search(board, alpha, beta, current_player)

        max_eval = -constants.INFINITY
        best_move = None
        moves = board.get_valid_moves()
        opponent = 3 - current_player
        original_alpha = alpha

        # Move ordering: TT best move first, then killer moves, then by history
        if tt_best_move and tt_best_move in moves:
            moves.remove(tt_best_move)
            moves.insert(0, tt_best_move)

        killers = self.killer_moves.get(depth, [])
        for killer in reversed(killers):
            if killer in moves and killer != tt_best_move:
                moves.remove(killer)
                moves.insert(1 if tt_best_move else 0, killer)

        # Sort remaining moves by history heuristic
        # Keep TT and killer moves at front by giving them high scores
        def history_sort_key(m):
            if m == tt_best_move:
                return constants.INFINITY
            if m in killers:
                return constants.INFINITY - 1
            return self._get_history_score(m, current_player)

        moves.sort(key=history_sort_key, reverse=True)

        for move_index, move in enumerate(moves):
            if self.stop_search:
                break

            board.place_stone(move[0], move[1], current_player)

            # Determine if LMR applies to this move
            use_lmr = (
                move_index >= constants.LMR_FULL_MOVES and
                depth >= constants.LMR_MIN_DEPTH and
                not self._is_tactical_move(board, move, current_player)
            )

            if move_index == 0:
                # PV move: full window, full depth
                eval = -self.negamax(board, depth - 1, -beta, -alpha, opponent)
            elif use_lmr:
                # LMR: reduced depth, null window
                reduced_depth = max(1, depth - 1 - constants.LMR_REDUCTION)
                eval = -self.negamax(board, reduced_depth, -alpha - 1, -alpha, opponent)

                # Re-search with full depth if improved
                if eval > alpha:
                    eval = -self.negamax(board, depth - 1, -beta, -alpha, opponent)
            else:
                # Non-PV without LMR: null window, full depth (PVS)
                eval = -self.negamax(board, depth - 1, -alpha - 1, -alpha, opponent)

                # Re-search with full window if improved
                if alpha < eval < beta:
                    eval = -self.negamax(board, depth - 1, -beta, -alpha, opponent)

            board.undo_stone(move[0], move[1], current_player)

            if eval > max_eval:
                max_eval = eval
                best_move = move

            alpha = max(alpha, eval)
            if alpha >= beta:
                self._add_killer_move(depth, move)
                self._update_history(move, current_player, depth)
                break

        if max_eval <= original_alpha:
            flag = constants.UPPER
        elif max_eval >= beta:
            flag = constants.LOWER
        else:
            flag = constants.EXACT
        self.transposition_table[hash_key] = {
            "value": max_eval,
            "depth": depth,
            "flag": flag,
            "age": self.age,
            "best_move": best_move,
        }

        return max_eval

    def _add_killer_move(self, depth: int, move: Tuple[int, int]) -> None:
        """Track killer moves (moves that cause beta cutoffs)."""
        if depth not in self.killer_moves:
            self.killer_moves[depth] = []
        killers = self.killer_moves[depth]
        if move not in killers:
            killers.insert(0, move)
            if len(killers) > 2:
                killers.pop()

    def _update_history(self, move: Tuple[int, int], player: int, depth: int) -> None:
        """
        Update history score for a move that caused a beta cutoff.

        Args:
            move: The move (x, y)
            player: Player who made the move
            depth: Search depth where cutoff occurred (deeper = more valuable)
        """
        # Bonus scales with depth squared (deeper cutoffs are more significant)
        if constants.HISTORY_BONUS_DEPTH:
            bonus = depth * depth
        else:
            bonus = 1

        if move not in self.history_table[player]:
            self.history_table[player][move] = 0

        self.history_table[player][move] += bonus

        # Cap to prevent overflow
        if self.history_table[player][move] > constants.HISTORY_MAX_VALUE:
            self.history_table[player][move] = constants.HISTORY_MAX_VALUE

    def _decay_history(self) -> None:
        """
        Decay all history scores to prevent stale data from dominating.
        Called at the start of each new search (when age increments).
        """
        for player in [1, 2]:
            for move in list(self.history_table[player].keys()):
                self.history_table[player][move] = int(
                    self.history_table[player][move] * constants.HISTORY_DECAY_FACTOR
                )
            # Remove entries that decayed to 0
            self.history_table[player] = {
                m: s for m, s in self.history_table[player].items() if s > 0
            }

    def _get_history_score(self, move: Tuple[int, int], player: int) -> int:
        """Get history score for a move."""
        return self.history_table[player].get(move, 0)

    def quiescence_search(
        self, board, alpha: int, beta: int, current_player: int, qs_depth: int = 0
    ) -> int:
        """
        Quiescence search - continue searching only tactical moves at leaf nodes.

        Extends search at depth=0 to resolve tactical sequences and avoid
        the horizon effect where a critical threat is missed just beyond
        the search depth.

        Args:
            board: Current board state
            alpha: Alpha bound
            beta: Beta bound
            current_player: Player to move (1 or 2)
            qs_depth: Current quiescence depth (starts at 0)

        Returns:
            Evaluation score for the position
        """
        if self.stop_search:
            return 0
        self.nodes += 1

        # Stand-pat evaluation: the score if we choose not to make any tactical move
        stand_pat = self.evaluate(board) * (1 if current_player == 1 else -1)

        # Beta cutoff: position is already too good for opponent
        if stand_pat >= beta:
            return beta

        if stand_pat > alpha:
            alpha = stand_pat

        # Depth limit to prevent explosion
        if qs_depth >= constants.QUIESCENCE_MAX_DEPTH:
            return alpha

        # Delta pruning: if even the best tactical outcome can't improve alpha
        if stand_pat + constants.QUIESCENCE_DELTA < alpha:
            return alpha

        tactical_moves = self._get_quiescence_moves(board, current_player)

        if not tactical_moves:
            return stand_pat

        opponent = 3 - current_player

        for move in tactical_moves:
            if self.stop_search:
                break

            board.place_stone(move[0], move[1], current_player)

            score = -self.quiescence_search(board, -beta, -alpha, opponent, qs_depth + 1)

            board.undo_stone(move[0], move[1], current_player)

            if score >= beta:
                return beta  # Beta cutoff
            if score > alpha:
                alpha = score

        return alpha

    def _get_quiescence_moves(
        self, board, player: int
    ) -> List[Tuple[int, int]]:
        """
        Get moves to explore in quiescence search.

        Only returns tactical moves: winning moves, fours, open threes,
        and critical blocks. Limited to top 8 moves by priority.
        """
        tactical = []
        opponent = 3 - player
        all_moves = board.get_valid_moves()

        for move in all_moves:
            x, y = move

            board.place_stone(x, y, player)
            if board.check_win(x, y, player):
                board.undo_stone(x, y, player)
                return [move]

            our_threats = self._count_threats_cached(board, x, y, player)
            board.undo_stone(x, y, player)

            if our_threats["open_fours"] > 0 or our_threats["closed_fours"] > 0:
                tactical.append((move, 100))
                continue

            if our_threats["open_threes"] > 0:
                tactical.append((move, 50))
                continue

            board.place_stone(x, y, opponent)
            if board.check_win(x, y, opponent):
                board.undo_stone(x, y, opponent)
                tactical.append((move, 200))
                continue

            opp_threats = self._count_threats_cached(board, x, y, opponent)
            board.undo_stone(x, y, opponent)

            if opp_threats["open_fours"] > 0 or opp_threats["closed_fours"] > 0:
                tactical.append((move, 90))
            elif opp_threats["open_threes"] > 0:
                tactical.append((move, 40))

        tactical.sort(key=lambda x: -x[1])
        return [m[0] for m in tactical[:constants.QUIESCENCE_MAX_MOVES]]

    def _is_tactical_move(self, board, move: Tuple[int, int], player: int) -> bool:
        """
        Check if move is tactical (should not be reduced by LMR).
        Lightweight check - only examines our threats since stone is already placed.
        """
        x, y = move
        threats = self._count_threats_cached(board, x, y, player)

        if threats["open_fours"] > 0 or threats["closed_fours"] > 0:
            return True
        if threats["open_threes"] > 0:
            return True

        # For blocking detection, use a lightweight pattern check
        # without expensive board manipulation
        opponent = 3 - player
        opp_str = str(opponent)
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)
            # If line contains 3+ opponent stones nearby, likely blocking a threat
            if line.count(opp_str) >= 3:
                return True

        return False

    def evaluate(self, board) -> int:
        # If cache is empty and board has stones, do full evaluation
        if not board.eval_cache and board.move_count > 0:
            for y in range(board.height):
                for x in range(board.width):
                    stone = board.grid[y][x]
                    if stone != 0:
                        score = self._evaluate_position(board, x, y, stone)
                        board.eval_cache[(x, y, stone)] = score
                        board.eval_totals[stone] += score
            board.eval_dirty.clear()
        else:
            # Process dirty positions (incremental update)
            for x, y in board.eval_dirty:
                stone = board.grid[y][x]
                # Remove old cached score if exists
                for player in [1, 2]:
                    key = (x, y, player)
                    if key in board.eval_cache:
                        board.eval_totals[player] -= board.eval_cache[key]
                        del board.eval_cache[key]
                # Add new score if position has a stone
                if stone != 0:
                    score = self._evaluate_position(board, x, y, stone)
                    board.eval_cache[(x, y, stone)] = score
                    board.eval_totals[stone] += score
            board.eval_dirty.clear()

        return int(
            constants.ATTACK_MULTIPLIER * board.eval_totals[1]
            - constants.DEFENSE_MULTIPLIER * board.eval_totals[2]
        )

    def _evaluate_position(self, board, x: int, y: int, player: int) -> int:
        score = 0
        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)
            score += self._evaluate_line(line, player)
        return score

    def _get_line(self, board, x: int, y: int, dx: int, dy: int) -> str:
        line = []
        for i in range(-4, 5):
            nx, ny = x + i * dx, y + i * dy
            if 0 <= nx < board.width and 0 <= ny < board.height:
                stone = board.grid[ny][nx]
                line.append(str(stone) if stone != 0 else ".")
            else:
                line.append("#")
        return "".join(line)

    def _evaluate_line(self, line: str, player: int) -> int:

        patterns = constants.PATTERNS[player]

        score = 0

        if patterns["winning"]["five"] in line:
            score += constants.SCORE_FIVE
        if patterns["winning"]["open_four"] in line:
            score += constants.SCORE_OPEN_FOUR
        for pat in patterns["winning"]["closed_four"]:
            if pat in line:
                score += constants.SCORE_CLOSED_FOUR
                break
        for pat in patterns["winning"]["split_four"]:
            if pat in line:
                score += constants.SCORE_SPLIT_FOUR
                break

        if patterns["threat"]["open_three"] in line:
            score += constants.SCORE_OPEN_THREE
        for pat in patterns["threat"]["closed_three"]:
            if pat in line:
                score += constants.SCORE_CLOSED_THREE
                break
        for pat in patterns["threat"]["split_three"]:
            if pat in line:
                score += constants.SCORE_SPLIT_THREE
                break
        for pat in patterns["threat"]["broken_open_three"]:
            if pat in line:
                score += constants.SCORE_BROKEN_THREE
                break

        if patterns["development"]["open_two"] in line:
            score += constants.SCORE_OPEN_TWO
        for pat in patterns["development"]["closed_two"]:
            if pat in line:
                score += constants.SCORE_CLOSED_TWO
                break

        return score

    def _search_at_depth(
        self, board, player: int, depth: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        board_copy = board.copy()
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board_copy.get_valid_moves()
        moves = sorted(
            moves, key=lambda m: -self._move_heuristic(board_copy, m, player)
        )[:12]

        for move in moves:
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -constants.INFINITY, constants.INFINITY, opponent
            )
            board_copy.undo_stone(move[0], move[1], player)
            if value > best_value:
                best_value = value
                best_move = move

        return best_move, best_value

    def _search_at_depth_with_window(
        self, board, player: int, depth: int, alpha: int, beta: int
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        """Search at fixed depth with custom alpha-beta window (for aspiration windows)."""
        board_copy = board.copy()
        opponent = 3 - player
        best_move = None
        best_value = -constants.INFINITY

        moves = board_copy.get_valid_moves()
        moves = sorted(
            moves, key=lambda m: -self._move_heuristic(board_copy, m, player)
        )[:12]

        for move in moves:
            board_copy.place_stone(move[0], move[1], player)
            value = -self.negamax(
                board_copy, depth - 1, -beta, -alpha, opponent
            )
            board_copy.undo_stone(move[0], move[1], player)

            if value > best_value:
                best_value = value
                best_move = move

            alpha = max(alpha, value)
            if alpha >= beta:
                break

        return best_move, best_value

    def _move_heuristic(self, board, move, player: int) -> int:
        x, y = move
        opponent = 3 - player

        # Phase 1: Evaluate our move (stone placed)
        board.place_stone(x, y, player)

        if board.check_win(x, y, player):
            board.undo_stone(x, y, player)
            return constants.MOVE_WIN

        # Compute our threats ONCE and cache score
        our_threats = self._count_threats_cached(board, x, y, player)
        our_score = self._evaluate_position(board, x, y, player)

        total_fours = our_threats["open_fours"] + our_threats["closed_fours"]

        if total_fours >= 2:
            board.undo_stone(x, y, player)
            return constants.MOVE_DOUBLE_FOUR

        if total_fours >= 1 and our_threats["open_threes"] >= 1:
            board.undo_stone(x, y, player)
            return constants.MOVE_FOUR_THREE

        if our_threats["open_fours"] >= 1:
            board.undo_stone(x, y, player)
            return constants.MOVE_OPEN_FOUR

        if our_threats["open_threes"] >= 2:
            board.undo_stone(x, y, player)
            return constants.MOVE_FORK

        board.undo_stone(x, y, player)

        # Phase 2: Evaluate blocking opponent
        board.place_stone(x, y, opponent)
        blocks_win = board.check_win(x, y, opponent)

        if blocks_win:
            board.undo_stone(x, y, opponent)
            board.place_stone(x, y, player)
            opp_still_wins = self._has_winning_move(board, opponent)
            board.undo_stone(x, y, player)
            if opp_still_wins:
                return constants.MOVE_BLOCK_WIN // 2
            return constants.MOVE_BLOCK_WIN

        opp_threats = self._count_threats_cached(board, x, y, opponent)
        board.undo_stone(x, y, opponent)

        opp_fours = opp_threats["open_fours"] + opp_threats["closed_fours"]

        if opp_fours >= 2:
            return constants.MOVE_BLOCK_DOUBLE_FOUR

        if opp_fours >= 1 and opp_threats["open_threes"] >= 1:
            return constants.MOVE_BLOCK_FOUR_THREE

        if opp_threats["open_fours"] >= 1:
            return constants.MOVE_BLOCK_OPEN_FOUR

        if opp_threats.get("pre_open_fours", 0) >= 1:
            return constants.MOVE_BLOCK_PRE_OPEN_FOUR

        if opp_threats["split_threes"] >= 1:
            return constants.MOVE_BLOCK_SPLIT_THREE

        if opp_threats["open_threes"] >= 1:
            return constants.MOVE_BLOCK_OPEN_THREE

        if opp_threats.get("building_twos", 0) >= 1:
            return constants.MOVE_BLOCK_BUILDING_TWO

        # Phase 3: Return score based on our threats (already computed in Phase 1)
        if our_threats["split_threes"] >= 1:
            return constants.MOVE_SPLIT_THREE

        if our_score >= constants.SCORE_OPEN_THREE:
            return constants.MOVE_OPEN_THREE

        return our_score

    def _has_winning_move(self, board, player: int) -> bool:
        """Check if player has a winning move."""
        valid_moves = board.get_valid_moves()
        for mx, my in valid_moves:
            board.place_stone(mx, my, player)
            if board.check_win(mx, my, player):
                board.undo_stone(mx, my, player)
                return True
            board.undo_stone(mx, my, player)
        return False

    def _count_critical_threats(self, board, player: int) -> dict:
        """Count critical threats for a player across the entire board."""
        critical = {"winning": 0, "four_three": 0, "double_four": 0}
        valid_moves = board.get_valid_moves()

        for mx, my in valid_moves:
            board.place_stone(mx, my, player)

            if board.check_win(mx, my, player):
                critical["winning"] += 1
            else:
                threats = self._count_threats_cached(board, mx, my, player)
                total_fours = threats["open_fours"] + threats["closed_fours"]
                if total_fours >= 2:
                    critical["double_four"] += 1
                elif total_fours >= 1 and threats["open_threes"] >= 1:
                    critical["four_three"] += 1

            board.undo_stone(mx, my, player)

            # Early exit if already too many threats
            if critical["winning"] >= 2 or critical["four_three"] >= 2:
                break

        return critical

    def _check_immediate_critical(self, board, player: int) -> Optional[Tuple[int, int]]:
        """
        Ultra-fast check (< 1ms) for critical moves.
        Called BEFORE any search to guarantee a response.

        Checks:
        1. Immediate winning move (5 in a row)
        2. Block opponent's immediate win

        Returns move if found, None otherwise.
        """
        opponent = 3 - player
        valid_moves = board.get_valid_moves()

        # Limit to top 20 moves for speed (center-biased by get_valid_moves)
        check_moves = valid_moves[:20]

        # 1. Check if we can win immediately
        for move in check_moves:
            x, y = move
            board.place_stone(x, y, player)
            if board.check_win(x, y, player):
                board.undo_stone(x, y, player)
                return move  # Winning move!
            board.undo_stone(x, y, player)

        # 2. Check if opponent wins with any move (we must block)
        for move in check_moves:
            x, y = move
            board.place_stone(x, y, opponent)
            if board.check_win(x, y, opponent):
                board.undo_stone(x, y, opponent)
                return move  # Block opponent's win!
            board.undo_stone(x, y, opponent)

        return None

    def _get_immediate_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        moves = board.get_valid_moves()
        best_move = None
        best_score = -1

        for move in moves:
            score = self._move_heuristic(board, move, player)
            if score > best_score:
                best_score = score
                best_move = move

        # Use lower threshold to catch split_three blocks too
        if best_score >= constants.IMMEDIATE_MOVE_THRESHOLD:
            return best_move

        return None

    def _find_our_best_threat(
        self, board, player: int
    ) -> Optional[Tuple[Tuple[int, int], str]]:
        """
        Find our best offensive move.

        Returns (move, threat_type) or None.
        threat_type: 'win', 'fork', 'four', 'open_three', 'building'

        Priority: win > fork > four > open_three > building
        """
        best_move = None
        best_type = None

        valid_moves = board.get_valid_moves()[:20]  # Limit for speed

        for move in valid_moves:
            x, y = move
            board.place_stone(x, y, player)

            # Check for win (five)
            if board.check_win(x, y, player):
                board.undo_stone(x, y, player)
                return (move, 'win')

            threats = self._count_threats_cached(board, x, y, player)
            board.undo_stone(x, y, player)

            total_fours = threats["open_fours"] + threats["closed_fours"]

            # Fork: double four or four+open_three (unstoppable)
            if total_fours >= 2 or (total_fours >= 1 and threats["open_threes"] >= 1):
                return (move, 'fork')  # Best possible, return immediately

            # Four (forces opponent to block)
            if total_fours >= 1 and best_type not in ['fork']:
                best_move = move
                best_type = 'four'

            # Open three (only if no better found)
            if threats["open_threes"] >= 1 and best_type is None:
                best_move = move
                best_type = 'open_three'

            # Building move (develop position with open two)
            if threats.get("building_twos", 0) >= 1 and best_type is None:
                best_move = move
                best_type = 'building'

        if best_move and best_type:
            return (best_move, best_type)
        return None

    def _get_early_game_move(
        self, board, player: int, opponent: int
    ) -> Optional[Tuple[int, int]]:
        """
        Get a good move in the early game (first few moves).
        Prioritizes moves that are:
        1. Adjacent to our existing stones (connected)
        2. Near opponent stones (contesting space)
        3. Between our stone and opponent's stone
        """
        our_stones = []
        opp_stones = []

        for y in range(board.height):
            for x in range(board.width):
                if board.grid[y][x] == player:
                    our_stones.append((x, y))
                elif board.grid[y][x] == opponent:
                    opp_stones.append((x, y))

        if not our_stones or not opp_stones:
            return None

        # Find moves that are adjacent to our stones AND near opponent
        best_move = None
        best_score = -1

        for ox, oy in our_stones:
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = ox + dx, oy + dy
                    if (0 <= nx < board.width and 0 <= ny < board.height
                            and board.grid[ny][nx] == 0):
                        score = 0
                        dist = max(abs(dx), abs(dy))
                        if dist == 1:
                            score += 10
                        else:
                            score += 5

                        for ex, ey in opp_stones:
                            opp_dist = max(abs(nx - ex), abs(ny - ey))
                            if opp_dist <= 2:
                                score += (3 - opp_dist) * 3

                        for ex, ey in opp_stones:
                            if ox != ex or oy != ey:
                                dir_x = 1 if ex > ox else (-1 if ex < ox else 0)
                                dir_y = 1 if ey > oy else (-1 if ey < oy else 0)
                                if dx == dir_x and dy == dir_y:
                                    score += 8

                        if score > best_score:
                            best_score = score
                            best_move = (nx, ny)

        return best_move

    def _count_threats_cached(self, board, x: int, y: int, player: int) -> dict:
        """Count threats with caching based on board hash."""
        cache_key = (board.current_hash, x, y, player)
        if cache_key in self.threat_cache:
            return self.threat_cache[cache_key]

        threats = self._count_threats(board, x, y, player)

        # Limit cache size to prevent memory issues
        if len(self.threat_cache) < 10000:
            self.threat_cache[cache_key] = threats

        return threats

    def _count_threats(self, board, x: int, y: int, player: int) -> dict:
        """Count threats created by a stone at (x, y)."""
        threats = {
            "fives": 0,
            "open_fours": 0,
            "closed_fours": 0,
            "open_threes": 0,
            "split_threes": 0,
            "pre_open_fours": 0,  # .XXX. pattern - becomes open four
            "building_twos": 0,   # .XX. pattern - can become open three
        }
        patterns = constants.PATTERNS[player]
        player_str = str(player)
        # Pre-open-four pattern: .XXX. (3 in row with both ends open)
        pre_open_four_pattern = f".{player_str * 3}."
        # Building two pattern: .XX. (2 in row with both ends open)
        building_two_pattern = f".{player_str * 2}."

        for dx, dy in constants.DIRECTIONS:
            line = self._get_line(board, x, y, dx, dy)

            if patterns["winning"]["five"] in line:
                threats["fives"] += 1
                continue

            if patterns["winning"]["open_four"] in line:
                threats["open_fours"] += 1
                continue

            four_found = False
            for pat in patterns["winning"]["closed_four"]:
                if pat in line:
                    threats["closed_fours"] += 1
                    four_found = True
                    break
            if not four_found:
                for pat in patterns["winning"]["split_four"]:
                    if pat in line:
                        threats["closed_fours"] += 1
                        break

            # Check pre-open-four (.XXX. - will become open four next move)
            if pre_open_four_pattern in line:
                threats["pre_open_fours"] += 1

            if patterns["threat"]["open_three"] in line:
                threats["open_threes"] += 1
            else:
                # Check split three patterns (XX.X, X.XX, X.X.X)
                for pat in patterns["threat"]["split_three"]:
                    if pat in line:
                        threats["split_threes"] += 1
                        break

            # Check building two (.XX. - can become open three)
            if building_two_pattern in line:
                threats["building_twos"] += 1

        return threats

    def _scan_board_threats(self, board, opponent: int) -> dict:
        """
        Scan entire board for opponent threat patterns.
        Returns dict of critical threats requiring immediate action.
        """
        threats = {
            "fours": [],        # Four in a row (or split four)
            "open_threes": [],  # Open three (.XXX.)
            "split_threes": [], # Split three (XX.X, X.XX)
            "building_twos": [], # Two stones that can become three (.XX.)
        }

        for dx, dy in constants.DIRECTIONS:
            direction_name = self._direction_name(dx, dy)

            if dx == 1 and dy == 0:  # Horizontal
                for y in range(board.height):
                    self._scan_line(
                        board, 0, y, dx, dy, opponent, threats, direction_name
                    )
            elif dx == 0 and dy == 1:  # Vertical
                for x in range(board.width):
                    self._scan_line(
                        board, x, 0, dx, dy, opponent, threats, direction_name
                    )
            elif dx == 1 and dy == 1:  # Diagonal backslash
                for start in range(board.width + board.height - 1):
                    x = max(0, start - board.height + 1)
                    y = max(0, board.height - 1 - start)
                    self._scan_line(
                        board, x, y, dx, dy, opponent, threats, direction_name
                    )
            elif dx == 1 and dy == -1:  # Diagonal slash
                for start in range(board.width + board.height - 1):
                    x = max(0, start - board.height + 1)
                    y = min(board.height - 1, start)
                    self._scan_line(
                        board, x, y, dx, dy, opponent, threats, direction_name
                    )

        return threats

    def _scan_line(
        self,
        board,
        start_x: int,
        start_y: int,
        dx: int,
        dy: int,
        opponent: int,
        threats: dict,
        direction: str
    ):
        """Scan a single line for threat patterns."""
        opp_str = str(opponent)
        line = []
        positions = []

        x, y = start_x, start_y
        while 0 <= x < board.width and 0 <= y < board.height:
            stone = board.grid[y][x]
            line.append(str(stone) if stone else ".")
            positions.append((x, y))
            x += dx
            y += dy

        if len(positions) < 4:
            return

        line_str = "".join(line)

        # Check for four (XXXX or XXX.X, etc)
        four_patterns = [
            (opp_str * 4, None),
            (f"{opp_str * 3}.{opp_str}", 3),
            (f"{opp_str}.{opp_str * 3}", 1),
            (f"{opp_str * 2}.{opp_str * 2}", 2),
        ]
        for pat, gap_offset in four_patterns:
            idx = 0
            while True:
                idx = line_str.find(pat, idx)
                if idx == -1:
                    break
                threat_positions = positions[idx:idx + len(pat)]
                gap_pos = positions[idx + gap_offset] if gap_offset is not None else None
                threats["fours"].append({
                    "positions": threat_positions,
                    "direction": direction,
                    "gap": gap_pos,
                    "pattern": pat
                })
                idx += 1

        # Check for open three .XXX.
        open_three = f".{opp_str * 3}."
        idx = 0
        while True:
            idx = line_str.find(open_three, idx)
            if idx == -1:
                break
            threats["open_threes"].append({
                "positions": positions[idx:idx + 5],
                "direction": direction,
                "blocks": [positions[idx], positions[idx + 4]]
            })
            idx += 1

        # Check for split three patterns (XX.X, X.XX)
        split_patterns = [
            (f"{opp_str * 2}.{opp_str}", 2),  # XX.X
            (f"{opp_str}.{opp_str * 2}", 1),  # X.XX
        ]
        for pat, gap_offset in split_patterns:
            idx = 0
            while True:
                idx = line_str.find(pat, idx)
                if idx == -1:
                    break
                threats["split_threes"].append({
                    "positions": positions[idx:idx + len(pat)],
                    "direction": direction,
                    "gap": positions[idx + gap_offset]
                })
                idx += 1

        # Check for building twos (.XX. patterns that can become open three)
        # This is proactive defense - stop threats before they become critical
        building_two = f".{opp_str * 2}."
        idx = 0
        while True:
            idx = line_str.find(building_two, idx)
            if idx == -1:
                break
            # Extension points are the dots on either side
            threats["building_twos"].append({
                "positions": positions[idx:idx + 4],
                "direction": direction,
                "extensions": [positions[idx], positions[idx + 3]]
            })
            idx += 1

    def _direction_name(self, dx: int, dy: int) -> str:
        """Get human-readable direction name."""
        if dx == 1 and dy == 0:
            return "horizontal"
        elif dx == 0 and dy == 1:
            return "vertical"
        elif dx == 1 and dy == 1:
            return "diagonal_\\"
        else:
            return "diagonal_/"

    def _get_threat_moves(self, board, player: int) -> List[Tuple[int, int]]:
        """Return moves that create threats (fours, threes)."""
        threat_moves = []
        valid_moves = board.get_valid_moves()

        for x, y in valid_moves:
            board.place_stone(x, y, player)
            threats = self._count_threats_cached(board, x, y, player)
            board.undo_stone(x, y, player)

            if (threats["open_fours"] > 0 or
                threats["closed_fours"] > 0 or
                threats["open_threes"] > 0):
                threat_moves.append((x, y))

        return threat_moves

    def _get_defense_moves(self, board, attacker: int) -> List[Tuple[int, int]]:
        """Return moves that block attacker's threats."""
        defender = 3 - attacker
        defense_moves = set()
        valid_moves = board.get_valid_moves()

        for x, y in valid_moves:
            # 1. Directly block a threat
            board.place_stone(x, y, attacker)
            threats = self._count_threats_cached(board, x, y, attacker)
            board.undo_stone(x, y, attacker)

            if (threats["fives"] > 0 or
                threats["open_fours"] > 0 or
                threats["closed_fours"] > 0 or
                threats["open_threes"] > 0):
                defense_moves.add((x, y))

            # 2. Create a counter-threat
            board.place_stone(x, y, defender)
            counter = self._count_threats_cached(board, x, y, defender)
            board.undo_stone(x, y, defender)

            if counter["open_fours"] > 0 or counter["closed_fours"] > 0:
                defense_moves.add((x, y))

        return list(defense_moves)

    def _vct_search(
        self, board, current_player: int, attacker: int,
        depth: int, max_depth: int
    ) -> bool:
        """
        DFS search for Victory by Continuous Threats.

        Returns:
            True if VCT found for attacker.
        """
        # Immediate win?
        if self._has_winning_move(board, attacker):
            return True

        # Depth limit
        if depth >= max_depth:
            return False

        if current_player == attacker:
            # Attacker's turn: find ONE threat move leading to VCT
            threat_moves = self._get_threat_moves(board, attacker)
            threat_moves.sort(
                key=lambda m: -self._move_heuristic(board, m, attacker)
            )

            for move in threat_moves[:8]:
                x, y = move
                board.place_stone(x, y, attacker)

                result = self._vct_search(
                    board, 3 - attacker, attacker,
                    depth + 1, max_depth
                )

                board.undo_stone(x, y, attacker)

                if result:
                    return True

            return False

        else:
            # Defender's turn: must block ALL threats
            defense_moves = self._get_defense_moves(board, attacker)

            if not defense_moves:
                return True

            defense_moves.sort(
                key=lambda m: -self._move_heuristic(board, m, current_player)
            )

            for move in defense_moves[:6]:
                x, y = move
                board.place_stone(x, y, current_player)

                result = self._vct_search(
                    board, attacker, attacker,
                    depth + 1, max_depth
                )

                board.undo_stone(x, y, current_player)

                if not result:
                    return False

            return True

    def _threat_space_search(
        self, board, player: int, max_depth: int = 14, time_limit: float = 1.5
    ) -> Optional[Tuple[int, int]]:
        """
        Search for Victory by Continuous Threats (VCT).

        Returns the move leading to a forced win, or None.
        Uses iterative deepening to find quick wins first.
        """
        start_time = time.time()

        if self._has_winning_move(board, player):
            return None

        threat_moves = self._get_threat_moves(board, player)
        if not threat_moves:
            return None

        threat_moves.sort(
            key=lambda m: -self._move_heuristic(board, m, player)
        )
        threat_moves = threat_moves[:16]

        # Iterative deepening: try shallow depths first for quick wins
        for vct_depth in [6, 10, max_depth]:
            if time.time() - start_time > time_limit * 0.9:
                break

            for move in threat_moves:
                if time.time() - start_time > time_limit:
                    break

                x, y = move
                board.place_stone(x, y, player)

                vct_found = self._vct_search(
                    board, 3 - player, player,
                    depth=1, max_depth=vct_depth
                )

                board.undo_stone(x, y, player)

                if vct_found:
                    return move

        return None
