#!/usr/bin/env python3
"""银翼出击 - 战机射击游戏 启动入口"""

import sys
import os
import traceback

# 确保能找到game包
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    import pygame

    # 诊断信息
    print(f"Python: {sys.version}")
    print(f"Pygame: {pygame.version.ver}")
    print(f"工作目录: {os.getcwd()}")
    print(f"脚本目录: {os.path.dirname(os.path.abspath(__file__))}")
    print("正在初始化游戏窗口...", flush=True)

    from game.config import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE, BLACK

    pygame.init()
    pygame.mixer.init()

    # 窗口设置
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
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
    font_ok = False
    for p in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
              "C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/msyhbd.ttc"]:
        if os.path.exists(p):
            try:
                f = pygame.font.Font(p, 16)
                f.render("测试", True, (255,255,255))
                font_ok = True
                print(f"字体: {p}")
                break
            except:
                continue
    if not font_ok:
        print("警告: 未找到中文字体，文字可能无法显示")

    # 运行游戏
    from game.game import Game
    game = Game(screen)
    game.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("=" * 40)
        print("游戏发生错误:")
        traceback.print_exc()
        print("=" * 40)
        input("\n按 Enter 键退出...")
        sys.exit(1)
