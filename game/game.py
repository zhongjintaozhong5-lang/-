"""游戏核心：状态管理、碰撞检测、游戏流程"""

import random
import math
import pygame
from .config import *
from .effects import ParticleSystem, StarField
from .entities import Player, Enemy, BossIronwall, BossPluto, BossVoid, BossMiaohao, PowerUp, Bullet, Wingman
from .levels import WaveManager, LevelProgression
from .ui import HUD, Menu, PauseOverlay, LevelTransition, GameOver


# 游戏状态常量
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_LEVEL_TRANS = 3
STATE_GAME_OVER = 4
STATE_WIN = 5


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = STATE_MENU
        self.frame = 0
        self.high_score = 0

        # 组件
        self.stars = StarField()
        self.particles = ParticleSystem()
        self.player = None
        self.enemies = []
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.boss = None
        self.wave_manager = None
        self.wingmen = []

        # UI
        self.hud = HUD()
        self.menu = Menu()
        self.pause_overlay = PauseOverlay()
        self.level_trans = LevelTransition()
        self.game_over = GameOver()

        # 游戏状态
        self.level = 1
        self.shake = 0
        self.laser_damage_timer = 0
        self.input_pressed = {}  # 用于检测按键按下事件

        # Boss瞄准参考
        self.boss_target = None

    def new_game(self):
        self.level = 1
        self.player = Player()
        self.enemies.clear()
        self.bullets.clear()
        self.enemy_bullets.clear()
        self.powerups.clear()
        self.wingmen.clear()
        self.boss = None
        self.wave_manager = WaveManager(self.level)
        self.particles.clear()
        self.shake = 0
        self.laser_damage_timer = 0
        self.state = STATE_PLAYING

    def restart(self):
        self.new_game()

    def next_level(self):
        if self.level >= 6:
            self.state = STATE_WIN
            self.save_high_score()
            return

        self.level += 1
        self.enemies.clear()
        self.enemy_bullets.clear()
        self.bullets.clear()
        self.powerups.clear()
        self.wingmen.clear()
        self.boss = None
        self.wave_manager = WaveManager(self.level)
        self.player.invincible = 60
        self.state = STATE_LEVEL_TRANS
        self.level_trans.start()

    def save_high_score(self):
        if self.player and self.player.score > self.high_score:
            self.high_score = int(self.player.score)

    def spawn_powerup(self, x, y):
        if random.random() > 0.75:
            return
        types = ["S", "S", "P", "H", "M", "L", "W", "B", "B"]
        ptype = random.choice(types)
        if ptype == "H" and self.player.lives >= PLAYER_MAX_LIVES and self.player.hp >= self.player.max_hp:
            return
        if ptype == "M" and self.player.weapon_level < 4:
            return
        if ptype == "L" and self.player.weapon_level < 4:
            return
        if ptype == "W" and len(self.wingmen) >= 2:
            return  # 最多2架僚机
        if ptype == "B" and self.player.shield >= self.player.shield_max:
            return
        self.powerups.append(PowerUp(x, y, ptype))

    def apply_powerup(self, pu):
        if pu.type == "S":
            self.player.weapon_level = min(4, self.player.weapon_level + 1)
        elif pu.type == "M":
            self.player.missile_count = min(40, self.player.missile_count + 15)
            self.player.weapon_level = max(self.player.weapon_level, 4)
        elif pu.type == "H":
            if self.player.hp < self.player.max_hp:
                self.player.hp += 1
            elif self.player.lives < PLAYER_MAX_LIVES:
                self.player.lives += 1
        elif pu.type == "P":
            self.player.shoot_interval = max(4, self.player.shoot_interval - 1)
        elif pu.type == "L":
            self.player.weapon_level = max(self.player.weapon_level, 5)
            self.player.laser_charges = min(PLAYER_LASER_MAX_CHARGES, self.player.laser_charges + 20)
            self.player.laser_cooldown = 0
        elif pu.type == "W":
            side = 1 if len(self.wingmen) % 2 == 0 else -1
            self.wingmen.append(Wingman(self.player, side))
        elif pu.type == "B":
            self.player.shield = min(self.player.shield_max, self.player.shield + 1)

    def player_death(self):
        self.save_high_score()
        if self.player.lives <= 0:
            self.state = STATE_GAME_OVER

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                key = event.key
                self.input_pressed[key] = True

                if key == pygame.K_ESCAPE:
                    self.running = False

                # 全局按键
                if self.state in (STATE_MENU, STATE_GAME_OVER, STATE_WIN):
                    if key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.new_game()
                elif self.state == STATE_PLAYING:
                    if key == pygame.K_p:
                        self.state = STATE_PAUSED
                elif self.state == STATE_PAUSED:
                    if key in (pygame.K_p, pygame.K_SPACE):
                        self.state = STATE_PLAYING

    def was_pressed(self, key):
        if self.input_pressed.get(key):
            self.input_pressed[key] = False
            return True
        return False

    def update(self):
        self.frame += 1
        self.stars.update()
        self.input_pressed.clear()  # 重置按键状态，由handle_events设置

        # 先处理事件
        self.handle_events()

        # 菜单
        if self.state == STATE_MENU:
            self.menu.update()
            return

        # 关卡过渡
        if self.state == STATE_LEVEL_TRANS:
            self.particles.update()
            done = self.level_trans.update()
            if done:
                self.state = STATE_PLAYING
            return

        # 游戏结束/胜利
        if self.state in (STATE_GAME_OVER, STATE_WIN):
            self.particles.update()
            # 胜利时自动生成庆祝粒子
            if self.state == STATE_WIN and self.frame % 3 == 0:
                x = random.randint(40, WINDOW_WIDTH - 40)
                y = random.randint(40, WINDOW_HEIGHT - 40)
                colors = [(255, 220, 0), (255, 0, 255), (0, 255, 255),
                         (255, 100, 0), (100, 255, 0)]
                self.particles.explode(x, y, 6, colors, 3, 4)
            return

        # 暂停
        if self.state == STATE_PAUSED:
            return

        # ===== 游戏中 =====
        self.particles.update()

        # 屏幕震动衰减
        if self.shake > 0:
            self.shake *= 0.88
            if self.shake < 0.5:
                self.shake = 0

        # 更新玩家
        if self.player and self.player.alive:
            new_bullets, laser_active = self.player.update(pygame.key.get_pressed(), self)
            for b in new_bullets:
                # 设置追踪目标
                if b.homing:
                    # 找最近的敌人
                    closest = None
                    min_d = 400
                    for e in self.enemies:
                        if e.alive:
                            d = math.hypot(e.x - b.x, e.y - b.y)
                            if d < min_d:
                                min_d = d
                                closest = e
                    if self.boss and self.boss.alive:
                        d = math.hypot(self.boss.x - b.x, self.boss.y - b.y)
                        if d < min_d:
                            min_d = d
                            closest = self.boss
                    b.target = closest
                self.bullets.append(b)

            # 尾焰效果
            self.particles.trail(self.player.x, self.player.y + 20, (60, 160, 255))

            # Boss引力场影响
            if self.boss and self.boss.alive and hasattr(self.boss, 'get_gravity_at'):
                gx, gy = self.boss.get_gravity_at(self.player.x, self.player.y)
                self.player.vx += gx
                self.player.vy += gy

            # 穿透激光伤害
            if laser_active:
                self.laser_damage_timer -= 1
                if self.laser_damage_timer <= 0:
                    self.laser_damage_timer = 6
                    laser_rect = pygame.Rect(self.player.x - 3, 0, 6, self.player.y - 15)
                    # 对敌人
                    for e in self.enemies:
                        if e.alive and laser_rect.colliderect(e.get_rect()):
                            e.hp -= 1
                            e.flash = 6
                            self.particles.explode(e.x, e.y, 4, [(255,0,255),(255,200,255)], 2, 2)
                            if e.hp <= 0:
                                e.alive = False
                                self.player.score += int(e.score * LevelProgression.get_level_mult(self.level))
                                self.player.combo += 1
                                self.player.combo_timer = 120
                                self.particles.explode(e.x, e.y, 20, [(255,100,60),(255,170,0),(255,255,255)], 3, 4)
                                self.shake = 3
                                self.spawn_powerup(e.x, e.y)
                                self.enemies.remove(e)
                    # 对Boss
                    if self.boss and self.boss.alive and laser_rect.colliderect(self.boss.get_rect()):
                        if getattr(self.boss, 'laser_immune', False):
                            # 激光免疫，只显示效果不掉血
                            self.particles.explode(self.player.x, self.boss.y, 5, [(200,200,255),(255,255,255)], 2, 3)
                        elif hasattr(self.boss, 'hit_by_bullet'):
                            self.boss.hit_by_bullet(1)
                            self.particles.explode(self.player.x, self.boss.y, 5, [(255,0,255),(255,200,255)], 2, 3)
                        else:
                            self.boss.hp -= 1
                            self.boss.flash = 4
                            self.particles.explode(self.player.x, self.boss.y, 5, [(255,0,255),(255,200,255)], 2, 3)
                        if not self.boss.alive:
                            score_mult = LevelProgression.get_level_mult(self.level)
                            self.player.score += int(self.boss.score * score_mult)
                            self.particles.boss_explode(self.boss.x, self.boss.y)
                            self.shake = 12
                            self.spawn_powerup(self.boss.x - 30, self.boss.y)
                            self.spawn_powerup(self.boss.x + 30, self.boss.y)
                            self.next_level()

        # 僚机更新
        for w in self.wingmen[:]:
            w_bullets = w.update(self.enemies, self.boss)
            for b in w_bullets:
                self.bullets.append(b)
            if not w.alive:
                self.wingmen.remove(w)

        # 波次管理
        if self.wave_manager and not self.boss:
            wave_enemies = self.wave_manager.update()
            if wave_enemies:
                for info in wave_enemies:
                    self.enemies.append(Enemy(info["type"], info["x"], info["y"], self.level))

            # Boss生成
            if self.wave_manager.should_spawn_boss():
                self.wave_manager.boss_spawned = True
                # 清屏
                self.enemies.clear()
                self.boss = BossMiaohao(self.level) if self.level >= 6 else BossPluto(self.level) if self.level >= 5 else BossIronwall(self.level) if self.level >= 4 else BossVoid(self.level)
                self.boss_target = self.player

        # 更新Boss
        if self.boss and self.boss.alive:
            self.boss.update()
            self.boss.shoot_timer -= 1
            if self.boss.shoot_timer <= 0:
                boss_bullets = self.boss.shoot()
                for b in boss_bullets:
                    self.enemy_bullets.append(b)

        # 更新我方子弹
        for i in range(len(self.bullets) - 1, -1, -1):
            b = self.bullets[i]
            b.update()

            # 追踪更新
            if b.homing and b.target and not b.target.alive:
                # 找新目标
                closest = None
                min_d = 400
                for e in self.enemies:
                    if e.alive:
                        d = math.hypot(e.x - b.x, e.y - b.y)
                        if d < min_d:
                            min_d = d
                            closest = e
                if self.boss and self.boss.alive:
                    d = math.hypot(self.boss.x - b.x, self.boss.y - b.y)
                    if d < min_d:
                        min_d = d
                        closest = self.boss
                b.target = closest

            if not b.alive:
                self.bullets.pop(i)
                continue

            b_rect = b.get_rect()
            hit = False

            # 碰撞敌人
            for j in range(len(self.enemies) - 1, -1, -1):
                e = self.enemies[j]
                if not e.alive:
                    self.enemies.pop(j)
                    continue
                if b_rect.colliderect(e.get_rect()):
                    e.hp -= b.damage
                    e.flash = 6
                    hit = True

                    if e.hp <= 0:
                        e.alive = False
                        score_mult = LevelProgression.get_level_mult(self.level)
                        self.player.score += int(e.score * score_mult)
                        self.player.combo += 1
                        self.player.combo_timer = 120
                        self.particles.explode(e.x, e.y, 25,
                            [(255, 100, 60), (255, 170, 0), (255, 255, 255)],
                            4, 5)
                        self.particles.debris(e.x, e.y)
                        self.shake = 4
                        self.spawn_powerup(e.x, e.y)
                        if self.player.combo > 2:
                            self.particles.score_popup(e.x, e.y - 15,
                                f"+{int(e.score * score_mult)}",
                                (255, 220, 50))
                        self.enemies.pop(j)
                    break

            if hit:
                self.bullets.pop(i)
                continue

            # 碰撞Boss
            if self.boss and self.boss.alive and b_rect.colliderect(self.boss.get_rect()):
                # 统一伤害处理（BossIronwall有护盾逻辑）
                if hasattr(self.boss, 'hit_by_bullet'):
                    self.boss.hit_by_bullet(b.damage)
                else:
                    self.boss.hp -= b.damage
                    self.boss.flash = 4
                hit = True
                self.particles.explode(b.x, b.y, 6,
                    [(255, 0, 60), (255, 60, 120), (255, 255, 255)], 2, 3)

                if not self.boss.alive:
                    score_mult = LevelProgression.get_level_mult(self.level)
                    self.player.score += int(self.boss.score * score_mult)
                    self.particles.boss_explode(self.boss.x, self.boss.y)
                    self.shake = 12
                    if self.player.combo > 2:
                        self.particles.score_popup(self.boss.x, self.boss.y - 50,
                            f"+{int(self.boss.score * score_mult)}",
                            (255, 220, 50))
                    self.spawn_powerup(self.boss.x - 30, self.boss.y)
                    self.spawn_powerup(self.boss.x + 30, self.boss.y)
                    self.next_level()
                    return  # next_level清空了列表，退出update

                self.bullets.pop(i)

        # 更新敌人
        for i in range(len(self.enemies) - 1, -1, -1):
            e = self.enemies[i]
            e.update()

            if not e.alive:
                self.enemies.pop(i)
                continue

            # 射击
            if e.can_shoot and e.shoot_timer <= 0:
                e_bullets = e.shoot()
                for eb in e_bullets:
                    self.enemy_bullets.append(eb)

            # 碰撞玩家
            if self.player and self.player.alive:
                if e.get_rect().colliderect(self.player.get_rect()):
                    e.alive = False
                    self.particles.explode(e.x, e.y, 20,
                        [(255, 100, 60), (255, 170, 0), (255, 255, 255)], 3, 4)
                    if self.player.take_damage(1):
                        self.particles.explode(self.player.x, self.player.y, 60,
                            [(60, 140, 255), (140, 220, 255), (255, 255, 255)], 5, 6)
                        self.shake = 10
                        self.player_death()
                    self.enemies.pop(i)

        # 更新敌弹
        for i in range(len(self.enemy_bullets) - 1, -1, -1):
            b = self.enemy_bullets[i]
            b.update()
            if not b.alive:
                self.enemy_bullets.pop(i)
                continue

            if self.player and self.player.alive:
                if b.get_rect().colliderect(self.player.get_rect()):
                    self.particles.explode(b.x, b.y, 8,
                        [(255, 60, 60), (255, 255, 255)], 2, 3)
                    if self.player.take_damage(b.damage):
                        self.particles.explode(self.player.x, self.player.y, 60,
                            [(60, 140, 255), (140, 220, 255), (255, 255, 255)], 5, 6)
                        self.shake = 10
                        self.player_death()
                    self.enemy_bullets.pop(i)

        # 更新道具
        for i in range(len(self.powerups) - 1, -1, -1):
            pu = self.powerups[i]
            pu.update()
            if not pu.alive:
                self.powerups.pop(i)
                continue

            if self.player and self.player.alive:
                if pu.get_rect().colliderect(self.player.get_rect()):
                    self.apply_powerup(pu)
                    info = pu.get_info()
                    self.particles.score_popup(pu.x, pu.y - 10,
                        info["name"], info["color"])
                    self.powerups.pop(i)

        # 苗浩毁灭者 - 吸收场上道具并反击
        if self.boss and self.boss.alive and hasattr(self.boss, 'absorb_powerups'):
            self.boss.absorb_powerups(self.powerups, self.enemy_bullets, self.player)

        # 检查过关条件（BOSS关卡必须击败BOSS才能过关）
        if not self.boss and self.level not in (3, 4, 5, 6):
            if LevelProgression.check_level_up(self.level, self.player.score):
                self.next_level()

    def draw(self):
        # 背景
        self.screen.fill(BLACK)

        # 菜单
        if self.state == STATE_MENU:
            self.stars.draw(self.screen)
            self.menu.draw(self.screen, self.high_score)
            pygame.display.flip()
            return

        # 屏幕震动
        shake_ox = shake_oy = 0
        if self.shake > 0.5:
            shake_ox = random.randint(-int(self.shake), int(self.shake))
            shake_oy = random.randint(-int(self.shake), int(self.shake))

        # 星空
        self.stars.draw(self.screen)

        # 道具
        for pu in self.powerups:
            pu.draw(self.screen)

        # 敌人子弹
        for b in self.enemy_bullets:
            b.draw(self.screen)

        # 敌人
        for e in self.enemies:
            e.draw(self.screen)

        # Boss
        if self.boss and self.boss.alive:
            self.boss.draw(self.screen)

        # 我方子弹
        for b in self.bullets:
            b.draw(self.screen)

        # 粒子
        self.particles.draw(self.screen)

        # 玩家（应用震动）
        if shake_ox or shake_oy:
            self.screen.scroll(shake_ox, shake_oy)

        # 僚机
        for w in self.wingmen:
            w.draw(self.screen)

        if self.player:
            self.player.draw(self.screen)

        if shake_ox or shake_oy:
            self.screen.scroll(-shake_ox, -shake_oy)

        # HUD
        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_LEVEL_TRANS):
            self.hud.draw(self.screen, self.player, self.level, self.high_score)

        # 覆盖层
        if self.state == STATE_PAUSED:
            self.pause_overlay.draw(self.screen)
        elif self.state == STATE_LEVEL_TRANS:
            self.level_trans.draw(self.screen, self.level, self.player.score)
        elif self.state == STATE_GAME_OVER:
            self.game_over.draw(self.screen,
                               self.player.score if self.player else 0,
                               self.level, self.high_score, False)
        elif self.state == STATE_WIN:
            self.game_over.draw(self.screen,
                               self.player.score if self.player else 0,
                               self.level, self.high_score, True)

        # 更新显示
        pygame.display.flip()

    def run(self):
        import traceback
        while self.running:
            try:
                self.update()
                self.draw()
                self.clock.tick(FPS)
            except Exception as e:
                print(f"游戏循环错误: {e}")
                traceback.print_exc()
                self.running = False

        pygame.quit()
