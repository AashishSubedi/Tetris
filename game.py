"""
Main game logic and rendering
"""
import pygame
import random
from constants import *
from tetromino import Tetromino
from board import Board
from particle import ParticleSystem

class Game:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        
        # Game state
        self.board = Board()
        self.current_piece = None
        self.next_piece = Tetromino()
        self.held_piece = None
        self.can_hold = True
        
        self.score = 0
        self.lines = 0
        self.level = 1
        
        self.fall_speed = INITIAL_FALL_SPEED
        self.fall_timer = 0
        self.fast_falling = False
        
        self.game_over = False
        self.paused = False
        
        # Visual effects
        self.particles = ParticleSystem()
        self.shake_amount = 0
        self.combo = 0
        
        # UI positions
        self.board_x = width // 2 - (GRID_WIDTH * BLOCK_SIZE) // 2
        self.board_y = 50
        
        # Font
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_small = pygame.font.Font(None, 24)
        
        # Start game
        self.spawn_piece()
    
    def spawn_piece(self):
        """Spawn a new piece"""
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()
        self.can_hold = True
        
        if not self.board.is_valid_position(self.current_piece):
            self.game_over = True
    
    def hold_piece(self):
        """Hold current piece"""
        if not self.can_hold:
            return
        
        if self.held_piece is None:
            self.held_piece = Tetromino(self.current_piece.shape_type)
            self.spawn_piece()
        else:
            self.current_piece, self.held_piece = (
                Tetromino(self.held_piece.shape_type),
                Tetromino(self.current_piece.shape_type)
            )
        
        self.can_hold = False
    
    def move(self, dx, dy):
        """Move current piece"""
        if self.current_piece:
            self.current_piece.x += dx
            self.current_piece.y += dy
            
            if not self.board.is_valid_position(self.current_piece):
                self.current_piece.x -= dx
                self.current_piece.y -= dy
                return False
            return True
        return False
    
    def rotate_piece(self):
        """Rotate current piece with wall kicks"""
        if not self.current_piece:
            return
        
        old_rotation = self.current_piece.rotation
        self.current_piece.rotate()
        
        # Try wall kicks
        if not self.board.is_valid_position(self.current_piece):
            for dx in [0, 1, -1, 2, -2]:
                self.current_piece.x += dx
                if self.board.is_valid_position(self.current_piece):
                    return
                self.current_piece.x -= dx
            
            # Revert rotation
            for _ in range(3):
                self.current_piece.rotate()
    
    def hard_drop(self):
        """Drop piece instantly"""
        if not self.current_piece:
            return
        
        drop_distance = 0
        while self.move(0, 1):
            drop_distance += 1
        
        self.score += drop_distance * 2
        self.lock_piece()
    
    def lock_piece(self):
        """Lock piece to board"""
        if not self.current_piece:
            return
        
        self.board.place_tetromino(self.current_piece)
        
        # Emit particles
        for x, y in self.current_piece.get_cells():
            px = self.board_x + x * BLOCK_SIZE + BLOCK_SIZE // 2
            py = self.board_y + y * BLOCK_SIZE + BLOCK_SIZE // 2
            self.particles.emit(px, py, self.current_piece.color, count=5)
        
        # Clear lines
        lines_cleared = self.board.clear_lines()
        if lines_cleared > 0:
            self.lines += lines_cleared
            self.combo += 1
            
            # Score calculation
            points = [0, 100, 300, 500, 800]
            self.score += points[min(lines_cleared, 4)] * self.level
            self.score += self.combo * 50
            
            # Screen shake
            self.shake_amount = min(lines_cleared * 3, 15)
            
            # Line clear particles
            for row in self.board.flash_rows:
                py = self.board_y + row * BLOCK_SIZE + BLOCK_SIZE // 2
                self.particles.emit_line_clear(
                    self.board_x, py, 
                    GRID_WIDTH * BLOCK_SIZE,
                    (255, 255, 255)
                )
            
            # Level up
            if self.lines >= self.level * 10:
                self.level += 1
                self.fall_speed = max(0.1, INITIAL_FALL_SPEED - (self.level - 1) * LEVEL_SPEED_DECREASE)
        else:
            self.combo = 0
        
        # Check game over
        if self.board.is_game_over():
            self.game_over = True
        else:
            self.spawn_piece()
        
        self.fall_timer = 0
    
    def update(self, dt):
        """Update game state"""
        if self.game_over or self.paused:
            return
        
        # Update flash effect
        if self.board.flash_timer > 0:
            self.board.flash_timer -= dt
        
        # Update particles
        self.particles.update(dt)
        
        # Update screen shake
        if self.shake_amount > 0:
            self.shake_amount = max(0, self.shake_amount - 30 * dt)
        
        # Fall timer
        speed = FAST_FALL_SPEED if self.fast_falling else self.fall_speed
        self.fall_timer += dt
        
        if self.fall_timer >= speed:
            self.fall_timer = 0
            
            if not self.move(0, 1):
                self.lock_piece()
    
    def handle_event(self, event):
        """Handle input events"""
        if event.type == pygame.KEYDOWN:
            if self.game_over:
                if event.key == pygame.K_r:
                    self.__init__(self.screen, self.width, self.height)
                return
            
            if event.key == pygame.K_p:
                self.paused = not self.paused
            elif event.key == pygame.K_LEFT:
                self.move(-1, 0)
            elif event.key == pygame.K_RIGHT:
                self.move(1, 0)
            elif event.key == pygame.K_DOWN:
                self.fast_falling = True
            elif event.key == pygame.K_UP or event.key == pygame.K_x:
                self.rotate_piece()
            elif event.key == pygame.K_SPACE:
                self.hard_drop()
            elif event.key == pygame.K_c:
                self.hold_piece()
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                self.fast_falling = False
    
    def draw_block(self, x, y, color, alpha=255, glow=False):
        """Draw a single block with effects"""
        px = self.board_x + x * BLOCK_SIZE
        py = self.board_y + y * BLOCK_SIZE
        
        # Apply shake
        if self.shake_amount > 0:
            px += random.randint(-int(self.shake_amount), int(self.shake_amount))
            py += random.randint(-int(self.shake_amount), int(self.shake_amount))
        
        # Glow effect
        if glow:
            glow_surf = pygame.Surface((BLOCK_SIZE + 10, BLOCK_SIZE + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*color, 50), (0, 0, BLOCK_SIZE + 10, BLOCK_SIZE + 10), border_radius=5)
            self.screen.blit(glow_surf, (px - 5, py - 5))
        
        # Main block
        block_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(block_surf, (*color, alpha), (0, 0, BLOCK_SIZE, BLOCK_SIZE), border_radius=3)
        
        # Inner highlight
        highlight = tuple(min(c + 50, 255) for c in color)
        pygame.draw.rect(block_surf, (*highlight, alpha // 2), (2, 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4), width=2, border_radius=2)
        
        self.screen.blit(block_surf, (px, py))
    
    def draw(self):
        """Draw everything"""
        # Background
        self.screen.fill(COLORS['bg'])
        
        # Draw grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                px = self.board_x + x * BLOCK_SIZE
                py = self.board_y + y * BLOCK_SIZE
                pygame.draw.rect(self.screen, COLORS['grid'], 
                               (px, py, BLOCK_SIZE, BLOCK_SIZE), width=1)
        
        # Draw placed blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.board.grid[y][x] is not None:
                    # Flash effect
                    if y in self.board.flash_rows and self.board.flash_timer > 0:
                        flash = int((self.board.flash_timer / 0.3) * 255)
                        self.draw_block(x, y, (255, 255, 255), alpha=flash, glow=True)
                    else:
                        self.draw_block(x, y, self.board.grid[y][x], glow=True)
        
        # Draw ghost piece
        if self.current_piece and not self.game_over:
            ghost = self.board.get_ghost_position(self.current_piece)
            for x, y in ghost.get_cells():
                if y >= 0:
                    self.draw_block(x, y, self.current_piece.color, alpha=50)
        
        # Draw current piece
        if self.current_piece:
            for x, y in self.current_piece.get_cells():
                if y >= 0:
                    self.draw_block(x, y, self.current_piece.color, glow=True)
        
        # Draw particles
        self.particles.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
        
        # Game over screen
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            text = self.font_large.render("GAME OVER", True, (255, 50, 50))
            self.screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2 - 50))
            
            text2 = self.font_medium.render("Press R to Restart", True, (255, 255, 255))
            self.screen.blit(text2, (self.width // 2 - text2.get_width() // 2, self.height // 2 + 20))
        
        # Pause screen
        if self.paused:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            text = self.font_large.render("PAUSED", True, (255, 255, 255))
            self.screen.blit(text, (self.width // 2 - text.get_width() // 2, self.height // 2))
    
    def draw_ui(self):
        """Draw UI elements"""
        # Score
        score_text = self.font_medium.render(f"Score: {self.score}", True, COLORS['text'])
        self.screen.blit(score_text, (20, 20))
        
        lines_text = self.font_small.render(f"Lines: {self.lines}", True, COLORS['text'])
        self.screen.blit(lines_text, (20, 60))
        
        level_text = self.font_small.render(f"Level: {self.level}", True, COLORS['text'])
        self.screen.blit(level_text, (20, 90))
        
        if self.combo > 1:
            combo_text = self.font_medium.render(f"Combo x{self.combo}!", True, (255, 255, 0))
            self.screen.blit(combo_text, (20, 130))
        
        # Next piece
        next_x = self.board_x + GRID_WIDTH * BLOCK_SIZE + 40
        next_y = 100
        
        next_label = self.font_medium.render("Next", True, COLORS['text'])
        self.screen.blit(next_label, (next_x, next_y - 40))
        
        for row_idx, row in enumerate(self.next_piece.shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    px = next_x + col_idx * BLOCK_SIZE
                    py = next_y + row_idx * BLOCK_SIZE
                    self.draw_block(col_idx, row_idx + (next_y - self.board_y) // BLOCK_SIZE, 
                                  self.next_piece.color, glow=True)
        
        # Held piece
        if self.held_piece:
            hold_x = self.board_x - 150
            hold_y = 100
            
            hold_label = self.font_medium.render("Hold", True, COLORS['text'])
            self.screen.blit(hold_label, (hold_x, hold_y - 40))
            
            for row_idx, row in enumerate(self.held_piece.shape):
                for col_idx, cell in enumerate(row):
                    if cell:
                        px = hold_x + col_idx * BLOCK_SIZE
                        py = hold_y + row_idx * BLOCK_SIZE
                        pygame.draw.rect(self.screen, self.held_piece.color,
                                       (px, py, BLOCK_SIZE, BLOCK_SIZE), border_radius=3)
        
        # Controls
        controls_x = self.board_x - 150
        controls_y = 300
        
        controls = [
            "Controls:",
            "← → Move",
            "↓ Soft Drop",
            "↑/X Rotate",
            "SPACE Hard Drop",
            "C Hold",
            "P Pause"
        ]
        
        for i, text in enumerate(controls):
            control_text = self.font_small.render(text, True, COLORS['text'])
            self.screen.blit(control_text, (controls_x, controls_y + i * 25))