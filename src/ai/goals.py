"""
Goal distance and room detection utilities for the Sokoban solver.
"""

from collections import deque
from typing import Tuple, Set


class GoalsMixin:
    def compute_goal_distance_map(self) -> dict[Tuple[int, int], int]:
        from collections import deque

        distances = {}
        queue = deque()
        visited = set()

        for target in self.targets_list:
            distances[target] = 0
            queue.append((target, 0))
            visited.add(target)

        while queue:
            (x, y), dist = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.game.state.width and
                    0 <= ny < self.game.state.height and
                    self.game.state.board[ny][nx] != 1 and
                    (nx, ny) not in visited):
                    visited.add((nx, ny))
                    distances[(nx, ny)] = dist + 1
                    queue.append(((nx, ny), dist + 1))

        return distances

    def compute_push_distance_map(self) -> dict[Tuple[int, int], dict[Tuple[int, int], int]]:
        width = self.game.state.width
        height = self.game.state.height

        def is_floor(pos: Tuple[int, int]) -> bool:
            x, y = pos
            return (0 <= x < width and 0 <= y < height and self.game.state.board[y][x] != 1)

        push_distance_map = {}
        for target in self.targets_list:
            queue = deque([target])
            distances = {target: 0}
            while queue:
                x, y = queue.popleft()
                dist = distances[(x, y)]
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    source = (x + dx, y + dy)
                    player_pos = (x - dx, y - dy)
                    if not is_floor(source) or not is_floor(player_pos):
                        continue
                    if source in distances:
                        continue
                    distances[source] = dist + 1
                    queue.append(source)
            push_distance_map[target] = distances

        return push_distance_map

    def get_push_distance(self, box: Tuple[int, int], target: Tuple[int, int]) -> int:
        return self.push_distance_map.get(target, {}).get(box, float('inf'))

    def compute_deadlock_map(self) -> list[list[bool]]:
        width = self.game.state.width
        height = self.game.state.height
        walls = {(x, y) for y, row in enumerate(self.game.state.board) for x, value in enumerate(row) if value == 1}
        dead_square = [[False for _ in range(width)] for _ in range(height)]
        reachable = set(self.targets_list)
        queue = deque(self.targets_list)

        def is_floor(pos: Tuple[int, int]) -> bool:
            x, y = pos
            return (0 <= x < width and 0 <= y < height and self.game.state.board[y][x] != 1)

        def is_box_stuck(pos: Tuple[int, int]) -> bool:
            x, y = pos
            if pos in self.targets_list:
                return False
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                prev_box = (x - dx, y - dy)
                next_box = (x + dx, y + dy)
                if is_floor(prev_box) and is_floor(next_box):
                    return False
            return True

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                prev_box = (x - dx, y - dy)
                player_pos = (x - 2 * dx, y - 2 * dy)

                if not is_floor(prev_box):
                    continue
                if not is_floor(player_pos):
                    continue
                if prev_box in reachable:
                    continue

                reachable.add(prev_box)
                queue.append(prev_box)

        for y in range(height):
            for x in range(width):
                if (x, y) in walls:
                    dead_square[y][x] = False
                elif (x, y) in self.targets_list:
                    dead_square[y][x] = False
                else:
                    dead_square[y][x] = (x, y) not in reachable and is_box_stuck((x, y))

        return dead_square

    def detect_goal_rooms(self):
        width = self.game.state.width
        height = self.game.state.height
        walkable = {
            (x, y)
            for y, row in enumerate(self.game.state.board)
            for x, value in enumerate(row)
            if value != 1
        }

        adjacency = {}
        for x, y in walkable:
            neighbors = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (x + dx, y + dy)
                if neighbor in walkable:
                    neighbors.append(neighbor)
            adjacency[(x, y)] = neighbors

        def is_linear_region(tiles: Set[Tuple[int, int]]) -> bool:
            xs = {x for x, _ in tiles}
            ys = {y for _, y in tiles}
            return len(xs) == 1 or len(ys) == 1

        discovery = {}
        low = {}
        parent = {}
        articulation_points = set()
        current_time = 0

        def dfs(node):
            nonlocal current_time
            discovery[node] = current_time
            low[node] = current_time
            current_time += 1
            children = 0

            for neighbor in adjacency[node]:
                if neighbor not in discovery:
                    parent[neighbor] = node
                    children += 1
                    dfs(neighbor)
                    low[node] = min(low[node], low[neighbor])

                    if parent.get(node) is None and children > 1:
                        articulation_points.add(node)
                    if parent.get(node) is not None and low[neighbor] >= discovery[node]:
                        articulation_points.add(node)
                elif neighbor != parent.get(node):
                    low[node] = min(low[node], discovery[neighbor])

        for tile in walkable:
            if tile not in discovery:
                parent[tile] = None
                dfs(tile)

        non_ap_tiles = walkable - articulation_points
        visited = set()
        self.goal_rooms = []
        self.tile_to_goal_room = {}

        for tile in non_ap_tiles:
            if tile in visited:
                continue
            region = set()
            queue = deque([tile])
            visited.add(tile)

            while queue:
                current = queue.popleft()
                region.add(current)
                for neighbor in adjacency[current]:
                    if neighbor in non_ap_tiles and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)

            entrances = set()
            for region_tile in region:
                for neighbor in adjacency[region_tile]:
                    if neighbor in articulation_points:
                        entrances.add(neighbor)

            targets = {pos for pos in region if pos in self.targets_list}
            if len(targets) < 2 or not entrances or len(entrances) > 4:
                continue

            room_tiles = region | entrances
            if is_linear_region(room_tiles):
                continue

            distances = {}
            scan_queue = deque()
            for entry in entrances:
                distances[entry] = 0
                scan_queue.append(entry)

            while scan_queue:
                pos = scan_queue.popleft()
                for neighbor in adjacency[pos]:
                    if neighbor in room_tiles and neighbor not in distances:
                        distances[neighbor] = distances[pos] + 1
                        scan_queue.append(neighbor)

            target_depths = {target: distances.get(target, float('inf')) for target in targets}
            room_priority = min(target_depths.values()) + len(entrances) * 8 + len(room_tiles) // 3
            room = {
                'tiles': room_tiles,
                'targets': targets,
                'entrances': entrances,
                'target_depths': target_depths,
                'priority': room_priority,
            }

            self.goal_rooms.append(room)
            room_index = len(self.goal_rooms) - 1
            for pos in room_tiles:
                self.tile_to_goal_room.setdefault(pos, []).append(room_index)

        self.goal_rooms.sort(key=lambda room: room['priority'])
        self.tile_to_goal_room = {}
        for room_index, room in enumerate(self.goal_rooms):
            for pos in room['tiles']:
                self.tile_to_goal_room.setdefault(pos, []).append(room_index)
