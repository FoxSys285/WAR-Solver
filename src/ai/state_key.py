"""
State key wrapper for Sokoban solver state hashing.
"""

from typing import Tuple


class StateKey:
    __slots__ = ('player_pos', 'boxes', 'hash')

    def __init__(self, player_pos: Tuple[int, int], boxes: Tuple[Tuple[int, int], ...], hash_value: int):
        self.player_pos = player_pos
        self.boxes = boxes
        self.hash = hash_value

    def __hash__(self) -> int:
        return self.hash

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, StateKey) and
            self.player_pos == other.player_pos and
            self.boxes == other.boxes
        )

    def __repr__(self) -> str:
        return f"StateKey(player={self.player_pos}, boxes={self.boxes})"
