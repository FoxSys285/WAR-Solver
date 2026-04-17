"""
Level management for Sokoban
"""

from typing import List, Tuple
from .state import GameState


class Level:
    """Represents a Sokoban level"""
    
    def __init__(self, name: str, width: int, height: int):
        """
        Initialize a level
        
        Args:
            name: Name of the level
            width: Width of the level
            height: Height of the level
        """
        self.name = name
        self.width = width
        self.height = height
        self.state = GameState(width, height)
    
    @staticmethod
    def from_string(name: str, level_string: str) -> 'Level':
        """
        Create a level from a string representation
        
        Format:
            # = Wall
            . = Empty space
            P = Player
            B = Box
            T = Target
            * = Box on target
            @ = Player on target
        
        Args:
            name: Name of the level
            level_string: String representation of the level
            
        Returns:
            A Level object
        """
        lines = level_string.strip().split('\n')
        height = len(lines)
        width = max(len(line) for line in lines) if lines else 0
        
        level = Level(name, width, height)
        
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == '#':
                    level.state.set_wall(x, y)
                elif char == 'P':
                    level.state.set_player_pos(x, y)
                elif char == 'B':
                    level.state.add_box(x, y)
                elif char == 'T':
                    level.state.set_target(x, y)
                elif char == '*':
                    level.state.set_target(x, y)
                    level.state.add_box(x, y)
                elif char == '@':
                    level.state.set_player_pos(x, y)
                    level.state.set_target(x, y)
        
        return level
    
    @staticmethod
    def from_file(filepath: str) -> 'Level':
        """
        Load a level from a file
        
        Args:
            filepath: Path to the level file
            
        Returns:
            A Level object
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract level name from file
        name = filepath.split('/')[-1].split('.')[0]
        
        # Assume first line is name or use filename
        lines = content.strip().split('\n')
        if lines[0].startswith(';'):
            name = lines[0][1:].strip()
            level_string = '\n'.join(lines[1:])
        else:
            level_string = content
        
        return Level.from_string(name, level_string)
    
    def to_string(self) -> str:
        """Convert level to string representation"""
        return self.state.to_string()
    
    def print_level(self):
        """Print the level"""
        print(f"Level: {self.name}")
        print("=" * (self.width + 2))
        self.state.print_state()
        print("=" * (self.width + 2))


# Sample levels
SAMPLE_LEVEL_1 = """
######################
#          #         #
# P      B      T    #
#          #         #
######################
"""

SAMPLE_LEVEL_2 = """
#############
#     #     #
# B   P     #
#   #    T  #
#     #     #
#############
"""

SAMPLE_LEVEL_3 = """
##########
#        #
#  B P   #
#   #  T #
#   #  . #
#        #
##########
"""
