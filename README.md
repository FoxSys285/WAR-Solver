# Sokoban AI

Dự án xây dựng một AI giải quyết trò chơi Sokoban sử dụng các thuật toán tìm kiếm và trí tuệ nhân tạo.

## Tính Năng

- ✅ **Game Logic Hoàn Chỉnh**: Triển khai đầy đủ logic game Sokoban
- ✅ **GUI Tkinter**: Giao diện người dùng với hình ảnh tùy chỉnh
- ✅ **Main Menu**: Menu chính với chọn level và preview
- ✅ **Sprite System**: Hệ thống sprite với load hình ảnh từ file
- ✅ **Controls**: Điều khiển bằng keyboard (WASD/Arrow keys)
- 🔄 **AI Solvers**: Thuật toán tìm kiếm (đang phát triển)

## Cấu trúc Dự Án

```
NewSokoban/
├── src/                    # Source code
│   ├── game/              # Game logic
│   ├── ai/                # AI solvers
│   ├── ui/                # UI (Tkinter)
│   └── utils/             # Utilities
├── data/                  # Data files
│   └── levels/            # Level files
├── images/                # Game sprites
├── tests/                 # Unit tests
├── docs/                  # Documentation
├── config/                # Configuration files
├── logs/                  # Log files
├── results/               # Results and outputs
├── requirements.txt       # Dependencies
├── README.md             # This file
├── main.py               # Entry point (Main Menu)
└── run_gui.py            # Level selector
```

## Cài Đặt & Chạy Game

### Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

Thư viện cần thiết:
- **tkinter** - Built-in (GUI framework)
- **Pillow** - Xử lý hình ảnh

### Chạy Game

#### Main Menu (Khuyến nghị)

```bash
python main.py
```

Mở menu chính với:
- Chọn level từ 3 màn chơi có sẵn
- Preview mini của mỗi level
- Giao diện đẹp với hình ảnh tùy chỉnh

#### Level Selector (Cũ)

```bash
python run_gui.py
```

### Điều Khiển Game

- **Di chuyển**: ↑↓←→ hoặc WASD
- **Reset**: R
- **In trạng thái**: SPACE
- **Thoát**: ESC hoặc đóng cửa sổ

### Hình Ảnh Game

Game sử dụng các file hình ảnh trong thư mục `images/`:
- `player.png` - Nhân vật người chơi
- `box.png` - Hộp cần đẩy
- `box_in_target.png` - Hộp trên mục tiêu
- `wall.png` - Tường
- `floor.png` - Sàn
- `target.png` - Mục tiêu
- `space.png` - Không gian trống
- `bg.png` - Nền
```

#### 3. Chế độ Console (Text-based)

Sửa `main.py` để gọi `main_cli()` thay vì `main_gui()`

## Điều Khiển

- **Arrow Keys / WASD** - Di chuyển
- **R** - Reset level
- **SPACE** - In trạng thái board
- **ESC / Đóng cửa sổ** - Thoát

## Game Logic

### Trạng thái Game (GameState)
- Quản lý board, vị trí player, hộp, mục tiêu
- Xử lý logic di chuyển và đẩy hộp

### Level
- Load từ string hoặc file
- Hỗ trợ định dạng: `P` (player), `B` (box), `T` (target), `#` (wall)

### Game Engine
- Quản lý vòng lặp game
- Xử lý input và update state
- Kiểm tra điều kiện thắng

## Giao Diện (Tkinter)

### SpriteManager
- Tạo sprite bằng PIL
- Tự động scale theo tile_size
- Không cần file ảnh ngoài

### GameDisplay
- Canvas-based rendering
- HUD hiển thị info game
- Support keyboard & button controls

## Cấu Trúc Thư Mục

### src/game/
- `state.py` - Game state management
- `level.py` - Level definition & loading
- `engine.py` - Game engine & logic

### src/ui/
- `tkinter_display.py` - Main Tkinter GUI
- `display.py` - Pygame GUI (optional)

### src/ai/
- Chứa AI algorithms (chưa implement)

## Chạy Tests

```bash
python tests/test_game.py
```

## Docs

- [TKINTER_GUIDE.md](docs/TKINTER_GUIDE.md) - Chi tiết Tkinter GUI
- [GUI_GUIDE.md](docs/GUI_GUIDE.md) - Hướng dẫn Pygame (tuỳ chọn)

## Tác Giả

[Tên tác giả]

## Giấy Phép

[Loại giấy phép]
