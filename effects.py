# effects.py
import pygame
import random
from dataclasses import dataclass
from utils import clamp

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple
    size: float

class Particles:
    def __init__(self):
        self.items = []

    def burst(self, x, y, base_color, n=22, spread=220, speed=(160, 520), size=(2, 6), life=(0.22, 0.55)):
        for _ in range(n):
            ang = random.uniform(-3.14159, 3.14159)
            spd = random.uniform(*speed)
            v = pygame.math.Vector2(1, 0).rotate_rad(ang) * spd
            self.items.append(Particle(
                x=x + random.uniform(-spread * 0.06, spread * 0.06),
                y=y + random.uniform(-spread * 0.06, spread * 0.06),
                vx=v.x, vy=v.y,
                life=random.uniform(*life),
                color=base_color,
                size=random.uniform(*size)
            ))

    def update(self, dt):
        g = 980
        for p in self.items:
            p.life -= dt
            p.vy += g * dt * 0.30
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.985
            p.vy *= 0.985
        self.items = [p for p in self.items if p.life > 0]

    def draw(self, surf, shake=(0, 0)):
        sx, sy = int(shake[0]), int(shake[1])
        for p in self.items:
            a = int(255 * clamp(p.life / 0.55, 0, 1))
            col = (*p.color, a)
            r = pygame.Rect(int(p.x + sx), int(p.y + sy), int(p.size), int(p.size))
            pygame.draw.rect(surf, col, r, border_radius=2)

class ScreenShake:
    def __init__(self):
        self.mag = 0.0

    def add(self, amt):
        self.mag = min(16.0, self.mag + amt)

    def update(self, decay):
        self.mag *= decay

    def offset(self):
        if self.mag < 0.25:
            return (0, 0)
        return (random.uniform(-self.mag, self.mag), random.uniform(-self.mag, self.mag))
