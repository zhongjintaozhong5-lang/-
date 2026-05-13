"""跑酷敌人：步行者、飞行者、炮台"""
import math
import random
import pygame
from .config import *
from game.entities import Bullet

class ParkourEnemy:
    def __init__(self, x, y, etype, scroll_speed=0):
        self.x = x
        self.y = y
        self.type = etype
        cfg = ENEMY_TYPES[etype]
        self.hp = cfg["hp"]
        self.max_hp = cfg["hp"]
        self.w = cfg["w"]
        self.h = cfg["h"]
        self.score = cfg["score"]
        self.color = cfg["color"]
        self.speed = cfg["speed"]
        self.alive = True
        self.flash = 0
        self.phase = random.uniform(0, math.pi * 2)
        self.start_x = x
        self.start_y = y
        self.patrol_dir = -1
        self.shoot_timer = random.randint(40, 100)
        self.scroll_speed = scroll_speed

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self, scroll_speed):
        self.phase += 0.03
        self.scroll_speed = scroll_speed
        if self.flash > 0:
            self.flash -= 1

        # 卷轴带动敌人向左移动
        self.x -= scroll_speed

        if self.type == "walker":
            # 地面巡逻
            self.x += self.speed * self.patrol_dir * 0.5
            if abs(self.x - self.start_x) > 80:
                self.patrol_dir *= -1
        elif self.type == "flyer":
            # 空中浮动 + 正弦波
            base_y = self.start_y
            self.y = base_y + 20 * math.sin(self.phase * 2)
            self.x += math.sin(self.phase * 1.5) * 0.3
        elif self.type == "turret":
            pass  # 固定

    def shoot(self):
        self.shoot_timer -= 1
        if self.shoot_timer > 0:
            return []
        self.shoot_timer = max(30, 80 - self.hp * 5)

        bullets = []
        spd = 3.0
        if self.type == "flyer":
            bullets.append(Bullet(self.x - 12, self.y, -spd, 0, (255, 100, 60), 1, 4, 4, is_enemy=True))
        elif self.type == "turret":
            for i in range(-1, 2):
                bullets.append(Bullet(self.x - 16, self.y + i * 8,
                                      -spd, i * 0.5,
                                      (200, 60, 255), 1, 4, 4, is_enemy=True))
        return bullets

    def hit(self, damage=1):
        self.hp -= damage
        self.flash = 6
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface, offset_x=0):
        if not self.alive:
            return
        px = int(self.x - offset_x)
        py = int(self.y)
        # 屏幕外裁剪
        if px < -50 or px > SCREEN_WIDTH + 50:
            return

        c = self.color if self.flash % 4 < 2 else WHITE

        if self.type == "walker":
            body = pygame.Rect(px - self.w // 2, py - self.h // 2, self.w, self.h)
            pygame.draw.ellipse(surface, c, body)
            pygame.draw.ellipse(surface, (40, 40, 60), body, 2)
            # 眼睛
            pygame.draw.circle(surface, WHITE, (px - 5, py - 3), 3)
            pygame.draw.circle(surface, WHITE, (px + 5, py - 3), 3)
            pygame.draw.circle(surface, RED, (px - 5, py - 3), 1)
            pygame.draw.circle(surface, RED, (px + 5, py - 3), 1)
            # 腿
            leg = 4 * math.sin(self.phase * 3)
            pygame.draw.line(surface, c, (px - 8, py + 10), (px - 10 + leg, py + 16), 3)
            pygame.draw.line(surface, c, (px + 8, py + 10), (px + 10 - leg, py + 16), 3)

        elif self.type == "flyer":
            # 菱形机身
            pts = [(px, py - 12), (px + 14, py), (px, py + 12), (px - 14, py)]
            pygame.draw.polygon(surface, c, pts)
            pygame.draw.polygon(surface, (40, 40, 60), pts, 2)
            # 翅膀
            wing_flap = 6 * math.sin(self.phase * 4)
            pygame.draw.line(surface, c, (px, py - 8), (px - 16, py - 6 - wing_flap), 3)
            pygame.draw.line(surface, c, (px, py + 8), (px - 16, py + 6 + wing_flap), 3)

        elif self.type == "turret":
            # 底座
            base = pygame.Rect(px - 16, py - 4, 32, 12)
            pygame.draw.rect(surface, (60, 60, 80), base)
            # 炮管
            aim = (self.phase * 2) % math.pi - math.pi / 2
            # 炮口
            pygame.draw.circle(surface, c, (px, py - 4), 10)
            pygame.draw.circle(surface, WHITE, (px, py - 4), 4)
            # 炮管
            for i in range(-1, 2):
                cx = px + i * 4
                pygame.draw.rect(surface, (100, 100, 120),
                               pygame.Rect(cx - 2, py - 18, 4, 16))
                pygame.draw.circle(surface, RED if self.shoot_timer < 15 else (60, 0, 0),
                                 (cx, py - 18), 3)
