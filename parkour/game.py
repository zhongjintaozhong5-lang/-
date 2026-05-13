"""跑酷射击游戏主逻辑"""
import sys
import math
import random
import pygame
from .config import *
from .player import ParkourPlayer
from .enemy import ParkourEnemy
from .level import LevelGenerator, Platform
from .ui import TitleScreen, HUD, LevelIntro, GameOver, WinScreen
from game.effects import ParticleSystem, StarField, ScorePopup
from game.entities import Bullet, PowerUp
from game.config import get_font

STATE_TITLE = 0
STATE_INTRO = 1
STATE_PLAYING = 2
STATE_GAME_OVER = 3
STATE_WIN = 4

class ParkourGame:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_TITLE
        self.frame = 0

        # 组件
        self.particles = ParticleSystem()
        self.stars = StarField()
        self.title_screen = TitleScreen()
        self.hud = HUD()
        self.level_intro = None
        self.game_over = None
        self.win_screen = None

        # 游戏状态
        self.player = None
        self.level = 0
        self.level_gen = None
        self.platforms = []
        self.enemies = []
        self.bullets = []       # 玩家子弹
        self.enemy_bullets = []  # 敌方子弹
        self.powerup_items = []
        self.scroll_x = 0
        self.high_score = 0
        self.score = 0
        self.boss_enemy = None
        self.boss_hp_bar = 0
        self.boss_max_hp = 0

        # 按键按下状态（用于单次触发）
        self.keys_down = set()

    def reset_game(self):
        self.player = ParkourPlayer()
        self.level = 0
        self.score = 0
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.powerup_items.clear()
        self.particles.clear()
        self.boss_enemy = None
        self.next_level()

    def next_level(self):
        self.level += 1
        if self.level > 5:
            self.state = STATE_WIN
            self.win_screen = WinScreen(self.score)
            return

        self.level_gen = LevelGenerator(self.level)
        self.platforms = self.level_gen.platforms[:]
        self.enemies.clear()
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.powerup_items.clear()
        self.boss_enemy = None
        self.scroll_x = 0

        # 生成敌人实体
        for ed in self.level_gen.enemies:
            if ed["type"] == "boss":
                boss_def = self.level_gen.boss_def
                e = ParkourEnemy(ed["x"], ed["y"], "turret")
                e.hp = boss_def["hp"]
                e.max_hp = boss_def["hp"]
                e.score = boss_def["score"]
                e.is_boss = True
                e.w = 60
                e.h = 50
                e.color = (200, 30, 80)
                self.boss_enemy = e
                self.boss_hp_bar = boss_def["hp"]
                self.boss_max_hp = boss_def["hp"]
            else:
                e = ParkourEnemy(ed["x"], ed["y"], ed["type"], self.level_gen.scroll_speed)
                self.enemies.append(e)

        # 进入关卡介绍
        self.state = STATE_INTRO
        self.level_intro = LevelIntro(self.level)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.state == STATE_TITLE and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.reset_game()
                elif self.state == STATE_GAME_OVER:
                    if event.key == pygame.K_SPACE and self.game_over and self.game_over.timer > 60:
                        self.reset_game()
                elif self.state == STATE_WIN:
                    if event.key == pygame.K_SPACE and self.win_screen and self.win_screen.timer > 90:
                        self.state = STATE_TITLE
                elif self.state == STATE_PLAYING:
                    if event.key in (pygame.K_z, pygame.K_LSHIFT):
                        self.keys_down.add("shoot")
                    if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        self.keys_down.add("jump")
                    if event.key == pygame.K_ESCAPE:
                        self.state = STATE_TITLE
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_z, pygame.K_LSHIFT):
                    self.keys_down.discard("shoot")

    def get_pressed_keys(self):
        return pygame.key.get_pressed()

    def update(self):
        self.frame += 1
        self.particles.update()
        self.stars.update()

        if self.state == STATE_TITLE:
            self.title_screen.update()
            return

        elif self.state == STATE_INTRO:
            if self.level_intro and not self.level_intro.update():
                self.state = STATE_PLAYING
            return

        elif self.state == STATE_GAME_OVER:
            if self.game_over:
                self.game_over.update()
            return

        elif self.state == STATE_WIN:
            if self.win_screen:
                self.win_screen.update()
            return

        # === STATE_PLAYING ===
        keys = self.get_pressed_keys()

        # 处理跳跃（单次触发）
        if "jump" in self.keys_down:
            self.keys_down.discard("jump")
            if self.player and self.player.alive:
                self.player.jump()

        # 更新卷轴
        scroll_speed = self.level_gen.scroll_speed if self.level_gen else BASE_SCROLL_SPEED
        self.scroll_x += scroll_speed

        # 更新玩家
        if self.player and self.player.alive:
            self.player.update(keys, self.platforms, scroll_speed)

        # 更新平台
        if self.level_gen:
            self.level_gen.update()
            self.platforms = [p for p in self.level_gen.platforms if p.alive]

        # 更新敌人
        for e in self.enemies[:]:
            e.update(scroll_speed)
            if not e.alive:
                self.enemies.remove(e)
                self.particles.explode(e.x, e.y, 15,
                                      [(100,200,255),(60,140,255),(255,255,255)], 3, 4)
                self.score += e.score
            else:
                # 敌人射击
                for b in e.shoot():
                    self.enemy_bullets.append(b)

        # Boss
        if self.boss_enemy and self.boss_enemy.alive:
            self.boss_enemy.update(scroll_speed)
            # Boss射击
            for b in self.boss_enemy.shoot():
                self.enemy_bullets.append(b)
            # Boss跟随卷轴保持在屏幕右侧
            target_x = self.scroll_x + SCREEN_WIDTH - 100
            self.boss_enemy.x += (target_x - self.boss_enemy.x) * 0.02
            self.boss_enemy.y = 100 + 80 * math.sin(self.frame * 0.02)

        # 更新玩家子弹
        for b in self.bullets[:]:
            b.update()
            if (b.x < self.scroll_x - 50 or b.x > self.scroll_x + SCREEN_WIDTH + 50 or
                b.y < -50 or b.y > SCREEN_HEIGHT + 50 or not b.alive):
                self.bullets.remove(b)

        # 更新敌方子弹
        for b in self.enemy_bullets[:]:
            b.update()
            if (b.x < self.scroll_x - 50 or b.x > self.scroll_x + SCREEN_WIDTH + 50 or
                b.y < -50 or b.y > SCREEN_HEIGHT + 50 or not b.alive):
                self.enemy_bullets.remove(b)

        # 更新道具
        for pu in self.powerup_items[:]:
            pu.y += 1
            if pu.y > SCREEN_HEIGHT + 20:
                self.powerup_items.remove(pu)

        # === 碰撞检测 ===
        if self.player and self.player.alive:
            pr = self.player.get_rect()

            # 玩家子弹 vs 敌人
            for b in self.bullets[:]:
                br = b.get_rect()
                # vs 普通敌人
                for e in self.enemies[:]:
                    if br.colliderect(e.get_rect()):
                        e.hit(b.damage)
                        b.alive = False
                        self.particles.explode(b.x, b.y, 8, [(255,255,255),(CYAN)], 2, 3)
                        if not e.alive:
                            self.particles.explode(e.x, e.y, 20,
                                                  [e.color, WHITE, CYAN], 4, 5)
                            self.score += e.score
                        break
                # vs Boss
                if self.boss_enemy and self.boss_enemy.alive:
                    if br.colliderect(self.boss_enemy.get_rect()):
                        self.boss_enemy.hit(b.damage)
                        b.alive = False
                        self.particles.explode(b.x, b.y, 8, [(255,100,150),(WHITE)], 2, 4)
                        if not self.boss_enemy.alive:
                            self.particles.boss_explode(self.boss_enemy.x, self.boss_enemy.y)
                            self.score += self.boss_enemy.score
                            # Boss击杀 → 过关条件满足

            # 敌方子弹 vs 玩家
            for b in self.enemy_bullets[:]:
                if br.colliderect(b.get_rect()):
                    b.alive = False
                    self.player.take_damage(1)
                    self.particles.explode(b.x, b.y, 10, [(255,60,60),(WHITE)], 2, 3)

            # 敌人碰撞玩家
            for e in self.enemies[:]:
                if e.alive and pr.colliderect(e.get_rect()):
                    e.alive = False
                    self.player.take_damage(2)
                    self.particles.explode(e.x, e.y, 15, [(255,100,100),(RED)], 3, 4)

            # Boss碰撞玩家
            if self.boss_enemy and self.boss_enemy.alive:
                if pr.colliderect(self.boss_enemy.get_rect()):
                    self.player.take_damage(2)
                    # 推开玩家
                    self.player.vx = -8

            # 收集道具
            for pu in self.powerup_items[:]:
                if abs(self.player.x - pu.x) < 30 and abs(self.player.y - pu.y) < 30:
                    if pu.type == "battery":
                        self.score += 50
                        self.particles.score_popup(pu.x, pu.y, "+50", YELLOW)
                    elif pu.type == "weapon":
                        self.player.weapon_level = min(4, self.player.weapon_level + 1)
                        self.particles.score_popup(pu.x, pu.y, "武器升级!", CYAN)
                    self.powerup_items.remove(pu)

            # 玩家射击
            if "shoot" in self.keys_down or keys[pygame.K_z]:
                new_bullets = self.player.shoot()
                for b in new_bullets:
                    self.bullets.append(b)

            # 检查玩家存活
            if not self.player.alive:
                self.state = STATE_GAME_OVER
                self.game_over = GameOver(self.score, self.level)
                if self.score > self.high_score:
                    self.high_score = self.score

        # 检查过关条件：到达关卡终点
        if self.level_gen and self.player and self.player.alive:
            if self.player.x >= self.level_gen.length:
                self.next_level()

    def draw(self):
        self.screen.fill(BLACK)

        if self.state == STATE_TITLE:
            self.stars.draw(self.screen)
            self.title_screen.draw(self.screen)
            pygame.display.flip()
            return

        # 绘制星空背景（随卷轴缓慢移动）
        self.stars.draw(self.screen)

        if self.state in (STATE_PLAYING, STATE_INTRO):
            offset_x = self.scroll_x

            # 绘制平台
            for p in self.platforms:
                p.draw(self.screen, offset_x)

            # 绘制道具
            for pu in self.powerup_items:
                # 使用基础圆表示
                px = int(pu.x - offset_x)
                py = int(pu.y)
                if -20 < px < SCREEN_WIDTH + 20:
                    color = (0, 255, 136) if pu.type == "battery" else (255, 180, 0)
                    pygame.draw.circle(self.screen, color, (px, py), 8)
                    pygame.draw.circle(self.screen, WHITE, (px, py), 4)
                    label = "B" if pu.type == "battery" else "W"
                    lt = get_font(12).render(label, True, BLACK)
                    self.screen.blit(lt, lt.get_rect(center=(px, py)))

            # 绘制敌人
            for e in self.enemies:
                e.draw(self.screen, offset_x)

            # 绘制Boss
            if self.boss_enemy and self.boss_enemy.alive:
                self.boss_enemy.draw(self.screen, offset_x)
                # Boss血条（屏幕上方）
                boss_name = self.level_gen.boss_def["name"] if self.level_gen else ""
                bw = 200
                bx = SCREEN_WIDTH // 2 - bw // 2
                by = 12
                pygame.draw.rect(self.screen, (20, 0, 0), (bx, by, bw, 12))
                ratio = self.boss_enemy.hp / self.boss_enemy.max_hp
                fill_color = (255, 50, 80) if ratio > 0.5 else (255, 150, 0) if ratio > 0.25 else (255, 0, 0)
                pygame.draw.rect(self.screen, fill_color, (bx + 1, by + 1, int((bw - 2) * ratio), 10))
                pygame.draw.rect(self.screen, (255, 60, 100), (bx, by, bw, 12), 1)
                nt = get_font(16).render(boss_name, True, WHITE)
                self.screen.blit(nt, (bx + bw // 2 - 40, by + 14))

            # 绘制玩家子弹
            for b in self.bullets:
                bx = b.x - offset_x
                by = b.y
                if -20 < bx < SCREEN_WIDTH + 20:
                    pygame.draw.rect(self.screen, b.color,
                                   pygame.Rect(bx - b.w // 2, by - b.h // 2, b.w, b.h))

            # 绘制敌方子弹
            for b in self.enemy_bullets:
                bx = b.x - offset_x
                by = b.y
                if -20 < bx < SCREEN_WIDTH + 20:
                    for r in [b.w, b.w * 2]:
                        alpha = 60 if r == b.w else 20
                        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*b.color[:3], alpha), (r, r), r)
                        self.screen.blit(s, (int(bx - r), int(by - r)))
                    pygame.draw.circle(self.screen, WHITE, (int(bx), int(by)), b.w // 2)

            # 绘制玩家
            if self.player:
                self.player.draw(self.screen, offset_x)

            # 绘制粒子
            self.particles.draw(self.screen)

            # 如果正在Playing, 绘制HUD
            if self.state == STATE_PLAYING:
                progress = self.player.x if self.player else 0
                total = self.level_gen.length if self.level_gen else 1
                self.hud.draw(self.screen, self.player, self.level,
                            LEVEL_NAMES[self.level - 1] if self.level <= 5 else "")
                # 额外绘制进度条
                bar_w = 150
                bar_h = 8
                bar_x = SCREEN_WIDTH - bar_w - 16
                bar_y = 16
                pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
                if total > 0:
                    fill = min(1.0, progress / total)
                    pygame.draw.rect(self.screen, (0, 200, 255),
                                   (bar_x, bar_y, int(bar_w * fill), bar_h))
                pygame.draw.rect(self.screen, (60, 60, 80), (bar_x, bar_y, bar_w, bar_h), 1)

        elif self.state == STATE_GAME_OVER:
            self.particles.draw(self.screen)
            if self.game_over:
                self.game_over.draw(self.screen)

        elif self.state == STATE_WIN:
            self.particles.draw(self.screen)
            if self.win_screen:
                self.win_screen.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
