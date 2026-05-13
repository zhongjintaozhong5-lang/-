"""游戏界面：菜单、HUD、关卡过渡、游戏结束等"""

import math
import random
import pygame
from .config import *

class HUD:
    """游戏内HUD"""
    def __init__(self):
        self.font_small = get_font(20)
        self.font_med = get_font(28)
        self.font_large = get_font(48)
        self.combo_font = get_font(36)

    def draw(self, surface, player, level, high_score):
        # 分数
        score_text = self.font_large.render(f"{int(player.score)}", True, (255, 255, 255))
        surface.blit(score_text, (18, 12))

        # 关卡信息
        lv_color = (100, 160, 255)
        lv_text = self.font_small.render(f"第{level}关", True, lv_color)
        lv_rect = lv_text.get_rect(topright=(WINDOW_WIDTH - 18, 12))
        surface.blit(lv_text, lv_rect)

        name_text = self.font_small.render(LEVEL_NAMES[level - 1], True, (140, 180, 255))
        name_rect = name_text.get_rect(topright=(WINDOW_WIDTH - 18, 32))
        surface.blit(name_text, name_rect)

        # 生命图标
        for i in range(player.lives):
            x = 18 + i * 24
            y = 56
            pygame.draw.polygon(surface, (255, 60, 140),
                              [(x, y), (x - 8, y + 12), (x + 8, y + 12)])

        # HP条
        if player.hp > 0:
            hp_w = 90
            pygame.draw.rect(surface, (30, 30, 50),
                           pygame.Rect(18, 76, hp_w, 7))
            hp_color = (60, 255, 100) if player.hp > 1 else (255, 60, 60)
            pygame.draw.rect(surface, hp_color,
                           pygame.Rect(18, 76, hp_w * (player.hp / player.max_hp), 7))

        # 武器等级
        wpn_color = (0, 220, 255)
        wpn_text = self.font_small.render(f"武器 Lv.{player.weapon_level}", True, wpn_color)
        surface.blit(wpn_text, (18, 90))

        # 导弹能量条
        if player.missile_count > 0:
            ms_w = 100
            pygame.draw.rect(surface, (30, 30, 50),
                           pygame.Rect(WINDOW_WIDTH - 118, 56, ms_w, 5))
            pygame.draw.rect(surface, (255, 100, 0),
                           pygame.Rect(WINDOW_WIDTH - 118, 56,
                                     ms_w * (player.missile_count / 40), 5))
            ms_text = self.font_small.render("导弹", True, (255, 140, 0))
            ms_rect = ms_text.get_rect(right=(WINDOW_WIDTH - 18), top=62)
            surface.blit(ms_text, ms_rect)

        # 激光能量条
        if player.laser_charges > 0:
            lw = 100
            pygame.draw.rect(surface, (30, 30, 50),
                           pygame.Rect(WINDOW_WIDTH - 118, 72, lw, 5))
            pygame.draw.rect(surface, (255, 0, 255),
                           pygame.Rect(WINDOW_WIDTH - 118, 72,
                                     lw * (player.laser_charges / PLAYER_LASER_MAX_CHARGES), 5))
            las_text = self.font_small.render("激光", True, (255, 0, 255))
            las_rect = las_text.get_rect(right=(WINDOW_WIDTH - 18), top=78)
            surface.blit(las_text, las_rect)

        # Combo
        if player.combo > 2:
            alpha = min(1, player.combo_timer / 30)
            combo_text = self.combo_font.render(f"{player.combo} COMBO!", True, (255, 220, 50))
            combo_text.set_alpha(int(alpha * 255))
            combo_rect = combo_text.get_rect(center=(WINDOW_WIDTH // 2, 52))
            surface.blit(combo_text, combo_rect)

        # 最高分
        hs_text = self.font_small.render(f"最高: {high_score}", True, (80, 100, 130))
        surface.blit(hs_text, (18, 108))


class Menu:
    """主菜单"""
    def __init__(self):
        self.phase = 0
        self.title_particles = []
        for _ in range(20):
            self.title_particles.append({
                "x": random.uniform(0, WINDOW_WIDTH),
                "y": random.uniform(0, WINDOW_HEIGHT),
                "size": random.uniform(1, 3),
                "speed": random.uniform(0.2, 0.8),
                "angle": random.uniform(0, math.pi * 2),
                "color": (random.randint(100, 200),
                         random.randint(150, 220),
                         random.randint(200, 255))
            })

    def update(self):
        self.phase += 0.02
        for p in self.title_particles:
            p["x"] += math.cos(p["angle"]) * p["speed"]
            p["y"] += math.sin(p["angle"]) * p["speed"]
            if p["x"] < 0 or p["x"] > WINDOW_WIDTH:
                p["angle"] = math.pi - p["angle"]
            if p["y"] < 0 or p["y"] > WINDOW_HEIGHT:
                p["angle"] = -p["angle"]

    def draw(self, surface, high_score):
        # 浮动粒子
        for p in self.title_particles:
            alpha = int(60 + 40 * math.sin(self.phase * 2 + p["x"] * 0.01))
            c = p["color"]
            pygame.draw.circle(surface, (*c, alpha),
                             (int(p["x"]), int(p["y"])), int(p["size"]))

        # 标题光晕
        glow = pygame.Surface((400, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (40, 100, 255, 30),
                          pygame.Rect(50, 20, 300, 80))
        surface.blit(glow, (WINDOW_WIDTH // 2 - 200, 140))

        # 标题 - 阴影层
        shadow_font = get_font(72)
        shadow = shadow_font.render("银翼出击", True, (20, 60, 140))
        shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + 3, 173))
        surface.blit(shadow, shadow_rect)

        # 标题 - 主层
        title_font = get_font(72)
        title = title_font.render("银翼出击", True, (60, 180, 255))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 170))
        surface.blit(title, title_rect)

        # 标题装饰线
        for i, offset in enumerate([-3, 0, 3]):
            c = (40 + i * 30, 120 + i * 30, 255)
            sub = get_font(72 - i * 2)
            t = sub.render("银翼出击", True, c)
            r = t.get_rect(center=(WINDOW_WIDTH // 2, 170 + offset))
            surface.blit(t, r)

        # 副标题
        sub_font = get_font(22)
        subtitle = sub_font.render("— 战机射击游戏 —", True, (120, 160, 220))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, 215))
        surface.blit(subtitle, subtitle_rect)

        # 飞机装饰
        px, py = WINDOW_WIDTH // 2, 290
        glow_size = 60 + 10 * math.sin(self.phase * 2)
        glow_s = pygame.Surface((int(glow_size * 2), int(glow_size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(glow_s, (50, 120, 255, 25),
                         (int(glow_size), int(glow_size)), int(glow_size))
        surface.blit(glow_s, (px - int(glow_size), py - int(glow_size)))

        # 飞机绘制
        plane_pts = [(px, py - 28), (px - 14, py - 6), (px - 22, py + 10),
                     (px - 8, py + 18), (px, py + 8), (px + 8, py + 18),
                     (px + 22, py + 10), (px + 14, py - 6)]
        pygame.draw.polygon(surface, (50, 130, 230), plane_pts)
        pygame.draw.polygon(surface, (80, 180, 255), plane_pts, 2)
        pygame.draw.ellipse(surface, (140, 230, 255),
                          pygame.Rect(px - 5, py - 10, 10, 14))

        # 引擎尾焰
        fl = 10 + math.sin(self.phase * 4) * 5
        pygame.draw.polygon(surface, (255, 140, 0),
                          [(px - 6, py + 18), (px, py + 18 + fl), (px + 6, py + 18)])

        # 闪烁提示
        blink = 0.5 + 0.5 * math.sin(self.phase * 3)
        if blink > 0.3:
            start_font = get_font(26)
            start_text = start_font.render("按 Enter 或 空格 开始游戏", True,
                                          (200, 220, 255))
            start_text.set_alpha(int(200 * blink))
            start_rect = start_text.get_rect(center=(WINDOW_WIDTH // 2, 420))
            surface.blit(start_text, start_rect)

        # 操作说明
        instructions = [
            ("方向键/WASD", "移动战机"),
            ("空格/Z", "射击（可按住连发）"),
            ("P", "暂停游戏"),
        ]
        instr_font = get_font(20)
        title_font_small = get_font(18)
        title_small = title_font_small.render("操作说明", True, (120, 150, 200))
        title_small_rect = title_small.get_rect(center=(WINDOW_WIDTH // 2, 490))
        surface.blit(title_small, title_small_rect)

        for i, (key, desc) in enumerate(instructions):
            key_text = instr_font.render(key, True, (180, 200, 230))
            surface.blit(key_text, (WINDOW_WIDTH // 2 - 100, 518 + i * 30))
            desc_text = instr_font.render(desc, True, (140, 160, 190))
            surface.blit(desc_text, (WINDOW_WIDTH // 2 + 10, 518 + i * 30))

        # 难度说明
        diff_font = get_font(18)
        diff_text = diff_font.render("5关渐进难度 · 从新手到王牌", True, (100, 130, 170))
        diff_rect = diff_text.get_rect(center=(WINDOW_WIDTH // 2, 620))
        surface.blit(diff_text, diff_rect)

        # 关卡列表
        lv_font = get_font(16)
        for i, (name, desc) in enumerate(zip(LEVEL_NAMES, LEVEL_DESCS)):
            color = (80, 120, 180) if i > 0 else (100, 200, 255)
            lv_text = lv_font.render(f"第{i+1}关 {name} - {desc}", True, color)
            lv_rect = lv_text.get_rect(center=(WINDOW_WIDTH // 2, 650 + i * 22))
            surface.blit(lv_text, lv_rect)

        # 最高分
        if high_score > 0:
            hs_font = get_font(22)
            hs_text = hs_font.render(f"最高分: {high_score}", True, (255, 200, 50))
            hs_rect = hs_text.get_rect(center=(WINDOW_WIDTH // 2, 770))
            surface.blit(hs_text, hs_rect)


class PauseOverlay:
    def draw(self, surface):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        font = get_font(56)
        text = font.render("暂停", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        surface.blit(text, text_rect)

        font2 = get_font(24)
        text2 = font2.render("按 P 或 空格 继续", True, (160, 180, 220))
        text2_rect = text2.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
        surface.blit(text2, text2_rect)


class LevelTransition:
    def __init__(self):
        self.timer = 0

    def start(self):
        self.timer = 120

    def update(self):
        if self.timer > 0:
            self.timer -= 1
        return self.timer <= 0

    def draw(self, surface, level, score):
        if self.timer <= 0:
            return True

        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 10, 160))
        surface.blit(overlay, (0, 0))

        progress = 1 - self.timer / 120

        if progress > 0.2:
            # 关卡数字 - 大
            big_font = get_font(72)
            glow = big_font.render(f"第 {level} 关", True, (40, 100, 255))
            glow_rect = glow.get_rect(center=(WINDOW_WIDTH // 2 + 2, WINDOW_HEIGHT // 2 - 52))
            surface.blit(glow, glow_rect)

            main = big_font.render(f"第 {level} 关", True, (100, 200, 255))
            main_rect = main.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            surface.blit(main, main_rect)

            # 关卡名
            name_font = get_font(36)
            name = name_font.render(LEVEL_NAMES[level - 1], True, (180, 220, 255))
            name_rect = name.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10))
            surface.blit(name, name_rect)

            # 描述
            desc_font = get_font(20)
            desc = desc_font.render(LEVEL_DESCS[level - 1], True, (140, 170, 210))
            desc_rect = desc.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 45))
            surface.blit(desc, desc_rect)

            # 分数
            score_font = get_font(22)
            score_text = score_font.render(f"当前分数: {int(score)}", True, (200, 200, 200))
            score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 85))
            surface.blit(score_text, score_rect)

        return False


class GameOver:
    def draw(self, surface, score, level, high_score, is_win=False):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        if is_win:
            # 胜利
            title_font = get_font(60)
            shadow = title_font.render("恭喜通关!", True, (180, 150, 0))
            shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + 3, WINDOW_HEIGHT // 2 - 83))
            surface.blit(shadow, shadow_rect)
            title = title_font.render("恭喜通关!", True, (255, 220, 50))
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
            surface.blit(title, title_rect)

            sub = get_font(22)
            sub_text = sub.render("你已成为王牌飞行员！", True, (200, 200, 255))
            sub_rect = sub_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40))
            surface.blit(sub_text, sub_rect)
        else:
            # 失败
            title_font = get_font(56)
            title = title_font.render("游戏结束", True, (255, 60, 60))
            title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
            surface.blit(title, title_rect)

        # 分数
        score_font = get_font(36)
        score_text = score_font.render(f"最终分数: {int(score)}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(score_text, score_rect)

        # 新纪录
        if score >= high_score and score > 0:
            record_font = get_font(28)
            record = record_font.render("★ 新纪录! ★", True, (255, 220, 50))
            record_rect = record.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
            surface.blit(record, record_rect)

        # 关卡信息
        info_font = get_font(22)
        info = info_font.render(f"到达关卡: 第{level}关 · {LEVEL_NAMES[level-1]}",
                               True, (180, 180, 200))
        info_rect = info.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 75))
        surface.blit(info, info_rect)

        # 重新开始
        restart_font = get_font(24)
        restart = restart_font.render("按 Enter 或 空格 重新开始", True, (160, 180, 220))
        restart_rect = restart.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 115))
        surface.blit(restart, restart_rect)

        # 最高分
        hs_font = get_font(20)
        hs_text = hs_font.render(f"最高分: {high_score}", True, (120, 140, 170))
        hs_rect = hs_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 150))
        surface.blit(hs_text, hs_rect)
