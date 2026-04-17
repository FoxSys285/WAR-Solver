import os
import sys
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Tuple, Optional
from pathlib import Path
from PIL import Image, ImageDraw, ImageTk


def get_resource_path(relative_path: str) -> str:
    """Return absolute resource path for dev or PyInstaller executable."""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Use project root when running from source
        base_path = Path(__file__).resolve().parents[2]
    return str((base_path / relative_path).resolve())


class SpriteManager:
    """Manages game sprites using images or colored squares"""
    
    def __init__(self, image_dir: str = "images", tile_size: int = 40, root: tk.Tk = None):
        """
        Initialize sprite manager
        
        Args:
            image_dir: Directory containing sprite images
            tile_size: Size of each tile in pixels
            root: Tkinter root window (for PhotoImage)
        """
        self.image_dir = image_dir if os.path.isabs(image_dir) else get_resource_path(image_dir)
        self.tile_size = tile_size
        self.root = root
        self.sprites: Dict[str, ImageTk.PhotoImage] = {}
        self.sprite_images: Dict[str, Image.Image] = {}
        self.load_sprites()
    
    def load_sprites(self):
        """Load all sprite images"""
        sprite_names = [
            'player', 'box', 'box_in_target', 'wall', 
            'floor', 'target', 'space', 'bg'
        ]
        
        for name in sprite_names:
            self.load_sprite(name)
    
    def load_sprite(self, name: str) -> Optional[Image.Image]:
        """
        Load a single sprite
        
        Args:
            name: Name of the sprite (without extension)
            
        Returns:
            PIL Image if loaded, None if file not found
        """
        # Try different extensions
        extensions = ['.png', '.PNG', '.jpg', '.jpeg', '.gif']
        
        for ext in extensions:
            filepath = os.path.join(self.image_dir, f"{name}{ext}")
            if os.path.exists(filepath):
                try:
                    sprite = Image.open(filepath)
                    sprite = sprite.resize((self.tile_size, self.tile_size), Image.Resampling.LANCZOS)
                    self.sprite_images[name] = sprite
                    print(f"✓ Loaded sprite: {name} from {filepath}")
                    return sprite
                except Exception as e:
                    print(f"✗ Error loading {filepath}: {e}")
        
        # Create placeholder if image not found
        print(f"⚠ Image not found for {name}, creating placeholder")
        self.sprite_images[name] = self._create_placeholder(name)
        return self.sprite_images[name]
    
    def _create_placeholder(self, name: str) -> Image.Image:
        """Create a placeholder image if file not found"""
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
        img = Image.new('RGB', (self.tile_size, self.tile_size), color)
        draw = ImageDraw.Draw(img)
        
        # Add border
        draw.rectangle(
            [(1, 1), (self.tile_size-2, self.tile_size-2)],
            outline=(100, 100, 100),
            width=1
        )
        
        # Add text
        font_size = min(self.tile_size // 4, 12)
        try:
            font = ImageDraw.getfont(font_size)
        except:
            font = None
        
        text = name[:3].upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (self.tile_size - text_width) // 2
        y = (self.tile_size - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        return img
    
    def get_sprite(self, name: str) -> Image.Image:
        """Get sprite by name (returns PIL Image)"""
        return self.sprite_images.get(name, self.sprite_images.get('space'))
    
    def get_photo_image(self, name: str) -> ImageTk.PhotoImage:
        """Get sprite as PhotoImage"""
        img = self.get_sprite(name)
        return ImageTk.PhotoImage(img)


class GameDisplay(tk.Frame):
    """Game display frame for Sokoban game"""
    
    def __init__(self, parent, game, tile_size: int = 40, on_back_callback=None, level_id=None, levels_data=None, on_next_level_callback=None):
        """
        Initialize game display frame
        
        Args:
            parent: Parent widget
            game: Game object
            tile_size: Size of each tile in pixels
            on_back_callback: Callback when back button is pressed
            level_id: Current level ID
            levels_data: Dict of all levels
            on_next_level_callback: Callback when next level button is pressed
        """
        super().__init__(parent, bg='gray20')
        
        self.game = game
        self.tile_size = tile_size
        self.sprite_manager = SpriteManager("images", tile_size, root=parent)
        self.on_back_callback = on_back_callback
        self.level_id = level_id
        self.levels_data = levels_data
        self.on_next_level_callback = on_next_level_callback
        
        # Import AI solver
        from ai import AISolver
        self.ai_solver = AISolver(game)
        
        # Cache for PhotoImages to prevent garbage collection
        self.photo_cache = {}
        
        # Calculate sizes
        self.board_width = game.state.width * tile_size
        self.board_height = game.state.height * tile_size
        
        # Create main layout with grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Left panel fixed width
        self.grid_columnconfigure(1, weight=1)  # Right panel expands
        
        # Left panel for controls
        self.left_panel = tk.Frame(self, bg='gray20', width=200)
        self.left_panel.grid(row=0, column=0, sticky='ns', padx=(10, 5), pady=10)
        self.left_panel.grid_propagate(False)  # Don't resize based on content
        
        # Right panel for game board
        self.right_panel = tk.Frame(self, bg='gray20')
        self.right_panel.grid(row=0, column=1, sticky='nsew', padx=(5, 10), pady=10)
        
        # Create HUD frame in left panel
        self.create_hud()
        
        # Create button frame in left panel
        self.create_buttons()
        
        # Create canvas for game board in right panel
        self.canvas = tk.Canvas(
            self.right_panel,
            width=self.board_width,
            height=self.board_height,
            bg='gray40',
            highlightthickness=0
        )
        self.canvas.pack(expand=True)
        
        # Bind keyboard events
        self.bind_all('<Up>', lambda e: self.game.move('UP'))
        self.bind_all('<Down>', lambda e: self.game.move('DOWN'))
        self.bind_all('<Left>', lambda e: self.game.move('LEFT'))
        self.bind_all('<Right>', lambda e: self.game.move('RIGHT'))
        self.bind_all('w', lambda e: self.game.move('UP'))
        self.bind_all('s', lambda e: self.game.move('DOWN'))
        self.bind_all('a', lambda e: self.game.move('LEFT'))
        self.bind_all('d', lambda e: self.game.move('RIGHT'))
        self.bind_all('r', lambda e: self.reset_game())
        self.bind_all('<space>', lambda e: self.print_state())
        
        # Start update loop
        self.running = True
        self.update_game()
    
    def create_hud(self):
        """Create heads-up display"""
        hud_frame = tk.Frame(self.left_panel, bg='gray30', height=40)
        hud_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Level info
        self.level_label = tk.Label(
            hud_frame, text="", 
            bg='gray30', fg='white', font=('Arial', 10)
        )
        self.level_label.pack(side=tk.TOP, pady=2)
        
        # Moves info
        self.moves_label = tk.Label(
            hud_frame, text="",
            bg='gray30', fg='white', font=('Arial', 10)
        )
        self.moves_label.pack(side=tk.TOP, pady=2)
        
        # Progress info
        self.progress_label = tk.Label(
            hud_frame, text="",
            bg='gray30', fg='white', font=('Arial', 10)
        )
        self.progress_label.pack(side=tk.TOP, pady=2)
    
    def update_hud(self):
        """Update HUD display"""
        level_text = f"Level: {self.game.level.name}"
        moves_text = f"Moves: {len(self.game.state.move_history)}"
        progress_text = f"Progress: {self.game.state.get_boxes_on_targets()}/{len(self.game.state.targets)}"
        
        self.level_label.config(text=level_text)
        self.moves_label.config(text=moves_text)
        self.progress_label.config(text=progress_text)
    
    def create_buttons(self):
        """Create control buttons"""
        button_frame = tk.Frame(self.left_panel, bg='gray20')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Reset button
        reset_btn = tk.Button(
            button_frame, text="Reset (R)",
            command=self.reset_game,
            bg='gray50', fg='white', width=15, height=2
        )
        reset_btn.pack(pady=3)
        
        # Print state button
        state_btn = tk.Button(
            button_frame, text="Print State",
            command=self.print_state,
            bg='gray50', fg='white', width=15, height=2
        )
        state_btn.pack(pady=3)
        
        # AI Quick button
        self.ai_quick_btn = tk.Button(
            button_frame, text="AI Quick",
            command=self.start_ai_quick,
            bg='#2ecc71', fg='white', width=15, height=2
        )
        self.ai_quick_btn.pack(pady=3)
        
        # Stop AI button
        self.ai_stop_btn = tk.Button(
            button_frame, text="Stop AI",
            command=self.stop_ai,
            bg='#e67e22', fg='white', width=15, height=2, state='disabled'
        )
        self.ai_stop_btn.pack(pady=3)
        
        # Back button
        back_btn = tk.Button(
            button_frame, text="Quay Lại",
            command=self.go_back,
            bg='#e74c3c', fg='white', width=15, height=2
        )
        back_btn.pack(pady=3)
        
        # Next Level button
        if self.on_next_level_callback and self.level_id:
            next_btn = tk.Button(
                button_frame, text="Màn Tiếp Theo",
                command=self.go_next_level,
                bg='#27ae60', fg='white', width=15, height=2
            )
            next_btn.pack(pady=3)
        
        # Info label
        self.info_label = tk.Label(
            button_frame, text="Arrow Keys /\nWASD to move",
            bg='gray20', fg='yellow', font=('Arial', 8),
            justify=tk.CENTER
        )
        self.info_label.pack(pady=(10, 0))
    
    def start_ai_quick(self):
        """Start AI with fast mode for quicker, suboptimal solution"""
        print("Starting AI quick solver in background...")
        import threading
        
        self.ai_quick_btn.config(state='disabled')
        
        def solve_in_background():
            if self.ai_solver.fast_solve(timeout_seconds=500):
                self.ai_solver.start_auto_play()
                self.ai_stop_btn.config(state='normal')
            else:
                messagebox.showerror("AI Error", "Quick solver could not find a solution")
                self.ai_quick_btn.config(state='normal')
        
        solver_thread = threading.Thread(target=solve_in_background, daemon=True)
        solver_thread.start()
    
    def stop_ai(self):
        """Stop AI solver"""
        self.ai_solver.stop_auto_play()
        self.ai_quick_btn.config(state='normal')
        self.ai_stop_btn.config(state='disabled')
    
    def go_back(self):
        """Go back to menu"""
        self.running = False
        if self.on_back_callback:
            self.on_back_callback()
    
    def go_next_level(self):
        """Go to next level"""
        if self.on_next_level_callback and self.level_id:
            self.on_next_level_callback(self.level_id)
    
    def draw_game(self):
        """Draw the entire game board"""
        self.canvas.delete('all')
        state = self.game.state
        
        # Draw all tiles
        for y in range(state.height):
            for x in range(state.width):
                self.draw_tile(x, y)
        
        # Draw boxes
        for bx, by in state.boxes:
            if (bx, by) in state.targets:
                self.draw_sprite(bx, by, 'box_in_target')
            else:
                self.draw_sprite(bx, by, 'box')
        
        # Draw player
        px, py = state.player_pos
        self.draw_sprite(px, py, 'player')
    
    def draw_tile(self, x: int, y: int):
        """Draw a tile at position (x, y)"""
        state = self.game.state
        
        if state.board[y][x] == 1:
            self.draw_sprite(x, y, 'wall')
        elif (x, y) in state.targets:
            self.draw_sprite(x, y, 'target')
        else:
            self.draw_sprite(x, y, 'floor')
    
    def draw_sprite(self, x: int, y: int, sprite_type: str):
        """Draw a sprite at tile position"""
        # Get cached PhotoImage or create one
        if sprite_type not in self.photo_cache:
            self.photo_cache[sprite_type] = self.sprite_manager.get_photo_image(sprite_type)
        
        sprite = self.photo_cache[sprite_type]
        px = x * self.tile_size
        py = y * self.tile_size
        self.canvas.create_image(px, py, image=sprite, anchor='nw')
    
    def reset_game(self):
        """Reset game"""
        self.game.reset()
        print("Game reset!")
    
    def print_state(self):
        """Print game state"""
        print("\n" + self.game.state.to_string())
    
    def update_game(self):
        """Update game display"""
        try:
            if self.running:
                # Auto play if AI is solving
                if self.ai_solver.is_solving:
                    move = self.ai_solver.get_next_move()
                    if move:
                        self.game.move(move)
                    else:
                        # AI finished
                        self.ai_quick_btn.config(state='normal')
                        self.ai_stop_btn.config(state='disabled')
                
                self.draw_game()
                self.update_hud()
                
                # Check if level is solved
                if self.game.is_won:
                    self.show_win_message()
                
                # Schedule next update
                self.after(50, self.update_game)
        except tk.TclError:
            # Window was closed
            pass
    
    def show_win_message(self):
        """Show win message"""
        moves = len(self.game.state.move_history)
        solve_time_text = ""
        if getattr(self.ai_solver, "last_solve_time", None) is not None and self.ai_solver.last_solve_time > 0:
            solve_time_text = f"\nSolve time: {self.ai_solver.last_solve_time:.2f}s"
        result = messagebox.showinfo(
            "Level Solved!",
            f"🎉 Congratulations!\n\nTotal moves: {moves}{solve_time_text}"
        )
        self.game.reset()


class MainMenu(tk.Frame):
    """Main menu for Sokoban AI game"""
    
    def __init__(self, parent, levels_data: Dict[str, Tuple[str, str]], on_level_selected=None):
        """
        Initialize main menu frame
        
        Args:
            parent: Parent widget
            levels_data: Dict of level_id -> (level_string, level_name)
            on_level_selected: Callback when a level is selected
        """
        super().__init__(parent, bg='#2c3e50')
        
        self.levels_data = levels_data
        self.sprite_manager = SpriteManager("images", tile_size=60, root=parent)
        self.on_level_selected = on_level_selected
        
        # Create UI
        self.create_title()
        self.create_level_buttons()
        self.create_info_section()
    
    def create_title(self):
        """Create title section"""
        title_frame = tk.Frame(self, bg='#2c3e50')
        title_frame.pack(pady=20)
        
        # Title
        title_label = tk.Label(
            title_frame, 
            text="SOKOBAN AI",
            font=('Arial', 36, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack()
        
        # Subtitle
        subtitle_label = tk.Label(
            title_frame,
            text="Trí Tuệ Nhân Tạo - Đồ Án",
            font=('Arial', 14),
            fg='#bdc3c7',
            bg='#2c3e50'
        )
        subtitle_label.pack(pady=(5, 0))
    
    def create_level_buttons(self):
        """Create level selection buttons with scrollable canvas"""
        levels_frame = tk.Frame(self, bg='#2c3e50')
        levels_frame.pack(pady=20, expand=True, fill=tk.BOTH, padx=100)
        
        # Level title
        level_title = tk.Label(
            levels_frame,
            text="Chọn Màn Chơi:",
            font=('Arial', 18, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        level_title.pack(pady=(0, 15), anchor='w')
        
        # Create scrollable frame
        canvas_frame = tk.Frame(levels_frame, bg='#2c3e50')
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas with scrollbar
        canvas = tk.Canvas(
            canvas_frame,
            bg='#2c3e50',
            highlightthickness=0,
            height=300
        )
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        
        # Scrollable frame inside canvas
        scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Create level buttons in grid
        row_frame = None
        buttons_per_row = 10
        button_count = 0
        
        for level_id, (level_string, level_name) in self.levels_data.items():
            if button_count % buttons_per_row == 0:
                row_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
                row_frame.pack(pady=5, expand=True)
            
            # Create button with preview
            self.create_level_button(row_frame, level_id, level_name, level_string)
            button_count += 1
    
    def create_level_button(self, parent, level_id: str, level_name: str, level_string: str):
        """Create a level selection button"""
        button_frame = tk.Frame(parent, bg='#34495e', relief='raised', bd=1)
        button_frame.pack(side=tk.LEFT, padx=5)
        
        # Level name (shorter)
        name_label = tk.Label(
            button_frame,
            text=level_name[:15],
            font=('Arial', 9, 'bold'),
            fg='#ecf0f1',
            bg='#34495e'
        )
        name_label.pack(pady=(3, 0))
        
        # Mini preview canvas (smaller)
        preview_canvas = tk.Canvas(
            button_frame,
            width=80, height=60,
            bg='#2c3e50',
            highlightthickness=0
        )
        preview_canvas.pack(pady=3)
        
        # Draw mini preview
        self.draw_mini_preview(preview_canvas, level_string)
        
        # Play button (smaller)
        play_button = tk.Button(
            button_frame,
            text="Chơi",
            command=lambda: self.start_level(level_id, level_name, level_string),
            bg='#27ae60',
            fg='white',
            font=('Arial', 8, 'bold'),
            width=6,
            relief='flat',
            padx=3,
            pady=1
        )
        play_button.pack(pady=(0, 3))
        
        # Bind hover effects
        button_frame.bind("<Enter>", lambda e: button_frame.config(bg='#2c3e50'))
        button_frame.bind("<Leave>", lambda e: button_frame.config(bg='#34495e'))
    
    def draw_mini_preview(self, canvas: tk.Canvas, level_string: str):
        """Draw a mini preview of the level"""
        try:
            # Parse level string
            lines = level_string.strip().split('\n')
            height = len(lines)
            width = max(len(line) for line in lines) if lines else 0
            
            # Scale to fit canvas
            scale_x = 120 / width
            scale_y = 80 / height
            scale = min(scale_x, scale_y, 8)  # Max 8 pixels per tile
            
            for y, line in enumerate(lines):
                for x, char in enumerate(line):
                    color = self.get_tile_color(char)
                    if color:
                        canvas.create_rectangle(
                            x * scale, y * scale,
                            (x + 1) * scale, (y + 1) * scale,
                            fill=color,
                            outline='#2c3e50'
                        )
        except:
            # Fallback: just draw a simple rectangle
            canvas.create_rectangle(10, 10, 110, 70, fill='#34495e', outline='#2c3e50')
    
    def get_tile_color(self, char: str) -> str:
        """Get color for tile character"""
        color_map = {
            '#': '#34495e',  # Wall - dark
            'P': '#3498db',  # Player - blue
            'B': '#8b4513',  # Box - brown
            'T': '#e74c3c',  # Target - red
            '*': '#f39c12',  # Box on target - orange
            '@': '#9b59b6',  # Player on target - purple
        }
        return color_map.get(char, '#2c3e50')  # Default background
    
    def create_info_section(self):
        """Create info section"""
        info_frame = tk.Frame(self, bg='#2c3e50')
        info_frame.pack(pady=20, fill=tk.X)
        
        # Controls info
        controls_text = """
Điều Khiển: ↑↓←→ hoặc WASD để di chuyển
R: Reset level    SPACE: In trạng thái    Quay lại: Back button
        """
        
        controls_label = tk.Label(
            info_frame,
            text=controls_text,
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#2c3e50',
            justify=tk.LEFT
        )
        controls_label.pack()
    
    def start_level(self, level_id: str, level_name: str, level_string: str):
        """Start the selected level"""
        if self.on_level_selected:
            self.on_level_selected(level_id, level_name, level_string)


class UnifiedSokobanUI(tk.Tk):
    """Unified Sokoban UI with menu and game in one window"""
    
    def __init__(self, levels_data: Dict[str, Tuple[str, str]]):
        """
        Initialize unified UI
        
        Args:
            levels_data: Dict of level_id -> (level_string, level_name)
        """
        super().__init__()
        
        self.levels_data = levels_data
        self.current_game_display = None
        
        # Window setup
        self.title("Sokoban AI")
        self.geometry("1200x600")
        self.resizable(False, False)
        self.configure(bg='#2c3e50')
        
        # Create main container
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        # Create menu frame
        menu_frame = MainMenu(self.container, levels_data, on_level_selected=self.show_game)
        self.frames['menu'] = menu_frame
        menu_frame.grid(row=0, column=0, sticky="nsew")
        
        # Show menu
        self.show_menu()
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def show_menu(self):
        """Show menu frame"""
        frame = self.frames['menu']
        frame.tkraise()
    
    def show_game(self, level_id: str, level_name: str, level_string: str):
        """Show game frame"""
        print(f"Starting level: {level_name}")
        
        try:
            # Import here to avoid circular imports
            from game import Level, Game
            
            # Create level and game
            level = Level.from_string(level_name, level_string)
            game = Game(level)
            
            # Remove old game frame if exists
            if 'game' in self.frames:
                self.frames['game'].destroy()
            
            # Create new game display frame
            game_display = GameDisplay(
                self.container, 
                game, 
                tile_size=40,
                on_back_callback=self.on_game_back,
                level_id=level_id,
                levels_data=self.levels_data,
                on_next_level_callback=self.on_next_level
            )
            self.frames['game'] = game_display
            game_display.grid(row=0, column=0, sticky="nsew")
            
            # Show game
            game_display.tkraise()
            game_display.focus_set()
            
        except Exception as e:
            print(f"Error starting level: {e}")
            import traceback
            traceback.print_exc()
    
    def on_game_back(self):
        """Called when back button is pressed in game"""
        self.show_menu()
        self.focus_set()
    
    def on_next_level(self, current_level_id: str):
        """Called when next level button is pressed"""
        # Get list of level ids
        level_ids = list(self.levels_data.keys())
        try:
            current_index = level_ids.index(current_level_id)
            next_index = (current_index + 1) % len(level_ids)
            next_level_id = level_ids[next_index]
            
            level_string, level_name = self.levels_data[next_level_id]
            self.show_game(next_level_id, level_name, level_string)
        except (ValueError, KeyError):
            print("Error: Could not find next level")
