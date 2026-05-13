"""跑酷玩家：物理、跳跃、射击"""
import math
import pygame
from .config import *
from game.entities import Bullet

class ParkourPlayer:
    def __init__(self):
        self.x = 80
        self.y = SCREEN_HEIGHT // 2
        self.w = 24
        self.h = 32
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.jump_count = 0
        self.max_jumps = 2
        self.dir = 1  # 1=右, -1=左
        self.lives = PLAYER_MAX_LIVES
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.weapon_level = 1
        self.score = 0
        self.alive = True
        self.invincible = 0
        self.shoot_timer = 0
        self.shoot_interval = PLAYER_SHOOT_INTERVAL
        self.phase = 0
        self.walk_frame = 0
        self.landed = False

    def get_rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def jump(self):
        if self.jump_count < self.max_jumps:
            if self.jump_count == 0:
                self.vy = JUMP_VEL
            else:
                self.vy = DOUBLE_JUMP_VEL
            self.jump_count += 1
            self.on_ground = False

    def update(self, keys, platforms, scroll_speed):
        self.phase += 0.05
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        if self.invincible > 0:
            self.invincible -= 1

        # 水平输入
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
            self.dir = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
            self.dir = 1
        if dx:
            self.walk_frame += 0.2

        # 水平物理
        target_vx = dx * PLAYER_SPEED + scroll_speed
        self.vx += (target_vx - self.vx) * 0.25
        if dx == 0:
            self.vx = scroll_speed + (self.vx - scroll_speed) * FRICTION

        # 重力
        self.vy += GRAVITY
        if self.vy > 15:
            self.vy = 15

        # 移动
        self.x += self.vx
        self.y += self.vy

        # 平台碰撞
        self.on_ground = False
        player_rect = self.get_rect()
        for plat in platforms:
            if not plat.alive:
                continue
            pr = plat.get_rect()
            if player_rect.colliderect(pr):
                # 从上方落下
                if self.vy > 0 and player_rect.bottom - self.vy <= pr.top + 4:
                    self.y = pr.top - self.h // 2
                    self.vy = 0
                    self.on_ground = True
                    self.jump_count = 0
                # 从下方撞到
                elif self.vy < 0 and player_rect.top - self.vy >= pr.bottom - 4:
                    self.y = pr.bottom + self.h // 2
                    self.vy = 0
                # 侧面碰撞（阻挡横向移动）
                elif self.vx > 0 and player_rect.right - self.vx <= pr.left + 4:
                    self.x = pr.left - self.w // 2
                elif self.vx < 0 and player_rect.left - self.vx >= pr.right - 4:
                    self.x = pr.right + self.w // 2

        # 边界
        if self.x < 20:
            self.x = 20
        if self.y < 20:
            self.y = 20

        # 掉出屏幕
        if self.y > SCREEN_HEIGHT + 50:
            self.lose_life()

        # 动画帧
        if self.on_ground:
            self.landed = True

        return self.alive

    def lose_life(self):
        if self.invincible > 0:
            return
        if self.lives > 0:
            self.lives -= 1
            self.weapon_level = max(1, self.weapon_level - 1)
            self.hp = self.max_hp
            self.invincible = PLAYER_INVINCIBLE_TIME
            # 重置位置到上一个安全区域
            self.y = SCREEN_HEIGHT // 2
            self.vy = 0
        if self.lives <= 0:
            self.alive = False

    def take_damage(self, dmg=1):
        if self.invincible > 0:
            return False
        self.hp -= dmg
        if self.hp <= 0:
            self.lose_life()
        self.invincible = 30
        return self.hp <= 0

    def shoot(self):
        if self.shoot_timer > 0:
            return []
        self.shoot_timer = self.shoot_interval
        bullets = []
        bs = BULLET_SPEED
        cx = self.x + self.dir * 16
        cy = self.y - 4

        if self.weapon_level == 1:
            bullets.append(Bullet(cx, cy, self.dir * bs, 0, CYAN, 1, 4, 10))
        elif self.weapon_level == 2:
            bullets.append(Bullet(cx, cy - 3, self.dir * bs, 0, CYAN, 1, 4, 10))
            bullets.append(Bullet(cx, cy + 3, self.dir * bs, 0, CYAN, 1, 4, 10))
        elif self.weapon_level == 3:
            bullets.append(Bullet(cx, cy, self.dir * bs, 0, (0, 255, 136), 1, 5, 12))
            bullets.append(Bullet(cx, cy - 5, self.dir * bs * 0.9, -0.8, (0, 255, 136), 1, 3, 10))
            bullets.append(Bullet(cx, cy + 5, self.dir * bs * 0.9, 0.8, (0, 255, 136), 1, 3, 10))
        elif self.weapon_level >= 4:
            offsets = [0, -6, 6, -12, 12]
            yoffs = [0, -4, 4, -2, 2]
            for i in range(5):
                bullets.append(Bullet(cx + offsets[i], cy + yoffs[i],
                                      self.dir * bs, -0.3 + i * 0.15,
                                      (0, 255, 255) if i == 0 else (0, 220 - i * 20, 255),
                                      2 if i == 0 else 1, 4, 10))
        return bullets

    def draw(self, surface, offset_x=0):
        if self.invincible > 0 and self.invincible % 6 < 3:
            return
        px = int(self.x - offset_x)
        py = int(self.y)

        # 引擎光效（奔跑时）
        if not self.on_ground or abs(self.vx - BASE_SCROLL_SPEED) > 1:
            flicker = 6 + 3 * math.sin(self.phase * 6)
            for i in range(2, 0, -1):
                r = 6 + i * 3 + int(flicker * 0.3)
                alpha = 30 // i
                s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                ex = px - 10 * self.dir
                pygame.draw.circle(s, (60, 160, 255, alpha), (r, r), r)
                surface.blit(s, (ex - r, py + 10 - r))

        # 身体
        body_color = (200, 200, 220) if self.invincible % 4 < 2 else (180, 180, 200)
        # 躯干
        pygame.draw.ellipse(surface, body_color,
                          pygame.Rect(px - 10, py - 14, 20, 24))
        # 头盔
        pygame.draw.circle(surface, (100, 180, 255), (px, py - 18), 10)
        pygame.draw.circle(surface, (150, 220, 255), (px, py - 18), 7)
        # 目镜
        eye_color = CYAN
        pygame.draw.circle(surface, eye_color, (px + 3 * self.dir, py - 18), 3)
        # 手臂
        arm_swing = 4 * math.sin(self.walk_frame) if self.on_ground else 2
        pygame.draw.line(surface, body_color,
                        (px - 8, py - 8), (px - 14, py - 4 + arm_swing), 4)
        pygame.draw.line(surface, body_color,
                        (px + 8, py - 8), (px + 14, py - 4 - arm_swing), 4)
        # 腿
        leg_swing = 4 * math.sin(self.walk_frame) if self.on_ground else 0
        pygame.draw.line(surface, (100, 100, 140),
                        (px - 5, py + 8), (px - 7 + leg_swing, py + 16), 4)
        pygame.draw.line(surface, (100, 100, 140),
                        (px + 5, py + 8), (px + 7 - leg_swing, py + 16), 4)

        # 武器
        pygame.draw.rect(surface, (200, 200, 200),
                        pygame.Rect(px + 10 * self.dir, py - 6, 12 * self.dir, 4))
