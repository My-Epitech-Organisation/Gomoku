##
## EPITECH PROJECT, 2025
## Gomoku
## File description:
## ai
##

import sys
import threading
import time
from typing import List, Optional, Tuple

from . import constants


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
        self.transposition_table = {}
        self.killer_moves = {}
        self.age = 0

    def get_best_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        self.stop_search = False
        self.nodes = 0
        self.age += 1
        start_time = time.time()

        # Phase 1: Check for immediate/forced moves
        immediate_move = self._get_immediate_move(board, player)

        # Phase 2: Threat Space Search (VCT) if no immediate move
        vct_move = None
        if immediate_move is None:
            vct_move = self._threat_space_search(board, player, max_depth=14, time_limit=1.5)
            if vct_move is not None:
                print(f"[AI] VCT found: {vct_move}", file=sys.stderr)

        # Determine if we have a decided move
        decided_move = immediate_move or vct_move

        # Phase 3: Time Banking or Full Search
        if decided_move is not None and constants.TIME_BANK_ENABLED:
            # We have a forced move - use remaining time to warm TT
            return self._time_banked_return(board, player, decided_move, start_time)
        elif decided_move is not None:
            # Time banking disabled - return immediately
            return decided_move
        else:
            # No forced move - do full iterative deepening search
            return self._full_iterative_search(board, player, start_time)

    def _time_banked_return(
        self,
        board,
        player: int,
        decided_move: Tuple[int, int],
        start_time: float
    ) -> Tuple[int, int]:
        """
        Return decided move at deadline, using remaining time to warm TT.
        This pre-computes positions for likely future moves.
        """
        elapsed = time.time() - start_time
        remaining = constants.RESPONSE_DEADLINE - elapsed

        if remaining < constants.MIN_THINKING_TIME:
            return decided_move

        # Create board with our decided move played
        future_board = board.copy()
        future_board.place_stone(decided_move[0], decided_move[1], player)

        # Predict opponent responses and search them to warm TT
        opponent = 3 - player
        predicted_responses = self._get_top_opponent_moves(future_board, opponent, count=3)

        def warm_tt_thread():
            """Background: shallow search on predicted positions."""
            for pred_move in predicted_responses:
                if self.stop_search:
                    break
                pred_board = future_board.copy()
                pred_board.place_stone(pred_move[0], pred_move[1], opponent)
                # Shallow search to populate TT
                self._search_at_depth(pred_board, player, depth=constants.TT_WARMUP_DEPTH)

        thread = threading.Thread(target=warm_tt_thread, daemon=True)
        thread.start()

        # Wait until deadline
        time.sleep(max(0, remaining - 0.05))  # 50ms safety margin
        self.stop_search = True
        thread.join(timeout=0.05)

        print(
            f"[AI] Time banked: warmed TT for {len(predicted_responses)} predictions",
            file=sys.stderr,
        )

        return decided_move

    def _full_iterative_search(
        self,
        board,
        player: int,
        start_time: float
    ) -> Optional[Tuple[int, int]]:
        """Full iterative deepening search with time control."""
        best_move = [None]

        def search_thread():
            current_depth = 1
            while not self.stop_search:
                move, value = self._search_at_depth(board, player, current_depth)
                if move is not None:
                    best_move[0] = move
                current_depth += 1

            elapsed = time.time() - start_time
            print(
                f"[AI] Stats: depth {current_depth-1}, nodes {self.nodes}, "
                f"time {elapsed:.2f}s",
                file=sys.stderr,
            )

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

        elapsed = time.time() - start_time
        remaining = constants.RESPONSE_DEADLINE - elapsed
        time.sleep(max(0, remaining))

        self.stop_search = True
        thread.join(timeout=0.1)

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

        if depth == 0 or board.is_full():
            return self.evaluate(board) * (1 if current_player == 1 else -1)

        max_eval = -constants.INFINITY
        best_move = None
        moves = board.get_valid_moves()
        opponent = 3 - current_player
        original_alpha = alpha

        # Move ordering: TT best move first, then killer moves
        if tt_best_move and tt_best_move in moves:
            moves.remove(tt_best_move)
            moves.insert(0, tt_best_move)

        killers = self.killer_moves.get(depth, [])
        for killer in reversed(killers):
            if killer in moves and killer != tt_best_move:
                moves.remove(killer)
                moves.insert(1 if tt_best_move else 0, killer)

        for move in moves:
            board.place_stone(move[0], move[1], current_player)
            eval = -self.negamax(board, depth - 1, -beta, -alpha, opponent)
            board.undo_stone(move[0], move[1], current_player)

            if eval > max_eval:
                max_eval = eval
                best_move = move

            alpha = max(alpha, eval)
            if alpha >= beta:
                self._add_killer_move(depth, move)
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

    def _move_heuristic(self, board, move, player: int) -> int:
        x, y = move
        opponent = 3 - player

        # === 1. Check if move wins ===
        board.place_stone(x, y, player)
        if board.check_win(x, y, player):
            board.undo_stone(x, y, player)
            return constants.MOVE_WIN

        # === 2. Count our threats ===
        our_threats = self._count_threats(board, x, y, player)

        total_fours = our_threats["open_fours"] + our_threats["closed_fours"]

        # Double-four = forced win
        if total_fours >= 2:
            board.undo_stone(x, y, player)
            return constants.MOVE_DOUBLE_FOUR

        # Four-three = forced win
        if total_fours >= 1 and our_threats["open_threes"] >= 1:
            board.undo_stone(x, y, player)
            return constants.MOVE_FOUR_THREE

        # Open four
        if our_threats["open_fours"] >= 1:
            board.undo_stone(x, y, player)
            return constants.MOVE_OPEN_FOUR

        # Double-three = becomes four-three next move
        if our_threats["open_threes"] >= 2:
            board.undo_stone(x, y, player)
            return constants.MOVE_FORK

        board.undo_stone(x, y, player)

        # === 3. Check opponent threats to block (PRIORITY) ===
        board.place_stone(x, y, opponent)
        blocks_win = board.check_win(x, y, opponent)
        if blocks_win:
            board.undo_stone(x, y, opponent)
            # This move blocks opponent win - MANDATORY
            # But check if we have a counter-attack
            board.place_stone(x, y, player)
            opp_still_wins = self._has_winning_move(board, opponent)
            board.undo_stone(x, y, player)
            if opp_still_wins:
                # Even after blocking, opponent wins - lost position
                return constants.MOVE_BLOCK_WIN // 2
            return constants.MOVE_BLOCK_WIN

        opp_threats = self._count_threats(board, x, y, opponent)
        board.undo_stone(x, y, opponent)

        opp_fours = opp_threats["open_fours"] + opp_threats["closed_fours"]

        # Block opponent double-four
        if opp_fours >= 2:
            return constants.MOVE_BLOCK_DOUBLE_FOUR

        # Block opponent four-three
        if opp_fours >= 1 and opp_threats["open_threes"] >= 1:
            return constants.MOVE_BLOCK_FOUR_THREE

        # Block open four
        if opp_threats["open_fours"] >= 1:
            return constants.MOVE_BLOCK_OPEN_FOUR

        # Block open three
        if opp_threats["open_threes"] >= 1:
            return constants.MOVE_BLOCK_OPEN_THREE

        # === 4. Evaluate move potential ===
        board.place_stone(x, y, player)
        score = self._evaluate_position(board, x, y, player)
        board.undo_stone(x, y, player)

        if score >= constants.SCORE_OPEN_THREE:
            return constants.MOVE_OPEN_THREE

        return score

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
                threats = self._count_threats(board, mx, my, player)
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

    def _get_immediate_move(self, board, player: int) -> Optional[Tuple[int, int]]:
        moves = board.get_valid_moves()
        best_move = None
        best_score = -1

        for move in moves:
            score = self._move_heuristic(board, move, player)
            if score > best_score:
                best_score = score
                best_move = move

        if best_score >= constants.MOVE_BLOCK_OPEN_FOUR:
            return best_move

        return None

    def _count_threats(self, board, x: int, y: int, player: int) -> dict:
        """Count threats created by a stone at (x, y)."""
        threats = {
            "fives": 0,
            "open_fours": 0,
            "closed_fours": 0,
            "open_threes": 0,
        }
        patterns = constants.PATTERNS[player]

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

            if patterns["threat"]["open_three"] in line:
                threats["open_threes"] += 1

        return threats

    # ==================== THREAT SPACE SEARCH (TSS) ====================

    def _get_threat_moves(self, board, player: int) -> List[Tuple[int, int]]:
        """Return moves that create threats (fours, threes)."""
        threat_moves = []
        valid_moves = board.get_valid_moves()

        for x, y in valid_moves:
            board.place_stone(x, y, player)
            threats = self._count_threats(board, x, y, player)
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
            threats = self._count_threats(board, x, y, attacker)
            board.undo_stone(x, y, attacker)

            if (threats["fives"] > 0 or
                threats["open_fours"] > 0 or
                threats["closed_fours"] > 0 or
                threats["open_threes"] > 0):
                defense_moves.add((x, y))

            # 2. Create a counter-threat
            board.place_stone(x, y, defender)
            counter = self._count_threats(board, x, y, defender)
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
