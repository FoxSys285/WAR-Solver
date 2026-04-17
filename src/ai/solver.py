"""
AI Solver for Sokoban using Weighted A* search
"""

from collections import deque
import heapq
import random
import time
from typing import Tuple, Optional, List, Set


class SymmetryReducer:
    """Symmetry Reduction (Giảm thiểu đối xứng) - Phát hiện và loại bỏ các trạng thái đối xứng"""
    
    def __init__(self, width: int, height: int, walls: Set[Tuple[int, int]], targets: Set[Tuple[int, int]]):
        """
        Initialize Symmetry Reducer
        
        Args:
            width: Board width
            height: Board height
            walls: Set of wall positions
            targets: Set of target positions
        """
        self.width = width
        self.height = height
        self.walls = walls
        self.targets = targets
        self.symmetries = self._detect_board_symmetries()
        self.symmetry_cache = {}
    
    def _detect_board_symmetries(self) -> List[str]:
        """Phát hiện các loại đối xứng của bảng"""
        symmetries = []
        
        # Kiểm tra đối xứng ngang (horizontal flip)
        if self._is_symmetric_horizontal():
            symmetries.append('horizontal')
        
        # Kiểm tra đối xứng dọc (vertical flip)
        if self._is_symmetric_vertical():
            symmetries.append('vertical')
        
        # Kiểm tra đối xứng quay 180 độ (180-degree rotation)
        if self._is_symmetric_rotation_180():
            symmetries.append('rotation_180')
        
        return symmetries
    
    def _tile_status(self, pos: Tuple[int, int]) -> Tuple[bool, bool]:
        """Return the wall/target status for a tile."""
        return (pos in self.walls, pos in self.targets)

    def _is_symmetric_horizontal(self) -> bool:
        """Kiểm tra bảng có đối xứng ngang không"""
        for y in range(self.height):
            for x in range(self.width // 2 + 1):
                left = (x, y)
                right = (self.width - 1 - x, y)
                if self._tile_status(left) != self._tile_status(right):
                    return False
        return True
    
    def _is_symmetric_vertical(self) -> bool:
        """Kiểm tra bảng có đối xứng dọc không"""
        for y in range(self.height // 2 + 1):
            for x in range(self.width):
                top = (x, y)
                bottom = (x, self.height - 1 - y)
                if self._tile_status(top) != self._tile_status(bottom):
                    return False
        return True
    
    def _is_symmetric_rotation_180(self) -> bool:
        """Kiểm tra bảng có đối xứng quay 180 độ không"""
        for y in range(self.height):
            for x in range(self.width):
                pos1 = (x, y)
                pos2 = (self.width - 1 - x, self.height - 1 - y)
                if self._tile_status(pos1) != self._tile_status(pos2):
                    return False
        return True
    
    def _flip_horizontal(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        """Lật ngang vị trí người chơi và hộp"""
        px, py = player_pos
        new_player = (self.width - 1 - px, py)
        new_boxes = tuple(sorted(set(
            (self.width - 1 - bx, by) for bx, by in boxes
        )))
        return new_player, new_boxes
    
    def _flip_vertical(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        """Lật dọc vị trí người chơi và hộp"""
        px, py = player_pos
        new_player = (px, self.height - 1 - py)
        new_boxes = tuple(sorted(set(
            (bx, self.height - 1 - by) for bx, by in boxes
        )))
        return new_player, new_boxes
    
    def _rotate_180(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        """Quay 180 độ vị trí người chơi và hộp"""
        px, py = player_pos
        new_player = (self.width - 1 - px, self.height - 1 - py)
        new_boxes = tuple(sorted(set(
            (self.width - 1 - bx, self.height - 1 - by) for bx, by in boxes
        )))
        return new_player, new_boxes
    
    def get_canonical_state(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        """
        Chuyển đổi trạng thái thành dạng canonical (chính tắc) bằng cách chọn biểu diễn nhỏ nhất
        từ tất cả các đối xứng có thể.
        
        Điều này cho phép phát hiện và loại bỏ các trạng thái đối xứng trong quá trình tìm kiếm.
        """
        cache_key = (player_pos, boxes)
        if cache_key in self.symmetry_cache:
            return self.symmetry_cache[cache_key]
        
        states = [(player_pos, boxes)]
        
        # Thêm các đối xứng ngang nếu có
        if 'horizontal' in self.symmetries:
            states.append(self._flip_horizontal(player_pos, boxes))
        
        # Thêm các đối xứng dọc nếu có
        if 'vertical' in self.symmetries:
            states.append(self._flip_vertical(player_pos, boxes))
        
        # Thêm các đối xứng quay 180 độ nếu có
        if 'rotation_180' in self.symmetries:
            states.append(self._rotate_180(player_pos, boxes))
        
        # Chọn biểu diễn canonical (nhỏ nhất)
        canonical = min(states, key=lambda s: (s[0], s[1]))
        
        self.symmetry_cache[cache_key] = canonical
        return canonical
    
    def get_all_symmetric_states(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Set[Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]]:
        """Lấy tất cả các trạng thái đối xứng của một trạng thái cho trước"""
        symmetric_states = {(player_pos, boxes)}
        
        if 'horizontal' in self.symmetries:
            symmetric_states.add(self._flip_horizontal(player_pos, boxes))
        
        if 'vertical' in self.symmetries:
            symmetric_states.add(self._flip_vertical(player_pos, boxes))
        
        if 'rotation_180' in self.symmetries:
            symmetric_states.add(self._rotate_180(player_pos, boxes))
        
        return symmetric_states


class StateKey:
    __slots__ = ('player_pos', 'boxes', 'hash')

    def __init__(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...], hash_value: int):
        self.player_pos = player_pos
        self.boxes = boxes
        self.hash = hash_value

    def __hash__(self) -> int:
        return self.hash

    def __eq__(self, other) -> bool:
        return (isinstance(other, StateKey) and
                self.player_pos == other.player_pos and
                self.boxes == other.boxes)

    def __repr__(self) -> str:
        return f"StateKey(player={self.player_pos}, boxes={self.boxes})"


class AISolver:
    """AI solver for Sokoban using Weighted A* search"""
    
    def __init__(self, game, weight=2.0):
        """
        Initialize AI solver
        
        Args:
            game: Game object
            weight: Weight for heuristic in weighted A* (w > 1 for faster but suboptimal solutions)
        """
        self.game = game
        self.initial_weight = weight
        self.weight = weight
        self.weight_schedule = [
            (0, self.initial_weight),
            (2000, max(self.initial_weight, 3.0)),
            (10000, max(self.initial_weight, 3.5)),
            (40000, max(self.initial_weight, 4.0)),
            (120000, max(self.initial_weight, 6.0)),
        ]
        self.solution_moves = []
        self.current_move_index = 0
        self.is_solving = False
        self.last_solve_time = None
        self.transposition_table = {}
        self.initial_heuristic = 0
        self.distance_cache = {}
        self.reachable_distances_cache = {}
        self.reachable_paths_cache = {}
        self.push_paths_cache = {}
        self.flood_fill_cache = {}
        self.pdb_cache = {}
        self.targets_list = list(self.game.state.targets)
        self.walls = {
            (x, y)
            for y, row in enumerate(self.game.state.board)
            for x, value in enumerate(row)
            if value == 1
        }
        self.symmetry_reducer = SymmetryReducer(self.game.state.width, self.game.state.height, self.walls, self.game.state.targets)
        self.symmetries_detected = self.symmetry_reducer.symmetries
        self.goal_rooms = []
        self.tile_to_goal_room = {}
        self.zobrist_player = {}
        self.zobrist_box = {}
        self._initialize_zobrist_table()
        self.goal_distance_map = self.compute_goal_distance_map()
        self.dead_square_map = self.compute_deadlock_map()
        self.detect_goal_rooms()
        if self.symmetries_detected:
            print(f"[Symmetry Reduction] Detected symmetries: {self.symmetries_detected}")
        else:
            print("[Symmetry Reduction] No board symmetry detected")
    
    def _initialize_zobrist_table(self):
        """Initialize Zobrist tables for player and box positions."""
        rng = random.Random(self.game.state.width * 1009 + self.game.state.height)
        for y in range(self.game.state.height):
            for x in range(self.game.state.width):
                self.zobrist_player[(x, y)] = rng.getrandbits(64)
                self.zobrist_box[(x, y)] = rng.getrandbits(64)

    def _hash_state(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> int:
        """Compute the Zobrist hash for the given state."""
        h = self.zobrist_player[player_pos]
        for box in boxes:
            h ^= self.zobrist_box[box]
        return h

    def _make_state_key(self, state):
        """Wrap a tuple state into a raw StateKey with cached Zobrist hash."""
        if isinstance(state, StateKey):
            return state
        player_pos, boxes = state
        boxes_tuple = tuple(sorted(set(boxes)))
        return StateKey(player_pos, boxes_tuple, self._hash_state(player_pos, boxes_tuple))

    def _canonical_player_position(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        """Normalize player position within the same reachable region."""
        boxes_set = set(boxes)
        reachable_tiles = self.compute_reachable_tiles(player_pos, boxes_set)
        if not reachable_tiles:
            return player_pos
        return min(reachable_tiles)

    def _canonical_state_key(self, player_pos: Tuple[int, int], boxes) -> StateKey:
        boxes_set = set(boxes)
        boxes_tuple = tuple(sorted(boxes_set))

        if self.symmetries_detected:
            player_pos, boxes_tuple = self.symmetry_reducer.get_canonical_state(player_pos, boxes_tuple)
            boxes_set = set(boxes_tuple)

        player_pos = self._canonical_player_position(player_pos, boxes_tuple)
        return StateKey(player_pos, boxes_tuple, self._hash_state(player_pos, boxes_tuple))

    def _is_symmetric_state_visited(self, state) -> bool:
        """
        [SYMMETRY REDUCTION] Kiểm tra xem trạng thái hoặc bất kỳ đối xứng nào của nó đã được thăm qua chưa
        
        Returns:
            True nếu bất kỳ trạng thái đối xứng nào đã được thăm qua
        """
        canonical_state = self._canonical_state_key(state.player_pos, state.boxes)
        return canonical_state in self.transposition_table

    def compute_reachable_tiles(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
        """Compute the region of tiles the player can reach without pushing any boxes."""
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

    def _compute_distances_from(self, source: Tuple[int, int]) -> dict[Tuple[int, int], int]:
        """Compute BFS distances from a single source to all reachable floor tiles."""
        from collections import deque

        distances = {source: 0}
        queue = deque([source])

        while queue:
            x, y = queue.popleft()
            dist = distances[(x, y)]
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < self.game.state.width and
                    0 <= ny < self.game.state.height and
                    self.game.state.board[ny][nx] != 1 and
                    (nx, ny) not in distances):
                    distances[(nx, ny)] = dist + 1
                    queue.append((nx, ny))

        return distances

    def compute_goal_distance_map(self) -> dict[Tuple[int, int], int]:
        """
        Compute the goal distance map: minimum distance from each position to any target.
        Uses multi-source BFS from all targets and stores per-target distance maps.
        
        Returns:
            Dictionary mapping (x, y) to minimum distance to nearest target.
        """
        distances = {}
        self.goal_distance_by_target = {}

        for target in self.targets_list:
            target_distances = self._compute_distances_from(target)
            self.goal_distance_by_target[target] = target_distances
            for pos, dist in target_distances.items():
                if pos not in distances or dist < distances[pos]:
                    distances[pos] = dist

        return distances

    def compute_deadlock_map(self) -> list[list[bool]]:
        """Compute a static dead square map for the current board.

        A dead square is a floor tile that is not a goal and from which a box
        can never be moved to any goal position.
        """
        width = self.game.state.width
        height = self.game.state.height
        walls = {(x, y) for y, row in enumerate(self.game.state.board) for x, value in enumerate(row) if value == 1}
        dead_square = [[False for _ in range(width)] for _ in range(height)]
        reachable = set(self.targets_list)
        queue = deque(self.targets_list)

        def is_floor(pos: Tuple[int, int]) -> bool:
            x, y = pos
            return (0 <= x < width and 0 <= y < height and
                    self.game.state.board[y][x] != 1)

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
                    dead_square[y][x] = (x, y) not in reachable

        return dead_square

    def detect_goal_rooms(self):
        """Detect enclosed goal rooms and store room tiles, targets, and entrances."""
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

        discovery = {}
        low = {}
        parent = {}
        articulation_points = set()
        time = 0

        def dfs(node):
            nonlocal time
            discovery[node] = time
            low[node] = time
            time += 1
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

            target_depths = {
                target: distances.get(target, float('inf'))
                for target in targets
            }

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

    def goal_room_penalty(self, boxes: Tuple[Tuple[int, int], ...]) -> int:
        """Compute additional heuristic penalty for goal-room packing problems."""
        penalty = 0
        boxes_set = set(boxes)
        room_box_map = {}

        for box in boxes:
            room_indices = self.tile_to_goal_room.get(box)
            if not room_indices:
                continue
            for room_index in room_indices:
                room_box_map.setdefault(room_index, []).append(box)

        for room_index, room_boxes in room_box_map.items():
            room = self.goal_rooms[room_index]
            targets = room['targets']
            entrances = room['entrances']
            target_depths = room['target_depths']

            boxes_on_targets = {box for box in room_boxes if box in targets}
            empty_targets = targets - boxes_on_targets

            if not room_boxes:
                continue

            # Wrong packing order: if any target is filled while a deeper target is still empty.
            if empty_targets and boxes_on_targets:
                deepest_empty = max(target_depths[target] for target in empty_targets)
                for filled in boxes_on_targets:
                    if target_depths[filled] < deepest_empty:
                        penalty += 10
                        break

            # Penalty for any box blocking a room entrance.
            if any(entrance in boxes_set for entrance in entrances):
                penalty += 15

            # If remaining targets are empty and the current packing order makes them unreachable.
            if empty_targets and boxes_on_targets:
                max_filled_depth = max(target_depths[box] for box in boxes_on_targets)
                min_empty_depth = min(target_depths[target] for target in empty_targets)
                if max_filled_depth < min_empty_depth:
                    penalty += 50
                elif any(entrance in boxes_set for entrance in entrances):
                    penalty += 50

            # Penalty if a critical entrance is blocked when the room still needs boxes.
            if any(self.is_goal_room_entrance_blocking(entrance, boxes_set) for entrance in entrances):
                penalty += 200

        return penalty

    def is_goal_room_entrance_blocking(self, pos: Tuple[int, int], boxes_set: Set[Tuple[int, int]]) -> bool:
        """Detect if a box is blocking the only available entrance to a goal room with remaining targets."""
        if pos not in boxes_set:
            return False
        if pos not in self.tile_to_goal_room:
            return False
        if pos in self.game.state.targets:
            return False

        for room_index in self.tile_to_goal_room[pos]:
            room = self.goal_rooms[room_index]
            empty_targets = room['targets'] - boxes_set
            if not empty_targets:
                continue

            if pos not in room['entrances']:
                continue

            other_open = any(
                entrance != pos and entrance not in boxes_set
                for entrance in room['entrances']
            )
            if not other_open:
                return True

        return False

    def is_two_box_tunnel_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
        """Detect tunnel deadlocks caused by two adjacent boxes in a narrow corridor."""
        if box in self.game.state.targets:
            return False

        bx, by = box
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (bx + dx, by + dy)
            if neighbor not in boxes:
                continue

            if dx != 0:
                above = self.game.state.board[by-1][bx] == 1 if by > 0 else True
                below = self.game.state.board[by+1][bx] == 1 if by < self.game.state.height-1 else True
                above_n = self.game.state.board[neighbor[1]-1][neighbor[0]] == 1 if neighbor[1] > 0 else True
                below_n = self.game.state.board[neighbor[1]+1][neighbor[0]] == 1 if neighbor[1] < self.game.state.height-1 else True
                if above and below and above_n and below_n:
                    return True
            else:
                left = self.game.state.board[by][bx-1] == 1 if bx > 0 else True
                right = self.game.state.board[by][bx+1] == 1 if bx < self.game.state.width-1 else True
                left_n = self.game.state.board[neighbor[1]][neighbor[0]-1] == 1 if neighbor[0] > 0 else True
                right_n = self.game.state.board[neighbor[1]][neighbor[0]+1] == 1 if neighbor[0] < self.game.state.width-1 else True
                if left and right and left_n and right_n:
                    return True

        return False

    def solve(self, timeout_seconds: int = 300, fast_mode: bool = True) -> bool:
        """
        Solve the puzzle using weighted A* search with dynamic weight reduction.
        Includes Symmetry Reduction (Giảm thiểu đối xứng) to minimize search space.
        
        Args:
            timeout_seconds: Maximum time to spend solving (default 300s = 5 minutes)
            fast_mode: If True, use a simpler heuristic and higher weight to favor speed over optimality.
                       Default is True to prefer faster solving for most levels.
        
        Returns:
            True if solution found, False otherwise
        """
        if fast_mode:
            weight = max(self.initial_weight, 3.0)
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

        initial_key = self._canonical_state_key(initial_state.player_pos, initial_state.boxes)
        open_queue = []
        initial_f = weight * initial_h
        heap_counter = 0
        heapq.heappush(open_queue, (initial_f, 0, heap_counter, initial_state, initial_raw_player, []))
        heap_counter += 1
        self.transposition_table[initial_key] = 0

        visited_count = 0
        pruned_count = 0  # [SYMMETRY REDUCTION] Đếm các trạng thái bị cắt tỉa
        start_time = time.time()

        while open_queue:
            current_time = time.time()
            if current_time - start_time > timeout_seconds:
                self.last_solve_time = current_time - start_time
                print(f"Timeout reached after {timeout_seconds} seconds. States visited: {visited_count}")
                return False
                
            f, g, _, state, player_pos, path = heapq.heappop(open_queue)
            visited_count += 1

            current_key = self._canonical_state_key(state.player_pos, state.boxes)
            if current_key in self.transposition_table and g > self.transposition_table[current_key]:
                continue

            if self.is_goal_state(state):
                self.solution_moves = path
                self.last_solve_time = time.time() - start_time
                print(f"Solution found! Moves: {len(path)}, States visited: {visited_count}")
                if self.symmetries_detected:
                    print(f"[Symmetry Reduction] Pruned states due to symmetry: {pruned_count}")
                return True

            for direction_path, new_state, move_cost, new_player_pos in self.get_push_moves(state, player_pos):
                # Macro move: path is player walk to push-behind + push directions.
                new_g = g + move_cost
                new_state_key = self._canonical_state_key(new_state.player_pos, new_state.boxes)
                if new_state_key in self.transposition_table and new_g >= self.transposition_table[new_state_key]:
                    continue

                if self.symmetries_detected and self._is_symmetric_state_visited(new_state):
                    pruned_count += 1
                    continue

                h = heuristic_fn(new_state, new_player_pos)
                current_weight = weight if fast_mode else self.get_dynamic_weight(h, visited_count)
                new_f = new_g + current_weight * h
                self.transposition_table[new_state_key] = new_g
                heapq.heappush(open_queue, (new_f, new_g, heap_counter, new_state, new_player_pos, path + direction_path))
                heap_counter += 1

            if visited_count % 500 == 0:
                sym_info = f", pruned: {pruned_count}" if self.symmetries_detected else ""
                print(f"Visited {visited_count} states{sym_info}, current open size: {len(open_queue)}, latest f: {f:.2f}")

        self.last_solve_time = time.time() - start_time
        print(f"No solution found. States visited: {visited_count}")
        if self.symmetries_detected:
            print(f"[Symmetry Reduction] Pruned states due to symmetry: {pruned_count}")
        return False

    def ida_solve(self) -> bool:
        """
        Solve the puzzle using Iterative Deepening A* (IDA*) search.
        More memory-efficient than A* for Sokoban puzzles.
        Includes Symmetry Reduction to minimize search space.
        
        Returns:
            True if solution found, False otherwise
        """
        print("Starting AI solver with IDA*...")
        if self.symmetries_detected:
            print(f"[Symmetry Reduction] Using symmetry reduction with {len(self.symmetries_detected)} detected symmetries")
        
        start_time = time.time()
        initial_raw_player = self.game.state.player_pos
        initial_state = self._make_state_key(self.get_state_tuple())
        initial_h = self.heuristic(initial_state, initial_raw_player)
        initial_f = initial_h  # f = g + h, initial g=0
        
        threshold = initial_f
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
                self.last_solve_time = time.time() - start_time
                print(f"Solution found! Moves: {len(path)}, IDA* iterations: {iteration}")
                return True
            
            if new_threshold == float('inf'):
                self.last_solve_time = time.time() - start_time
                print("No solution found.")
                return False
            
            threshold = new_threshold

    def bidirectional_solve(self) -> bool:
        """
        Solve the puzzle using Bidirectional BFS search.
        
        Returns:
            True if solution found, False otherwise
        """
        print("Starting bidirectional BFS solver...")
        initial_state = self._make_state_key(self.get_state_tuple())
        initial_raw_player = self.game.state.player_pos
        goal_boxes = tuple(sorted(self.targets_list))
        goal_player_pos = self.game.state.player_pos
        goal_state = self._make_state_key((goal_player_pos, goal_boxes))

        if not self.is_valid_position(*goal_player_pos) or self.game.state.board[goal_player_pos[1]][goal_player_pos[0]] == 1 or goal_player_pos in set(goal_boxes):
            # Choose another pos, e.g. first target
            goal_player_pos = self.targets_list[0]
            goal_state = self._make_state_key((goal_player_pos, goal_boxes))

        forward_queue = deque([(initial_state, initial_raw_player, [])])
        backward_queue = deque([(goal_state, goal_player_pos, [])])
        forward_visited = {initial_state}
        backward_visited = {goal_state}
        forward_paths = {initial_state: []}
        backward_paths = {goal_state: []}

        while forward_queue and backward_queue:
            # Forward
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

            # Backward
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

    def ida_search(self, state, player_pos, g, threshold, path):
        """
        Recursive IDA* search function.
        
        Returns:
            (found, path, new_threshold)
        """
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
            
            # Check transposition table to avoid revisiting states
            new_state_key = self._canonical_state_key(new_state.player_pos, new_state.boxes)
            if new_state_key in self.transposition_table and new_g >= self.transposition_table[new_state_key]:
                continue

            self.transposition_table[new_state_key] = new_g

            found, solution_path, new_thresh = self.ida_search(new_state, new_player_pos, new_g, threshold, path + direction_path)

            if found:
                return True, solution_path, threshold
            
            min_threshold = min(min_threshold, new_thresh)
        
        return False, [], min_threshold

    def dfs_search(self, state, player_pos, g, threshold, path, visited):
        """
        Legacy DFS method retained for compatibility.

        Returns:
            (found, moves, new_threshold, states_visited)
        """
        state_key = self._canonical_state_key(state.player_pos, state.boxes)
        if state_key in self.transposition_table and g > self.transposition_table[state_key]:
            return False, [], float('inf'), 0

        boxes = state.boxes
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
    
    def get_state_tuple(self) -> Tuple:
        """Get current game state as tuple for hashing"""
        state = self.game.state
        boxes_tuple = tuple(sorted(state.boxes))
        return (state.player_pos, boxes_tuple)
    
    def get_greedy_subgoal_heuristic(self, boxes: List[Tuple[int, int]], targets: List[Tuple[int, int]], boxes_set: Set[Tuple[int, int]]) -> int:
        """
        Calculate a lower bound on the total box-to-target assignment cost.
        Uses exact Hungarian matching for all equal-size assignments and
        falls back to greedy matching otherwise.
        """
        if not boxes or not targets:
            return 0

        if len(boxes) == len(targets):
            return self.get_minimum_assignment_distance(boxes, targets)

        # Fallback to greedy for unmatched counts.
        total_cost = 0
        assigned_targets = set()
        for box in boxes:
            if box in targets:
                continue
            min_dist = float('inf')
            best_target = None
            for target in targets:
                if target in assigned_targets:
                    continue
                dist = self.get_distance(box, target)
                if dist < min_dist:
                    min_dist = dist
                    best_target = target
            if best_target:
                assigned_targets.add(best_target)
                total_cost += min_dist
            else:
                total_cost += min(self.get_distance(box, t) for t in targets)
        return total_cost

    def get_minimum_assignment_distance(self, boxes: List[Tuple[int, int]], targets: List[Tuple[int, int]]) -> int:
        """Compute exact min-cost assignment distance from boxes to targets."""
        n = len(boxes)
        if n == 0:
            return 0

        cost_matrix = []
        for box in boxes:
            row = []
            for target in targets:
                dist = self.get_distance(box, target)
                if dist == float('inf'):
                    row.append(10000)
                else:
                    row.append(dist)
            cost_matrix.append(row)

        return int(self._hungarian_min_cost(cost_matrix))

    def _hungarian_min_cost(self, cost_matrix: List[List[int]]) -> int:
        """Compute the minimum cost perfect assignment for a square matrix."""
        n = len(cost_matrix)
        if n == 0:
            return 0

        size = n
        u = [0] * (size + 1)
        v = [0] * (size + 1)
        p = [0] * (size + 1)
        way = [0] * (size + 1)

        for i in range(1, size + 1):
            p[0] = i
            j0 = 0
            minv = [float('inf')] * (size + 1)
            used = [False] * (size + 1)
            while True:
                used[j0] = True
                i0 = p[j0]
                delta = float('inf')
                j1 = 0
                for j in range(1, size + 1):
                    if used[j]:
                        continue
                    cur = cost_matrix[i0-1][j-1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
                for j in range(size + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta
                j0 = j1
                if p[j0] == 0:
                    break
            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        return int(-v[0])

    def heuristic(self, state, player_pos=None) -> int:
        """
        Calculate heuristic for A* search.
        Use PDB-backed Hungarian assignment when the number of boxes equals targets.
        Add player-to-box cost, box mobility, linear conflicts, and soft deadlock penalties.
        """
        if player_pos is None:
            player_pos = state.player_pos
        boxes = state.boxes
        boxes_list = list(boxes)
        targets_list = self.targets_list
        boxes_set = set(boxes)
        total_distance = 0
        conflict_penalty = 0

        if len(boxes_list) == len(targets_list):
            # Use greedy subgoal heuristic for better assignment
            total_distance = self.get_greedy_subgoal_heuristic(boxes_list, targets_list, boxes_set)
        else:
            for box in boxes_list:
                if box in self.game.state.targets:
                    continue
                dist = self.goal_distance_map.get(box, float('inf'))
                if dist != float('inf'):
                    total_distance += dist

        player_box_penalty = self.player_to_pushable_box_cost(player_pos, boxes_set)
        mobility_penalty = self.box_mobility_penalty(boxes, boxes_set)
        connectivity_penalty = self.player_connectivity_penalty(player_pos, boxes_set)
        soft_deadlock = self.soft_deadlock_penalty(boxes, boxes_set)
        hard_deadlock = self.deadlock_penalty(boxes)
        goal_penalty = self.goal_room_penalty(boxes)
        return int(total_distance + player_box_penalty + mobility_penalty + conflict_penalty + connectivity_penalty + soft_deadlock + hard_deadlock + goal_penalty)

    def fast_heuristic(self, state, player_pos=None) -> int:
        """
        Fast heuristic for quick solving: uses exact box-to-goal assignment when possible.
        This is slightly more expensive than the old fast heuristic, but much stronger for large puzzle states.
        """
        if player_pos is None:
            player_pos = state.player_pos

        boxes = list(state.boxes)
        targets = list(self.targets_list)
        if len(boxes) == len(targets):
            return self.get_minimum_assignment_distance(boxes, targets)

        total_distance = 0
        for box in boxes:
            if box in self.game.state.targets:
                continue
            dist = self.goal_distance_map.get(box, float('inf'))
            if dist == float('inf'):
                return 10000
            total_distance += dist

        return int(total_distance)

    def fast_solve(self, timeout_seconds: int = 60) -> bool:
        """
        Solve using faster mode for a quick, suboptimal solution.
        """
        return self.solve(timeout_seconds=timeout_seconds, fast_mode=True)

    def get_pdb_cost_row(self, box: Tuple[int, int], boxes_set: Optional[Set[Tuple[int, int]]] = None) -> List[int]:
        """Return cached minimal box-to-target distances for this box position and local box pattern."""
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
            dist = self.get_distance(box, target)
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
        """Calculate Simple Sum of Min Distances: mỗi box tính đến target gần nhất.
        
        Phương pháp này O(n*m) thay vì O(n³) của Hungarian algorithm, nhanh hơn nhiều.
        """
        if not boxes or not targets:
            return 0
        
        total_distance = 0
        
        # Với mỗi box, tính khoảng cách đến target gần nhất
        for box in boxes:
            min_dist = float('inf')
            
            # Tìm target gần nhất
            for target in targets:
                dist = self.get_distance(box, target)
                if dist < min_dist:
                    min_dist = dist
            
            # Thêm khoảng cách này vào tổng
            if min_dist != float('inf'):
                total_distance += min_dist
            else:
                # Nếu không thể đến được, penalize lớn
                total_distance += 10000
        
        return total_distance



    def linear_conflict_penalty(self, boxes, targets):
        """Deprecated: linear_conflict_penalty được tính dựa trên Simple Sum of Min Distances.
        
        Note: Hàm này giữ lại cho tương thích với code cũ, nhưng không được sử dụng
        khi sử dụng phương pháp sum_of_min_distances.
        """
        return 0



    def soft_deadlock_penalty(self, boxes: Tuple, boxes_set: Set[Tuple[int, int]]) -> int:
        """Softly penalize risky configurations that are not yet proven deadlocks."""
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
        """Penalize states where the player is far from the nearest pushable box."""
        reachable = self.get_reachable_distances(player_pos, boxes)
        min_cost = float('inf')

        for box in boxes:
            bx, by = box
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                behind = (bx - dx, by - dy)
                push_to = (bx + dx, by + dy)

                if behind not in reachable:
                    continue
                if not self.is_valid_position(*push_to):
                    continue
                if self.game.state.board[push_to[1]][push_to[0]] == 1:
                    continue
                if push_to in boxes:
                    continue

                min_cost = min(min_cost, reachable[behind])

        if min_cost == float('inf'):
            return 1000
        return int(min_cost)

    def player_blocking_penalty(self, player_pos: Tuple[int, int], boxes_set: Set[Tuple[int, int]]) -> int:
        """Estimate extra cost when reachable push opportunities are blocked by box/wall patterns."""
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
        """Penalize states where the player is disconnected from important boxes."""
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
        """Reward boxes with more pushable directions and penalize low-mobility boxes."""
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
        """Calculate a dynamic weight that increases with the number of visited states."""
        if self.initial_weight <= 1.0:
            return 1.0
        for threshold, weight in reversed(self.weight_schedule):
            if visited_count >= threshold:
                return max(self.initial_weight, weight)
        return max(self.initial_weight, self.weight_schedule[0][1])

    def deadlock_penalty(self, boxes: Tuple) -> int:
        """
        Penalty for box placements that are likely to lead to deadlocks.
        """
        penalty = 0
        box_set = set(boxes)
        for box in boxes:
            if box in self.game.state.targets:
                continue
            if self.is_corner_deadlock(box):
                penalty += 2000
            elif self.is_tunnel_deadlock(box):
                penalty += 1200
            elif self.is_two_box_tunnel_deadlock(box, box_set):
                penalty += 1800
            elif self.is_diagonal_deadlock(box, box_set):
                penalty += 2200
            elif self.is_freeze_deadlock(box, box_set):
                penalty += 1600
            elif self.is_pattern_deadlock(box, box_set):
                penalty += 1800
            elif self.is_box_frozen(box, box_set):
                penalty += 1500
        
        # Additional penalties for group deadlocks
        if self.is_2x2_block_deadlock(box_set):
            penalty += 2500
        if self.is_freeze_deadlock_group(box_set):
            penalty += 2000
        
        return penalty

    def is_corner_deadlock(self, box: Tuple[int, int]) -> bool:
        """Detect simple corner deadlocks for a single box."""
        bx, by = box
        if box in self.game.state.targets:
            return False

        up_wall = self.game.state.board[by-1][bx] == 1 if by > 0 else True
        down_wall = self.game.state.board[by+1][bx] == 1 if by < self.game.state.height-1 else True
        left_wall = self.game.state.board[by][bx-1] == 1 if bx > 0 else True
        right_wall = self.game.state.board[by][bx+1] == 1 if bx < self.game.state.width-1 else True
        return ((up_wall and left_wall) or
                (up_wall and right_wall) or
                (down_wall and left_wall) or
                (down_wall and right_wall))

    def is_tunnel_deadlock(self, box: Tuple[int, int]) -> bool:
        """Detect tunnel deadlocks only when the full corridor is sealed and target-free."""
        if box in self.game.state.targets:
            return False

        bx, by = box
        left_wall = self.game.state.board[by][bx-1] == 1 if bx > 0 else True
        right_wall = self.game.state.board[by][bx+1] == 1 if bx < self.game.state.width-1 else True
        up_wall = self.game.state.board[by-1][bx] == 1 if by > 0 else True
        down_wall = self.game.state.board[by+1][bx] == 1 if by < self.game.state.height-1 else True

        if up_wall and down_wall:
            left = bx
            while left >= 0 and self.game.state.board[by][left] != 1:
                if (left, by) in self.game.state.targets:
                    return False
                if by > 0 and self.game.state.board[by-1][left] != 1:
                    return False
                if by < self.game.state.height - 1 and self.game.state.board[by+1][left] != 1:
                    return False
                left -= 1

            right = bx
            while right < self.game.state.width and self.game.state.board[by][right] != 1:
                if (right, by) in self.game.state.targets:
                    return False
                if by > 0 and self.game.state.board[by-1][right] != 1:
                    return False
                if by < self.game.state.height - 1 and self.game.state.board[by+1][right] != 1:
                    return False
                right += 1
            return True

        if left_wall and right_wall:
            up = by
            while up >= 0 and self.game.state.board[up][bx] != 1:
                if (bx, up) in self.game.state.targets:
                    return False
                if bx > 0 and self.game.state.board[up][bx-1] != 1:
                    return False
                if bx < self.game.state.width - 1 and self.game.state.board[up][bx+1] != 1:
                    return False
                up -= 1

            down = by
            while down < self.game.state.height and self.game.state.board[down][bx] != 1:
                if (bx, down) in self.game.state.targets:
                    return False
                if bx > 0 and self.game.state.board[down][bx-1] != 1:
                    return False
                if bx < self.game.state.width - 1 and self.game.state.board[down][bx+1] != 1:
                    return False
                down += 1
            return True

        return False

    def is_tunnel_tile(self, pos: Tuple[int, int], direction: str) -> bool:
        """Check whether a tile is part of a one-tile-wide corridor for the given push direction."""
        x, y = pos
        if self.game.state.board[y][x] == 1:
            return False

        left_wall = x == 0 or self.game.state.board[y][x-1] == 1
        right_wall = x == self.game.state.width-1 or self.game.state.board[y][x+1] == 1
        up_wall = y == 0 or self.game.state.board[y-1][x] == 1
        down_wall = y == self.game.state.height-1 or self.game.state.board[y+1][x] == 1

        if direction in ['UP', 'DOWN']:
            return left_wall and right_wall and not up_wall and not down_wall
        if direction in ['LEFT', 'RIGHT']:
            return up_wall and down_wall and not left_wall and not right_wall
        return False

    def tunnel_macro(self, box_pos: Tuple[int, int], direction: str, boxes: Set[Tuple[int, int]]) -> Tuple[Tuple[int, int], int]:
        """Advance a pushed box through a one-tile tunnel until it stops."""
        final_pos = box_pos
        dx, dy = self.get_direction_vector(direction)

        if not self.is_tunnel_tile(final_pos, direction):
            return final_pos, 1

        while True:
            if final_pos in self.targets_list:
                break

            next_pos = (final_pos[0] + dx, final_pos[1] + dy)
            nx, ny = next_pos

            if not self.is_valid_position(nx, ny):
                break
            if self.game.state.board[ny][nx] == 1:
                break
            if next_pos in boxes:
                break
            if self.dead_square_map[ny][nx] and next_pos not in self.targets_list:
                break

            if next_pos in self.targets_list:
                final_pos = next_pos
                break

            if not self.is_tunnel_tile(next_pos, direction):
                break

            final_pos = next_pos

        distance = abs(final_pos[0] - box_pos[0]) + abs(final_pos[1] - box_pos[1])
        return final_pos, max(distance + 1, 1)

    def is_freeze_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
        """Detect frozen deadlocks caused by walls and neighboring frozen boxes."""
        bx, by = box
        if box in self.game.state.targets:
            return False

        def blocked(pos):
            x, y = pos
            if x < 0 or x >= self.game.state.width or y < 0 or y >= self.game.state.height:
                return True
            return self.game.state.board[y][x] == 1 or pos in boxes

        def blocker_stuck(pos):
            x, y = pos
            if x < 0 or x >= self.game.state.width or y < 0 or y >= self.game.state.height:
                return True
            if self.game.state.board[y][x] == 1:
                return True
            if pos in self.game.state.targets:
                return False
            return pos in boxes and self.is_box_frozen(pos, boxes)

        neighbors = [((bx, by-1), (bx-1, by)),
                     ((bx, by-1), (bx+1, by)),
                     ((bx, by+1), (bx-1, by)),
                     ((bx, by+1), (bx+1, by))]

        for pos1, pos2 in neighbors:
            if blocked(pos1) and blocked(pos2) and blocker_stuck(pos1) and blocker_stuck(pos2):
                return True

        return False

    def is_freeze_deadlock_group(self, boxes: Set[Tuple[int, int]]) -> bool:
        """Detect freeze deadlock groups: boxes stuck against walls that lock each other in perpendicular directions."""
        for box in boxes:
            if box in self.game.state.targets:
                continue
            bx, by = box
            
            # Check if box is stuck against a wall in one direction
            left_wall = bx == 0 or self.game.state.board[by][bx-1] == 1
            right_wall = bx == self.game.state.width-1 or self.game.state.board[by][bx+1] == 1
            up_wall = by == 0 or self.game.state.board[by-1][bx] == 1
            down_wall = by == self.game.state.height-1 or self.game.state.board[by+1][bx] == 1
            
            # If stuck horizontally (against left or right wall), check vertical neighbors
            if left_wall or right_wall:
                # Check boxes above and below
                above = (bx, by-1)
                below = (bx, by+1)
                if above in boxes and self.is_box_frozen(above, boxes):
                    return True
                if below in boxes and self.is_box_frozen(below, boxes):
                    return True
            
            # If stuck vertically (against up or down wall), check horizontal neighbors
            if up_wall or down_wall:
                # Check boxes left and right
                left = (bx-1, by)
                right = (bx+1, by)
                if left in boxes and self.is_box_frozen(left, boxes):
                    return True
                if right in boxes and self.is_box_frozen(right, boxes):
                    return True
        
        return False

    def is_pattern_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
        """Detect common 2x2 deadlock patterns of boxes/walls without targets."""
        if box in self.game.state.targets:
            return False

        for dx in (0, -1):
            for dy in (0, -1):
                square = [(box[0] + dx + ox, box[1] + dy + oy) for ox in (0, 1) for oy in (0, 1)]
                if any(x < 0 or x >= self.game.state.width or y < 0 or y >= self.game.state.height for x, y in square):
                    continue
                if any((x, y) in self.game.state.targets for x, y in square):
                    continue
                if all(self.game.state.board[y][x] == 1 or (x, y) in boxes for x, y in square):
                    return True

        return False

    def is_2x2_block_deadlock(self, boxes: Set[Tuple[int, int]]) -> bool:
        """Detect 2x2 block deadlocks: 4 adjacent positions forming a square with at least one box not on target."""
        for box in boxes:
            if box in self.game.state.targets:
                continue
            bx, by = box
            # Check all possible 2x2 squares containing this box
            for dx in (0, -1):
                for dy in (0, -1):
                    square = [(bx + dx + ox, by + dy + oy) for ox in (0, 1) for oy in (0, 1)]
                    if any(x < 0 or x >= self.game.state.width or y < 0 or y >= self.game.state.height for x, y in square):
                        continue
                    # Count boxes and walls in the square
                    box_count = sum(1 for x, y in square if (x, y) in boxes)
                    wall_count = sum(1 for x, y in square if self.game.state.board[y][x] == 1)
                    target_count = sum(1 for x, y in square if (x, y) in self.game.state.targets)
                    if box_count + wall_count == 4 and box_count >= 1 and target_count < box_count:
                        return True
        return False

    def is_box_frozen(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
        """Detect if a box is completely frozen by walls and other boxes."""
        bx, by = box
        can_move_up = by > 0 and self.game.state.board[by-1][bx] != 1 and (bx, by-1) not in boxes
        can_move_down = by < self.game.state.height-1 and self.game.state.board[by+1][bx] != 1 and (bx, by+1) not in boxes
        can_move_left = bx > 0 and self.game.state.board[by][bx-1] != 1 and (bx-1, by) not in boxes
        can_move_right = bx < self.game.state.width-1 and self.game.state.board[by][bx+1] != 1 and (bx+1, by) not in boxes
        return not (can_move_up or can_move_down or can_move_left or can_move_right)

    def is_diagonal_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
        """Detect deadlocks where a box is blocked by walls/boxes in both perpendicular directions."""
        if box in self.game.state.targets:
            return False

        bx, by = box
        def blocked(pos):
            x, y = pos
            if x < 0 or x >= self.game.state.width or y < 0 or y >= self.game.state.height:
                return True
            return self.game.state.board[y][x] == 1 or pos in boxes

        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            side1 = (bx + dx, by)
            side2 = (bx, by + dy)
            diagonal = (bx + dx, by + dy)
            if blocked(side1) and blocked(side2) and blocked(diagonal):
                return True

        return False

    def is_goal_state(self, state) -> bool:
        """Check if state is goal state"""
        boxes = state.boxes
        # All boxes should be on targets
        for box in boxes:
            if box not in self.game.state.targets:
                return False
        return len(boxes) == len(self.game.state.targets)
    
    def is_deadlock(self, boxes: Tuple) -> bool:
        """
        Check if current box configuration is in deadlock
        
        Args:
            boxes: Tuple of box positions
            
        Returns:
            True if deadlock detected, False otherwise
        """
        box_set = set(boxes)
        for box in boxes:
            if box in self.game.state.targets:
                continue

            # Hard pruning: any box on a dead square that is not a target is unsolvable.
            if self.dead_square_map[box[1]][box[0]]:
                return True

            # Corner / freeze deadlock: box is trapped by walls or frozen neighbors.
            if self.is_corner_deadlock(box) or self.is_freeze_deadlock(box, box_set) or self.is_diagonal_deadlock(box, box_set):
                return True

            # Tunnel and common pattern deadlock checks remain valid hard pruning rules.
            if (self.is_tunnel_deadlock(box) or
                self.is_pattern_deadlock(box, box_set) or
                self.is_two_box_tunnel_deadlock(box, box_set)):
                return True

        # Check for 2x2 block deadlocks across all boxes
        if self.is_2x2_block_deadlock(box_set):
            return True

        # Check for freeze deadlock groups
        if self.is_freeze_deadlock_group(box_set):
            return True

        return False
    
    def flood_fill(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]], walls: Optional[Set[Tuple[int, int]]] = None, width: Optional[int] = None, height: Optional[int] = None) -> Set[Tuple[int, int]]:
        """Compute all reachable tiles from player_pos using BFS.

        Args:
            player_pos: The starting player position (x, y).
            boxes: Set of box positions treated as obstacles.
            walls: Optional set of wall positions. If omitted, walls are inferred from the current board.
            width: Optional board width. If omitted, inferred from current state.
            height: Optional board height. If omitted, inferred from current state.

        Returns:
            Set of reachable positions.
        """
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
                next_pos = (nx, ny)
                if nx < 0 or ny < 0 or nx >= width or ny >= height:
                    continue
                if next_pos in walls or next_pos in boxes or next_pos in visited:
                    continue
                visited.add(next_pos)
                queue.append(next_pos)

        if use_default_board:
            self.flood_fill_cache[cache_key] = visited

        return visited

    def flood_fill_distances(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]], walls: Optional[Set[Tuple[int, int]]] = None, width: Optional[int] = None, height: Optional[int] = None) -> dict[Tuple[int, int], int]:
        """Compute reachable distances from player_pos using BFS.

        Args:
            player_pos: The starting player position (x, y).
            boxes: Set of box positions treated as obstacles.
            walls: Optional set of wall positions. If omitted, walls are inferred from the current board.
            width: Optional board width. If omitted, inferred from current state.
            height: Optional board height. If omitted, inferred from current state.

        Returns:
            Dictionary mapping reachable positions to their shortest distance from player_pos.
        """
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
        """Return cached reachable distances from player_pos to every reachable tile."""
        return self.flood_fill_distances(player_pos, boxes)

    def get_reachable_paths(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> dict[Tuple[int, int], List[str]]:
        """
        Calculate shortest paths for player to reachable positions using BFS.
        """
        cache_key = (player_pos, tuple(sorted(boxes)))
        if cache_key in self.reachable_paths_cache:
            return self.reachable_paths_cache[cache_key]

        from collections import deque
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
        """Manhattan distance used as a heuristic for player path search."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_pushable_paths(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> dict[Tuple[int, int], List[str]]:
        """Find shortest player paths to valid push-behind positions.

        This supports macro push moves: the player path ends at the square behind a box,
        then the AI executes the push action itself.
        """
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

                if target_positions:
                    heur = min(self.manhattan(nxt, target) for target in target_positions)
                else:
                    heur = 0

                heapq.heappush(open_queue, (new_g + heur, new_g, nxt, path + [direction]))

        self.push_paths_cache[cache_key] = push_paths
        return push_paths

    def get_distance(self, start: Tuple[int, int], end: Tuple[int, int]) -> int:
        """
        Calculate shortest path distance from start to end using BFS
        Ignores boxes, only considers walls
        
        Args:
            start: Starting position (x, y)
            end: Ending position (x, y)
            
        Returns:
            Distance if reachable, float('inf') otherwise
        """
        if start == end:
            return 0

        cache_key = (start, end)
        if cache_key in self.distance_cache:
            return self.distance_cache[cache_key]

        if end in self.goal_distance_by_target:
            return self.goal_distance_by_target[end].get(start, float('inf'))

        queue = deque([(start, 0)])
        visited = set([start])
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
    

    
    def is_irreversible_move(self, box: Tuple[int, int], direction: str, boxes_set: Set[Tuple[int, int]]) -> bool:
        """Check if pushing a box in this direction would create an irreversible deadlock."""
        dx, dy = self.get_direction_vector(direction)
        push_to = (box[0] + dx, box[1] + dy)
        
        # Check if pushing into a corner deadlock
        if self.is_corner_deadlock(push_to):
            return True
            
        # Check if pushing into a tunnel deadlock
        if self.is_tunnel_deadlock(push_to):
            return True
            
        # Check if pushing into a freeze deadlock position
        if self.is_freeze_deadlock(push_to, boxes_set):
            return True
            
        return False

    def get_push_moves(self, state, player_pos=None) -> List[Tuple[List[str], StateKey, int, Tuple[int, int]]]:
        """Generate macro push moves from the current state.

        Each move is a complete push action: the player walks to the push-behind square
        then pushes a box, optionally through a tunnel macro.
        """
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

                if behind not in reachable_tiles:
                    continue
                if behind not in reachable_paths:
                    continue
                if not self.is_valid_position(push_to[0], push_to[1]):
                    continue
                if self.game.state.board[push_to[1]][push_to[0]] == 1:
                    continue
                if push_to in boxes_set:
                    continue
                if self.dead_square_map[push_to[1]][push_to[0]] and push_to not in self.targets_list:
                    continue

                # Strong pruning: check for irreversible moves
                if self.is_irreversible_move(box, direction, boxes_set):
                    continue

                final_box, push_steps = self.tunnel_macro(push_to, direction, boxes_set)

                if self.dead_square_map[final_box[1]][final_box[0]] and final_box not in self.targets_list:
                    continue

                new_boxes = set(boxes)
                new_boxes.remove(box)
                new_boxes.add(final_box)
                boxes_tuple = tuple(sorted(new_boxes))

                player_after_push = (final_box[0] - dx, final_box[1] - dy)
                new_state = self._make_state_key((player_after_push, boxes_tuple))

                if self.is_deadlock(boxes_tuple):
                    continue

                path_to_behind = reachable_paths[behind]
                move_path = path_to_behind + [direction] * push_steps
                move_cost = 1  # Use push macro cost (1 per push)
                push_moves.append((move_path, new_state, move_cost, player_after_push))

        return push_moves

    def get_reverse_push_moves(self, state, player_pos=None) -> List[Tuple[List[str], StateKey, int, Tuple[int, int]]]:
        """Generate reverse push moves (pull moves) from the current state."""
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
                if self.game.state.board[behind[1]][behind[0]] == 1:
                    continue
                if behind in boxes_set:
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
                move_path = [reverse_direction]
                move_cost = 1
                reverse_moves.append((move_path, new_state, move_cost, new_player_pos))

        return reverse_moves

    def try_move(self, state, direction: str):
        """
        Try to make a move and return new state
        
        Args:
            state: Current state
            direction: Direction to move
            
        Returns:
            New state as StateKey if move is valid, None otherwise
        """
        player_pos, boxes = state.player_pos, state.boxes
        px, py = player_pos
        
        # Calculate new position
        dx, dy = self.get_direction_vector(direction)
        new_px, new_py = px + dx, py + dy
        
        # Check boundaries
        if not self.is_valid_position(new_px, new_py):
            return None
        
        # Check wall collision
        if self.game.state.board[new_py][new_px] == 1:
            return None
        
        new_boxes = set(boxes)
        
        # Check if there's a box at new position
        if (new_px, new_py) in new_boxes:
            # Calculate box new position
            box_new_x = new_px + dx
            box_new_y = new_py + dy
            
            # Check if box can move
            if not self.is_valid_position(box_new_x, box_new_y):
                return None
            if self.game.state.board[box_new_y][box_new_x] == 1:
                return None
            if (box_new_x, box_new_y) in new_boxes:
                return None
            
            # Move box
            new_boxes.remove((new_px, new_py))
            new_boxes.add((box_new_x, box_new_y))
        
        # Check for hard deadlock: any moved box in a dead square is immediately invalid.
        if any(self.dead_square_map[y][x] and (x, y) not in self.targets_list for x, y in new_boxes):
            return None

        if self.is_deadlock(tuple(sorted(new_boxes))):
            return None

        return self._make_state_key(((new_px, new_py), tuple(sorted(new_boxes))))

    def reverse_path(self, path: List[str]) -> List[str]:
        """Reverse the path directions"""
        reverse_map = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
        return [reverse_map[d] for d in reversed(path)]

    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if position is valid"""
        return 0 <= x < self.game.state.width and 0 <= y < self.game.state.height
    
    def get_direction_vector(self, direction: str) -> Tuple[int, int]:
        """Get direction vector"""
        directions = {
            'UP': (0, -1),
            'DOWN': (0, 1),
            'LEFT': (-1, 0),
            'RIGHT': (1, 0),
        }
        return directions.get(direction, (0, 0))
    
    def get_reverse_direction(self, direction: str) -> str:
        """Get reverse direction"""
        reverse_map = {
            'UP': 'DOWN',
            'DOWN': 'UP',
            'LEFT': 'RIGHT',
            'RIGHT': 'LEFT'
        }
        return reverse_map.get(direction, direction)
    
    def start_auto_play(self) -> bool:
        """Start auto play using solution"""
        if not self.solution_moves:
            print("No solution available. Solving...")
            if not self.fast_solve(timeout_seconds=120):
                return False
        
        self.is_solving = True
        self.current_move_index = 0
        print("Auto play started")
        return True
    
    def stop_auto_play(self):
        """Stop auto play"""
        self.is_solving = False
        self.current_move_index = 0
        print("Auto play stopped")
    
    def get_next_move(self) -> Optional[str]:
        """Get next move for auto play"""
        if not self.is_solving or not self.solution_moves:
            return None
        
        if self.current_move_index >= len(self.solution_moves):
            print("Solution completed!")
            self.is_solving = False
            return None
        
        move = self.solution_moves[self.current_move_index]
        self.current_move_index += 1
        return move
    
    def print_symmetry_info(self):
        """In thông tin chi tiết về Symmetry Reduction"""
        print("\n" + "="*60)
        print("SYMMETRY REDUCTION INFORMATION")
        print("="*60)
        print(f"Board size: {self.game.state.width}x{self.game.state.height}")
        print(f"Number of boxes: {len(self.targets_list)}")
        
        if self.symmetries_detected:
            print(f"\nDetected Symmetries ({len(self.symmetries_detected)}):")
            for sym in self.symmetries_detected:
                if sym == 'horizontal':
                    print(f"  ✓ Horizontal flip (ngang)")
                elif sym == 'vertical':
                    print(f"  ✓ Vertical flip (dọc)")
                elif sym == 'rotation_180':
                    print(f"  ✓ 180-degree rotation (quay 180°)")
            
            reduction_factor = 2 ** len(self.symmetries_detected)
            print(f"\nPotential state space reduction: ~{reduction_factor}x")
            print(f"This means the search space can be reduced to ~1/{reduction_factor} of the original size")
        else:
            print("\nNo board symmetries detected - Symmetry Reduction will not be used")
        
        print("="*60 + "\n")
