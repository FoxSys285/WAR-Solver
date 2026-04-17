"""
Game engine for Sokoban
"""

from typing import Tuple, List, Optional
from .state import GameState
from .level import Level


class Game:
    """Main game engine for Sokoban"""
    
    # Direction constants
    DIRECTIONS = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'LEFT': (-1, 0),
        'RIGHT': (1, 0),
    }
    
    def __init__(self, level: Level):
        """
        Initialize game with a level
        
        Args:
            level: A Level object
        """
        self.level = level
        self.state = level.state
        self.initial_state = self._save_state()
        self.is_won = False
    
    def _save_state(self) -> dict:
        """Save current game state"""
        return {
            'player_pos': self.state.player_pos,
            'boxes': self.state.boxes.copy(),
            'move_history': self.state.move_history.copy(),
        }
    
    def _restore_state(self, saved_state: dict):
        """Restore a saved game state"""
        self.state.player_pos = saved_state['player_pos']
        self.state.boxes = saved_state['boxes'].copy()
        self.state.move_history = saved_state['move_history'].copy()
    
    def move(self, direction: str) -> bool:
        """
        Move the player in a direction
        
        Args:
            direction: 'UP', 'DOWN', 'LEFT', or 'RIGHT'
            
        Returns:
            True if move was successful, False otherwise
        """
        if direction not in self.DIRECTIONS:
            return False
        
        dx, dy = self.DIRECTIONS[direction]
        success = self.state.move_player(dx, dy)
        
        if success:
            self.is_won = self.state.is_solved()
        
        return success
    
    def move_direction(self, dx: int, dy: int) -> bool:
        """
        Move player in direction (dx, dy)
        
        Args:
            dx: Change in x
            dy: Change in y
            
        Returns:
            True if move was successful, False otherwise
        """
        success = self.state.move_player(dx, dy)
        
        if success:
            self.is_won = self.state.is_solved()
        
        return success
    
    def reset(self):
        """Reset the game to initial state"""
        self.state.player_pos = self.initial_state['player_pos']
        self.state.boxes = self.initial_state['boxes'].copy()
        self.state.move_history = []
        self.is_won = False
    
    def undo_move(self) -> bool:
        """
        Undo the last move
        
        Returns:
            True if undo was successful, False otherwise
        """
        if not self.state.move_history:
            return False
        
        # This is a simplified undo - need full state history for proper implementation
        return False
    
    def get_possible_moves(self) -> List[str]:
        """
        Get list of valid moves from current state
        
        Returns:
            List of valid direction strings
        """
        valid_moves = []
        
        for direction, (dx, dy) in self.DIRECTIONS.items():
            # Check if we can move in this direction
            px, py = self.state.player_pos
            nx, ny = px + dx, py + dy
            
            if not self.state.is_valid_position(nx, ny):
                continue
            
            # Check if there's a box that can't be pushed
            if (nx, ny) in self.state.boxes:
                bx, by = nx, ny
                bnx, bny = bx + dx, by + dy
                
                if not self.state.is_valid_position(bnx, bny):
                    continue
                
                if (bnx, bny) in self.state.boxes:
                    continue
            
            valid_moves.append(direction)
        
        return valid_moves
    
    def get_state_for_ai(self) -> GameState:
        """
        Get current game state (for AI algorithms)
        
        Returns:
            A copy of the current GameState
        """
        from copy import deepcopy
        return deepcopy(self.state)
    
    def apply_moves(self, moves: List[Tuple[int, int]]) -> bool:
        """
        Apply a sequence of moves
        
        Args:
            moves: List of (dx, dy) tuples
            
        Returns:
            True if all moves were successful, False otherwise
        """
        for dx, dy in moves:
            if not self.move_direction(dx, dy):
                return False
        
        return True
    
    def get_move_sequence_from_direction_list(self, directions: List[str]) -> List[Tuple[int, int]]:
        """
        Convert list of direction strings to move tuples
        
        Args:
            directions: List of direction strings
            
        Returns:
            List of (dx, dy) tuples
        """
        moves = []
        for direction in directions:
            if direction in self.DIRECTIONS:
                moves.append(self.DIRECTIONS[direction])
        return moves
    
    def print_game(self):
        """Print current game state"""
        print(f"\n{self.level.name}")
        print("=" * (self.state.width + 2))
        self.state.print_state()
        print(f"Moves: {len(self.state.move_history)}")
        print(f"Valid moves: {self.get_possible_moves()}")
        if self.is_won:
            print("🎉 LEVEL SOLVED! 🎉")
        print("=" * (self.state.width + 2))
