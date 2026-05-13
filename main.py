#!/usr/bin/env python3
"""银翼出击 - 战机射击游戏 启动入口"""
import sys, os, traceback, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def show_mode_menu(screen):
    """显示模式选择菜单，返回选择的模式名称"""
    import pygame
    from game.config import get_font, BLACK, WHITE, CYAN, WINDOW_WIDTH, WINDOW_HEIGHT

    clock = pygame.time.Clock()
    phase = 0
    selected = 0
    modes = [
        ("经典模式", "竖屏卷轴射击 · 6关 · 4大Boss"),
        ("跑酷模式", "横版跑酷射击 · 5关 · 全新剧情"),
    ]

    while True:
        phase += 0.03
        screen.fill(BLACK)

        # 星空
        for i in range(40):
            sx = (i * 31 + 7) % WINDOW_WIDTH
            sy = (i * 47 + 13) % WINDOW_HEIGHT
            b = 20 + (math.sin(phase * 2 + i) * 0.5 + 0.5) * 30
            pygame.draw.circle(screen, (int(b), int(b), int(b + 10)), (sx, sy), 1)

        # 标题
        title_font = get_font(44, bold=True)
        title = title_font.render("银翼出击", True, (100, 200, 255))
        screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, 120)))
        sub = get_font(20).render("SILVER WING STRIKE", True, (120, 120, 150))
        screen.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, 165)))

        # 模式选择
        for i, (name, desc) in enumerate(modes):
            y = 300 + i * 120
            color = CYAN if i == selected else (120, 120, 140)
            bg_color = (30, 50, 80) if i == selected else (15, 15, 30)

            box = pygame.Rect(WINDOW_WIDTH // 2 - 160, y - 30, 320, 80)
            pygame.draw.rect(screen, bg_color, box, border_radius=8)
            if i == selected:
                glow = math.sin(phase * 3) * 0.5 + 0.5
                pygame.draw.rect(screen, (*CYAN[:3], int(40 + 30 * glow)), box, 2, border_radius=8)

            ft = get_font(28, bold=(i == selected))
            nt = ft.render(name, True, color)
            screen.blit(nt, nt.get_rect(center=(WINDOW_WIDTH // 2, y - 5)))

            dt = get_font(14).render(desc, True, (140, 140, 160))
            screen.blit(dt, dt.get_rect(center=(WINDOW_WIDTH // 2, y + 22)))

        # 操作提示
        hint = get_font(16).render("↑↓ 选择 · Enter 确认", True, (100, 100, 120))
        screen.blit(hint, hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 60)))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(modes)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(modes)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return modes[selected][0]

        clock.tick(60)


def main():
    import pygame
    from game.config import TITLE, BLACK

    pygame.init()
    pygame.mixer.init()

    # 先选择模式
    temp_screen = pygame.display.set_mode((540, 780))
    pygame.display.set_caption(TITLE)

    # 图标
    try:
        icon = pygame.Surface((32, 32))
        icon.fill(BLACK)
        pygame.draw.polygon(icon, (50, 130, 230),
                          [(16, 2), (8, 12), (4, 22), (10, 20),
                           (12, 28), (20, 28), (22, 20),
                           (28, 22), (24, 12)])
        pygame.display.set_icon(icon)
    except:
        pass

    # 检查中文字体
    for p in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
              "C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/msyhbd.ttc"]:
        if os.path.exists(p):
            try:
                f = pygame.font.Font(p, 16)
                f.render("测试", True, (255, 255, 255))
                break
            except:
                continue

    while True:
        mode = show_mode_menu(temp_screen)
        if mode is None:
            break

        if mode == "跑酷模式":
            from parkour.config import SCREEN_WIDTH, SCREEN_HEIGHT
            from parkour.game import ParkourGame
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("银翼出击：逃亡 - 跑酷射击")
            game = ParkourGame(screen)
        else:
            from game.game import Game
            screen = temp_screen
            screen = pygame.display.set_mode((540, 780))
            pygame.display.set_caption(TITLE)
            game = Game(screen)

        game.run()
        # 游戏结束后回到模式选择


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("=" * 40)
        traceback.print_exc()
        print("=" * 40)
        input("\n按 Enter 键退出...")
        sys.exit(1)
