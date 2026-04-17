"""
Configuration for Sokoban AI project
"""

# Game settings
GAME_WIDTH = 20
GAME_HEIGHT = 20
TILE_SIZE = 32

# AI settings
MAX_DEPTH = 1000
ALGORITHM = "BFS"  # BFS, DFS, A*, IDDFS

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = "logs/sokoban.log"

# Display settings
SHOW_STEPS = False
DELAY_MS = 100
