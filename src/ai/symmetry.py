"""
Symmetry reduction utilities for Sokoban AI.
"""

import random
from typing import Tuple, List, Set
from .state_key import StateKey


class SymmetryReducer:
    """Symmetry Reduction (Giảm thiểu đối xứng) - Phát hiện và loại bỏ các trạng thái đối xứng"""

    def __init__(self, width: int, height: int, walls: Set[Tuple[int, int]], targets: Set[Tuple[int, int]]):
        self.width = width
        self.height = height
        self.walls = walls
        self.targets = targets
        self.symmetries = self._detect_board_symmetries()
        self.symmetry_cache = {}

    def _detect_board_symmetries(self) -> List[str]:
        symmetries = []
        if self._is_symmetric_horizontal():
            symmetries.append('horizontal')
        if self._is_symmetric_vertical():
            symmetries.append('vertical')
        if self._is_symmetric_rotation_180():
            symmetries.append('rotation_180')
        return symmetries

    def _tile_status(self, pos: Tuple[int, int]) -> Tuple[bool, bool]:
        return (pos in self.walls, pos in self.targets)

    def _is_symmetric_horizontal(self) -> bool:
        for y in range(self.height):
            for x in range(self.width // 2 + 1):
                left = (x, y)
                right = (self.width - 1 - x, y)
                if self._tile_status(left) != self._tile_status(right):
                    return False
        return True

    def _is_symmetric_vertical(self) -> bool:
        for y in range(self.height // 2 + 1):
            for x in range(self.width):
                top = (x, y)
                bottom = (x, self.height - 1 - y)
                if self._tile_status(top) != self._tile_status(bottom):
                    return False
        return True

    def _is_symmetric_rotation_180(self) -> bool:
        for y in range(self.height):
            for x in range(self.width):
                pos1 = (x, y)
                pos2 = (self.width - 1 - x, self.height - 1 - y)
                if self._tile_status(pos1) != self._tile_status(pos2):
                    return False
        return True

    def _flip_horizontal(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        px, py = player_pos
        new_player = (self.width - 1 - px, py)
        new_boxes = tuple(sorted({(self.width - 1 - bx, by) for bx, by in boxes}))
        return new_player, new_boxes

    def _flip_vertical(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        px, py = player_pos
        new_player = (px, self.height - 1 - py)
        new_boxes = tuple(sorted({(bx, self.height - 1 - by) for bx, by in boxes}))
        return new_player, new_boxes

    def _rotate_180(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        px, py = player_pos
        new_player = (self.width - 1 - px, self.height - 1 - py)
        new_boxes = tuple(sorted({(self.width - 1 - bx, self.height - 1 - by) for bx, by in boxes}))
        return new_player, new_boxes

    def get_canonical_state(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]:
        cache_key = (player_pos, boxes)
        if cache_key in self.symmetry_cache:
            return self.symmetry_cache[cache_key]

        states = [(player_pos, boxes)]
        if 'horizontal' in self.symmetries:
            states.append(self._flip_horizontal(player_pos, boxes))
        if 'vertical' in self.symmetries:
            states.append(self._flip_vertical(player_pos, boxes))
        if 'rotation_180' in self.symmetries:
            states.append(self._rotate_180(player_pos, boxes))

        canonical = min(states, key=lambda s: (s[0], s[1]))
        self.symmetry_cache[cache_key] = canonical
        return canonical

    def get_all_symmetric_states(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Set[Tuple[Tuple[int, int], Tuple[Tuple[int, int], ...]]]:
        symmetric_states = {(player_pos, boxes)}
        if 'horizontal' in self.symmetries:
            symmetric_states.add(self._flip_horizontal(player_pos, boxes))
        if 'vertical' in self.symmetries:
            symmetric_states.add(self._flip_vertical(player_pos, boxes))
        if 'rotation_180' in self.symmetries:
            symmetric_states.add(self._rotate_180(player_pos, boxes))
        return symmetric_states


class SymmetryMixin:
    def _initialize_zobrist_table(self):
        rng = random.Random(self.game.state.width * 1009 + self.game.state.height)
        self.zobrist_player = {}
        self.zobrist_box = {}
        for y in range(self.game.state.height):
            for x in range(self.game.state.width):
                self.zobrist_player[(x, y)] = rng.getrandbits(64)
                self.zobrist_box[(x, y)] = rng.getrandbits(64)

    def _hash_state(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> int:
        h = self.zobrist_player[player_pos]
        for box in boxes:
            h ^= self.zobrist_box[box]
        return h

    def _make_state_key(self, state):
        if isinstance(state, StateKey):
            return state
        player_pos, boxes = state
        boxes_tuple = tuple(sorted(set(boxes)))
        return StateKey(player_pos, boxes_tuple, self._hash_state(player_pos, boxes_tuple))

    def get_canonical_player_pos(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...]) -> Tuple[int, int]:
        boxes_set = set(boxes)
        reachable = self.compute_reachable_tiles(player_pos, boxes_set)
        if not reachable:
            return player_pos
        return min(reachable)

    def _canonical_state_key(self, player_pos: Tuple[int, int], boxes) -> StateKey:
        boxes_set = set(boxes)
        boxes_tuple = tuple(sorted(boxes_set))
        canonical_player_pos = self.get_canonical_player_pos(player_pos, boxes_tuple)
        if self.symmetries_detected:
            canonical_player_pos, boxes_tuple = self.symmetry_reducer.get_canonical_state(canonical_player_pos, boxes_tuple)
        return StateKey(canonical_player_pos, boxes_tuple, self._hash_state(canonical_player_pos, boxes_tuple))

    def _is_symmetric_state_visited(self, state) -> bool:
        canonical_state = self._canonical_state_key(state.player_pos, state.boxes)
        return canonical_state in self.transposition_table

    def print_symmetry_info(self):
        print("\n" + "="*60)
        print("SYMMETRY REDUCTION INFORMATION")
        print("="*60)
        print(f"Board size: {self.game.state.width}x{self.game.state.height}")
        print(f"Number of boxes: {len(self.targets_list)}")
        if self.symmetries_detected:
            print(f"\nDetected Symmetries ({len(self.symmetries_detected)}):")
            for sym in self.symmetries_detected:
                if sym == 'horizontal':
                    print("  Horizontal flip (ngang)")
                elif sym == 'vertical':
                    print("  Vertical flip (dọc)")
                elif sym == 'rotation_180':
                    print("  180-degree rotation (quay 180°)")
            reduction_factor = 2 ** len(self.symmetries_detected)
            print(f"\nPotential state space reduction: ~{reduction_factor}x")
            print(f"This means the search space can be reduced to ~1/{reduction_factor} of the original size")
        else:
            print("\nNo board symmetries detected - Symmetry Reduction will not be used")
        print("="*60 + "\n")
