# settings.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    # Board
    COLS: int = 10
    ROWS: int = 20
    HIDDEN_ROWS: int = 2
    TILE: int = 30

    # Window / Layout
    PAD: int = 28
    SIDE_W: int = 240
    FPS: int = 120

    # Background
    BG_TOP: tuple = (14, 54, 66)
    BG_BOT: tuple = (18, 74, 88)
    VIGNETTE: tuple = (0, 0, 0)

    # Board styling
    BOARD_BG: tuple = (10, 18, 22)
    BOARD_FRAME: tuple = (180, 200, 210)
    BOARD_FRAME_SOFT: tuple = (120, 140, 150)
    GRID_LINE: tuple = (24, 36, 42)

    # Cards (glass panels)
    CARD_BG: tuple = (26, 54, 62)
    CARD_BG2: tuple = (20, 44, 52)
    CARD_BORDER: tuple = (80, 110, 120)
    TEXT: tuple = (235, 245, 248)
    MUTED: tuple = (170, 195, 202)

    # Piece colors
    COLORS: dict = None

    # Timing / controls (seconds)
    GRAVITY_START: float = 0.85
    GRAVITY_MIN: float = 0.06
    GRAVITY_DECAY: float = 0.93
    LOCK_DELAY: float = 0.35

    # Movement: DAS/ARR (seconds)
    DAS: float = 0.13
    ARR: float = 0.025

    # Soft drop multiplier (smaller = faster)
    SOFT_DROP_MULT: float = 0.08

    # Visual effects
    SHAKE_DECAY: float = 0.85
    GLOW_PASSES: int = 1
    GLOW_SCALE: int = 3
    PARTICLES_PER_LINE: int = 28

    # Line clear animation
    CLEAR_ANIM_TIME: float = 0.18

S = Settings(COLORS={
    "I": (0, 220, 235),
    "O": (245, 230, 0),
    "T": (175, 90, 255),
    "S": (0, 220, 80),
    "Z": (255, 70, 80),
    "J": (60, 90, 255),
    "L": (255, 160, 0),
})
