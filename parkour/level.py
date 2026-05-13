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

        # 地面平台（每隔一段距离放置）
        ground_y = SCREEN_HEIGHT - 40
        last_x = 0

        # 起始安全平台
        self.platforms.append(Platform(0, ground_y, 200, 40, "normal"))

        segment_length = 400 + self.level * 50
        plat_count = self.length // segment_length

        for i in range(plat_count):
            seg_start = last_x + segment_length

            # 地面间隙（随关卡增大）
            gap = rng.randint(40, 60 + self.level * 15)
            gap = min(gap, 180)

            # 平台配置
            plat_w = rng.randint(120, 280 - self.level * 10)
            plat_w = max(60, plat_w)

            # 高度变化
            if i % 3 == 0:
                y = ground_y - rng.randint(40, 100)
            elif i % 3 == 1:
                y = ground_y - rng.randint(80, 160)
            else:
                y = ground_y

            # 平台类型
            ptype = "normal"
            if self.level >= 3 and i > 2 and rng.random() < 0.25:
                ptype = "moving" if rng.random() < 0.6 else "crumbling"

            plat = Platform(seg_start + gap, y, plat_w, 20, ptype)
            self.platforms.append(plat)

            # 上层小平台（跳跃路线）
            if i > 0 and rng.random() < 0.5 + self.level * 0.05:
                up_y = y - rng.randint(90, 180)
                up_w = rng.randint(50, 120)
                up_plat = Platform(seg_start + gap + 30, up_y, up_w, 16, "normal")
                self.platforms.append(up_plat)

                # 上层平台的敌人
                if rng.random() < 0.4 + self.level * 0.05:
                    etype = "walker" if rng.random() < 0.6 else "flyer"
                    self.enemies.append({
                        "x": up_plat.x + up_w // 2,
                        "y": up_plat.y - 20,
                        "type": etype
                    })

            # 地面敌人
            if rng.random() < 0.3 + self.level * 0.05:
                etype = "walker"
                self.enemies.append({
                    "x": seg_start + gap + plat_w // 2,
                    "y": y - 20,
                    "type": etype
                })

            # 空中敌人
            if rng.random() < 0.2 + self.level * 0.05:
                self.enemies.append({
                    "x": seg_start + gap + plat_w // 2,
                    "y": rng.randint(80, 250),
                    "type": "flyer"
                })

            # 炮台
            if self.level >= 2 and rng.random() < 0.15 + self.level * 0.02:
                self.enemies.append({
                    "x": seg_start + gap + plat_w // 2,
                    "y": ground_y - 40,
                    "type": "turret"
                })

            # 收集道具
            if rng.random() < 0.3:
                self.powerups.append({
                    "x": seg_start + gap + plat_w // 2,
                    "y": y - 60,
                    "type": "battery"
                })
            if rng.random() < 0.15 and self.level > 1:
                self.powerups.append({
                    "x": seg_start + gap + plat_w // 2,
                    "y": y - 100,
                    "type": "weapon"
                })

            last_x = seg_start + gap + plat_w

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
