"""
Pathfinding utilities for Sokoban solver.
"""

from collections import deque
import heapq
from typing import Tuple, List, Set, Optional

from .state_key import StateKey


class PathfindingMixin:
    def compute_reachable_tiles(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        if not isinstance(boxes, set):
            boxes = set(boxes)

        cache_key = (player_pos, tuple(sorted(boxes)))
        if cache_key in self.flood_fill_cache:
            return self.flood_fill_cache[cache_key]

        visited = {player_pos}
        queue = deque([player_pos])

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                next_pos = (nx, ny)
                if not self.is_valid_position(nx, ny):
                    continue
                if next_pos in self.walls or next_pos in boxes or next_pos in visited:
                    continue
                visited.add(next_pos)
                queue.append(next_pos)

        self.flood_fill_cache[cache_key] = visited
        return visited

    def flood_fill(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]], walls: Optional[Set[Tuple[int, int]]] = None, width: Optional[int] = None, height: Optional[int] = None) -> Set[Tuple[int, int]]:
        use_default_board = walls is None and width is None and height is None
        cache_key = (player_pos, tuple(sorted(boxes)))
        if use_default_board and cache_key in self.flood_fill_cache:
            return self.flood_fill_cache[cache_key]

        if width is None:
            width = self.game.state.width
        if height is None:
            height = self.game.state.height
        if walls is None:
            walls = {(x, y) for y, row in enumerate(self.game.state.board) for x, value in enumerate(row) if value == 1}

        visited = {player_pos}
        queue = deque([player_pos])

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                next_pos = (nx, ny)
                if next_pos in walls or next_pos in boxes or next_pos in visited:
                    continue
                visited.add(next_pos)
                queue.append(next_pos)

        if use_default_board:
            self.flood_fill_cache[cache_key] = visited

        return visited

    def flood_fill_distances(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]], walls: Optional[Set[Tuple[int, int]]] = None, width: Optional[int] = None, height: Optional[int] = None) -> dict[Tuple[int, int], int]:
        use_default_board = walls is None and width is None and height is None
        cache_key = (player_pos, tuple(sorted(boxes)))
        if use_default_board and cache_key in self.reachable_distances_cache:
            return self.reachable_distances_cache[cache_key]

        if width is None:
            width = self.game.state.width
        if height is None:
            height = self.game.state.height
        if walls is None:
            walls = {(x, y) for y, row in enumerate(self.game.state.board) for x, value in enumerate(row) if value == 1}

        distances = {player_pos: 0}
        queue = deque([player_pos])

        while queue:
            x, y = queue.popleft()
            current_dist = distances[(x, y)]
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                next_pos = (nx, ny)
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                if next_pos in walls or next_pos in boxes or next_pos in distances:
                    continue
                distances[next_pos] = current_dist + 1
                queue.append(next_pos)

        if use_default_board:
            self.reachable_distances_cache[cache_key] = distances

        return distances

    def get_reachable_distances(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> dict[Tuple[int, int], int]:
        return self.flood_fill_distances(player_pos, boxes)

    def get_state_tuple(self) -> Tuple:
        """Get current game state as tuple for hashing."""
        state = self.game.state
        boxes_tuple = tuple(sorted(state.boxes))
        return (state.player_pos, boxes_tuple)

    def get_reachable_paths(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> dict[Tuple[int, int], List[str]]:
        cache_key = (player_pos, tuple(sorted(boxes)))
        if cache_key in self.reachable_paths_cache:
            return self.reachable_paths_cache[cache_key]

        queue = deque([(player_pos, [])])
        paths = {player_pos: []}

        while queue:
            (x, y), path = queue.popleft()
            for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                dx, dy = self.get_direction_vector(direction)
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.game.state.width and
                    0 <= ny < self.game.state.height and
                    self.game.state.board[ny][nx] != 1 and
                    (nx, ny) not in boxes and
                    (nx, ny) not in paths):
                    next_path = path + [direction]
                    paths[(nx, ny)] = next_path
                    queue.append(((nx, ny), next_path))

        self.reachable_paths_cache[cache_key] = paths
        return paths

    def manhattan(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_pushable_paths(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> dict[Tuple[int, int], List[str]]:
        cache_key = (player_pos, tuple(sorted(boxes)))
        if cache_key in self.push_paths_cache:
            return self.push_paths_cache[cache_key]

        candidates = {}
        for box in boxes:
            bx, by = box
            for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                dx, dy = self.get_direction_vector(direction)
                behind = (bx - dx, by - dy)
                push_to = (bx + dx, by + dy)

                if not self.is_valid_position(*behind) or not self.is_valid_position(*push_to):
                    continue
                if self.game.state.board[push_to[1]][push_to[0]] == 1:
                    continue
                if push_to in boxes:
                    continue
                candidates.setdefault(behind, []).append((box, direction, push_to))

        if not candidates:
            self.push_paths_cache[cache_key] = {}
            return {}

        target_positions = set(candidates.keys())
        open_queue = []
        start_h = min(self.manhattan(player_pos, target) for target in target_positions)
        heapq.heappush(open_queue, (start_h, 0, player_pos, []))
        g_scores = {player_pos: 0}
        push_paths = {}

        while open_queue and target_positions:
            _, g, pos, path = heapq.heappop(open_queue)
            if pos in push_paths:
                continue
            if pos in target_positions:
                push_paths[pos] = path
                target_positions.remove(pos)
                if not target_positions:
                    break

            x, y = pos
            for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                dx, dy = self.get_direction_vector(direction)
                nxt = (x + dx, y + dy)
                if (not self.is_valid_position(*nxt) or
                    self.game.state.board[nxt[1]][nxt[0]] == 1 or
                    nxt in boxes):
                    continue

                new_g = g + 1
                if nxt in g_scores and new_g >= g_scores[nxt]:
                    continue
                g_scores[nxt] = new_g

                heur = min(self.manhattan(nxt, target) for target in target_positions) if target_positions else 0
                heapq.heappush(open_queue, (new_g + heur, new_g, nxt, path + [direction]))

        self.push_paths_cache[cache_key] = push_paths
        return push_paths

    def is_irreversible_move(self, box: Tuple[int, int], direction: str, boxes_set: Set[Tuple[int, int]]) -> bool:
        dx, dy = self.get_direction_vector(direction)
        push_to = (box[0] + dx, box[1] + dy)
        if self.is_corner_deadlock(push_to):
            return True
        if self.is_tunnel_deadlock(push_to):
            return True
        if self.is_freeze_deadlock(push_to, boxes_set):
            return True
        if self.is_goal_room_entrance_blocking(push_to, boxes_set):
            return True
        return False

    def get_push_moves(self, state, player_pos=None) -> List[Tuple[List[str], StateKey, int, Tuple[int, int]]]:
        if player_pos is None:
            player_pos = state.player_pos
        boxes = state.boxes
        boxes_set = set(boxes)
        reachable_tiles = self.compute_reachable_tiles(player_pos, boxes_set)
        reachable_paths = self.get_pushable_paths(player_pos, boxes_set)
        push_moves = []

        for box in boxes:
            bx, by = box
            for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                dx, dy = self.get_direction_vector(direction)
                behind = (bx - dx, by - dy)
                push_to = (bx + dx, by + dy)

                if behind not in reachable_tiles or behind not in reachable_paths:
                    continue
                if not self.is_valid_position(push_to[0], push_to[1]):
                    continue
                if self.game.state.board[push_to[1]][push_to[0]] == 1 or push_to in boxes_set:
                    continue
                if self.dead_square_map[push_to[1]][push_to[0]] and push_to not in self.targets_list:
                    continue
                if self.is_irreversible_move(box, direction, boxes_set):
                    continue

                final_box, push_steps = self.tunnel_macro(push_to, direction, boxes_set)
                if self.dead_square_map[final_box[1]][final_box[0]] and final_box not in self.targets_list:
                    continue

                new_boxes = set(boxes)
                new_boxes.remove(box)
                new_boxes.add(final_box)
                if self.is_goal_room_entrance_blocking(final_box, new_boxes):
                    continue
                boxes_tuple = tuple(sorted(new_boxes))
                player_after_push = (final_box[0] - dx, final_box[1] - dy)
                new_state = self._make_state_key((player_after_push, boxes_tuple))
                if self.is_deadlock(boxes_tuple):
                    continue

                path_to_behind = reachable_paths[behind]
                move_path = path_to_behind + [direction] * push_steps
                # Use push-count cost for search guidance rather than raw player-step cost.
                # This reduces the search space by prioritizing fewer box pushes.
                move_cost = 1
                push_moves.append((move_path, new_state, move_cost, player_after_push))

        return push_moves

    def get_reverse_push_moves(self, state, player_pos=None) -> List[Tuple[List[str], StateKey, int, Tuple[int, int]]]:
        if player_pos is None:
            player_pos = state.player_pos
        boxes = state.boxes
        boxes_set = set(boxes)
        reachable_tiles = self.compute_reachable_tiles(player_pos, boxes_set)
        reverse_moves = []

        for tile in reachable_tiles:
            for direction in ['UP', 'DOWN', 'LEFT', 'RIGHT']:
                dx, dy = self.get_direction_vector(direction)
                box_pos = (tile[0] + dx, tile[1] + dy)
                if box_pos not in boxes_set:
                    continue
                behind = (box_pos[0] + dx, box_pos[1] + dy)
                if not self.is_valid_position(*behind):
                    continue
                if self.game.state.board[behind[1]][behind[0]] == 1 or behind in boxes_set:
                    continue

                new_player_pos = box_pos
                new_boxes = set(boxes)
                new_boxes.remove(box_pos)
                new_boxes.add(behind)
                if self.dead_square_map[behind[1]][behind[0]] and behind not in self.targets_list:
                    continue
                boxes_tuple = tuple(sorted(new_boxes))
                new_state = self._make_state_key((new_player_pos, boxes_tuple))
                if self.is_deadlock(boxes_tuple):
                    continue

                reverse_direction = self.get_reverse_direction(direction)
                reverse_moves.append(([reverse_direction], new_state, 1, new_player_pos))

        return reverse_moves

    def get_distance(self, start: Tuple[int, int], end: Tuple[int, int]) -> int:
        if start == end:
            return 0

        cache_key = (start, end)
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]

        queue = deque([(start, 0)])
        visited = {start}
        distance = float('inf')

        while queue:
            (x, y), dist = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.game.state.width and
                    0 <= ny < self.game.state.height and
                    self.game.state.board[ny][nx] != 1 and
                    (nx, ny) not in visited):
                    if (nx, ny) == end:
                        distance = dist + 1
                        queue.clear()
                        break
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))

        self.distance_cache[cache_key] = distance
        return distance

    def is_valid_position(self, x: int, y: int) -> bool:
        return 0 <= x < self.game.state.width and 0 <= y < self.game.state.height

    def get_direction_vector(self, direction: str) -> Tuple[int, int]:
        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0),
        }
        return directions.get(direction, (0, 0))

    def get_reverse_direction(self, direction: str) -> str:
        reverse_map = {
            'UP': 'DOWN',
            'DOWN': 'UP',
            'LEFT': 'RIGHT',
            'RIGHT': 'LEFT',
        }
        return reverse_map.get(direction, direction)

    def try_move(self, state, direction: str):
        player_pos, boxes = state.player_pos, state.boxes
        px, py = player_pos
        dx, dy = self.get_direction_vector(direction)
        new_px, new_py = px + dx, py + dy

        if not self.is_valid_position(new_px, new_py):
            return None
        if self.game.state.board[new_py][new_px] == 1:
            return None

        new_boxes = set(boxes)
        if (new_px, new_py) in new_boxes:
            box_new_x = new_px + dx
            box_new_y = new_py + dy
            if not self.is_valid_position(box_new_x, box_new_y):
                return None
            if self.game.state.board[box_new_y][box_new_x] == 1:
                return None
            if (box_new_x, box_new_y) in new_boxes:
                return None
            new_boxes.remove((new_px, new_py))
            new_boxes.add((box_new_x, box_new_y))

        if any(self.dead_square_map[y][x] and (x, y) not in self.targets_list for x, y in new_boxes):
            return None
        if self.is_deadlock(tuple(sorted(new_boxes))):
            return None

        return self._make_state_key(((new_px, new_py), tuple(sorted(new_boxes))))

    def reverse_path(self, path: List[str]) -> List[str]:
        reverse_map = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
        return [reverse_map[d] for d in reversed(path)]
