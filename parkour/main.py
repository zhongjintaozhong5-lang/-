#!/usr/bin/env python3
"""银翼出击：逃亡 - 跑酷射击游戏 启动入口"""
import sys, os, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    import pygame
    from parkour.config import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, BLACK
    from parkour.game import ParkourGame

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)

    game = ParkourGame(screen)
    game.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("=" * 40)
        traceback.print_exc()
        print("=" * 40)
        input("\n按 Enter 键退出...")
        sys.exit(1)
