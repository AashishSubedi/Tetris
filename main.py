# main.py
import sys
import time
import pygame

from settings import S
from tetris import Game
from ui import UI
from effects import Particles, ScreenShake
from platform_store import load_high_score, save_high_score, IS_WEB


class EffectsBundle:
    def __init__(self):
        self.particles = Particles()
        self.shake = ScreenShake()


def _init_display():
    pygame.display.set_caption("Tetris")

    # temp screen to compute final UI size
    temp = pygame.display.set_mode((1, 1))
    ui = UI(temp)

    # final size
    screen = pygame.display.set_mode((ui.w, ui.h))
    ui = UI(screen)
    return screen, ui


def _run_frame(clock, screen, ui, effects, state_box):
    """One frame of the game. Returns (running: bool)."""
    state = state_box["state"]
    game = state_box["game"]
    high_score = state_box["high_score"]

    dt = clock.tick(S.FPS) / 1000.0
    t = time.time() - state_box["t0"]

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            # On web, QUIT events are unusual; allow it anyway.
            return False

        if e.type == pygame.KEYDOWN:
            # Global keys
            if e.key == pygame.K_F1:
                state = "help" if state != "help" else "menu"

            if state == "menu":
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    game = Game(effects=effects)
                    state = "play"
                elif e.key in (pygame.K_h, pygame.K_SLASH, pygame.K_QUESTION):
                    state = "help"
                elif e.key == pygame.K_ESCAPE:
                    # On web, ESC shouldn't "close" the tab, but we can go idle.
                    if not IS_WEB:
                        return False

            elif state == "help":
                if e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    state = "menu"
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    game = Game(effects=effects)
                    state = "play"

            elif state == "play":
                # If dead: allow quick actions
                if game.dead:
                    if e.key == pygame.K_r:
                        game.reset()
                    elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE):
                        # save and return to menu
                        high_score = max(high_score, game.score)
                        save_high_score(high_score)
                        game = None
                        state = "menu"
                    continue

                # Pause toggle
                if e.key == pygame.K_p:
                    game.toggle_pause()
                    continue

                if e.key == pygame.K_ESCAPE:
                    # back to menu (save)
                    high_score = max(high_score, game.score)
                    save_high_score(high_score)
                    game = None
                    state = "menu"
                    continue

                if game.paused:
                    continue

                # Controls
                if e.key == pygame.K_r:
                    game.reset()

                if e.key == pygame.K_LEFT:
                    game.left_held = True
                    game.right_held = False
                    game.move(-1)
                    game.last_dir = -1
                    game.das_t = 0.0
                    game.arr_t = 0.0

                if e.key == pygame.K_RIGHT:
                    game.right_held = True
                    game.left_held = False
                    game.move(+1)
                    game.last_dir = +1
                    game.das_t = 0.0
                    game.arr_t = 0.0

                if e.key == pygame.K_DOWN:
                    game.soft_drop = True

                if e.key == pygame.K_z:
                    game.rotate(-1)
                if e.key == pygame.K_x or e.key == pygame.K_UP:
                    game.rotate(+1)

                if e.key == pygame.K_c:
                    game.hold()

                if e.key == pygame.K_SPACE:
                    game.hard_drop()

        if e.type == pygame.KEYUP and state == "play" and game is not None:
            if e.key == pygame.K_LEFT:
                game.left_held = False
            if e.key == pygame.K_RIGHT:
                game.right_held = False
            if e.key == pygame.K_DOWN:
                game.soft_drop = False

    # Update / render per state
    shake = effects.shake.offset()

    if state == "menu":
        ui.draw_background(t, shake=shake)
        ui.draw_title_screen(t, high_score=high_score, shake=shake)
        effects.particles.update(dt)
        effects.shake.update(S.SHAKE_DECAY)

    elif state == "help":
        ui.draw_background(t, shake=shake)
        ui.draw_help_screen(t, shake=shake)
        effects.particles.update(dt)
        effects.shake.update(S.SHAKE_DECAY)

    elif state == "play":
        keys = pygame.key.get_pressed()
        game.soft_drop = bool(keys[pygame.K_DOWN]) if not game.dead else False

        game.update(dt)
        effects.particles.update(dt)
        effects.shake.update(S.SHAKE_DECAY)

        # Line-clear particles on cleared rows (visual only)
        rows = getattr(game, "just_cleared_rows", [])
        if rows:
            br = ui.board_rect()
            for ry in rows:
                vy = ry - S.HIDDEN_ROWS
                if 0 <= vy < S.ROWS:
                    y_px = br.y + vy * S.TILE + S.TILE // 2
                    for k in range(6):
                        x_px = br.x + int((k + 0.5) * br.w / 6)
                        effects.particles.burst(
                            x_px, y_px,
                            (235, 235, 245),
                            n=18, spread=220, speed=(160, 520)
                        )
            game.just_cleared_rows = []

        # Render
        ui.draw_background(t, shake=shake)
        ui.draw_grid_cells(game, shake=shake)

        if not game.dead:
            gy = game.ghost_y()
            ghost = type(game.cur)(game.cur.kind, game.cur.x, gy)
            ghost.rot = game.cur.rot
            ui.draw_piece(ghost, alpha=180, ghost=True, shake=shake)
            ui.draw_piece(game.cur, shake=shake)

        ui.draw_panel(game, t, high_score=high_score, shake=shake)
        effects.particles.draw(screen, shake=shake)

        if game.paused:
            ui.draw_pause_overlay(shake=shake)

        ui.draw_game_over(game, shake=shake)

        if game.dead and game.score > high_score:
            high_score = game.score
            save_high_score(high_score)

    pygame.display.flip()

    state_box["state"] = state
    state_box["game"] = game
    state_box["high_score"] = high_score
    return True


def main_desktop():
    pygame.init()
    clock = pygame.time.Clock()
    screen, ui = _init_display()

    effects = EffectsBundle()
    high_score = load_high_score()

    state_box = {
        "state": "menu",
        "game": None,
        "high_score": high_score,
        "t0": time.time(),
    }

    running = True
    while running:
        running = _run_frame(clock, screen, ui, effects, state_box)

    # Save on exit
    if state_box["game"] is not None:
        hs = max(state_box["high_score"], state_box["game"].score)
        save_high_score(hs)

    pygame.quit()


async def main_web():
    """
    Web (pygbag/emscripten) needs yielding so the browser stays responsive.
    """
    import asyncio

    pygame.init()
    clock = pygame.time.Clock()
    screen, ui = _init_display()

    effects = EffectsBundle()
    high_score = load_high_score()

    state_box = {
        "state": "menu",
        "game": None,
        "high_score": high_score,
        "t0": time.time(),
    }

    running = True
    while running:
        running = _run_frame(clock, screen, ui, effects, state_box)
        # IMPORTANT: yield to browser event loop
        await asyncio.sleep(0)

    if state_box["game"] is not None:
        hs = max(state_box["high_score"], state_box["game"].score)
        save_high_score(hs)

    pygame.quit()


if __name__ == "__main__":
    if IS_WEB:
        # pygbag runs async main
        import asyncio
        asyncio.run(main_web())
    else:
        main_desktop()
