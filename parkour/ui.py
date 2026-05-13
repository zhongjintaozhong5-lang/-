"""跑酷游戏界面"""
import math
import pygame
from .config import *
from game.config import get_font

class TitleScreen:
    def __init__(self):
        self.title_font = get_font(48, bold=True)
        self.sub_font = get_font(20)
        self.info_font = get_font(16)
        self.phase = 0
        self.alpha = 0
        self.state = "fade_in"

    def update(self):
        self.phase += 0.02

    def draw(self, surface):
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT

        # 背景
        surface.fill(BLACK)
        # 星空
        for i in range(60):
            sx = (i * 37 + 13) % w
            sy = (i * 53 + 7) % h
            b = 30 + (math.sin(self.phase * 2 + i) * 0.5 + 0.5) * 40
            pygame.draw.circle(surface, (int(b), int(b), int(b + 10)), (sx, sy), 1)

        # 标题
        title = self.title_font.render("银翼出击：逃亡", True, (100, 200, 255))
        title_rect = title.get_rect(center=(w // 2, h // 2 - 80))
        # 发光效果
        for r in range(10, 0, -2):
            glow = self.title_font.render("银翼出击：逃亡", True, (30, 80, 120, 30 // r))
            gr = glow.get_rect(center=(w // 2, h // 2 - 80))
            surface.blit(glow, gr)
        surface.blit(title, title_rect)

        # 副标题
        sub = self.sub_font.render("A PARKOUR SHOOTER", True, (150, 150, 180))
        surface.blit(sub, sub.get_rect(center=(w // 2, h // 2 - 30)))

        # 装饰线
        line_color = (60, 120, 180)
        pygame.draw.line(surface, line_color, (w // 2 - 150, h // 2 - 10),
                        (w // 2 + 150, h // 2 - 10), 1)

        # 操作提示
        keys_info = [
            "A/D 或 ←/→  移动",
            "Space / W / ↑  跳跃（空中再按 = 二段跳）",
            "Z  射击",
        ]
        for i, txt in enumerate(keys_info):
            kt = self.info_font.render(txt, True, (160, 160, 180))
            surface.blit(kt, kt.get_rect(center=(w // 2, h // 2 + 20 + i * 24)))

        # 闪烁提示
        blink = (math.sin(self.phase * 3) + 1) * 0.5
        alpha = int(180 + 75 * blink)
        start_text = self.sub_font.render("按 Space 开始游戏", True, (255, 255, 255))
        start_text.set_alpha(alpha)
        surface.blit(start_text, start_text.get_rect(center=(w // 2, h // 2 + 140)))

        # 版本信息
        ver = self.info_font.render("基于《银翼出击》世界观", True, (80, 80, 100))
        surface.blit(ver, ver.get_rect(center=(w // 2, h - 30)))


class HUD:
    def __init__(self):
        self.font_l = get_font(32)
        self.font_m = get_font(20)
        self.font_s = get_font(16)

    def draw(self, surface, player, level, level_name):
        # 分数
        score_text = self.font_l.render(f"{player.score}", True, WHITE)
        surface.blit(score_text, (16, 12))

        # 关卡
        lv_text = self.font_s.render(f"第{level}关 · {level_name}", True, (100, 180, 255))
        surface.blit(lv_text, (16, 48))

        # 生命（心形图标用三角代替）
        for i in range(player.lives):
            x = 16 + i * 22
            y = 72
            pygame.draw.polygon(surface, (255, 60, 140),
                              [(x, y + 6), (x - 7, y - 2), (x + 7, y - 2)])

        # HP条
        if player.hp > 0:
            hp_x = 16
            hp_y = 94
            hp_w = 80
            pygame.draw.rect(surface, (30, 30, 50), (hp_x, hp_y, hp_w, 6))
            c = GREEN if player.hp > 1 else RED
            pygame.draw.rect(surface, c, (hp_x, hp_y, hp_w * (player.hp / player.max_hp), 6))

        # 武器等级
        wpn = self.font_s.render(f"武器 Lv.{player.weapon_level}", True, CYAN)
        surface.blit(wpn, (16, 108))

        # 右上角距离进度
        # (由game传入当前距离)
        self._draw_progress(surface)

    def _draw_progress(self, surface, progress=0, total=1):
        bar_w = 150
        bar_h = 8
        bar_x = SCREEN_WIDTH - bar_w - 16
        bar_y = 16
        pygame.draw.rect(surface, (30, 30, 50), (bar_x, bar_y, bar_w, bar_h))
        if total > 0:
            fill = min(1.0, progress / total)
            pygame.draw.rect(surface, (0, 200, 255), (bar_x, bar_y, int(bar_w * fill), bar_h))
        pygame.draw.rect(surface, (60, 60, 80), (bar_x, bar_y, bar_w, bar_h), 1)
        pct_text = self.font_s.render(f"{int(progress/total*100) if total > 0 else 0}%", True, (180, 180, 200))
        surface.blit(pct_text, (bar_x + bar_w // 2 - 20, bar_y + bar_h + 4))


class LevelIntro:
    def __init__(self, level):
        self.level = level
        self.timer = 120  # 2秒
        self.font_t = get_font(40, bold=True)
        self.font_s = get_font(22)
        self.font_d = get_font(16)

    def update(self):
        self.timer -= 1
        return self.timer > 0

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_t.render(LEVEL_NAMES[self.level - 1], True, (100, 200, 255))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))

        subtitle = self.font_s.render(LEVEL_TITLES[self.level - 1], True, (160, 160, 200))
        surface.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 5)))

        desc = self.font_d.render(LEVEL_DESCS[self.level - 1], True, (140, 140, 160))
        surface.blit(desc, desc.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35)))


class GameOver:
    def __init__(self, score, level):
        self.score = score
        self.level = level
        self.timer = 0
        self.font_b = get_font(48, bold=True)
        self.font_m = get_font(24)
        self.font_s = get_font(18)

    def update(self):
        self.timer += 1

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # 标题
        title = self.font_b.render("任务失败", True, (255, 80, 80))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))

        # 信息
        info = self.font_m.render(f"抵达第{self.level}关 · 得分 {self.score}", True, (180, 180, 200))
        surface.blit(info, info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        if self.timer > 60:
            blink = (math.sin(self.timer * 0.05) + 1) * 0.5
            restart = self.font_s.render("按 Space 重新开始", True, (200, 200, 200))
            restart.set_alpha(int(150 + 105 * blink))
            surface.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60)))


class WinScreen:
    def __init__(self, score):
        self.score = score
        self.timer = 0
        self.font_b = get_font(40, bold=True)
        self.font_m = get_font(24)
        self.font_s = get_font(18)

    def update(self):
        self.timer += 1

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 5, 20, 200))
        surface.blit(overlay, (0, 0))

        title = self.font_b.render("信号已接通", True, (100, 200, 255))
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))

        sub = self.font_m.render("救援即将抵达。银翼号会再次起飞。", True, (160, 180, 220))
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)))

        score_text = self.font_m.render(f"最终得分：{self.score}", True, (255, 220, 60))
        surface.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20)))

        if self.timer > 90:
            restart = self.font_s.render("按 Space 再来一次", True, (180, 180, 200))
            surface.blit(restart, restart.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70)))
