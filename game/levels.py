"""关卡管理：敌人生成、波次控制"""

import random
import math
from .config import WINDOW_WIDTH, ENEMY_TYPES, LEVEL_SCORES

class WaveManager:
    def __init__(self, level):
        self.level = level
        self.timer = 0
        self.wave_count = 0
        self.enemies_spawned = 0
        self.boss_spawned = False
        self.can_spawn_miniboss = True

    def get_spawn_interval(self):
        base = {1: 85, 2: 65, 3: 50, 4: 38, 5: 28, 6: 20}.get(self.level, 50)
        return max(15, base - self.wave_count * 0.3)

    def get_enemy_types(self):
        if self.level == 1:
            return ["scout"]
        elif self.level == 2:
            return ["scout", "fighter"]
        elif self.level == 3:
            return ["scout", "fighter", "runner"]
        elif self.level == 4:
            return ["scout", "fighter", "runner", "tank"]
        elif self.level >= 5:
            return ["scout", "fighter", "runner", "tank"]
        return ["scout"]

    def generate_formation(self, primary_type):
        """生成编队阵型"""
        types = self.get_enemy_types()
        count = random.randint(2, min(5, 2 + self.level))

        # 随机阵型
        formation = random.choice(["line", "v", "arc", "double"])
        enemies = []

        for i in range(count):
            # 混入更强敌人
            etype = primary_type
            if self.level >= 3 and random.random() < 0.2:
                etype = random.choice(types)

            spacing = 45
            if formation == "line":
                ex = WINDOW_WIDTH // 2 + (i - count / 2) * spacing
                ey = -30 - i * 18
            elif formation == "v":
                offset = (i - count / 2) * spacing * 0.7
                ex = WINDOW_WIDTH // 2 + offset
                ey = -30 - abs(offset) * 0.4
            elif formation == "arc":
                angle = (i / count) * math.pi - math.pi / 2
                ex = WINDOW_WIDTH // 2 + math.cos(angle) * 110
                ey = -30 + math.sin(angle) * 50 + 40
            else:  # double
                side = 1 if i % 2 == 0 else -1
                row = i // 2
                ex = WINDOW_WIDTH // 2 + side * (40 + row * 30)
                ey = -30 - row * 25

            enemies.append({
                "type": etype,
                "x": max(28, min(WINDOW_WIDTH - 28, ex)),
                "y": ey
            })
        return enemies

    def update(self):
        """更新波次，返回生成的敌人列表或None"""
        self.timer += 1
        interval = self.get_spawn_interval()

        if self.timer >= interval:
            self.timer = 0
            self.wave_count += 1
            self.enemies_spawned += 1

            # 小Boss事件
            if (self.level >= 3 and self.can_spawn_miniboss and
                self.wave_count % 6 == 0 and self.wave_count > 3):
                self.can_spawn_miniboss = False
                return [{"type": "miniboss", "x": WINDOW_WIDTH // 2, "y": -40}]

            # 每4波重置小Boss冷却
            if self.wave_count % 4 == 0:
                self.can_spawn_miniboss = True

            # 普通编队
            types = self.get_enemy_types()
            primary = random.choice(types)
            return self.generate_formation(primary)

        return None

    def should_spawn_boss(self):
        """是否应该生成Boss"""
        threshold = {1: 999, 2: 999, 3: 20, 4: 18, 5: 14, 6: 16}
        req = threshold.get(self.level, 999)
        return self.enemies_spawned >= req and not self.boss_spawned


class LevelProgression:
    """管理关卡间过渡和状态"""

    @staticmethod
    def check_level_up(level, score):
        """检查是否达到下一关条件"""
        if level >= 6:
            return False
        return score >= LEVEL_SCORES[level]

    @staticmethod
    def get_level_mult(level):
        """关卡难度倍率"""
        return 1 + (level - 1) * 0.12
