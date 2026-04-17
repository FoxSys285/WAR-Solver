"""
Game state management for Sokoban
"""

import random
from typing import Tuple, List, Set
from copy import deepcopy


class GameState:
    """Represents the state of a Sokoban game"""

    _zobrist_table_cache = {}
    
    def __init__(self, width: int, height: int):
        """
        Initialize game state
        
        Args:
            width: Width of the game board
            height: Height of the game board
        """
        self.width = width
        self.height = height
        
        # 0: empty, 1: wall, 2: target
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        
        # Player position (x, y)
        self.player_pos = (0, 0)
        
        # Set of box positions
        self.boxes = set()
        
        # Set of target positions
        self.targets = set()
        
        # Move history
        self.move_history = []
        self._initialize_zobrist()

    def _initialize_zobrist(self):
        """Initialize zobrist tables for this game board."""
        key = (self.width, self.height)
        if key not in GameState._zobrist_table_cache:
            rng = random.Random(self.width * 1009 + self.height)
            player_table = {}
            box_table = {}
            for y in range(self.height):
                for x in range(self.width):
                    player_table[(x, y)] = rng.getrandbits(64)
                    box_table[(x, y)] = rng.getrandbits(64)
            GameState._zobrist_table_cache[key] = (player_table, box_table)

        self._zobrist_player_table, self._zobrist_box_table = GameState._zobrist_table_cache[key]
        self._recompute_zobrist()

    def _recompute_zobrist(self):
        """Recompute the zobrist hash for the current state."""
        self._zobrist_hash = 0
        if self.player_pos in self._zobrist_player_table:
            self._zobrist_hash ^= self._zobrist_player_table[self.player_pos]
        for box in self.boxes:
            self._zobrist_hash ^= self._zobrist_box_table[box]

    def _update_zobrist_player(self, old_pos: Tuple[int, int], new_pos: Tuple[int, int]):
        self._zobrist_hash ^= self._zobrist_player_table[old_pos]
        self._zobrist_hash ^= self._zobrist_player_table[new_pos]

    def _update_zobrist_box(self, old_pos: Tuple[int, int], new_pos: Tuple[int, int]):
        self._zobrist_hash ^= self._zobrist_box_table[old_pos]
        self._zobrist_hash ^= self._zobrist_box_table[new_pos]

    def is_valid_position(self, x: int, y: int) -> bool:
        """
        Check if a position is valid (in bounds and not a wall)
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if position is valid, False otherwise
        """
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return False
        return self.board[y][x] != 1
    
    def set_wall(self, x: int, y: int):
        """Set a wall at position (x, y)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.board[y][x] = 1
    
    def set_target(self, x: int, y: int):
        """Set a target position at (x, y)"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.targets.add((x, y))
    
    def set_player_pos(self, x: int, y: int):
        """Set player position"""
        if self.is_valid_position(x, y):
            new_pos = (x, y)
            if new_pos != self.player_pos:
                self._update_zobrist_player(self.player_pos, new_pos)
                self.player_pos = new_pos
    
    def add_box(self, x: int, y: int):
        """Add a box at position (x, y)"""
        if self.is_valid_position(x, y) and (x, y) not in self.boxes:
            self.boxes.add((x, y))
            self._zobrist_hash ^= self._zobrist_box_table[(x, y)]
    
    def move_player(self, dx: int, dy: int) -> bool:
        """
        Move player in direction (dx, dy)
        
        Args:
            dx: Change in x
            dy: Change in y
            
        Returns:
            True if move was successful, False otherwise
        """
        px, py = self.player_pos
        nx, ny = px + dx, py + dy
        
        # Check if new position is valid
        if not self.is_valid_position(nx, ny):
            return False
        
        # Check if there's a box in the way
        if (nx, ny) in self.boxes:
            # Try to push the box
            bx, by = nx, ny
            bnx, bny = bx + dx, by + dy
            
            # Check if box can be pushed
            if not self.is_valid_position(bnx, bny):
                return False
            
            if (bnx, bny) in self.boxes:
                return False
            
            # Push the box
            self.boxes.remove((bx, by))
            self._update_zobrist_box((bx, by), (bnx, bny))
            self.boxes.add((bnx, bny))
        
        # Move player
        self._update_zobrist_player(self.player_pos, (nx, ny))
        self.player_pos = (nx, ny)
        self.move_history.append((dx, dy))
        return True
    
    def is_solved(self) -> bool:
        """
        Check if the puzzle is solved
        
        Returns:
            True if all boxes are on targets, False otherwise
        """
        if not self.targets:
            return False
        
        if len(self.boxes) != len(self.targets):
            return False
        
        return self.boxes == self.targets
    
    def get_boxes_on_targets(self) -> int:
        """Get number of boxes on target positions"""
        return len(self.boxes & self.targets)
    
    def __deepcopy__(self, memo):
        """Create a deep copy of the game state"""
        new_state = GameState(self.width, self.height)
        new_state.board = deepcopy(self.board, memo)
        new_state.player_pos = self.player_pos
        new_state.boxes = deepcopy(self.boxes, memo)
        new_state.targets = deepcopy(self.targets, memo)
        new_state.move_history = deepcopy(self.move_history, memo)
        new_state._zobrist_hash = self._zobrist_hash
        new_state._zobrist_player_table = self._zobrist_player_table
        new_state._zobrist_box_table = self._zobrist_box_table
        return new_state
    
    def __hash__(self):
        """Hash for using state in sets/dicts"""
        return self._zobrist_hash
    
    def __eq__(self, other):
        """Check equality with another state"""
        if not isinstance(other, GameState):
            return False
        return (self.player_pos == other.player_pos and 
                self.boxes == other.boxes)
    
    def to_string(self) -> str:
        """Convert state to string representation"""
        lines = []
        for y in range(self.height):
            line = []
            for x in range(self.width):
                if (x, y) == self.player_pos:
                    line.append('P')
                elif (x, y) in self.boxes:
                    if (x, y) in self.targets:
                        line.append('*')  # Box on target
                    else:
                        line.append('B')  # Box
                elif (x, y) in self.targets:
                    line.append('T')  # Target
                elif self.board[y][x] == 1:
                    line.append('#')  # Wall
                else:
                    line.append('.')  # Empty
            lines.append(''.join(line))
        return '\n'.join(lines)
    
    def print_state(self):
        """Print the current state"""
        print(self.to_string())
        print(f"Solved: {self.is_solved()}")
        print(f"Boxes on targets: {self.get_boxes_on_targets()}/{len(self.targets)}")
