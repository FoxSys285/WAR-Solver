"""
Deadlock detection and penalty utilities for the Sokoban solver.
"""

from collections import deque
from typing import Tuple, Set, List, Optional


class DeadlockMixin:
    def is_goal_room_entrance_blocking(self, pos: Tuple[int, int], boxes_set: Set[Tuple[int, int]]) -> bool:
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
    def is_player_reachable(self, target_pos: Tuple[int, int], current_player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
            """Kiểm tra xem người chơi có thể đi bộ đến target_pos không."""
            if target_pos == current_player_pos:
                return True
                
            tx, ty = target_pos
            # Nếu đích đến là tường hoặc có hộp chặn thì không thể đứng vào đó
            if self.game.state.board[ty][tx] == 1 or target_pos in boxes:
                return False

            width = self.game.state.width
            height = self.game.state.height
            
            queue = deque([current_player_pos])
            visited = {current_player_pos}
            
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) == target_pos:
                        return True
                    if 0 <= nx < width and 0 <= ny < height:
                        # Người chơi chỉ đi qua được ô trống (không phải tường, không phải hộp)
                        if self.game.state.board[ny][nx] != 1 and (nx, ny) not in boxes and (nx, ny) not in visited:
                            visited.add((nx, ny))
                            queue.append((nx, ny))
            return False
    def get_corrals(self, player_pos: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> List[Set[Tuple[int, int]]]:
        """Tìm các vùng ô trống mà người chơi không thể tiếp cận."""
        width = self.game.state.width
        height = self.game.state.height
        board = self.game.state.board
        
        # 1. Tìm tất cả các ô người chơi có thể tới (Reachability)
        reachable = set()
        queue = deque([player_pos])
        reachable.add(player_pos)
        
        while queue:
            curr_x, curr_y = queue.popleft()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = curr_x + dx, curr_y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if board[ny][nx] != 1 and (nx, ny) not in boxes and (nx, ny) not in reachable:
                        reachable.add((nx, ny))
                        queue.append((nx, ny))
        
        # 2. Tìm các ô trống/mục tiêu mà người chơi KHÔNG thể tới
        unreachable_empty_tiles = set()
        for y in range(height):
            for x in range(width):
                pos = (x, y)
                if board[y][x] != 1 and pos not in boxes and pos not in reachable:
                    unreachable_empty_tiles.add(pos)
                    
        # 3. Phân nhóm các ô không tới được thành từng Corral riêng biệt
        corrals = []
        visited = set()
        for pos in unreachable_empty_tiles:
            if pos not in visited:
                current_corral = set()
                q = deque([pos])
                visited.add(pos)
                while q:
                    curr = q.popleft()
                    current_corral.add(curr)
                    cx, cy = curr
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        np = (cx + dx, cy + dy)
                        if np in unreachable_empty_tiles and np not in visited:
                            visited.add(np)
                            q.append(np)
                corrals.append(current_corral)
        return corrals

    def is_corral_deadlock(self, player_pos: Tuple[int, int], boxes_set: Set[Tuple[int, int]]) -> bool:
        corrals = self.get_corrals(player_pos, boxes_set)
        if not corrals:
            return False
            
        targets = self.game.state.targets
        for corral in corrals:
            # 1. Tìm các mục tiêu nằm trong vùng bị cô lập này
            corral_targets = [p for p in corral if p in targets]
            if not corral_targets:
                continue # Nếu vùng bị cô lập không có mục tiêu nào thì kệ nó
            
            # 2. Kiểm tra xem có bất kỳ hộp nào có thể được đẩy VÀO corral này không
            can_push_any_box_in = False
            for bx, by in boxes_set:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    # target_pos là ô bên trong corral
                    target_pos = (bx + dx, by + dy)
                    # player_side là ô đối diện để người chơi đứng vào đẩy
                    player_side = (bx - dx, by - dy)
                    
                    if target_pos in corral:
                        # Nếu người chơi có thể đi đến ô đối diện để đẩy hộp vào corral
                        if self.is_player_reachable(player_side, player_pos, boxes_set):
                            can_push_any_box_in = True
                            break
                if can_push_any_box_in: break
            
            # 3. Nếu có mục tiêu mà KHÔNG cách nào đẩy hộp vào được -> DEADLOCK
            if not can_push_any_box_in:
                return True
                
        return False
    
    
    def goal_room_penalty(self, boxes: Tuple[Tuple[int, int], ...]) -> int:
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

            if empty_targets and boxes_on_targets:
                deepest_empty = max(target_depths[target] for target in empty_targets)
                for filled in boxes_on_targets:
                    if target_depths[filled] < deepest_empty:
                        penalty += 10
                        break

            if any(entrance in boxes_set for entrance in entrances):
                penalty += 15

            if empty_targets and boxes_on_targets:
                max_filled_depth = max(target_depths[box] for box in boxes_on_targets)
                min_empty_depth = min(target_depths[target] for target in empty_targets)
                if max_filled_depth < min_empty_depth:
                    penalty += 50
                elif any(entrance in boxes_set for entrance in entrances):
                    penalty += 50

            if any(self.is_goal_room_entrance_blocking(entrance, boxes_set) for entrance in entrances):
                penalty += 2000

        return penalty

    def deadlock_penalty(self, boxes: Tuple) -> int:
        cache_key = tuple(sorted(boxes))
        if cache_key in self.deadlock_penalty_cache:
            return self.deadlock_penalty_cache[cache_key]

        penalty = 0
        box_set = set(boxes)
        for box in boxes:
            if box in self.game.state.targets:
                continue
            if self.dead_square_map[box[1]][box[0]]:
                self.deadlock_penalty_cache[cache_key] = 10000
                return 10000
            if self.is_corner_deadlock(box):
                penalty += 2000
            if self.is_tunnel_deadlock(box):
                penalty += 1200
            if self.is_two_box_tunnel_deadlock(box, box_set):
                penalty += 1800
            if self.is_diagonal_deadlock(box, box_set):
                penalty += 2200
            if self.is_freeze_deadlock(box, box_set):
                penalty += 1600
            if self.is_pattern_deadlock(box, box_set):
                penalty += 1800
            if self.is_goal_room_entrance_blocking(box, box_set):
                penalty += 2000
            if self.is_box_frozen(box, box_set):
                penalty += 1000

        if self.is_2x2_block_deadlock(box_set):
            penalty += 2500
        if self.is_freeze_deadlock_group(box_set):
            penalty += 2000

        self.deadlock_penalty_cache[cache_key] = penalty
        return penalty
    def find_player_position(self) -> Tuple[int, int]:
        """Quét bản đồ để tìm vị trí người chơi (ký hiệu thường là '@' hoặc số tương ứng)."""
        board = self.game.state.board
        for y in range(self.game.state.height):
            for x in range(self.game.state.width):
                # Giả sử trong mảng board của bạn, người chơi được ký hiệu là một số cụ thể
                # Ví dụ: 2 là người chơi, 3 là người chơi đứng trên mục tiêu
                if board[y][x] == 'P' or board[y][x] == '@':
                    return (x, y)
        return (0, 0)
    def is_deadlock(self, boxes: Tuple[Tuple[int, int], ...]) -> bool:
        cache_key = tuple(sorted(boxes))
        if cache_key in self.deadlock_cache:
            return self.deadlock_cache[cache_key]
        player_pos = self.find_player_position()
        boxes_set = set(boxes)
        result = False
        for box in boxes:
            if box in self.game.state.targets:
                continue
            bx, by = box
            if self.dead_square_map[by][bx]:
                result = True
                break
            if self.is_corner_deadlock(box):
                result = True
                break
            if self.is_tunnel_deadlock(box):
                result = True
                break
            if self.is_two_box_tunnel_deadlock(box, boxes_set):
                result = True
                break
            if self.is_diagonal_deadlock(box, boxes_set):
                result = True
                break
            if self.is_freeze_deadlock(box, boxes_set):
                result = True
                break
            if self.is_pattern_deadlock(box, boxes_set):
                result = True
                break
            if self.is_goal_room_entrance_blocking(box, boxes_set):
                result = True
                break
            if self.is_box_frozen(box, boxes_set):
                result = True
                break
        if self.is_corral_deadlock(player_pos, boxes_set):
            return True
        if not result:
            if self.is_2x2_block_deadlock(boxes_set) or self.is_freeze_deadlock_group(boxes_set):
                result = True

        self.deadlock_cache[cache_key] = result
        return result

    def is_goal_state(self, state) -> bool:
        for box in state.boxes:
            if box not in self.game.state.targets:
                return False
        return len(state.boxes) == len(self.game.state.targets)

    def is_corner_deadlock(self, box, targets):
        # NẾU HỘP ĐANG Ở TRÊN MỤC TIÊU -> KHÔNG PHẢI DEADLOCK
        if box in targets:
            return False
        
        x, y = box
        board = self.game.state.board
        
        # Kiểm tra các phía có phải là tường (1) không
        up = board[y-1][x] == 1
        down = board[y+1][x] == 1
        left = board[y][x-1] == 1
        right = board[y][x+1] == 1
        
        # Nếu bị kẹt bởi 2 bức tường tạo thành góc (L)
        if (up and left) or (up and right) or (down and left) or (down and right):
            return True
        return False

    def is_tunnel_deadlock(self, box: Tuple[int, int]) -> bool:
        if box in self.game.state.targets:
            return False

        bx, by = box
        left_wall = self.game.state.board[by][bx-1] == 1 if bx > 0 else True
        right_wall = self.game.state.board[by][bx+1] == 1 if bx < self.game.state.width-1 else True
        up_wall = self.game.state.board[by-1][bx] == 1 if by > 0 else True
        down_wall = self.game.state.board[by+1][bx] == 1 if by < self.game.state.height-1 else True

        if up_wall and down_wall:
            # Horizontal tunnel: check the full reachable horizontal corridor
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
            # Vertical tunnel: check the full reachable vertical corridor
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
        x, y = pos

        board = self.game.state.board
        width = self.game.state.width
        height = self.game.state.height

        if board[y][x] == 1:
            return False

        # cache các ô xung quanh (tránh lookup nhiều lần)
        left_wall  = (x == 0) or (board[y][x-1] == 1)
        right_wall = (x == width - 1) or (board[y][x+1] == 1)
        up_wall    = (y == 0) or (board[y-1][x] == 1)
        down_wall  = (y == height - 1) or (board[y+1][x] == 1)

        # giảm cost so sánh string
        if direction == 'UP':
            return left_wall and right_wall and not up_wall
        elif direction == 'DOWN':
            return left_wall and right_wall and not down_wall
        elif direction == 'LEFT':
            return up_wall and down_wall and not left_wall
        elif direction == 'RIGHT':
            return up_wall and down_wall and not right_wall

        return False

    def tunnel_macro(self, box_pos, direction, boxes):
        final_pos = box_pos
        dx, dy = self.get_direction_vector(direction)

        # MUST: chỉ macro nếu đang ở tunnel
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
            if self.is_goal_room_entrance_blocking(next_pos, boxes):
                break

            if not self.is_tunnel_tile(next_pos, direction):
                if next_pos in self.targets_list:
                    final_pos = next_pos
                break

            final_pos = next_pos

        distance = abs(final_pos[0] - box_pos[0]) + abs(final_pos[1] - box_pos[1])
        return final_pos, max(distance, 1)

    def is_freeze_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
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
        for box in boxes:
            if box in self.game.state.targets:
                continue
            bx, by = box
            left_wall = bx == 0 or self.game.state.board[by][bx-1] == 1
            right_wall = bx == self.game.state.width-1 or self.game.state.board[by][bx+1] == 1
            up_wall = by == 0 or self.game.state.board[by-1][bx] == 1
            down_wall = by == self.game.state.height-1 or self.game.state.board[by+1][bx] == 1

            if left_wall or right_wall:
                above = (bx, by-1)
                below = (bx, by+1)
                if above in boxes and self.is_box_frozen(above, boxes):
                    return True
                if below in boxes and self.is_box_frozen(below, boxes):
                    return True

            if up_wall or down_wall:
                left = (bx-1, by)
                right = (bx+1, by)
                if left in boxes and self.is_box_frozen(left, boxes):
                    return True
                if right in boxes and self.is_box_frozen(right, boxes):
                    return True

        return False

    def is_pattern_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
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
        for box in boxes:
            if box in self.game.state.targets:
                continue
            bx, by = box
            for dx in (0, -1):
                for dy in (0, -1):
                    square = [(bx + dx + ox, by + dy + oy) for ox in (0, 1) for oy in (0, 1)]
                    if any(x < 0 or x >= self.game.state.width or y < 0 or y >= self.game.state.height for x, y in square):
                        continue
                    box_count = sum(1 for x, y in square if (x, y) in boxes)
                    wall_count = sum(1 for x, y in square if self.game.state.board[y][x] == 1)
                    target_count = sum(1 for x, y in square if (x, y) in self.game.state.targets)
                    if box_count + wall_count == 4 and box_count >= 1 and target_count < box_count:
                        return True
        return False

    def is_box_frozen(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
        bx, by = box
        can_move_up = by > 0 and self.game.state.board[by-1][bx] != 1 and (bx, by-1) not in boxes
        can_move_down = by < self.game.state.height-1 and self.game.state.board[by+1][bx] != 1 and (bx, by+1) not in boxes
        can_move_left = bx > 0 and self.game.state.board[by][bx-1] != 1 and (bx-1, by) not in boxes
        can_move_right = bx < self.game.state.width-1 and self.game.state.board[by][bx+1] != 1 and (bx+1, by) not in boxes
        return not (can_move_up or can_move_down or can_move_left or can_move_right)

    def is_diagonal_deadlock(self, box: Tuple[int, int], boxes: Set[Tuple[int, int]]) -> bool:
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
