"""
Search algorithms for the Sokoban solver.
"""

from collections import deque
import heapq
import time
from typing import List, Tuple


class SearchMixin:
    def fast_solve(self, timeout_seconds: int = 60) -> bool:
        return self.solve(timeout_seconds=timeout_seconds, fast_mode=True)

    def solve(self, timeout_seconds: int = 300, fast_mode: bool = False) -> bool:
        if fast_mode:
            weight = max(self.initial_weight, 2.0)
            print(f"Starting AI solver in fast mode (initial weight={weight}, timeout={timeout_seconds}s)...")
        else:
            weight = self.initial_weight
            print(f"Starting AI solver with weighted A* (initial weight={weight}, timeout={timeout_seconds}s)...")
        if self.symmetries_detected:
            print(f"[Symmetry Reduction] Using symmetry reduction with {len(self.symmetries_detected)} detected symmetries")

        heuristic_fn = self.fast_heuristic if fast_mode else self.heuristic
        initial_raw_player = self.game.state.player_pos
        initial_state = self._make_state_key(self.get_state_tuple())
        initial_h = heuristic_fn(initial_state, initial_raw_player)
        self.initial_heuristic = max(initial_h, 1)
        self.transposition_table.clear()
        if hasattr(self, 'heuristic_cache'):
            self.heuristic_cache.clear()
        if hasattr(self, 'fast_heuristic_cache'):
            self.fast_heuristic_cache.clear()

        initial_key = self._canonical_state_key(initial_state.player_pos, initial_state.boxes)
        open_queue = []
        initial_f = weight * initial_h
        heap_counter = 0
        heapq.heappush(open_queue, (initial_f, 0, heap_counter, initial_state, initial_raw_player, []))
        heap_counter += 1
        self.transposition_table[initial_key] = 0

        visited_count = 0
        pruned_count = 0
        start_time = time.time()

        while open_queue:
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                print(f"Timeout reached after {timeout_seconds} seconds. States visited: {visited_count}")
                return False

            f, g, _, state, player_pos, path = heapq.heappop(open_queue)
            visited_count += 1

            current_key = self._canonical_state_key(state.player_pos, state.boxes)
            if current_key in self.transposition_table and g > self.transposition_table[current_key]:
                continue

            if self.is_goal_state(state):
                self.solution_moves = path
                print(f"Solution found! Moves: {len(path)}, States visited: {visited_count}")
                if self.symmetries_detected:
                    print(f"[Symmetry Reduction] Pruned states due to symmetry: {pruned_count}")
                return True

            for direction_path, new_state, move_cost, new_player_pos in self.get_push_moves(state, player_pos):
                new_g = g + move_cost
                new_state_key = self._canonical_state_key(new_state.player_pos, new_state.boxes)
                if new_state_key in self.transposition_table and new_g >= self.transposition_table[new_state_key]:
                    continue

                h = heuristic_fn(new_state, new_player_pos)
                if fast_mode:
                    current_weight = max(weight, self.get_dynamic_weight(h, visited_count))
                else:
                    current_weight = self.get_dynamic_weight(h, visited_count)
                new_f = new_g + current_weight * h
                self.transposition_table[new_state_key] = new_g
                heapq.heappush(open_queue, (new_f, new_g, heap_counter, new_state, new_player_pos, path + direction_path))
                heap_counter += 1

            if visited_count % 500 == 0:
                sym_info = f", pruned: {pruned_count}" if self.symmetries_detected else ""
                print(f"Visited {visited_count} states{sym_info}, current open size: {len(open_queue)}, latest f: {f:.2f}")

        print(f"No solution found. States visited: {visited_count}")
        if self.symmetries_detected:
            print(f"[Symmetry Reduction] Pruned states due to symmetry: {pruned_count}")
        return False

    def ida_solve(self) -> bool:
        print("Starting AI solver with IDA*...")
        if self.symmetries_detected:
            print(f"[Symmetry Reduction] Using symmetry reduction with {len(self.symmetries_detected)} detected symmetries")

        initial_raw_player = self.game.state.player_pos
        initial_state = self._make_state_key(self.get_state_tuple())
        initial_h = self.heuristic(initial_state, initial_raw_player)
        threshold = initial_h
        self.transposition_table.clear()

        initial_key = self._canonical_state_key(initial_state.player_pos, initial_state.boxes)
        self.transposition_table[initial_key] = 0

        iteration = 0
        while True:
            iteration += 1
            print(f"IDA* iteration {iteration} with threshold: {threshold}")
            self.transposition_table.clear()
            result, path, new_threshold = self.ida_search(initial_state, initial_raw_player, 0, threshold, [])
            if result:
                self.solution_moves = path
                print(f"Solution found! Moves: {len(path)}, IDA* iterations: {iteration}")
                return True
            if new_threshold == float('inf'):
                print("No solution found.")
                return False
            threshold = new_threshold

    def bidirectional_solve(self) -> bool:
        print("Starting bidirectional BFS solver...")
        initial_state = self._make_state_key(self.get_state_tuple())
        initial_raw_player = self.game.state.player_pos
        goal_boxes = tuple(sorted(self.targets_list))
        goal_player_pos = self.game.state.player_pos
        goal_state = self._make_state_key((goal_player_pos, goal_boxes))

        if not self.is_valid_position(*goal_player_pos) or self.game.state.board[goal_player_pos[1]][goal_player_pos[0]] == 1 or goal_player_pos in set(goal_boxes):
            goal_player_pos = self.targets_list[0]
            goal_state = self._make_state_key((goal_player_pos, goal_boxes))

        forward_queue = deque([(initial_state, initial_raw_player, [])])
        backward_queue = deque([(goal_state, goal_player_pos, [])])
        forward_visited = {initial_state}
        backward_visited = {goal_state}
        forward_paths = {initial_state: []}
        backward_paths = {goal_state: []}

        while forward_queue and backward_queue:
            state_f, player_pos_f, path_f = forward_queue.popleft()
            if state_f in backward_visited:
                total_path = path_f + self.reverse_path(backward_paths[state_f])
                self.solution_moves = total_path
                print(f"Solution found! Moves: {len(total_path)}")
                return True

            for direction_path, new_state, _, new_player_pos in self.get_push_moves(state_f, player_pos_f):
                if new_state not in forward_visited:
                    forward_visited.add(new_state)
                    new_path = path_f + direction_path
                    forward_paths[new_state] = new_path
                    forward_queue.append((new_state, new_player_pos, new_path))

            state_b, player_pos_b, path_b = backward_queue.popleft()
            if state_b in forward_visited:
                total_path = forward_paths[state_b] + self.reverse_path(path_b)
                self.solution_moves = total_path
                print(f"Solution found! Moves: {len(total_path)}")
                return True

            for direction_path, new_state, _, new_player_pos in self.get_reverse_push_moves(state_b, player_pos_b):
                if new_state not in backward_visited:
                    backward_visited.add(new_state)
                    new_path = path_b + direction_path
                    backward_paths[new_state] = new_path
                    backward_queue.append((new_state, new_player_pos, new_path))

        print("No solution found.")
        return False

    def start_auto_play(self) -> None:
        """Start auto-playing the current solution moves."""
        if not self.solution_moves:
            raise RuntimeError("No solution moves available. Call solve() before auto-play.")
        self.current_move_index = 0
        self.is_solving = True

    def stop_auto_play(self) -> None:
        """Stop auto-playing solution moves."""
        self.is_solving = False

    def get_next_move(self):
        """Return the next move in the solution sequence, or None when finished."""
        if not self.is_solving:
            return None
        if self.current_move_index >= len(self.solution_moves):
            self.is_solving = False
            return None
        move = self.solution_moves[self.current_move_index]
        self.current_move_index += 1
        if self.current_move_index >= len(self.solution_moves):
            self.is_solving = False
        return move

    def ida_search(self, state, player_pos, g, threshold, path):
        f = g + self.heuristic(state, player_pos)
        if f > threshold:
            return False, [], f
        if self.is_goal_state(state):
            return True, path, threshold
        min_threshold = float('inf')

        for direction_path, new_state, move_cost, new_player_pos in self.get_push_moves(state, player_pos):
            new_g = g + move_cost
            new_f = new_g + self.heuristic(new_state, new_player_pos)
            if new_f > threshold:
                min_threshold = min(min_threshold, new_f)
                continue

            new_state_key = self._canonical_state_key(new_state.player_pos, new_state.boxes) if self.symmetries_detected else new_state
            if new_state_key in self.transposition_table and new_g >= self.transposition_table[new_state_key]:
                continue

            self.transposition_table[new_state_key] = new_g
            found, solution_path, new_thresh = self.ida_search(new_state, new_player_pos, new_g, threshold, path + direction_path)
            if found:
                return True, solution_path, threshold
            min_threshold = min(min_threshold, new_thresh)

        return False, [], min_threshold

    def dfs_search(self, state, player_pos, g, threshold, path, visited):
        state_key = self._canonical_state_key(state.player_pos, state.boxes)
        if state_key in self.transposition_table and g > self.transposition_table[state_key]:
            return False, [], float('inf'), 0

        h = self.heuristic(state, player_pos)
        weight = self.get_dynamic_weight(h)
        f = g + weight * h
        if f > threshold:
            return False, [], f, 1
        if self.is_goal_state(state):
            return True, path, threshold, 1

        if state_key not in self.transposition_table or g < self.transposition_table[state_key]:
            self.transposition_table[state_key] = g

        min_threshold = float('inf')
        states_visited = 1

        for direction_path, new_state, move_cost, new_player_pos in self.get_push_moves(state, player_pos):
            if new_state not in visited:
                visited.add(new_state)
                found, moves, new_thresh, sub_visited = self.dfs_search(new_state, new_player_pos, g + move_cost, threshold, path + direction_path, visited)
                states_visited += sub_visited
                if found:
                    return True, moves, threshold, states_visited
                if new_thresh < min_threshold:
                    min_threshold = new_thresh
                visited.remove(new_state)

        return False, [], min_threshold, states_visited
