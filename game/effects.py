"""粒子系统、星空背景和屏幕特效"""

import math
import random
import pygame
from .config import *

class Particle:
    def __init__(self, x, y, vx, vy, life, color, size=3, shrink=0.97, gravity=0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.shrink = shrink
        self.gravity = gravity

    @property
    def alive(self):
        return self.life > 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= 1
        self.size *= self.shrink
        return self.alive

    def draw(self, surface):
        if not self.alive:
            return
        alpha = max(0, self.life / self.max_life)
        size = max(0.5, self.size)
        try:
            c = self.color
            color = (min(255, int(c[0]*alpha + 30*(1-alpha))),
                     min(255, int(c[1]*alpha + 30*(1-alpha))),
                     min(255, int(c[2]*alpha + 30*(1-alpha))))
            pygame.draw.circle(surface, color, (int(self.x), int(self.y)), int(size))
        except (ValueError, IndexError):
            pass


class ScorePopup:
    def __init__(self, x, y, text, color=(255, 255, 0)):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 45
        self.max_life = 45
        self.vy = -2

    @property
    def alive(self):
        return self.life > 0

    def update(self):
        self.y += self.vy
        self.vy *= 0.96
        self.life -= 1
        return self.alive

    def draw(self, surface):
        if not self.alive:
            return
        alpha = self.life / self.max_life
        size = 18
        font = pygame.font.Font(None, size)
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(int(alpha * 255))
        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surf, rect)


class ParticleSystem:
    def __init__(self):
        self.particles = []
        self.popups = []

    def explode(self, x, y, count, colors, speed=5, size=5):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(speed * 0.3, speed)
            life = random.randint(20, 50)
            c = random.choice(colors)
            self.particles.append(Particle(
                x + random.uniform(-4, 4),
                y + random.uniform(-4, 4),
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                life, c,
                random.uniform(size * 0.5, size),
                random.uniform(0.95, 0.99)
            ))

    def debris(self, x, y):
        for _ in range(10):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(1, 4)
            c = random.choice([(120,120,120),(170,170,170),(200,200,200),(255,100,60)])
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                random.randint(30, 60), c,
                random.uniform(2, 5), 0.97, 0.05
            ))

    def trail(self, x, y, color=None):
        if color is None:
            color = (255, 136, 0)
        self.particles.append(Particle(
            x + random.uniform(-2, 2),
            y + random.uniform(-2, 2),
            random.uniform(-0.3, 0.3),
            random.uniform(0.5, 1.5),
            random.randint(15, 30), color,
            random.uniform(1, 3), 0.95
        ))

    def score_popup(self, x, y, text, color=(255, 255, 0)):
        self.popups.append(ScorePopup(x, y, text, color))

    def boss_explode(self, x, y):
        """大型Boss爆炸特效"""
        for _ in range(5):
            cx = x + random.uniform(-30, 30)
            cy = y + random.uniform(-30, 30)
            self.explode(cx, cy, 25,
                        [(255,0,60),(255,60,120),(255,170,0),(255,255,255),(255,100,0)],
                        6, 7)
        for _ in range(20):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(3, 8)
            life = random.randint(40, 80)
            self.particles.append(Particle(
                x, y,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                life, (255, random.randint(0, 100), 0),
                random.uniform(3, 8), 0.96, 0.02
            ))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]
        self.popups = [p for p in self.popups if p.update()]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for p in self.popups:
            p.draw(surface)

    def clear(self):
        self.particles.clear()
        self.popups.clear()


class StarField:
    def __init__(self):
        self.stars = []
        for _ in range(150):
            self.stars.append({
                "x": random.uniform(0, WINDOW_WIDTH),
                "y": random.uniform(0, WINDOW_HEIGHT),
                "size": random.uniform(0.5, 2.5),
                "speed": random.uniform(0.3, 2.0),
                "brightness": random.uniform(0.3, 1.0),
                "twinkle": random.uniform(0.01, 0.05) * 100
            })

    def update(self):
        for s in self.stars:
            s["y"] += s["speed"]
            if s["y"] > WINDOW_HEIGHT:
                s["y"] = -2
                s["x"] = random.uniform(0, WINDOW_WIDTH)

    def draw(self, surface):
        for s in self.stars:
            b = s["brightness"]
            alpha = int(b * 255)
            color = (alpha, alpha, min(255, alpha + 30))
            c = max(1, int(s["size"]))
            pygame.draw.circle(surface, color, (int(s["x"]), int(s["y"])), c)
