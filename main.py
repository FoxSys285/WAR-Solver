"""
Main entry point for Sokoban AI project
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from game import Level, Game
from ui import UnifiedSokobanUI


def load_maps_from_folder(levels_dir: str = "data/levels") -> dict:
    """
    Load Sokoban levels from a folder of .xsb files.
    
    Args:
        levels_dir: Path to a folder containing .xsb level files
        
    Returns:
        Dictionary of levels_data in format {level_id: (level_string, level_name)}
    """
    levels_path = Path(__file__).parent / levels_dir
    if not levels_path.exists() or not levels_path.is_dir():
        print(f"Warning: {levels_dir} not found. Using demo levels.")
        return {}

    levels_data = {}
    for level_file in sorted(levels_path.glob("*.xsb")):
        try:
            with open(level_file, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f.readlines()]

            if not lines:
                continue

            name = level_file.stem
            if lines[0].startswith(';'):
                comment = lines[0][1:].strip()
                if comment:
                    name = comment
                level_string = '\n'.join(lines[1:])
            else:
                level_string = '\n'.join(lines)

            levels_data[level_file.stem] = (level_string, name)
        except Exception as e:
            print(f"Error reading {level_file.name}: {e}")

    print(f"✓ Loaded {len(levels_data)} levels from {levels_dir}")
    return levels_data


def main_gui():
    """GUI mode - Tkinter-based gameplay with unified menu and game"""
    print("Starting Sokoban AI with Tkinter GUI...")
    
    # Load available levels from the xsb folder
    levels_data = load_maps_from_folder("data/levels")
    
    if not levels_data:
        print("No levels loaded!")
        return
    
    # Create unified UI
    app = UnifiedSokobanUI(levels_data)
    
    print("Unified UI opened!")
    print(f"Total levels available: {len(levels_data)}")
    print("Select a level to start playing.")
    
    # Start the GUI event loop
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("\nGame interrupted!")
    finally:
        print("Game closed.")


if __name__ == "__main__":
    main_gui()
