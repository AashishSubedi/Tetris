# utils.py
import pygame

def clamp(x, a, b):
    return a if x < a else b if x > b else x

def add_color(c, amt):
    return (min(255, c[0] + amt), min(255, c[1] + amt), min(255, c[2] + amt))

def mul_color(c, m):
    return (int(c[0] * m), int(c[1] * m), int(c[2] * m))

def draw_text(surf, font, text, pos, color, align="topleft"):
    img = font.render(text, True, color)
    r = img.get_rect()
    setattr(r, align, pos)
    surf.blit(img, r)
    return r

def glow_rect(surface, rect, color, intensity=120, passes=2, radius=10):
    for i in range(passes):
        t = (i + 1) / passes
        alpha = int(intensity * (1.0 - t) * 0.9)
        pad = int(radius * t * 1.2)
        glow = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, alpha), glow.get_rect(), border_radius=int(radius * t + 2))
        surface.blit(glow, (rect.x - pad, rect.y - pad), special_flags=pygame.BLEND_PREMULTIPLIED)
