"""
Heuristic and evaluation utilities for the Sokoban solver.
"""

from typing import Tuple, List, Set, Optional


class HeuristicMixin:
    def get_minimum_assignment_heuristic(self, boxes: List[Tuple[int, int]], targets: List[Tuple[int, int]]) -> int:
        if not boxes or not targets:
            return 0

        boxes_tuple = tuple(sorted(boxes))
        targets_tuple = tuple(sorted(targets))
        cache_key = (boxes_tuple, targets_tuple)
        if cache_key in self.assignment_cache:
            return self.assignment_cache[cache_key]

        boxes_set = set(boxes)
        n = len(boxes)
        m = len(targets)
        costs = [[0] * m for _ in range(n)]
        for i, box in enumerate(boxes):
            row = self.get_pdb_cost_row(box, boxes_set)
            for j, target in enumerate(targets):
                costs[i][j] = row[j]

        full_mask = 1 << m
        dp = [float('inf')] * full_mask
        dp[0] = 0

        for mask in range(full_mask):
            i = mask.bit_count()
            if i >= n or dp[mask] >= 10000:
                continue
            for j in range(m):
                if mask & (1 << j):
                    continue
                new_mask = mask | (1 << j)
                value = dp[mask] + costs[i][j]
                if value < dp[new_mask]:
                    dp[new_mask] = value

        result = min(dp[mask] for mask in range(full_mask) if mask.bit_count() == n)
        result = int(result if result != float('inf') else 10000)
        self.assignment_cache[cache_key] = result
        return result

    def get_greedy_subgoal_heuristic(self, boxes: List[Tuple[int, int]], targets: List[Tuple[int, int]], boxes_set: Set[Tuple[int, int]]) -> int:
        return self.get_minimum_assignment_heuristic(boxes, targets)

    def heuristic(self, state, player_pos=None) -> int:
        if player_pos is None:
            player_pos = state.player_pos
        cache_key = (player_pos, state.boxes)
        if cache_key in self.heuristic_cache:
            return self.heuristic_cache[cache_key]

        boxes_list = list(state.boxes)
        boxes_set = set(state.boxes)
        total_distance = 0

        if len(boxes_list) == len(self.targets_list):
            total_distance = self.get_greedy_subgoal_heuristic(boxes_list, self.targets_list, boxes_set)
        else:
            for box in boxes_list:
                if box in self.game.state.targets:
                    continue
                dist = self.goal_distance_map.get(box, float('inf'))
                if dist != float('inf'):
                    total_distance += dist

        player_box_penalty = self.player_to_pushable_box_cost(player_pos, boxes_set)
        mobility_penalty = self.box_mobility_penalty(boxes_list, boxes_set)
        connectivity_penalty = self.player_connectivity_penalty(player_pos, boxes_set)
        blocking_penalty = self.player_blocking_penalty(player_pos, boxes_set)
        soft_deadlock = self.soft_deadlock_penalty(boxes_list, boxes_set)
        hard_deadlock = self.deadlock_penalty(boxes_list)
        goal_penalty = self.goal_room_penalty(tuple(boxes_list))

        result = int(total_distance + player_box_penalty + mobility_penalty + connectivity_penalty + blocking_penalty + soft_deadlock + hard_deadlock + goal_penalty)
        self.heuristic_cache[cache_key] = result
        return result

    def fast_heuristic(self, state, player_pos=None) -> int:
        if player_pos is None:
            player_pos = state.player_pos
        cache_key = (player_pos, state.boxes)
        if cache_key in self.fast_heuristic_cache:
            return self.fast_heuristic_cache[cache_key]

        total_distance = 0
        boxes = list(state.boxes)
        boxes_set = set(boxes)
        if len(boxes) == len(self.targets_list):
            total_distance = self.get_minimum_assignment_heuristic(boxes, self.targets_list)
        else:
            for box in boxes:
                if box in self.game.state.targets:
                    continue
                dist = self.goal_distance_map.get(box, float('inf'))
                if dist == float('inf'):
                    return 10000
                total_distance += dist

        deadlock_penalty = self.deadlock_penalty(state.boxes)
        if deadlock_penalty >= 10000:
            return 10000
        total_distance += min(deadlock_penalty, 1500)

        total_distance += min(self.box_mobility_penalty(state.boxes, boxes_set) // 5, 300)
        total_distance += self.player_to_pushable_box_cost(player_pos, boxes_set) // 3

        result = int(total_distance)
        self.fast_heuristic_cache[cache_key] = result
        return result

    def get_pdb_cost_row(self, box: Tuple[int, int], boxes_set: Optional[Set[Tuple[int, int]]] = None) -> List[int]:
        if boxes_set is None:
            boxes_set = set()

        local_offsets = tuple(sorted(
            (other[0] - box[0], other[1] - box[1])
            for other in boxes_set
            if other != box and abs(other[0] - box[0]) + abs(other[1] - box[1]) <= 2
        ))
        cache_key = (box, local_offsets)
        if cache_key in self.pdb_cache:
            return self.pdb_cache[cache_key]

        row = []
        for target in self.targets_list:
            dist = self.get_push_distance(box, target)
            if dist == float('inf'):
                row.append(10000)
                continue

            penalty = 0
            for dx, dy in local_offsets:
                if abs(dx) + abs(dy) == 1:
                    penalty += 2
                elif abs(dx) + abs(dy) == 2 and (dx == 0 or dy == 0):
                    penalty += 1
                elif abs(dx) + abs(dy) == 2:
                    penalty += 1

            if self.is_tunnel_tile(box, 'UP') or self.is_tunnel_tile(box, 'DOWN'):
                penalty += sum(1 for dx, dy in local_offsets if dx == 0)
            if self.is_tunnel_tile(box, 'LEFT') or self.is_tunnel_tile(box, 'RIGHT'):
                penalty += sum(1 for dx, dy in local_offsets if dy == 0)

            row.append(dist + penalty)

        self.pdb_cache[cache_key] = row
        return row

    def sum_of_min_distances(self, boxes: List[Tuple[int, int]], targets: List[Tuple[int, int]], boxes_set: Set[Tuple[int, int]]) -> int:
        if not boxes or not targets:
            return 0

        total_distance = 0
        for box in boxes:
            min_dist = float('inf')
            for target in targets:
                dist = self.get_distance(box, target)
                if dist < min_dist:
                    min_dist = dist
            total_distance += min_dist if min_dist != float('inf') else 10000

        return total_distance

    def linear_conflict_penalty(self, boxes, targets):
        return 0

    def soft_deadlock_penalty(self, boxes: Tuple, boxes_set: Set[Tuple[int, int]]) -> int:
        penalty = 0
        for box in boxes:
            if box in self.game.state.targets:
                continue

            push_options = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                behind = (box[0] - dx, box[1] - dy)
                push_to = (box[0] + dx, box[1] + dy)
                if not self.is_valid_position(*behind) or not self.is_valid_position(*push_to):
                    continue
                if self.game.state.board[behind[1]][behind[0]] == 1 or self.game.state.board[push_to[1]][push_to[0]] == 1:
                    continue
                if behind in boxes_set or push_to in boxes_set:
                    continue
                push_options += 1

            if push_options == 0:
                penalty += 1000
            elif push_options == 1:
                penalty += 600
            elif push_options == 2:
                penalty += 250

            if self.is_tunnel_deadlock(box):
                penalty += 300
            if self.is_freeze_deadlock(box, boxes_set):
                penalty += 350
            if self.is_pattern_deadlock(box, boxes_set):
                penalty += 400

        return penalty

    def player_to_pushable_box_cost(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> int:
        reachable = self.get_reachable_distances(player_pos, boxes)
        min_cost = float('inf')

        for box in boxes:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                behind = (box[0] - dx, box[1] - dy)
                push_to = (box[0] + dx, box[1] + dy)
                if behind not in reachable:
                    continue
                if not self.is_valid_position(*push_to):
                    continue
                if self.game.state.board[push_to[1]][push_to[0]] == 1:
                    continue
                if push_to in boxes:
                    continue
                min_cost = min(min_cost, reachable[behind])

        return int(min_cost if min_cost != float('inf') else 1000)

    def player_blocking_penalty(self, player_pos: Tuple[int, int], boxes_set: Set[Tuple[int, int]]) -> int:
        reachable = self.get_reachable_distances(player_pos, boxes_set)
        blocking_penalty = 0

        for box in boxes_set:
            if box in self.game.state.targets:
                continue

            behind_reachable = False
            pushable = False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                behind = (box[0] - dx, box[1] - dy)
                push_to = (box[0] + dx, box[1] + dy)

                if behind not in reachable:
                    continue
                if not self.is_valid_position(*push_to):
                    continue
                if self.game.state.board[push_to[1]][push_to[0]] == 1:
                    behind_reachable = True
                    continue
                if push_to in boxes_set:
                    behind_reachable = True
                    continue

                behind_reachable = True
                pushable = True
                break

            if behind_reachable and not pushable:
                blocking_penalty = max(blocking_penalty, 800)
            elif not behind_reachable:
                blocking_penalty = max(blocking_penalty, 1000)

        return blocking_penalty

    def player_connectivity_penalty(self, player_pos: Tuple[int, int], boxes_set: Set[Tuple[int, int]]) -> int:
        reachable = self.compute_reachable_tiles(player_pos, boxes_set)
        disconnected_count = 0

        for box in boxes_set:
            if box in self.game.state.targets:
                continue
            if any((box[0] + dx, box[1] + dy) in reachable for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]):
                continue
            disconnected_count += 1

        return disconnected_count * 500

    def box_mobility_penalty(self, boxes: Tuple, boxes_set: Set[Tuple[int, int]]) -> int:
        penalty = 0
        for box in boxes:
            if box in self.game.state.targets:
                continue
            push_options = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                behind = (box[0] - dx, box[1] - dy)
                push_to = (box[0] + dx, box[1] + dy)
                if not self.is_valid_position(*behind) or not self.is_valid_position(*push_to):
                    continue
                if self.game.state.board[behind[1]][behind[0]] == 1 or self.game.state.board[push_to[1]][push_to[0]] == 1:
                    continue
                if behind in boxes_set or push_to in boxes_set:
                    continue
                push_options += 1

            if push_options == 0:
                penalty += 2000
            elif push_options == 1:
                penalty += 800
            elif push_options == 2:
                penalty += 300
            elif push_options == 3:
                penalty += 100

        return penalty

    def get_dynamic_weight(self, h: int, visited_count: int = 0) -> float:
        if self.initial_weight <= 1.0:
            return 1.0
        for threshold, weight in reversed(self.weight_schedule):
            if visited_count >= threshold:
                return max(self.initial_weight, weight)
        return max(self.initial_weight, self.weight_schedule[0][1])
