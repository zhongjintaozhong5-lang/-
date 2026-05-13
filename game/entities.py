"""游戏实体：玩家、子弹、敌人、道具、Boss"""

import math
import random
import pygame
from .config import *
from .effects import Particle

# ============================================================
# 子弹
# ============================================================
class Bullet:
    def __init__(self, x, y, vx, vy, color=CYAN, damage=1, w=4, h=14, is_enemy=False, homing=False):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.damage = damage
        self.w = w
        self.h = h
        self.is_enemy = is_enemy
        self.homing = homing
        self.alive = True
        self.trail = []
        self.target = None

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self):
        # 追踪
        if self.homing and self.target and self.target.alive:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 1:
                speed = math.hypot(self.vx, self.vy)
                self.vx += (dx / dist) * 0.3
                self.vy += (dy / dist) * 0.3
                mag = math.hypot(self.vx, self.vy)
                self.vx = (self.vx / mag) * speed
                self.vy = (self.vy / mag) * speed

        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)
        self.x += self.vx
        self.y += self.vy

        if (self.y < -30 or self.y > WINDOW_HEIGHT + 30 or
            self.x < -30 or self.x > WINDOW_WIDTH + 30):
            self.alive = False

    def draw(self, surface):
        # 拖尾
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int((i / len(self.trail)) * 100)
            s = max(1, int(self.w * (0.3 + 0.7 * i / len(self.trail))))
            c = (min(255, self.color[0]), min(255, self.color[1]), min(255, self.color[2]))
            pygame.draw.circle(surface, (c[0], c[1], c[2]), (int(tx), int(ty)), s)

        # 主体
        if self.is_enemy:
            # 敌方子弹 - 发光圆
            for r in [self.w, self.w * 0.6]:
                alpha = 60 if r == self.w else 180
                c = (min(255, self.color[0]), min(255, self.color[1]), min(255, self.color[2]))
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, alpha), (r, r), r)
                surface.blit(s, (self.x - r, self.y - r))
        else:
            # 我方子弹
            rect = self.get_rect()
            # 发光效果
            glow = pygame.Surface((self.w + 8, self.h + 8), pygame.SRCALPHA)
            c = self.color
            for i in range(4):
                g = pygame.Rect(4 - i, 4 - i, self.w + i * 2, self.h + i * 2)
                pygame.draw.rect(glow, (*c, 30 - i * 6), g, border_radius=3)
            surface.blit(glow, (self.x - self.w // 2 - 4, self.y - self.h // 2 - 4))
            pygame.draw.rect(surface, (255, 255, 255),
                           pygame.Rect(rect.x, rect.y, rect.w, rect.h), border_radius=2)
            pygame.draw.rect(surface, self.color,
                           pygame.Rect(rect.x + 1, rect.y + 1, rect.w - 2, rect.h - 2), border_radius=1)


# ============================================================
# 玩家
# ============================================================
class Player:
    def __init__(self):
        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT - 100
        self.lives = PLAYER_MAX_LIVES
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.alive = True
        self.invincible = 60
        self.shoot_timer = 0
        self.shoot_interval = PLAYER_SHOOT_INTERVAL
        self.weapon_level = 1
        self.missile_count = 0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.phase = 0
        # 平滑移动
        self.vx = 0.0
        self.vy = 0.0
        # 护盾
        self.shield = 0
        self.shield_max = PLAYER_SHIELD_MAX
        # 激光
        self.laser_charges = 0
        self.laser_active = False
        self.laser_timer = 0
        self.laser_cooldown = 0
        self.laser_trail_particles = []

    def reset(self):
        self.__init__()

    def get_rect(self):
        return pygame.Rect(self.x - 14, self.y - 16, 28, 32)

    def update(self, keys, input_mgr):
        self.phase += 0.05
        if self.invincible > 0:
            self.invincible -= 1
        if not self.alive:
            return ([], False)
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0
        if self.laser_cooldown > 0:
            self.laser_cooldown -= 1

        # 平滑移动
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        if dx and dy:
            dx *= 0.7071
            dy *= 0.7071

        target_vx = dx * PLAYER_MAX_SPEED
        target_vy = dy * PLAYER_MAX_SPEED
        self.vx += (target_vx - self.vx) * PLAYER_ACCELERATION
        self.vy += (target_vy - self.vy) * PLAYER_ACCELERATION
        self.vx *= PLAYER_FRICTION if dx == 0 else 1.0
        self.vy *= PLAYER_FRICTION if dy == 0 else 1.0

        self.x += self.vx
        self.y += self.vy
        self.x = max(18, min(WINDOW_WIDTH - 18, self.x))
        self.y = max(18, min(WINDOW_HEIGHT - 50, self.y))

        # 激光持续（weapon_level>=5 无限发射）
        self.laser_active = False
        shooting = keys[pygame.K_SPACE] or keys[pygame.K_z]
        if shooting and self.laser_cooldown <= 0:
            if self.laser_charges > 0 or self.weapon_level >= 5:
                self.laser_active = True
                self.laser_timer = 3
                if self.laser_charges > 0:
                    self.laser_charges -= PLAYER_LASER_DRAIN
            if self.laser_charges <= 0:
                self.laser_charges = 0

        if self.laser_timer > 0:
            self.laser_timer -= 1

        bullets = []
        if shooting and self.shoot_timer <= 0:
            bullets = self.fire()
        return (bullets, self.laser_active)

    def get_laser_endpoints(self):
        """返回激光的起点和终点"""
        start = (int(self.x), int(self.y - 18))
        end = (int(self.x), 0)
        return start, end

    def fire(self):
        self.shoot_timer = self.shoot_interval
        bullets = []
        bs = BULLET_SPEED

        if self.weapon_level == 1:
            bullets.append(Bullet(self.x, self.y - 20, 0, -bs, CYAN, 1, 4, 16))
        elif self.weapon_level == 2:
            bullets.append(Bullet(self.x - 7, self.y - 18, 0, -bs, CYAN, 1, 4, 14))
            bullets.append(Bullet(self.x + 7, self.y - 18, 0, -bs, CYAN, 1, 4, 14))
        elif self.weapon_level == 3:
            bullets.append(Bullet(self.x, self.y - 20, 0, -bs, (0, 255, 136), 1, 5, 16))
            bullets.append(Bullet(self.x - 6, self.y - 16, -1.2, -bs * 0.9, (0, 255, 136), 1, 3, 12))
            bullets.append(Bullet(self.x + 6, self.y - 16, 1.2, -bs * 0.9, (0, 255, 136), 1, 3, 12))
            bullets.append(Bullet(self.x, self.y - 14, 0, -bs * 0.7, CYAN, 1, 3, 10))
        elif self.weapon_level == 4:
            # 10发弹幕
            offsets = [0, 5, -5, 10, -10, 17, -17, 24, -24, 32]
            angles = [0, 0.25, -0.25, 0.55, -0.55, 1.0, -1.0, 1.6, -1.6, 2.4]
            for i in range(10):
                spd = bs * (0.97 - abs(angles[i]) * 0.03)
                dmg = 2 if i == 0 else 1
                clr = (0, 255, 255) if i == 0 else (0, 220 - i * 8, 255 - i * 12)
                bullets.append(Bullet(self.x + offsets[i], self.y - 18,
                                      angles[i], -spd, clr, dmg, 4, 14))
            # 追踪导弹替换最外侧2发
            if self.missile_count >= 2:
                self.missile_count -= 2
                bullets.pop()
                bullets.pop()
                bullets.append(Bullet(self.x - 5, self.y - 12, -0.3, -bs * 0.65,
                                      (255, 100, 0), 3, 6, 12, homing=True))
                bullets.append(Bullet(self.x + 5, self.y - 12, 0.3, -bs * 0.65,
                                      (255, 100, 0), 3, 6, 12, homing=True))
        else:  # weapon_level >= 5  (含激光)
            # 10发弹幕
            offsets = [0, 5, -5, 10, -10, 17, -17, 24, -24, 32]
            angles = [0, 0.25, -0.25, 0.55, -0.55, 1.0, -1.0, 1.6, -1.6, 2.4]
            for i in range(10):
                spd = bs * (0.97 - abs(angles[i]) * 0.03)
                dmg = 2 if i == 0 else 1
                clr = (0, 255, 255) if i == 0 else (0, 220 - i * 8, 255 - i * 12)
                bullets.append(Bullet(self.x + offsets[i], self.y - 18,
                                      angles[i], -spd, clr, dmg, 4, 14))
            # 追踪导弹替换最外侧2发
            if self.missile_count >= 2:
                self.missile_count -= 2
                bullets.pop()
                bullets.pop()
                bullets.append(Bullet(self.x - 5, self.y - 12, -0.3, -bs * 0.65,
                                      (255, 100, 0), 3, 6, 12, homing=True))
                bullets.append(Bullet(self.x + 5, self.y - 12, 0.3, -bs * 0.65,
                                      (255, 100, 0), 3, 6, 12, homing=True))
        return bullets

    def draw_laser(self, surface):
        """绘制穿透激光"""
        if not self.laser_active and self.laser_timer <= 0:
            return
        start, end = self.get_laser_endpoints()
        beam_width = 6 + 2 * math.sin(self.phase * 10)
        beam_h = start[1] - end[1]

        # 外层辉光
        for w in range(3, 0, -1):
            alpha = 40 + w * 20
            s = pygame.Surface((int(beam_width * 2 + w * 8), beam_h + 20), pygame.SRCALPHA)
            pygame.draw.line(s, (255, 0, 255, alpha),
                           (beam_width + w * 4, 10),
                           (beam_width + w * 4, beam_h + 10),
                           int(beam_width + w * 4))
            surface.blit(s, (start[0] - beam_width - w * 4, end[1] - 10))

        # 主光束（白色核心）
        s2 = pygame.Surface((int(beam_width), beam_h + 10), pygame.SRCALPHA)
        bw2 = max(1, int(beam_width * 0.5))
        pygame.draw.line(s2, (255, 255, 255, 220),
                       (beam_width // 2, 5),
                       (beam_width // 2, beam_h + 5), bw2)
        surface.blit(s2, (start[0] - beam_width // 2, end[1] - 5))

    def take_damage(self, dmg=1):
        if self.invincible > 0:
            return False
        # 护盾吸收
        if self.shield > 0:
            self.shield -= 1
            self.invincible = 60
            return False
        self.lives -= 1
        self.weapon_level = max(1, self.weapon_level - 1)
        self.hp = self.max_hp
        if self.lives > 0:
            self.invincible = 420  # 7秒免疫 (60fps * 7)
            return False
        else:
            self.alive = False
            return True

    def draw(self, surface):
        if not self.alive:
            return
        if self.invincible > 0 and self.invincible % 6 < 3:
            return

        # 引擎光效
        flicker = 8 + math.sin(self.phase * 8) * 3
        for i in range(3, 0, -1):
            r = 8 + i * 5 + flicker * (i / 3)
            alpha = 40 // i
            s = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (60, 160, 255, alpha), (int(r), int(r)), int(r))
            surface.blit(s, (self.x - r, self.y + 14 + flicker * 0.3 - r))

        # 机身
        points = [
            (0, -22), (-6, -12), (-14, 0), (-16, 10),
            (-5, 8), (-3, 20), (3, 20), (5, 8),
            (16, 10), (14, 0), (6, -12)
        ]
        pts = [(self.x + px, self.y + py) for px, py in points]

        # 发光
        glow_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.polygon(glow_surf, (40, 100, 255, 40),
                          [(px - self.x + 25, py - self.y + 25) for px, py in pts])
        surface.blit(glow_surf, (self.x - 25, self.y - 25))

        # 主体
        pygame.draw.polygon(surface, (50, 130, 230), pts)
        pygame.draw.polygon(surface, (80, 180, 255), pts, 2)

        # 机身高光
        highlight = [(self.x, self.y - 18), (self.x - 5, self.y - 4),
                     (self.x, self.y + 8), (self.x + 5, self.y - 4)]
        pygame.draw.polygon(surface, (100, 200, 255), highlight)

        # 座舱
        pygame.draw.ellipse(surface, (140, 230, 255),
                          pygame.Rect(self.x - 5, self.y - 10, 10, 14))

        # 武器指示
        if self.weapon_level >= 3:
            pygame.draw.circle(surface, (0, 255, 136), (int(self.x - 12), int(self.y + 2)), 2)
            pygame.draw.circle(surface, (0, 255, 136), (int(self.x + 12), int(self.y + 2)), 2)

        # 尾焰
        fl = 6 + math.sin(self.phase * 6) * 3
        pygame.draw.polygon(surface, (255, 140, 0),
                          [(self.x - 4, self.y + 20), (self.x, self.y + 20 + fl),
                           (self.x + 4, self.y + 20)])
        pygame.draw.polygon(surface, (255, 220, 100),
                          [(self.x - 2, self.y + 20), (self.x, self.y + 18 + fl * 0.6),
                           (self.x + 2, self.y + 20)])

        # 护盾
        if self.shield > 0:
            pulse = 0.7 + 0.3 * math.sin(self.phase * 4)
            for r in range(3, 0, -1):
                radius = int((30 + r * 8) * pulse)
                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                alpha = 30 + r * 15
                pygame.draw.circle(s, (0, 200, 255, alpha), (radius, radius), radius, 3 - r + 1)
                surface.blit(s, (self.x - radius, self.y - radius))
            # 护盾剩余指示
            shield_text = get_font(14).render(f"{'■' * self.shield}{'□' * (self.shield_max - self.shield)}", True, (100, 220, 255))
            surface.blit(shield_text, (self.x - 22, self.y - 38))

        # 激光
        self.draw_laser(surface)


# ============================================================
# 敌人基类
# ============================================================
class Enemy:
    def __init__(self, etype, x, y, level=1):
        self.type = etype
        self.x = x
        self.y = y
        self.base_x = x
        self.level = level
        self.alive = True
        self.flash = 0
        self.shoot_timer = random.randint(30, 90)
        self.phase = random.uniform(0, math.pi * 2)

        info = ENEMY_TYPES[etype]
        lv_mult = 1 + (level - 1) * 0.12

        self.max_hp = int(info["hp"] * (1 + level * 0.1)) if etype in ("tank", "miniboss") else info["hp"]
        self.hp = self.max_hp
        self.speed = info["speed"] * lv_mult
        self.w = info["w"]
        self.h = info["h"]
        self.score = info["score"]
        self.can_shoot = info["can_shoot"]
        self.color = info["color"]
        self.shoot_interval = info.get("shoot_interval", 999) if self.can_shoot else 999

        self.move_pattern = "straight"
        if etype == "fighter":
            self.move_pattern = "sine"
        elif etype == "miniboss":
            self.move_pattern = "enter"

    def get_rect(self):
        s = self.w * 0.7
        return pygame.Rect(self.x - s // 2, self.y - s // 2, s, s)

    def update(self):
        self.phase += 0.03
        if self.flash > 0:
            self.flash -= 1
        self.shoot_timer -= 1

        if self.move_pattern == "straight":
            self.y += self.speed
        elif self.move_pattern == "sine":
            self.y += self.speed
            self.x = self.base_x + math.sin(self.phase * 2) * 60
        elif self.move_pattern == "enter":
            if self.y < 80:
                self.y += self.speed * 1.5
            self.x = self.base_x + math.sin(self.phase * 1.5) * 70

        if self.y > WINDOW_HEIGHT + 50:
            self.alive = False

    def shoot(self):
        """返回子弹列表"""
        self.shoot_timer = self.shoot_interval + random.randint(-15, 15)
        bullets = []
        bs = ENEMY_BULLET_SPEED * (1 + self.level * 0.05)

        if self.type == "fighter":
            bullets.append(Bullet(self.x, self.y + self.h // 2, 0, bs,
                                  (255, 100, 60), 1, 6, 6, is_enemy=True))
        elif self.type == "tank":
            bullets.append(Bullet(self.x - 10, self.y + self.h // 2, -0.5, bs,
                                  (160, 60, 255), 1, 7, 7, is_enemy=True))
            bullets.append(Bullet(self.x + 10, self.y + self.h // 2, 0.5, bs,
                                  (160, 60, 255), 1, 7, 7, is_enemy=True))
        elif self.type == "miniboss":
            for i in range(-3, 4):
                angle = math.pi / 2 + i * 0.12
                bullets.append(Bullet(
                    self.x + i * 12, self.y + self.h // 2,
                    math.cos(angle) * 2.5, math.sin(angle) * 2.5,
                    (255, 40, 100), 1, 6, 6, is_enemy=True
                ))
        return bullets

    def draw(self, surface):
        if self.flash % 4 < 2 and self.flash > 0:
            draw_color = (255, 255, 255)
        else:
            draw_color = self.color

        if self.type == "scout":
            self._draw_scout(surface, draw_color)
        elif self.type == "fighter":
            self._draw_fighter(surface, draw_color)
        elif self.type == "runner":
            self._draw_runner(surface, draw_color)
        elif self.type == "tank":
            self._draw_tank(surface, draw_color)
        elif self.type == "miniboss":
            self._draw_miniboss(surface, draw_color)

        # 血条(血多的敌人)
        if self.max_hp > 2 and self.hp < self.max_hp:
            bw = self.w + 8
            bar_y = self.y - self.h // 2 - 8
            pygame.draw.rect(surface, (0, 0, 0, 180),
                           pygame.Rect(self.x - bw // 2, bar_y, bw, 4))
            hp_ratio = self.hp / self.max_hp
            hp_color = (60, 255, 60) if hp_ratio > 0.5 else (255, 255, 60) if hp_ratio > 0.25 else (255, 60, 60)
            pygame.draw.rect(surface, hp_color,
                           pygame.Rect(self.x - bw // 2 + 1, bar_y + 1,
                                     (bw - 2) * hp_ratio, 2))

    def _draw_scout(self, surface, color):
        px, py = int(self.x), int(self.y)
        pygame.draw.polygon(surface, color,
                          [(px, py - 14), (px - 12, py + 8), (px, py + 4), (px + 12, py + 8)])
        pygame.draw.circle(surface, (140, 200, 255), (px, py - 6), 3)

    def _draw_fighter(self, surface, color):
        px, py = int(self.x), int(self.y)
        pygame.draw.polygon(surface, color,
                          [(px, py - 17), (px - 10, py + 6), (px - 4, py + 4),
                           (px - 4, py + 14), (px + 4, py + 14),
                           (px + 4, py + 4), (px + 10, py + 6)])
        pygame.draw.ellipse(surface, (255, 180, 140),
                          pygame.Rect(px - 4, py - 6, 8, 10))
        fl = 4 + math.sin(self.phase * 5) * 2
        pygame.draw.polygon(surface, (255, 100, 0),
                          [(px - 3, py + 14), (px, py + 14 + fl), (px + 3, py + 14)])

    def _draw_runner(self, surface, color):
        px, py = int(self.x), int(self.y)
        pygame.draw.polygon(surface, color,
                          [(px, py - 14), (px - 8, py - 2), (px - 12, py + 12),
                           (px, py + 6), (px + 12, py + 12),
                           (px + 8, py - 2)])
        fl = 3 + math.sin(self.phase * 6) * 1.5
        pygame.draw.circle(surface, (255, 140, 0), (px, py + 12 + int(fl)), 3)

    def _draw_tank(self, surface, color):
        px, py = int(self.x), int(self.y)
        pygame.draw.polygon(surface, color,
                          [(px, py - 21), (px - 18, py - 6), (px - 21, py + 10),
                           (px - 6, py + 21), (px + 6, py + 21),
                           (px + 21, py + 10), (px + 18, py - 6)])
        pygame.draw.line(surface, (255, 255, 255, 40), (px - 12, py - 2), (px + 12, py - 2), 1)
        pygame.draw.ellipse(surface, (200, 140, 255),
                          pygame.Rect(px - 5, py - 8, 10, 8))

    def _draw_miniboss(self, surface, color):
        px, py = int(self.x), int(self.y)
        pygame.draw.polygon(surface, color,
                          [(px, py - 30), (px - 24, py - 12), (px - 30, py + 4),
                           (px - 22, py + 20), (px - 6, py + 30),
                           (px + 6, py + 30), (px + 22, py + 20),
                           (px + 30, py + 4), (px + 24, py - 12)])
        pygame.draw.ellipse(surface, (180, 30, 70),
                          pygame.Rect(px - 14, py - 10, 28, 30))
        pygame.draw.ellipse(surface, (255, 60, 120),
                          pygame.Rect(px - 6, py - 10, 12, 16))
        pygame.draw.circle(surface, (255, 170, 0), (px - 18, py + 4), 3)
        pygame.draw.circle(surface, (255, 170, 0), (px + 18, py + 4), 3)
        fl = 5 + math.sin(self.phase * 4) * 2
        pygame.draw.polygon(surface, (255, 100, 0),
                          [(px - 12, py + 30), (px - 8, py + 30 + fl), (px - 4, py + 30)])
        pygame.draw.polygon(surface, (255, 100, 0),
                          [(px + 4, py + 30), (px + 8, py + 30 + fl), (px + 12, py + 30)])


# ============================================================
# Boss（最终Boss）
# ============================================================
# Boss 1: 铁壁号（第4关）
# ============================================================
class BossIronwall:
    """铁壁号 - 重型装甲 Boss，旋转护盾 + 弹幕"""
    def __init__(self, level):
        self.x = WINDOW_WIDTH // 2
        self.y = -80
        self.level = level
        self.max_hp = 80 + level * 15
        self.hp = self.max_hp
        self.alive = True
        self.flash = 0
        self.shoot_timer = 50
        self.phase = 0
        self.attack_phase = 0
        self.attack_timer = 0
        self.entering = True
        self.w = 100
        self.h = 80
        self.base_x = WINDOW_WIDTH // 2
        self.score = 6000
        self.target_y = 65
        # 护盾系统
        self.shield_health = 30
        self.shield_max = 30
        self.shield_regen_timer = 0
        self.shield_active = True

    def get_rect(self):
        s = 60
        return pygame.Rect(self.x - s // 2, self.y - s // 2, s, s)

    def update(self):
        self.phase += 0.02
        if self.flash > 0:
            self.flash -= 1
        self.attack_timer += 1
        self.shoot_timer -= 1

        if self.entering:
            self.y += 1.5
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return

        # 缓慢左右移动
        self.x = self.base_x + math.sin(self.phase * 0.5) * 100

        # 护盾恢复
        if not self.shield_active and self.shield_regen_timer > 0:
            self.shield_regen_timer -= 1
        if not self.shield_active and self.shield_regen_timer <= 0:
            self.shield_health = min(self.shield_max, self.shield_health + 1)
            if self.shield_health >= self.shield_max:
                self.shield_active = True

        # 每180帧切换攻击模式
        if self.attack_timer > 180:
            self.attack_phase = (self.attack_phase + 1) % 3
            self.attack_timer = 0

    def shoot(self):
        if self.entering:
            return []
        self.shoot_timer = 20
        bullets = []
        spread_count = 5 + self.attack_phase * 2
        base_speed = 2.5 + self.attack_phase * 0.3

        if self.attack_phase == 0:
            # 旋转扇形弹幕
            offset = self.phase * 2
            for i in range(spread_count):
                angle = math.pi / 2 + (i - spread_count // 2) * 0.15 + offset * 0.1
                bullets.append(Bullet(
                    self.x, self.y + self.h // 2,
                    math.cos(angle) * base_speed, math.sin(angle) * base_speed,
                    (100, 200, 255), 1, 6, 6, is_enemy=True
                ))
        elif self.attack_phase == 1:
            # 两侧交叉弹
            for side in (-1, 1):
                for i in range(3):
                    angle = math.pi / 2 + side * (0.1 + i * 0.12)
                    bullets.append(Bullet(
                        self.x + side * 40, self.y + 10 + i * 15,
                        math.cos(angle) * (2.0 + i * 0.3),
                        math.sin(angle) * (2.0 + i * 0.3),
                        (200, 150, 255), 1, 6, 6, is_enemy=True
                    ))
        else:
            # 全方位弹 + 重力弹
            for i in range(8):
                angle = math.pi * 2 * i / 8 + self.phase * 0.5
                spd = 2.0
                bullets.append(Bullet(
                    self.x + math.cos(angle) * 30,
                    self.y + math.sin(angle) * 30,
                    math.cos(angle) * spd, math.sin(angle) * spd,
                    (255, 100, 200), 1, 5, 5, is_enemy=True
                ))
        return bullets

    def draw(self, surface):
        px, py = int(self.x), int(self.y)

        # 光晕
        glow = pygame.Surface((130, 130), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (60, 120, 255, 20),
                          pygame.Rect(15, 15, 100, 100))
        surface.blit(glow, (px - 65, py - 65))

        # 护盾
        if self.shield_active:
            shield_r = 50 + 5 * math.sin(self.phase * 2)
            for r in range(int(shield_r), int(shield_r - 15), -3):
                alpha = max(10, 60 - (shield_r - r) * 3)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (60, 180, 255, alpha), (r, r), r, 2)
                surface.blit(s, (px - r, py - r))

        # 主体 - 重型方舟造型
        body_color = (100, 100, 100) if self.flash % 4 < 2 and self.flash > 0 else (60, 80, 140)
        # 主体方块
        pygame.draw.rect(surface, body_color,
                       pygame.Rect(px - 35, py - 25, 70, 50), border_radius=8)
        # 上层
        pygame.draw.rect(surface, (50, 60, 120),
                       pygame.Rect(px - 25, py - 35, 50, 20), border_radius=4)
        # 装甲板
        for i in range(-2, 3):
            pygame.draw.rect(surface, (80, 100, 160),
                           pygame.Rect(px + i * 20 - 8, py - 20, 16, 40), border_radius=2)
        # 核心
        pulse = 0.7 + 0.3 * math.sin(self.phase * 2.5)
        pygame.draw.circle(surface, (100, 200, 255), (px, py), int(8 + 4 * pulse))
        pygame.draw.circle(surface, (200, 230, 255), (px, py), int(4 + 2 * pulse))
        # 座舱
        pygame.draw.ellipse(surface, (150, 200, 255),
                          pygame.Rect(px - 6, py - 10, 12, 16))
        # 两侧导弹舱
        for cx in (px - 30, px + 30):
            pygame.draw.rect(surface, (80, 60, 100),
                           pygame.Rect(cx - 5, py - 5, 10, 16), border_radius=2)
            pygame.draw.circle(surface, (255, 100, 50), (cx, py - 6), 2)
        # 引擎
        fl = 6 + math.sin(self.phase * 3) * 3
        for sx in (-20, -8, 8, 20):
            pygame.draw.polygon(surface, (60, 120, 255),
                              [(px + sx - 4, py + 25), (px + sx, py + 25 + fl),
                               (px + sx + 4, py + 25)])

        # 血条
        bw = 280; bar_y = 14
        pygame.draw.rect(surface, (20, 20, 40),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 14))
        ratio = self.hp / self.max_hp
        hp_color = (60, 140, 255) if ratio > 0.5 else (255, 200, 0) if ratio > 0.25 else (255, 60, 60)
        pygame.draw.rect(surface, hp_color,
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2 + 2, bar_y + 2,
                                 (bw - 4) * ratio, 10))
        pygame.draw.rect(surface, (60, 140, 255),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 14), 1)

        # 护盾指示器
        if self.shield_active:
            shield_text = get_font(16).render(f"护盾 {self.shield_health}/{self.shield_max}", True, (100, 200, 255))
            surface.blit(shield_text, (WINDOW_WIDTH // 2 - 50, bar_y + 18))
        else:
            cd = self.shield_regen_timer
            shield_text = get_font(16).render(f"护盾恢复中... {cd//60}", True, (150, 100, 100))
            surface.blit(shield_text, (WINDOW_WIDTH // 2 - 50, bar_y + 18))

        font = get_font(20)
        hp_text = font.render(f"铁壁号  {int(self.hp)}/{self.max_hp}", True, (255, 255, 255))
        text_rect = hp_text.get_rect(center=(WINDOW_WIDTH // 2, bar_y + 7))
        surface.blit(hp_text, text_rect)

        mode_names = ["旋转弹", "交叉火", "全方位"]
        mode_text = get_font(16).render(f"攻击: {mode_names[self.attack_phase]}", True, (180, 200, 255))
        surface.blit(mode_text, (WINDOW_WIDTH // 2 - 50, bar_y + 32))

    def hit_by_bullet(self, damage):
        """被子弹击中 - 护盾吸收"""
        if self.shield_active and self.shield_health > 0:
            self.shield_health -= damage
            if self.shield_health <= 0:
                self.shield_active = False
                self.shield_regen_timer = 240  # 4秒后恢复
            return False  # 护盾挡住了
        self.hp -= damage
        self.flash = 4
        if self.hp <= 0:
            self.alive = False
            return True
        return True


# ============================================================
# Boss 2: 冥王号（第5关 - 最终Boss）
# ============================================================
class BossPluto:
    """冥王号 - 最终Boss，多阶段高难度"""
    def __init__(self, level):
        self.x = WINDOW_WIDTH // 2
        self.y = -80
        self.level = level
        self.max_hp = 120 + level * 20
        self.hp = self.max_hp
        self.alive = True
        self.flash = 0
        self.shoot_timer = 40
        self.phase = 0
        self.attack_phase = 0
        self.attack_timer = 0
        self.entering = True
        self.w = 110
        self.h = 90
        self.base_x = WINDOW_WIDTH // 2
        self.score = 12000
        self.target_y = 60
        # 特殊攻击
        self.laser_angle = 0
        self.charge_dir = 1
        self.charge_speed = 0

    def get_rect(self):
        s = 65
        return pygame.Rect(self.x - s // 2, self.y - s // 2, s, s)

    def update(self):
        self.phase += 0.02
        if self.flash > 0:
            self.flash -= 1
        self.attack_timer += 1
        self.shoot_timer -= 1

        if self.entering:
            self.y += 1.8
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return

        # 大范围移动
        self.base_x += self.charge_dir * 0.5
        if self.base_x > WINDOW_WIDTH - 80:
            self.base_x = WINDOW_WIDTH - 80
            self.charge_dir = -1
        elif self.base_x < 80:
            self.base_x = 80
            self.charge_dir = 1
        self.x = self.base_x + math.sin(self.phase * 0.8) * 160

        # 血量低时狂暴
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.5:
            self.charge_speed = 1.5
        else:
            self.charge_speed = 0

        # 攻击切换
        switch_time = 150 if hp_ratio > 0.5 else 100
        if self.attack_timer > switch_time:
            self.attack_phase = (self.attack_phase + 1) % 4
            self.attack_timer = 0

    def shoot(self):
        if self.entering:
            return []
        self.shoot_timer = 15
        bullets = []
        hp_ratio = self.hp / self.max_hp
        speed_mult = 1.5 if hp_ratio < 0.5 else 1.0

        if self.attack_phase == 0:
            # 扇形激光网
            for i in range(-5, 6):
                angle = math.pi / 2 + i * 0.12
                spd = 3.0 * speed_mult
                bullets.append(Bullet(
                    self.x, self.y + self.h // 2,
                    math.cos(angle) * spd, math.sin(angle) * spd,
                    (255, 0, 100), 2, 7, 7, is_enemy=True
                ))
        elif self.attack_phase == 1:
            # 追踪弹群
            for i in range(5):
                angle = math.pi / 2 + random.uniform(-0.3, 0.3)
                spd = 2.0 * speed_mult
                b = Bullet(self.x + random.uniform(-30, 30), self.y + 20,
                          math.cos(angle) * spd, math.sin(angle) * spd,
                          (255, 100, 0), 1, 6, 6, is_enemy=True)
                b.homing = True
                bullets.append(b)
        elif self.attack_phase == 2:
            # 螺旋弹
            for i in range(12):
                angle = math.pi * 2 * i / 12 + self.phase
                spd = 1.8 * speed_mult
                bullets.append(Bullet(
                    self.x + math.cos(angle) * 20,
                    self.y + math.sin(angle) * 20,
                    math.cos(angle) * spd, math.sin(angle) * spd,
                    (200, 0, 200), 1, 5, 5, is_enemy=True
                ))
        else:
            # 绝望攻击 - 全方位高密度
            for ring in range(3):
                count = 8 + ring * 4
                for i in range(count):
                    angle = math.pi * 2 * i / count + self.phase * 0.5 + ring * 0.3
                    spd = 1.5 + ring * 0.5 * speed_mult
                    bullets.append(Bullet(
                        self.x, self.y,
                        math.cos(angle) * spd, math.sin(angle) * spd,
                        (255, 50, 50), 1, 4, 4, is_enemy=True
                    ))
        return bullets

    def draw(self, surface):
        px, py = int(self.x), int(self.y)
        hp_ratio = self.hp / self.max_hp
        rage = 1.0 + max(0, (0.5 - hp_ratio)) * 2

        body_color = (180, 0, 40) if self.flash % 4 < 2 and self.flash > 0 else (100, 0, 20)

        # 暗色光晕
        for r in range(60, 30, -10):
            alpha = int(15 / (r / 10))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (180, 0, 40, alpha), (r, r), r)
            surface.blit(s, (px - r, py - r))

        # 主体 - 暗黑旗舰
        points = [
            (px, py - 40), (px - 36, py - 24), (px - 48, py),
            (px - 42, py + 20), (px - 28, py + 40),
            (px - 8, py + 34), (px, py + 26),
            (px + 8, py + 34), (px + 28, py + 40),
            (px + 42, py + 20), (px + 48, py),
            (px + 36, py - 24)
        ]
        pygame.draw.polygon(surface, body_color, points)
        # 暗红外壳
        pygame.draw.polygon(surface, (80, 0, 20),
                          [(px, py - 30), (px - 22, py - 12), (px - 28, py + 6),
                           (px - 18, py + 28), (px + 18, py + 28),
                           (px + 28, py + 6), (px + 22, py - 12)])
        # 核心 - 脉动
        pulse = 0.6 + 0.4 * math.sin(self.phase * 3 * rage)
        for r in range(int(20 * pulse), 0, -4):
            alpha = int(30 * pulse)
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 0, 40, alpha), (r, r), r)
            surface.blit(s, (px - r, py - r))
        pygame.draw.circle(surface, (255, 0, 60), (px, py), int(10 * pulse))
        pygame.draw.circle(surface, (255, 100, 150), (px, py), int(5 * pulse))

        # 座舱
        pygame.draw.ellipse(surface, (200, 60, 100),
                          pygame.Rect(px - 8, py - 14, 16, 20))

        # 翅膀
        for dx in (-38, 38):
            pts = [(px + dx - 6, py - 10), (px + dx, py - 4),
                   (px + dx, py + 30), (px + dx - 6, py + 26)]
            pygame.draw.polygon(surface, (120, 0, 30), pts)

        # 炮台
        for cx in (px - 36, px + 36):
            pygame.draw.rect(surface, (180, 0, 40),
                           pygame.Rect(cx - 5, py - 5, 10, 12), border_radius=2)
            pygame.draw.circle(surface, (255, 50, 0), (cx, py), 3)
        # 底部大炮
        pygame.draw.rect(surface, (180, 0, 40),
                       pygame.Rect(px - 14, py + 30, 28, 8), border_radius=3)
        # 引擎
        fl = 10 + 6 * math.sin(self.phase * 4 * rage)
        for sx in (-22, -10, 10, 22):
            pygame.draw.polygon(surface, (200, 0, 0),
                              [(px + sx - 5, py + 40), (px + sx, py + 40 + fl),
                               (px + sx + 5, py + 40)])
            pygame.draw.polygon(surface, (255, 100, 0),
                              [(px + sx - 2, py + 40), (px + sx, py + 38 + fl * 0.6),
                               (px + sx + 2, py + 40)])

        # 血条
        bw = 300; bar_y = 14
        pygame.draw.rect(surface, (20, 0, 0),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 14))
        ratio = self.hp / self.max_hp
        hp_color = (200, 0, 0) if ratio > 0.5 else (255, 100, 0) if ratio > 0.25 else (255, 0, 0)
        pygame.draw.rect(surface, hp_color,
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2 + 2, bar_y + 2,
                                 (bw - 4) * ratio, 10))
        pygame.draw.rect(surface, (255, 0, 60),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 14), 1)

        font = get_font(20)
        hp_text = font.render(f"冥王号  {int(self.hp)}/{self.max_hp}", True, (255, 255, 255))
        text_rect = hp_text.get_rect(center=(WINDOW_WIDTH // 2, bar_y + 7))
        surface.blit(hp_text, text_rect)

        mode_names = ["激光网", "追踪弹", "螺旋弹", "绝望"]
        mode_text = get_font(16).render(f"攻击: {mode_names[self.attack_phase]}", True, (255, 150, 100))
        surface.blit(mode_text, (WINDOW_WIDTH // 2 - 50, bar_y + 18))

        if hp_ratio < 0.5:
            rage_text = get_font(18).render("⚡ 狂暴模式 ⚡", True, (255, 50, 50))
            r_rect = rage_text.get_rect(center=(WINDOW_WIDTH // 2, bar_y + 34))
            surface.blit(rage_text, r_rect)

    def hit_by_bullet(self, damage):
        """被子弹击中"""
        self.hp -= damage
        self.flash = 4
        if self.hp <= 0:
            self.alive = False
            return True
        return True


# ============================================================
# Boss 3: 虚空吞噬者（第3关）
# ============================================================
class BossVoid:
    """虚空吞噬者 - 引力黑洞Boss，重力场+跨维度攻击"""
    def __init__(self, level):
        self.x = WINDOW_WIDTH // 2
        self.y = -80
        self.level = level
        self.max_hp = 60 + level * 15
        self.hp = self.max_hp
        self.alive = True
        self.flash = 0
        self.shoot_timer = 40
        self.phase = 0
        self.attack_phase = 0
        self.attack_timer = 0
        self.entering = True
        self.w = 100
        self.h = 90
        self.base_x = WINDOW_WIDTH // 2
        self.score = 3000
        self.target_y = 68

        # 引力场
        self.gravity_pull = 0.0     # 0~1 强度
        self.gravity_phase = 0
        self.gravity_on = False

        # 裂隙传送门
        self.portals = []           # [{x, y, timer, side}]
        self.portal_timer = 0

        # 旋转扫射角
        self.sweep_angle = 0
        self.sweep_dir = 1

    def get_rect(self):
        s = 56
        return pygame.Rect(self.x - s // 2, self.y - s // 2, s, s)

    def get_gravity_at(self, px, py):
        """返回引力偏移量 (dx, dy)"""
        if self.gravity_pull <= 0 or not self.alive:
            return (0, 0)
        dx = self.x - px
        dy = self.y - py
        dist = math.hypot(dx, dy)
        if dist < 10:
            return (0, 0)
        strength = self.gravity_pull * 1.8
        return (dx / dist * strength, dy / dist * strength)

    def update(self):
        self.phase += 0.025
        if self.flash > 0:
            self.flash -= 1
        self.shoot_timer -= 1
        self.attack_timer += 1
        self.gravity_phase += 1

        if self.entering:
            self.y += 1.8
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return

        hp_ratio = self.hp / self.max_hp
        rage = hp_ratio < 0.3
        speed_mult = 1.5 if rage else 1.0

        # 移动
        self.x = self.base_x + math.sin(self.phase * 0.5) * 130

        # === 引力场周期 ===
        if self.gravity_phase > 200:
            self.gravity_phase = 0
            self.gravity_on = not self.gravity_on

        if self.gravity_on or rage:
            self.gravity_pull = min(1.0, self.gravity_pull + 0.015 * speed_mult)
        else:
            self.gravity_pull = max(0, self.gravity_pull - 0.008)

        # === 传送门 ===
        self.portal_timer += 1
        portal_gap = 280 if not rage else 180
        if self.portal_timer >= portal_gap:
            self.portal_timer = 0
            side = -1 if random.random() < 0.5 else 1
            self.portals.append({
                "x": 18 if side == -1 else WINDOW_WIDTH - 18,
                "y": random.randint(90, 350),
                "timer": 0,
                "side": side,
                "shots": 0
            })

        for p in self.portals[:]:
            p["timer"] += 1
            if p["timer"] > 150 or p["shots"] >= 4:
                self.portals.remove(p)

        # === 攻击切换 ===
        switch_time = 220 if not rage else 120
        if self.attack_timer > switch_time:
            self.attack_phase = (self.attack_phase + 1) % 4
            self.attack_timer = 0

        # 扫射角度
        self.sweep_angle += 0.025 * self.sweep_dir

    def shoot(self):
        if self.entering:
            return []
        self.shoot_timer = 15
        bullets = []
        hp_ratio = self.hp / self.max_hp
        rage = hp_ratio < 0.3
        spd_mult = 1.4 if rage else 1.0

        # 额外模式（狂暴时双模式）
        extra_bullets = []
        if rage:
            extra_phase = (self.attack_phase + 1) % 4

        if self.attack_phase == 0:
            # 引力牵引 - 螺旋扩散弹
            for i in range(10):
                angle = math.pi * 2 * i / 10 + self.phase * 1.5
                spd = 1.8 * spd_mult
                bullets.append(Bullet(
                    self.x + math.cos(angle) * 25,
                    self.y + math.sin(angle) * 25,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (180, 0, 255), 1, 6, 6, is_enemy=True
                ))
            if rage:
                for i in range(8):
                    angle = math.pi * 2 * i / 8 + self.phase * 1.5 + 0.3
                    spd = 2.2 * spd_mult
                    extra_bullets.append(Bullet(
                        self.x + math.cos(angle) * 15,
                        self.y + math.sin(angle) * 15,
                        math.cos(angle) * spd,
                        math.sin(angle) * spd,
                        (255, 0, 200), 1, 5, 5, is_enemy=True
                    ))

        elif self.attack_phase == 1:
            # 虚空裂隙 - 传送门瞄准射击
            for p in self.portals:
                p["shots"] += 1
                for i in range(3):
                    angle = math.pi / 2 + random.uniform(-0.3, 0.3)
                    spd = 2.5 * spd_mult
                    bullets.append(Bullet(
                        p["x"], p["y"],
                        math.cos(angle) * spd * p["side"],
                        math.sin(angle) * spd,
                        (200, 0, 200), 1, 5, 5, is_enemy=True
                    ))
            if rage:
                for p in self.portals:
                    if p["shots"] < 4:
                        p["shots"] += 1
                        bullets.append(Bullet(
                            p["x"], p["y"],
                            0, 3.0 * spd_mult,
                            (255, 100, 0), 1, 5, 5, is_enemy=True
                        ))

        elif self.attack_phase == 2:
            # 碎星弹幕 - 散射
            for i in range(5):
                angle = math.pi / 2 + (i - 2) * 0.12
                spd = 2.5 * spd_mult
                bullets.append(Bullet(
                    self.x, self.y + 20,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (150, 50, 255), 1, 7, 7, is_enemy=True
                ))
            # 狂暴额外弹
            if rage:
                for i in range(3):
                    angle = math.pi / 2 + (i - 1) * 0.2
                    spd = 3.0
                    bullets.append(Bullet(
                        self.x, self.y + 10,
                        math.cos(angle) * spd,
                        math.sin(angle) * spd,
                        (255, 0, 100), 1, 5, 5, is_enemy=True
                    ))

        else:
            # 湮灭扫射 - 旋转扩散 + 冲击波环
            for i in range(5):
                angle = self.sweep_angle + math.pi * 2 * i / 5
                spd = 2.0 * spd_mult
                bullets.append(Bullet(
                    self.x + math.cos(angle) * 20,
                    self.y + math.sin(angle) * 20,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (255, 50, 150), 1, 6, 6, is_enemy=True
                ))
            # 冲击波环（每2次射击）
            if self.attack_timer % 40 < 20:
                for i in range(16):
                    angle = math.pi * 2 * i / 16
                    spd = 1.5 * spd_mult
                    bullets.append(Bullet(
                        self.x, self.y,
                        math.cos(angle) * spd,
                        math.sin(angle) * spd,
                        (200, 100, 255), 1, 4, 4, is_enemy=True
                    ))
            if rage:
                for i in range(8):
                    angle = math.pi * 2 * i / 8 + self.phase
                    spd = 2.5
                    bullets.append(Bullet(
                        self.x, self.y,
                        math.cos(angle) * spd,
                        math.sin(angle) * spd,
                        (255, 0, 255), 1, 5, 5, is_enemy=True
                    ))

        if rage and extra_bullets:
            bullets.extend(extra_bullets)
        return bullets

    def hit_by_bullet(self, damage):
        self.hp -= damage
        self.flash = 4
        if self.hp <= 0:
            self.alive = False
            return True
        return True

    def draw(self, surface):
        px, py = int(self.x), int(self.y)
        hp_ratio = self.hp / self.max_hp
        rage = hp_ratio < 0.3

        # === 暗色光晕 ===
        glow_size = 80 + 20 * math.sin(self.phase * 2)
        for r in range(int(glow_size), 20, -15):
            alpha = 10 + int(15 * (1 - r / glow_size))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (80, 0, 120, alpha), (r, r), r)
            surface.blit(s, (px - r, py - r))

        # === 引力场视觉 ===
        if self.gravity_pull > 0.1:
            pull_intensity = int(30 * self.gravity_pull)
            for r in range(pull_intensity, 10, -8):
                alpha = 8 + int(12 * (1 - r / pull_intensity))
                s2 = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s2, (100, 0, 180, alpha), (r, r), r, 2)
                surface.blit(s2, (px - r, py - r))

        # === 旋转光环 ===
        for ring_i in range(3):
            ring_radius = 36 + ring_i * 14 + 6 * math.sin(self.phase * 2 + ring_i)
            ring_angle = self.phase * (0.5 + ring_i * 0.3)
            alpha_ring = 40 + ring_i * 15
            for dot in range(8):
                da = math.pi * 2 * dot / 8 + ring_angle
                dx = px + math.cos(da) * ring_radius
                dy = py + math.sin(da) * ring_radius
                ds = max(2, 4 - ring_i)
                color = (120, 40 + ring_i * 40, 200 - ring_i * 30)
                s3 = pygame.Surface((ds * 2, ds * 2), pygame.SRCALPHA)
                pygame.draw.circle(s3, (*color, alpha_ring), (ds, ds), ds)
                surface.blit(s3, (dx - ds, dy - ds))

        # === 传送门绘制 ===
        for p in self.portals:
            pp_alpha = 80 + 60 * math.sin(p["timer"] * 0.1)
            pr = 10 + 4 * math.sin(p["timer"] * 0.15)
            s4 = pygame.Surface((pr * 2, pr * 2), pygame.SRCALPHA)
            pygame.draw.circle(s4, (180, 0, 200, pp_alpha), (pr, pr), pr, 2)
            pygame.draw.circle(s4, (100, 0, 150, pp_alpha // 2), (pr, pr), pr - 2)
            surface.blit(s4, (p["x"] - pr, p["y"] - pr))

        # === 主体 ===
        body_color = (140, 0, 60) if (self.flash % 4 < 2 and self.flash > 0) else (60, 0, 40)

        # 外部触手/翼
        for side in (-1, 1):
            pts = [
                (px + side * 50, py - 10),
                (px + side * 38, py - 20),
                (px + side * 42, py),
                (px + side * 38, py + 18),
                (px + side * 48, py + 22),
            ]
            pygame.draw.polygon(surface, (40, 0, 30), pts)
            pygame.draw.polygon(surface, (80, 0, 60), pts, 1)

        # 主体圆盘
        pygame.draw.ellipse(surface, body_color,
                          pygame.Rect(px - 30, py - 22, 60, 44))
        pygame.draw.ellipse(surface, (80, 0, 50),
                          pygame.Rect(px - 24, py - 18, 48, 36))

        # 核心 - 脉动之眼
        if rage:
            core_pulse = 0.5 + 0.5 * math.sin(self.phase * 6)
        else:
            core_pulse = 0.6 + 0.4 * math.sin(self.phase * 2.5)

        core_r = int(14 * core_pulse)
        # 外核
        for r in range(core_r + 8, core_r - 2, -4):
            alpha = 60 if r > core_r else 120
            s5 = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            c = (200, 80, 255, alpha) if rage else (100, 0, 200, alpha)
            pygame.draw.circle(s5, c, (r, r), r)
            surface.blit(s5, (px - r, py - r))
        # 内核（亮）
        pygame.draw.circle(surface, (220, 150, 255), (px, py), core_r)
        pygame.draw.circle(surface, (255, 200, 255), (px, py), max(2, core_r - 4))

        # 狂暴红光
        if rage:
            red_glow = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(red_glow, (255, 0, 40, 60 + 40 * math.sin(self.phase * 4)),
                             (25, 25), 25)
            surface.blit(red_glow, (px - 25, py - 25))

        # 引擎
        fl = 7 + 4 * math.sin(self.phase * 3)
        for sx in (-16, 16):
            pygame.draw.polygon(surface, (120, 0, 100),
                              [(px + sx - 5, py + 22), (px + sx, py + 22 + fl),
                               (px + sx + 5, py + 22)])
            pygame.draw.polygon(surface, (200, 80, 180),
                              [(px + sx - 2, py + 22), (px + sx, py + 20 + fl * 0.6),
                               (px + sx + 2, py + 22)])

        # === 血条 ===
        bw = 280; bar_y = 14
        pygame.draw.rect(surface, (20, 0, 30),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 14))
        ratio = self.hp / self.max_hp
        hp_color = (140, 60, 255) if ratio > 0.5 else (255, 100, 0) if ratio > 0.3 else (255, 0, 60)
        pygame.draw.rect(surface, hp_color,
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2 + 2, bar_y + 2,
                                 (bw - 4) * ratio, 10))
        pygame.draw.rect(surface, (140, 60, 255),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 14), 1)

        font = get_font(20)
        hp_text = font.render(f"虚空吞噬者  {int(self.hp)}/{self.max_hp}", True, (255, 255, 255))
        text_rect = hp_text.get_rect(center=(WINDOW_WIDTH // 2, bar_y + 7))
        surface.blit(hp_text, text_rect)

        mode_names = ["引力牵引", "虚空裂隙", "碎星弹幕", "湮灭扫射"]
        mode_text = get_font(16).render(
            f"攻击: {mode_names[self.attack_phase]}{' ⚡狂怒' if rage else ''}",
            True, (200, 150, 255) if not rage else (255, 50, 50))
        surface.blit(mode_text, (WINDOW_WIDTH // 2 - 50, bar_y + 18))

        if self.gravity_pull > 0.1:
            grav_text = get_font(14).render(
                f"引力场 {int(self.gravity_pull * 100)}%", True,
                (180, 100, 255) if not rage else (255, 50, 50))
            surface.blit(grav_text, (WINDOW_WIDTH // 2 - 50, bar_y + 32))


# ============================================================
# Boss 4: 苗浩毁灭者（第6关 - 最终隐藏Boss）
# ============================================================
class BossMiaohao:
    """苗浩毁灭者 - 4阶段终极Boss，激光免疫，吸收道具反击"""
    def __init__(self, level):
        self.x = WINDOW_WIDTH // 2
        self.y = -80
        self.level = level
        self.max_hp = 200 + level * 25
        self.hp = self.max_hp
        self.alive = True
        self.flash = 0
        self.shoot_timer = 30
        self.combat_phase = 0   # 0,1,2,3 = 4条血
        self.anim_phase = 0.0    # 动画计时器
        self.phase_timer = 0    # 阶段切换动画计时
        self.phase_flash = 0    # 阶段切换闪光
        self.entering = True
        self.w = 120
        self.h = 100
        self.score = 20000
        self.target_y = 60
        self.base_x = WINDOW_WIDTH // 2

        # 特性
        self.laser_immune = True

        # 阶段0: 基础
        self.attack_timer = 0
        self.attack_phase = 0

        # 阶段1: 瞬移
        self.teleport_timer = 0
        self.teleport_cooldown = 0
        self.target_teleport_x = self.x
        self.target_teleport_y = self.y
        self.is_teleporting = False
        self.teleport_flash = 0

        # 阶段2: 双重射击
        self.split_offset = 0

        # 阶段3: 毁灭形态
        self.rage_pulse = 0

        # 道具吸收
        self.absorb_timer = 180

        # 锁血系统 - 每阶段强制锁血20秒
        self.phase_lock_timer = 1200  # 开场锁血20秒
        self.phase_hp_thresholds = [0.75, 0.50, 0.25, 0.0]

    def get_rect(self):
        s = 60
        return pygame.Rect(self.x - s // 2, self.y - s // 2, s, s)

    def get_phase(self):
        """根据当前HP返回阶段(0-3)"""
        ratio = self.hp / self.max_hp
        if ratio > 0.75:
            return 0
        elif ratio > 0.50:
            return 1
        elif ratio > 0.25:
            return 2
        else:
            return 3

    def on_phase_change(self):
        """阶段切换特效 + 强制锁血20秒"""
        self.phase_flash = 30
        self.phase_timer = 60
        self.phase_lock_timer = 1200  # 20秒锁血

    def update(self):
        self.anim_phase += 0.02
        if self.flash > 0:
            self.flash -= 1
        self.shoot_timer -= 1
        self.attack_timer += 1

        if self.phase_flash > 0:
            self.phase_flash -= 1
        if self.phase_timer > 0:
            self.phase_timer -= 1
        if self.phase_lock_timer > 0:
            self.phase_lock_timer -= 1

        if self.entering:
            self.y += 1.5
            if self.y >= self.target_y:
                self.y = self.target_y
                self.entering = False
            return

        # 检查阶段变化
        new_phase = self.get_phase()
        if new_phase > self.combat_phase:
            self.combat_phase = new_phase
            self.on_phase_change()

        hp_ratio = self.hp / self.max_hp
        rage = self.combat_phase >= 3
        speed_mult = 1.0 + self.combat_phase * 0.2

        # 基础移动
        if not self.is_teleporting:
            self.x = self.base_x + math.sin(self.anim_phase * 0.3) * 140
            if rage:
                self.x += math.sin(self.anim_phase * 0.8) * 30  # 狂暴抖动

        # === 阶段1+: 瞬移 ===
        if self.combat_phase >= 1:
            self.teleport_cooldown -= 1
            if self.is_teleporting:
                self.teleport_flash += 1
                # 快速移向目标
                self.x += (self.target_teleport_x - self.x) * 0.15
                self.y += (self.target_teleport_y - self.y) * 0.15
                if self.teleport_flash > 20:
                    self.is_teleporting = False
                    self.teleport_flash = 0
                    self.x = self.target_teleport_x
                    self.y = self.target_teleport_y
            elif self.teleport_cooldown <= 0 and random.random() < 0.02 * speed_mult:
                # 触发瞬移
                self.is_teleporting = True
                self.teleport_flash = 0
                margin = 80
                self.target_teleport_x = random.randint(margin, WINDOW_WIDTH - margin)
                self.target_teleport_y = random.randint(50, 250)
                self.teleport_cooldown = 120

        # === 攻击切换 ===
        switch_time = int(200 / speed_mult)
        if self.attack_timer > switch_time:
            self.attack_phase = (self.attack_phase + 1) % 3
            self.attack_timer = 0

        # 道具吸收计时
        self.absorb_timer -= 1
        if rage:
            self.absorb_timer = min(self.absorb_timer, 90)

    def absorb_powerups(self, powerups, enemy_bullets, player):
        """吸收场上道具并反击"""
        if self.entering or not self.alive:
            return
        if self.absorb_timer > 0:
            return
        self.absorb_timer = 180 if self.combat_phase < 3 else 90

        if not powerups:
            return

        for pu in powerups[:]:
            powerups.remove(pu)

        # 反击弹幕
        angle_base = math.atan2(player.y - self.y, player.x - self.x)
        for i in range(10):
            angle = angle_base + (i - 4.5) * 0.12
            spd = 2.5 + self.combat_phase * 0.5
            enemy_bullets.append(Bullet(
                self.x, self.y + 30,
                math.cos(angle) * spd,
                math.sin(angle) * spd,
                (255, 0, 100), 1, 6, 6, is_enemy=True
            ))

    def shoot(self):
        if self.entering:
            return []
        self.shoot_timer = max(8, 25 - self.combat_phase * 4)
        bullets = []
        hp_ratio = self.hp / self.max_hp
        rage = self.combat_phase >= 3
        spd_mult = 1.0 + self.combat_phase * 0.15

        if self.attack_phase == 0:
            # 3way散射
            for i in range(-1, 2):
                angle = math.pi / 2 + i * 0.12
                spd = 2.5 * spd_mult
                bullets.append(Bullet(
                    self.x + i * 10, self.y + 30,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (200, 50, 100), 1, 6, 6, is_enemy=True
                ))
            # 阶段2+: 双重射击（左右各一）
            if self.combat_phase >= 2:
                for side in (-1, 1):
                    for i in range(-1, 2):
                        angle = math.pi / 2 + i * 0.15
                        spd = 2.8 * spd_mult
                        bullets.append(Bullet(
                            self.x + side * 50 + i * 8, self.y + 20,
                            math.cos(angle) * spd,
                            math.sin(angle) * spd,
                            (255, 100, 200), 1, 5, 5, is_enemy=True
                        ))

        elif self.attack_phase == 1:
            # 瞄准弹
            if self.combat_phase >= 2:
                count = 5
            else:
                count = 3
            for i in range(count):
                angle = math.pi / 2 + (i - count // 2) * 0.1
                spd = 2.0 * spd_mult
                bullets.append(Bullet(
                    self.x + (i - count // 2) * 15, self.y + 25,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (255, 0, 80), 1, 5, 5, is_enemy=True
                ))

        else:
            # 环形弹 + 追踪弹（阶段2+）
            n = 6 + self.combat_phase * 2
            for i in range(n):
                angle = math.pi * 2 * i / n + self.anim_phase * 0.5
                spd = 1.8 * spd_mult
                bullets.append(Bullet(
                    self.x + math.cos(angle) * 20,
                    self.y + math.sin(angle) * 20,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (200, 0, 200), 1, 5, 5, is_enemy=True
                ))
            # 追踪弹
            if self.combat_phase >= 2:
                for i in range(3):
                    angle = math.pi / 2 + random.uniform(-0.3, 0.3)
                    spd = 1.5 * spd_mult
                    b = Bullet(
                        self.x + random.uniform(-20, 20), self.y + 20,
                        math.cos(angle) * spd, math.sin(angle) * spd,
                        (255, 100, 0), 1, 6, 6, is_enemy=True
                    )
                    b.homing = True
                    bullets.append(b)

        # 瞬移后环形爆发（阶段1+）
        if self.combat_phase >= 1 and self.teleport_flash > 15 and not self.is_teleporting:
            for i in range(12):
                angle = math.pi * 2 * i / 12
                spd = 2.5 * spd_mult
                bullets.append(Bullet(
                    self.x, self.y,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (255, 0, 255), 1, 5, 5, is_enemy=True
                ))

        # 阶段3: 毁灭密集弹幕
        if rage:
            for i in range(6):
                angle = self.anim_phase + math.pi * 2 * i / 6
                spd = 2.0
                bullets.append(Bullet(
                    self.x + math.cos(angle) * 10,
                    self.y + math.sin(angle) * 10,
                    math.cos(angle) * spd,
                    math.sin(angle) * spd,
                    (255, 50, 50), 1, 4, 4, is_enemy=True
                ))

        return bullets

    def hit_by_bullet(self, damage):
        # 激光免疫（实际在game.py中通过laser_immune判断，此处仅做通用处理）
        self.hp -= damage
        self.flash = 4

        # 强制锁血：20秒内不能掉到当前阶段阈值以下
        if self.phase_lock_timer > 0 and self.combat_phase < 3:
            min_hp = self.max_hp * self.phase_hp_thresholds[self.combat_phase]
            if self.hp < min_hp:
                self.hp = min_hp
        elif self.phase_lock_timer > 0 and self.combat_phase == 3:
            # 阶段3也锁20秒（HP锁定在1点不会死）
            if self.hp <= 0:
                self.hp = 1

        if self.hp <= 0:
            self.alive = False
            return True
        # 检查阶段切换（在update中处理）
        return True

    def draw(self, surface):
        px, py = int(self.x), int(self.y)
        hp_ratio = self.hp / self.max_hp
        rage = self.combat_phase >= 3

        # 阶段颜色
        phase_colors = [
            (120, 0, 80),    # 0: 紫
            (180, 0, 60),    # 1: 红
            (200, 60, 0),    # 2: 橙
            (255, 100, 50),   # 3: 炽白
        ]
        pc = phase_colors[self.combat_phase]

        # 瞬移闪光
        if self.is_teleporting and self.teleport_flash % 4 < 2:
            flash_color = (255, 255, 255)
            # 全屏闪烁效果
            for r in range(60, 20, -10):
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                alpha = 80 if r == 60 else 30
                pygame.draw.circle(s, (200, 200, 255, alpha), (r, r), r)
                surface.blit(s, (px - r, py - r))

        # 阶段切换闪光
        if self.phase_flash > 0:
            flash_intensity = int(200 * (self.phase_flash / 30))
            for r in range(80, 0, -20):
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                alpha = min(100, flash_intensity // (r // 10 + 1))
                pygame.draw.circle(s, (255, 255, 255, alpha), (r, r), r)
                surface.blit(s, (px - r, py - r))

        # 暗色光晕
        glow_r = 70 + 20 * math.sin(self.anim_phase * 2)
        for r in range(int(glow_r), 20, -15):
            alpha = 15 + int(15 * (1 - r / glow_r))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*pc, alpha), (r, r), r)
            surface.blit(s, (px - r, py - r))

        # 主体 - 大型毁灭者造型
        body_color = (80, 0, 20) if (self.flash % 4 < 2 and self.flash > 0) else pc

        # 外层装甲翼
        for side in (-1, 1):
            pts = [
                (px + side * 56, py - 8),
                (px + side * 42, py - 30),
                (px + side * 48, py + 6),
                (px + side * 40, py + 32),
                (px + side * 54, py + 38),
            ]
            pygame.draw.polygon(surface, (40, 0, 10), pts)
            pygame.draw.polygon(surface, (80, 0, 20), pts, 1)

        # 主体核心
        core_points = [
            (px, py - 38), (px - 40, py - 20), (px - 48, py + 6),
            (px - 36, py + 34), (px - 10, py + 44),
            (px + 10, py + 44), (px + 36, py + 34),
            (px + 48, py + 6), (px + 40, py - 20),
        ]
        pygame.draw.polygon(surface, body_color, core_points)
        pygame.draw.polygon(surface, (120, 20, 40), core_points, 2)

        # 内层装甲
        inner = [
            (px, py - 28), (px - 24, py - 12), (px - 30, py + 6),
            (px - 22, py + 24), (px + 22, py + 24),
            (px + 30, py + 6), (px + 24, py - 12),
        ]
        pygame.draw.polygon(surface, (60, 0, 15), inner)

        # 核心 - 毁灭之眼
        if rage:
            core_pulse = 0.5 + 0.5 * math.sin(self.anim_phase * 6)
        else:
            core_pulse = 0.7 + 0.3 * math.sin(self.anim_phase * 2.5)
        core_r = int(16 * core_pulse)

        for r in range(core_r + 10, core_r - 2, -5):
            alpha = 80 if r > core_r else 160
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            c = (min(255, pc[0] + 100), min(255, pc[1] + 100), min(255, pc[2] + 100), alpha)
            pygame.draw.circle(s, c, (r, r), r)
            surface.blit(s, (px - r, py - r))

        pygame.draw.circle(surface, (255, 200, 150), (px, py), core_r)
        pygame.draw.circle(surface, (255, 255, 255), (px, py), max(3, core_r - 4))
        pygame.draw.circle(surface, (255, 255, 200), (px, py), max(1, core_r - 6))

        # 毁灭形态光环
        if rage:
            for r in range(50, 20, -10):
                alpha = 20 + 15 * math.sin(self.anim_phase * 4)
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 50, 50, int(alpha)), (r, r), r, 2)
                surface.blit(s, (px - r, py - r))

        # 炮台
        for cx, cy in [(px - 34, py - 10), (px + 34, py - 10),
                       (px - 28, py + 16), (px + 28, py + 16)]:
            pygame.draw.rect(surface, (180, 0, 30),
                           pygame.Rect(cx - 6, cy - 4, 12, 8), border_radius=2)
            pygame.draw.circle(surface, (255, 50, 0), (cx, cy), 3)

        # 底部主炮
        pygame.draw.rect(surface, (180, 0, 30),
                       pygame.Rect(px - 16, py + 40, 32, 10), border_radius=3)
        pygame.draw.rect(surface, (255, 50, 0),
                       pygame.Rect(px - 6, py + 44, 12, 4), border_radius=2)

        # 引擎
        fl = 8 + 5 * math.sin(self.anim_phase * 3)
        for sx in (-20, -6, 6, 20):
            pygame.draw.polygon(surface, (120, 0, 30),
                              [(px + sx - 5, py + 44), (px + sx, py + 44 + fl),
                               (px + sx + 5, py + 44)])
            pygame.draw.polygon(surface, (255, 80, 30),
                              [(px + sx - 2, py + 44), (px + sx, py + 42 + fl * 0.6),
                               (px + sx + 2, py + 44)])

        # === 4段式血条 ===
        bw = 300; bar_y = 14
        # 背景
        pygame.draw.rect(surface, (20, 0, 0),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 16))
        # 4段
        seg_w = (bw - 6) / 4
        seg_colors = [(120, 0, 80), (180, 0, 60), (200, 80, 0), (255, 50, 50)]
        for i in range(4):
            seg_start = WINDOW_WIDTH // 2 - bw // 2 + 2 + i * seg_w
            seg_end = seg_start + seg_w - 1
            # 计算该段的填充比例
            seg_hp_start = 1.0 - (i / 4)
            seg_hp_end = 1.0 - ((i + 1) / 4)
            if hp_ratio >= seg_hp_start:
                fill = 1.0
            elif hp_ratio >= seg_hp_end:
                fill = (hp_ratio - seg_hp_end) / (seg_hp_start - seg_hp_end)
            else:
                fill = 0.0
            if fill > 0:
                color = seg_colors[i] if self.combat_phase >= i else (80, 0, 30)
                pygame.draw.rect(surface, color,
                               pygame.Rect(seg_start, bar_y + 2,
                                         int((seg_w - 1) * fill), 12))

        pygame.draw.rect(surface, (255, 50, 100),
                       pygame.Rect(WINDOW_WIDTH // 2 - bw // 2, bar_y, bw, 16), 1)

        # 名字
        font = get_font(20)
        hp_text = font.render(f"苗浩毁灭者  {int(self.hp)}/{self.max_hp}", True, (255, 255, 255))
        text_rect = hp_text.get_rect(center=(WINDOW_WIDTH // 2, bar_y + 8))
        surface.blit(hp_text, text_rect)

        # 阶段显示
        phase_names = ["初始形态", "瞬移突袭", "双重射击", "毁灭形态"]
        phase_text = get_font(16).render(
            f"{phase_names[self.combat_phase]}", True,
            (255, 200, 100) if not rage else (255, 50, 50))
        surface.blit(phase_text, (WINDOW_WIDTH // 2 - 50, bar_y + 20))

        # 锁血指示
        if self.phase_lock_timer > 0:
            lock_sec = self.phase_lock_timer // 60 + 1
            lock_color = (0, 200, 255) if lock_sec > 5 else (255, 200, 0)
            lock_text = get_font(14).render(
                f"锁血 {lock_sec}s", True, lock_color)
            surface.blit(lock_text, (WINDOW_WIDTH // 2 + 120, bar_y + 20))


# ============================================================
# 道具
# ============================================================
class PowerUp:
    def __init__(self, x, y, ptype):
        self.x = x
        self.y = y
        self.type = ptype
        self.vy = 1.5
        self.alive = True
        self.phase = random.uniform(0, math.pi * 2)
        self.appear_timer = 15

    def get_info(self):
        return POWERUP_TYPES[self.type]

    def get_rect(self):
        bob = math.sin(self.phase) * 3
        return pygame.Rect(self.x - 14, self.y - 14 + bob, 28, 28)

    def update(self):
        self.phase += 0.05
        self.y += self.vy
        if self.appear_timer > 0:
            self.appear_timer -= 1
        if self.y > WINDOW_HEIGHT + 30:
            self.alive = False

    def draw(self, surface):
        if self.appear_timer > 0:
            return
        info = self.get_info()
        color = info["color"]
        bob = math.sin(self.phase) * 3
        px, py = int(self.x), int(self.y + bob)

        # 光晕
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*color, 40), pygame.Rect(5, 5, 30, 30))
        surface.blit(glow, (px - 20, py - 20))

        # 外框
        pygame.draw.rect(surface, color,
                       pygame.Rect(px - 14, py - 14, 28, 28), border_radius=4)
        pygame.draw.rect(surface, (0, 0, 0, 100),
                       pygame.Rect(px - 12, py - 12, 24, 24), border_radius=3)
        pygame.draw.rect(surface, color,
                       pygame.Rect(px - 14, py - 14, 28, 28), 2, border_radius=4)

        # 文字
        font = get_font(24)
        text = font.render(info["label"], True, color)
        text_rect = text.get_rect(center=(px, py + 1))
        surface.blit(text, text_rect)


# ============================================================
# 僚机（小型飞机援助）
# ============================================================
class Wingman:
    """僚机 - 跟随玩家自动射击，10秒后飞走"""
    def __init__(self, player, side=1):
        self.player = player
        self.side = side  # 1=右侧, -1=左侧
        self.x = player.x - side * 40
        self.y = player.y + 10
        self.alive = True
        self.timer = 600  # 10秒
        self.shoot_timer = 0
        self.shoot_interval = 20
        self.phase = 0
        self.leaving = False
        self.leave_speed = 4

    def update(self, enemies, boss):
        self.phase += 0.05
        self.timer -= 1

        if self.leaving:
            self.y -= self.leave_speed
            self.x += self.side * 2
            if self.y < -50:
                self.alive = False
            return []

        if self.timer <= 60:
            self.leaving = True

        # 跟随玩家
        target_x = self.player.x - self.side * 45
        target_y = self.player.y + 5
        self.x += (target_x - self.x) * 0.08
        self.y += (target_y - self.y) * 0.08

        # 自动射击
        self.shoot_timer -= 1
        bullets = []
        if self.shoot_timer <= 0:
            self.shoot_timer = self.shoot_interval
            # 找最近的敌人瞄准
            target = None
            min_d = 350
            for e in enemies:
                if e.alive:
                    d = math.hypot(e.x - self.x, e.y - self.y)
                    if d < min_d:
                        min_d = d
                        target = e
            if boss and boss.alive:
                d = math.hypot(boss.x - self.x, boss.y - self.y)
                if d < min_d:
                    target = boss

            if target:
                angle = math.atan2(target.y - self.y, target.x - self.x)
                spd = 7
                bullets.append(Bullet(self.x, self.y,
                    math.cos(angle) * spd, math.sin(angle) * spd,
                    (255, 255, 100), 1, 3, 8))
            else:
                bullets.append(Bullet(self.x, self.y, 0, -7,
                    (255, 255, 100), 1, 3, 8))
        return bullets

    def draw(self, surface):
        if not self.alive:
            return
        px, py = int(self.x), int(self.y)

        # 闪烁（即将离开）
        if self.leaving and self.timer % 6 < 3:
            return

        # 机身
        pts = [(px, py - 10), (px - 8, py), (px - 12, py + 8),
               (px - 2, py + 6), (px, py + 4),
               (px + 2, py + 6), (px + 12, py + 8),
               (px + 8, py)]
        pygame.draw.polygon(surface, (255, 220, 50), pts)
        pygame.draw.polygon(surface, (255, 255, 150), pts, 1)
        # 座舱
        pygame.draw.ellipse(surface, (255, 255, 200),
                          pygame.Rect(px - 3, py - 6, 6, 8))
        # 引擎光
        fl = 4 + math.sin(self.phase * 5) * 2
        pygame.draw.polygon(surface, (255, 150, 0),
                          [(px - 3, py + 6), (px, py + 6 + fl), (px + 3, py + 6)])

        # 剩余时间指示
        if not self.leaving:
            bar_w = 30
            ratio = self.timer / 600
            pygame.draw.rect(surface, (30, 30, 30),
                           pygame.Rect(px - bar_w // 2, py + 14, bar_w, 3))
            pygame.draw.rect(surface, (255, 220, 0),
                           pygame.Rect(px - bar_w // 2, py + 14, bar_w * ratio, 3))
