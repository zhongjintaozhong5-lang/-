"""关卡生成器：程序化生成平台、敌人、收集品"""
import math
import random
import pygame
from .config import *

class Platform:
    def __init__(self, x, y, w, h, ptype="normal"):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = ptype  # normal, moving, crumbling
        self.alive = True
        self.timer = 0
        self.start_x = x
        self.start_y = y
        self.move_dir = 1
        self.crumble_timer = 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self, scroll_speed):
        self.x -= scroll_speed
        if self.type == "moving":
            self.timer += 0.03
            self.y = self.start_y + 40 * math.sin(self.timer * 1.5)
            self.x = self.start_x + 20 * math.sin(self.timer * 0.8) - self._get_scroll_offset(0)
        # 移出屏幕
        if self.x + self.w < -100:
            self.alive = False

    def _get_scroll_offset(self, base):
        return 0  # 由外部处理偏移

    def draw(self, surface, offset_x):
        if not self.alive:
            return
        px = int(self.x - offset_x)
        py = int(self.y)
        if px + self.w < -50 or px > SCREEN_WIDTH + 50:
            return

        if self.type == "normal":
            color = (60, 80, 120)
            light = (80, 100, 150)
            border = (40, 55, 85)
        elif self.type == "moving":
            color = (80, 60, 140)
            light = (110, 80, 170)
            border = (55, 40, 100)
        else:
            color = (120, 60, 40)
            light = (150, 80, 55)
            border = (85, 40, 25)

        # 主体
        rect = pygame.Rect(px, py, self.w, self.h)
        pygame.draw.rect(surface, color, rect)
        # 顶部高光
        pygame.draw.line(surface, light, (px, py), (px + self.w, py), 2)
        # 边框
        pygame.draw.rect(surface, border, rect, 1)
        # 表面纹理
        for i in range(0, self.w, 20):
            pygame.draw.line(surface, border, (px + i, py), (px + i, py + self.h), 1)


class LevelGenerator:
    """程序化关卡生成"""

    def __init__(self, level_num):
        self.level = level_num
        self.length = LEVEL_LENGTHS[level_num - 1]
        self.scroll_speed = min(MAX_SCROLL_SPEED, BASE_SCROLL_SPEED + (level_num - 1) * 0.8)
        self.platforms = []
        self.enemies = []
        self.powerups = []
        self.boss_def = BOSS_CONFIG.get(level_num)
        self.boss_spawned = False
        self.boss_x = self.length - 400
        self.completed = False

        self._generate()

    def _generate(self):
        """生成关卡内容"""
        seed = 42 + self.level * 7
        rng = random.Random(seed)

        # 地面平台
        ground_y = SCREEN_HEIGHT - 40
        last_x = 0

        # 连续地面（无断头）
        self.platforms.append(Platform(0, ground_y, 400, 40, "normal"))

        segment_length = 250 + self.level * 30
        plat_count = self.length // segment_length

        for i in range(plat_count):
            plat_w = rng.randint(300, 500)

            # 地面平台（无缝连接）
            ground_plat = Platform(last_x, ground_y, plat_w, 20, "normal")
            self.platforms.append(ground_plat)

            # 上层奖励路线（跳上去有额外道具和敌人）
            if i > 1 and rng.random() < 0.4 + self.level * 0.05:
                up_y = ground_y - rng.randint(90, 160)
                up_w = rng.randint(80, 160)
                up_x = last_x + rng.randint(20, max(40, plat_w - up_w - 20))
                self.platforms.append(Platform(up_x, up_y, up_w, 16, "normal"))

                # 上层敌人
                if rng.random() < 0.5:
                    etype = "flyer" if rng.random() < 0.5 else "walker"
                    self.enemies.append({
                        "x": up_x + up_w // 2,
                        "y": up_y - 20,
                        "type": etype
                    })
                # 上层道具
                if rng.random() < 0.7:
                    self.powerups.append({
                        "x": up_x + up_w // 2,
                        "y": up_y - 40,
                        "type": "weapon" if rng.random() < 0.4 else "battery"
                    })

            # 地面敌人
            if rng.random() < 0.4 + self.level * 0.05:
                self.enemies.append({
                    "x": last_x + plat_w // 2,
                    "y": ground_y - 20,
                    "type": "walker" if rng.random() < 0.6 else "turret"
                })

            # 空中敌人
            if rng.random() < 0.25 + self.level * 0.03:
                fx = last_x + rng.randint(0, plat_w)
                fy = rng.randint(100, 250)
                self.enemies.append({"x": fx, "y": fy, "type": "flyer"})

            # 地面道具
            if rng.random() < 0.6:
                self.powerups.append({
                    "x": last_x + plat_w // 2,
                    "y": ground_y - 50,
                    "type": "battery"
                })
            if rng.random() < 0.3:
                self.powerups.append({
                    "x": last_x + plat_w // 2 + 40,
                    "y": ground_y - 50,
                    "type": "weapon"
                })

            last_x += plat_w

        # 终点安全平台（Boss战区域）
        self.platforms.append(Platform(self.boss_x - 50, ground_y, 500, 40, "normal"))
        self.enemies.append({
            "x": self.boss_x,
            "y": 60,
            "type": "boss"
        })

    def update(self):
        """更新平台位置（卷轴移动）"""
        for p in self.platforms[:]:
            p.update(self.scroll_speed)
            if not p.alive:
                self.platforms.remove(p)

    def is_completed(self, player_x):
        return player_x >= self.length

    def get_start_x(self):
        return 0
