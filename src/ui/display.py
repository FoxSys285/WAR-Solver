"""
Graphics and display module for Sokoban using Pygame
"""

import os
import sys
import pygame
from typing import Dict, Optional, Tuple
from pathlib import Path


def get_resource_path(relative_path: str) -> str:
    """Return absolute resource path for dev or PyInstaller executable."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Use parent of src/ui as project root in development
        base_path = Path(__file__).resolve().parents[2]
    return str((base_path / relative_path).resolve())


class SpriteManager:
    """Manages game sprites and images"""
    
    def __init__(self, image_dir: str = "images", tile_size: int = 32):
        """
        Initialize sprite manager
        
        Args:
            image_dir: Directory containing sprite images
            tile_size: Size of each tile in pixels
        """
        self.image_dir = image_dir if os.path.isabs(image_dir) else get_resource_path(image_dir)
        self.tile_size = tile_size
        self.sprites: Dict[str, pygame.Surface] = {}
        self.load_sprites()
    
    def load_sprites(self):
        """Load all sprite images"""
        sprite_names = [
            'player', 'box', 'box_in_target', 'wall', 
            'floor', 'target', 'space', 'bg'
        ]
        
        for name in sprite_names:
            self.load_sprite(name)
    
    def load_sprite(self, name: str) -> Optional[pygame.Surface]:
        """
        Load a single sprite
        
        Args:
            name: Name of the sprite (without extension)
            
        Returns:
            pygame.Surface if loaded, None if file not found
        """
        filepath = os.path.join(self.image_dir, f"{name}.png")
        
        if not os.path.exists(filepath):
            # Create a placeholder surface if file doesn't exist
            print(f"Warning: Image not found at {filepath}. Creating placeholder.")
            self.sprites[name] = self._create_placeholder(name)
            return self.sprites[name]
        
        try:
            sprite = pygame.image.load(filepath)
            sprite = pygame.transform.scale(sprite, (self.tile_size, self.tile_size))
            self.sprites[name] = sprite
            print(f"Loaded sprite: {name}")
            return sprite
        except Exception as e:
            print(f"Error loading sprite {name}: {e}")
            self.sprites[name] = self._create_placeholder(name)
            return self.sprites[name]
    
    def _create_placeholder(self, name: str) -> pygame.Surface:
        """Create a placeholder surface if image not found"""
        colors = {
            'player': (0, 100, 200),      # Blue
            'box': (139, 69, 19),          # Brown
            'box_in_target': (255, 165, 0), # Orange
            'wall': (50, 50, 50),          # Dark gray
            'floor': (200, 200, 200),      # Light gray
            'target': (255, 0, 0),         # Red
            'space': (150, 150, 150),      # Medium gray
            'bg': (100, 100, 100),         # Gray
        }
        
        color = colors.get(name, (128, 128, 128))
        surface = pygame.Surface((self.tile_size, self.tile_size))
        surface.fill(color)
        
        # Add text to placeholder
        font = pygame.font.Font(None, 16)
        text = font.render(name[:3], True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.tile_size//2, self.tile_size//2))
        surface.blit(text, text_rect)
        
        return surface
    
    def get_sprite(self, name: str) -> pygame.Surface:
        """Get sprite by name"""
        return self.sprites.get(name, self.sprites.get('space'))


class GameDisplay:
    """Handles the display and rendering of Sokoban game"""
    
    def __init__(self, game, window_title: str = "Sokoban AI", 
                 image_dir: str = "images", tile_size: int = 32):
        """
        Initialize game display
        
        Args:
            game: Game object
            window_title: Title of the window
            image_dir: Directory containing sprite images
            tile_size: Size of each tile in pixels
        """
        self.game = game
        self.tile_size = tile_size
        self.sprite_manager = SpriteManager(image_dir, tile_size)
        
        # Calculate window size
        self.width = game.state.width * tile_size
        self.height = game.state.height * tile_size
        
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(window_title)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60
    
    def draw_tile(self, x: int, y: int, tile_type: str):
        """
        Draw a tile at position (x, y)
        
        Args:
            x: X coordinate in tiles
            y: Y coordinate in tiles
            tile_type: Type of tile to draw
        """
        sprite = self.sprite_manager.get_sprite(tile_type)
        rect = pygame.Rect(x * self.tile_size, y * self.tile_size, 
                          self.tile_size, self.tile_size)
        self.screen.blit(sprite, rect)
    
    def draw_game(self):
        """Draw the entire game board"""
        state = self.game.state
        
        # Draw background
        self.screen.fill((100, 100, 100))
        
        # Draw all tiles
        for y in range(state.height):
            for x in range(state.width):
                if state.board[y][x] == 1:
                    self.draw_tile(x, y, 'wall')
                elif (x, y) in state.targets:
                    self.draw_tile(x, y, 'target')
                else:
                    self.draw_tile(x, y, 'floor')
        
        # Draw boxes
        for bx, by in state.boxes:
            if (bx, by) in state.targets:
                self.draw_tile(bx, by, 'box_in_target')
            else:
                self.draw_tile(bx, by, 'box')
        
        # Draw player
        px, py = state.player_pos
        self.draw_tile(px, py, 'player')
        
        # Update display
        pygame.display.flip()
    
    def draw_hud(self):
        """Draw HUD (heads-up display) with game info"""
        # Draw semi-transparent HUD background at top
        hud_height = 30
        hud_bg = pygame.Surface((self.width, hud_height))
        hud_bg.set_alpha(200)
        hud_bg.fill((0, 0, 0))
        self.screen.blit(hud_bg, (0, 0))
        
        # Create HUD text
        font = pygame.font.Font(None, 20)
        level_text = font.render(f"Level: {self.game.level.name}", True, (255, 255, 255))
        moves_text = font.render(f"Moves: {len(self.game.state.move_history)}", True, (255, 255, 255))
        progress_text = font.render(
            f"Progress: {self.game.state.get_boxes_on_targets()}/{len(self.game.state.targets)}", 
            True, (255, 255, 255)
        )
        
        # Draw HUD text
        self.screen.blit(level_text, (10, 5))
        self.screen.blit(moves_text, (self.width // 3 + 10, 5))
        self.screen.blit(progress_text, (2 * self.width // 3 - 50, 5))
    
    def handle_events(self) -> bool:
        """
        Handle pygame events
        
        Returns:
            False if quit event, True otherwise
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return False
                
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.game.move('UP')
                
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.game.move('DOWN')
                
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.game.move('LEFT')
                
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.game.move('RIGHT')
                
                elif event.key == pygame.K_r:
                    self.game.reset()
                    print("\nGame reset!")
                
                elif event.key == pygame.K_SPACE:
                    print("\n" + self.game.state.to_string())
        
        return self.running
    
    def update(self):
        """Update display"""
        self.draw_game()
        self.draw_hud()
        self.clock.tick(self.fps)
    
    def show_message(self, message: str, duration: int = 3000):
        """
        Show a message on screen
        
        Args:
            message: Message to display
            duration: Duration in milliseconds
        """
        font = pygame.font.Font(None, 48)
        text = font.render(message, True, (255, 255, 0))
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        
        # Draw semi-transparent background
        bg = pygame.Surface((self.width, self.height))
        bg.set_alpha(128)
        bg.fill((0, 0, 0))
        
        self.screen.blit(bg, (0, 0))
        self.screen.blit(text, text_rect)
        pygame.display.flip()
        
        pygame.time.delay(duration)
    
    def quit(self):
        """Clean up and quit"""
        pygame.quit()
