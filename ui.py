import pygame
import math
from settings import S
from utils import draw_text, glow_rect, add_color, mul_color
from pieces import COLORS, ROTATIONS


class UI:
    def __init__(self, screen):
        self.screen = screen

        # Fonts
        self.font = pygame.font.SysFont("consolas", 16)
        self.font_big = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_huge = pygame.font.SysFont("consolas", 46, bold=True)

        # Geometry
        self.board_px_w = S.COLS * S.TILE
        self.board_px_h = S.ROWS * S.TILE

        self.left_w = S.SIDE_W
        self.right_w = S.SIDE_W

        self.w = S.PAD + self.left_w + S.PAD + self.board_px_w + S.PAD + self.right_w + S.PAD
        self.h = S.PAD * 2 + self.board_px_h

        # Anchors
        self.left_x = S.PAD
        self.board_x = self.left_x + self.left_w + S.PAD
        self.right_x = self.board_x + self.board_px_w + S.PAD
        self.y0 = S.PAD

        self.panel_pad = 16
        self.card_pad = 14

        # cache background so we don’t redraw gradient per pixel every frame
        self._bg_cache = None
        self._bg_cache_size = None

    # --- Rect helpers ---
    def board_rect(self):
        return pygame.Rect(self.board_x, self.y0, self.board_px_w, self.board_px_h)

    def left_panel_rect(self):
        return pygame.Rect(self.left_x, self.y0, self.left_w, self.board_px_h)

    def right_panel_rect(self):
        return pygame.Rect(self.right_x, self.y0, self.right_w, self.board_px_h)

    def to_px(self, gx, gy):
        br = self.board_rect()
        return (br.x + gx * S.TILE, br.y + gy * S.TILE)

    # --- Background / cards ---
    def _make_bg(self):
        w, h = self.screen.get_size()
        surf = pygame.Surface((w, h))

        # vertical gradient
        for y in range(h):
            t = y / max(1, h - 1)
            r = int(S.BG_TOP[0] * (1 - t) + S.BG_BOT[0] * t)
            g = int(S.BG_TOP[1] * (1 - t) + S.BG_BOT[1] * t)
            b = int(S.BG_TOP[2] * (1 - t) + S.BG_BOT[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

        # soft vignette
        vig = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2
        maxd = math.hypot(cx, cy)
        for i in range(10):
            t = i / 9
            a = int(140 * t)
            rad = int(maxd * (0.75 + 0.32 * t))
            pygame.draw.circle(vig, (*S.VIGNETTE, a), (cx, cy), rad)
        surf.blit(vig, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        return surf

    def _draw_card(self, rect, shake=(0, 0), inner=True):
        sx, sy = int(shake[0]), int(shake[1])
        r = rect.move(sx, sy)

        # outer glass
        pygame.draw.rect(self.screen, S.CARD_BG, r, border_radius=16)
        pygame.draw.rect(self.screen, S.CARD_BORDER, r, width=2, border_radius=16)

        # inner inset
        if inner:
            inner_r = r.inflate(-10, -10)
            pygame.draw.rect(self.screen, S.CARD_BG2, inner_r, border_radius=14)
        return r

    # --- Board / tiles ---
    def draw_background(self, t, shake=(0, 0)):
        # cached gradient bg
        if self._bg_cache is None or self._bg_cache_size != self.screen.get_size():
            self._bg_cache = self._make_bg()
            self._bg_cache_size = self.screen.get_size()
        self.screen.blit(self._bg_cache, (0, 0))

        sx, sy = int(shake[0]), int(shake[1])

        # board frame like screenshot
        br = self.board_rect().move(sx, sy)

        # outer frame (soft glow-ish)
        pygame.draw.rect(self.screen, S.BOARD_FRAME_SOFT, br.inflate(10, 10), width=6, border_radius=18)
        pygame.draw.rect(self.screen, S.BOARD_FRAME, br.inflate(10, 10), width=2, border_radius=18)

        # board background
        pygame.draw.rect(self.screen, S.BOARD_BG, br, border_radius=14)

        # grid lines (thin)
        for y in range(S.ROWS + 1):
            yy = br.y + y * S.TILE
            pygame.draw.line(self.screen, S.GRID_LINE, (br.x, yy), (br.right, yy))
        for x in range(S.COLS + 1):
            xx = br.x + x * S.TILE
            pygame.draw.line(self.screen, S.GRID_LINE, (xx, br.y), (xx, br.bottom))

        # side panel outlines
        lp = self.left_panel_rect().move(sx, sy)
        rp = self.right_panel_rect().move(sx, sy)
        pygame.draw.rect(self.screen, S.CARD_BORDER, lp, width=2, border_radius=18)
        pygame.draw.rect(self.screen, S.CARD_BORDER, rp, width=2, border_radius=18)

    def draw_tile(self, x, y, color, alpha=255, ghost=False, shake=(0, 0), scale=1.0):
        sx, sy = int(shake[0]), int(shake[1])
        px, py = self.to_px(x, y)
        px += sx
        py += sy
        r = pygame.Rect(px, py, S.TILE, S.TILE)

        tile = pygame.Surface((S.TILE, S.TILE), pygame.SRCALPHA)

        if ghost:
            # thin outline ghost
            pygame.draw.rect(tile, (*color, int(alpha * 0.22)), tile.get_rect(), width=2, border_radius=6)
        else:
            # flatter “clean” block like screenshot
            base = (*color, alpha)
            hi = (*add_color(color, 35), alpha)
            lo = (*mul_color(color, 0.65), alpha)

            pygame.draw.rect(tile, lo, tile.get_rect(), border_radius=6)
            pygame.draw.rect(tile, base, tile.get_rect().inflate(-4, -4), border_radius=6)

            # top highlight strip
            strip = tile.get_rect().inflate(-6, -6)
            strip.h = max(4, strip.h // 4)
            pygame.draw.rect(tile, hi, strip, border_radius=5)

        # scaled draw (for line clear animation)
        if scale != 1.0:
            s = max(2, int(S.TILE * scale))
            scaled = pygame.transform.smoothscale(tile, (s, s))
            ox = (S.TILE - s) // 2
            oy = (S.TILE - s) // 2
            self.screen.blit(scaled, (r.x + ox, r.y + oy))
        else:
            self.screen.blit(tile, r.topleft)

        if (not ghost) and S.GLOW_PASSES > 0 and scale >= 0.6:
            glow_rect(self.screen, r, color, intensity=45, passes=1, radius=10)

    def draw_grid_cells(self, game, shake=(0, 0)):
        prog = 0.0
        if getattr(game, "clear_anim_t", 0.0) > 0:
            prog = 1.0 - (game.clear_anim_t / max(S.CLEAR_ANIM_TIME, 1e-6))

        clearing = set(getattr(game, "clearing_rows", []))

        for gy in range(S.HIDDEN_ROWS, S.ROWS + S.HIDDEN_ROWS):
            vy = gy - S.HIDDEN_ROWS
            for gx in range(S.COLS):
                col = game.grid[gy][gx]
                if not col:
                    continue
                if gy in clearing:
                    alpha = int(255 * (1.0 - prog))
                    scale = max(0.15, 1.0 - prog * 0.85)
                    self.draw_tile(gx, vy, col, alpha=alpha, shake=shake, scale=scale)
                else:
                    self.draw_tile(gx, vy, col, shake=shake)

    def draw_piece(self, piece, offset_y_hidden=True, alpha=255, ghost=False, shake=(0, 0)):
        for gx, gy in piece.blocks():
            vy = gy - S.HIDDEN_ROWS if offset_y_hidden else gy
            if 0 <= vy < S.ROWS:
                self.draw_tile(gx, vy, COLORS[piece.kind], alpha=alpha, ghost=ghost, shake=shake)

    def _draw_mini_piece(self, kind, box_rect, compact=False):
        """Mini preview centered in a card area."""
        x, y, w, h = box_rect
        pad = 10
        tile = int(S.TILE * (0.52 if not compact else 0.46))
        tile = max(8, tile)

        # 4x4 area centered
        area_w = tile * 4
        area_h = tile * 4
        ax = x + (w - area_w) // 2
        ay = y + (h - area_h) // 2

        if not kind:
            return

        blocks = ROTATIONS[kind][0]
        minx = min(bx for bx, by in blocks)
        miny = min(by for bx, by in blocks)
        blocks = [(bx - minx, by - miny) for bx, by in blocks]

        col = COLORS[kind]
        for bx, by in blocks:
            rr = pygame.Rect(ax + bx * tile, ay + by * tile, tile, tile)
            pygame.draw.rect(self.screen, col, rr, border_radius=6)
            # subtle highlight
            hi = pygame.Rect(rr.x + 2, rr.y + 2, rr.w - 4, max(3, (rr.h - 4) // 4))
            pygame.draw.rect(self.screen, add_color(col, 35), hi, border_radius=5)

    # --- Panels like screenshot ---
    def draw_panel(self, game, t, high_score=0, shake=(0, 0)):
        sx, sy = int(shake[0]), int(shake[1])

        lp = self.left_panel_rect().move(sx, sy)
        rp = self.right_panel_rect().move(sx, sy)

        # LEFT: Hold + Score/Lines/Level
        x = lp.x + self.panel_pad
        y = lp.y + self.panel_pad
        w = lp.w - self.panel_pad * 2

        hold_h = 132
        hold_card = pygame.Rect(x, y, w, hold_h)
        self._draw_card(hold_card)
        draw_text(self.screen, self.font_big, "HOLD", (hold_card.x + self.card_pad, hold_card.y + 10), S.TEXT)
        inner = hold_card.inflate(-24, -60)
        inner.y += 46
        inner.h -= 8
        pygame.draw.rect(self.screen, S.CARD_BG2, inner, border_radius=12)
        self._draw_mini_piece(game.hold_kind, inner)

        y += hold_h + 18

        stats_h = 220
        stats = pygame.Rect(x, y, w, stats_h)
        self._draw_card(stats)

        # Stats layout
        sx0 = stats.x + self.card_pad
        sy0 = stats.y + 18

        def stat_row(label, value, yy):
            draw_text(self.screen, self.font, label, (sx0, yy), S.MUTED)
            draw_text(self.screen, self.font_big, str(value), (stats.right - self.card_pad, yy - 4), S.TEXT, align="topright")

        draw_text(self.screen, self.font, "SCORE", (sx0, sy0), S.MUTED)
        draw_text(self.screen, self.font_big, str(game.score), (sx0, sy0 + 22), S.TEXT)
        draw_text(self.screen, self.font, "LINES", (sx0, sy0 + 74), S.MUTED)
        draw_text(self.screen, self.font_big, str(game.lines), (sx0, sy0 + 96), S.TEXT)
        draw_text(self.screen, self.font, "LEVEL", (sx0, sy0 + 148), S.MUTED)
        draw_text(self.screen, self.font_big, str(game.level), (sx0, sy0 + 170), S.TEXT)

        # RIGHT: Next stack + Controls
        x = rp.x + self.panel_pad
        y = rp.y + self.panel_pad
        w = rp.w - self.panel_pad * 2

        next_h = 390
        next_card = pygame.Rect(x, y, w, next_h)
        self._draw_card(next_card)
        draw_text(self.screen, self.font_big, "NEXT", (next_card.x + self.card_pad, next_card.y + 10), S.TEXT)

        # Next list slots
        slot_w = w
        slot_h = 78
        base_y = next_card.y + 50
        for i in range(4):
            slot = pygame.Rect(next_card.x + 12, base_y + i * (slot_h + 12), slot_w - 24, slot_h)
            pygame.draw.rect(self.screen, S.CARD_BG2, slot, border_radius=14)

            kind = game.queue[i] if i < len(game.queue) else None
            self._draw_mini_piece(kind, slot, compact=True)

        # Controls card (bottom)
        controls_h = 176
        controls = pygame.Rect(x, rp.bottom - self.panel_pad - controls_h, w, controls_h)
        self._draw_card(controls)

        cx = controls.x + self.card_pad
        cy = controls.y + 16
        draw_text(self.screen, self.font, "←/→  Move", (cx, cy), S.MUTED)
        draw_text(self.screen, self.font, "↓    Soft Drop", (cx, cy + 26), S.MUTED)
        draw_text(self.screen, self.font, "Z/X  Rotate", (cx, cy + 52), S.MUTED)
        draw_text(self.screen, self.font, "SPACE  Hard Drop", (cx, cy + 78), S.TEXT)
        draw_text(self.screen, self.font, "C    Hold", (cx, cy + 104), S.MUTED)
        draw_text(self.screen, self.font, "P    Pause", (cx, cy + 130), S.MUTED)

    # overlays (keep yours, just visually consistent)
    def draw_game_over(self, game, shake=(0, 0)):
        if not game.dead:
            return
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        br = self.board_rect()
        cx = br.centerx
        cy = br.centery
        draw_text(self.screen, self.font_huge, "GAME OVER", (cx, cy - 26), (255, 170, 175), align="center")
        draw_text(self.screen, self.font, "R: Restart    ENTER: Menu", (cx, cy + 34), S.TEXT, align="center")

    def draw_pause_overlay(self, shake=(0, 0)):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        br = self.board_rect()
        cx = br.centerx
        cy = br.centery
        draw_text(self.screen, self.font_huge, "PAUSED", (cx, cy - 18), S.TEXT, align="center")
        draw_text(self.screen, self.font, "Press P to resume", (cx, cy + 38), S.MUTED, align="center")

    def draw_title_screen(self, t, high_score=0, shake=(0, 0)):
        br = self.board_rect()
        cx, cy = br.center
        pulse = 0.5 + 0.5 * math.sin(t * 2.6)

        draw_text(self.screen, self.font_huge, "TETRIS", (cx, cy - 150), S.TEXT, align="center")

        card = pygame.Rect(0, 0, 460, 190)
        card.center = (cx, cy)
        self._draw_card(card)

        draw_text(self.screen, self.font, "High Score", (card.x + 18, card.y + 18), S.MUTED)
        draw_text(self.screen, self.font_big, str(high_score), (card.right - 18, card.y + 14), S.TEXT, align="topright")

        draw_text(self.screen, self.font_big, "Press ENTER to Play", (cx, card.y + 84), S.TEXT, align="center")
        draw_text(self.screen, self.font, "F1: Help    ESC: Quit", (cx, card.y + 126), S.MUTED, align="center")
        if pulse > 0.35:
            draw_text(self.screen, self.font, "Tip: SPACE to drop fast, C to hold", (cx, card.y + 156), S.MUTED, align="center")

    def draw_help_screen(self, t, shake=(0, 0)):
        br = self.board_rect()
        cx, cy = br.center

        draw_text(self.screen, self.font_huge, "HELP", (cx, cy - 170), S.TEXT, align="center")
        card = pygame.Rect(0, 0, 520, 320)
        card.center = (cx, cy + 20)
        self._draw_card(card)

        x = card.x + 18
        y = card.y + 18
        rows = [
            ("Move", "LEFT / RIGHT"),
            ("Soft drop", "DOWN"),
            ("Rotate", "Z (CCW), X or UP (CW)"),
            ("Hard drop", "SPACE"),
            ("Hold", "C"),
            ("Pause", "P"),
            ("Reset run", "R"),
            ("Back", "ESC"),
        ]
        for a, b in rows:
            draw_text(self.screen, self.font, a, (x, y), S.MUTED)
            draw_text(self.screen, self.font, b, (card.right - 18, y), S.TEXT, align="topright")
            y += 28

        draw_text(self.screen, self.font, "ENTER: Play   ESC/BACKSPACE: Menu", (cx, card.bottom - 36), S.MUTED, align="center")
