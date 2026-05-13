"""跑酷射击游戏配置"""

# 窗口
SCREEN_WIDTH = 780
SCREEN_HEIGHT = 540
FPS = 60
TITLE = "银翼出击：逃亡 - 跑酷射击"

# 颜色（与主游戏一致）
BLACK = (5, 5, 20)
WHITE = (255, 255, 255)
RED = (255, 60, 60)
GREEN = (60, 255, 100)
BLUE = (60, 140, 255)
LIGHT_BLUE = (100, 200, 255)
YELLOW = (255, 220, 60)
ORANGE = (255, 140, 0)
PURPLE = (180, 60, 255)
PINK = (255, 60, 140)
CYAN = (0, 220, 255)
DARK_BLUE = (20, 30, 60)

# 物理
GRAVITY = 0.65
JUMP_VEL = -11.0
DOUBLE_JUMP_VEL = -9.0
PLAYER_SPEED = 5
PLAYER_MAX_SPEED = 7
FRICTION = 0.85

# 卷轴
BASE_SCROLL_SPEED = 2.5
MAX_SCROLL_SPEED = 7.0

# 玩家
PLAYER_MAX_LIVES = 5
PLAYER_MAX_HP = 3
PLAYER_SHOOT_INTERVAL = 12
PLAYER_INVINCIBLE_TIME = 120
BULLET_SPEED = 10

# 关卡
LEVEL_NAMES = ["坠落", "遗迹走廊", "风暴工厂", "数据深渊", "信标塔"]
LEVEL_TITLES = [
    "Crashed — 无名星球地表",
    "Ruins Corridor — 失落文明",
    "Storm Factory — 回响工区",
    "Data Abyss — 核心数据库",
    "Beacon Tower — 最终冲刺"
]
LEVEL_DESCS = [
    "银翼号坠毁了。信号塔在东方。出发。",
    "一座被吞噬的文明留下的最后痕迹。",
    "回响的工兵仍在运转。穿过工厂。",
    "这颗星球的记忆全部储存在这里。别被淹没。",
    "信号塔就在前方。回响的最后防线也在这里。"
]

# 敌机属性
ENEMY_TYPES = {
    "walker": {"hp": 2, "w": 30, "h": 24, "score": 100, "color": (80, 160, 255), "speed": 1.0},
    "flyer":  {"hp": 1, "w": 24, "h": 20, "score": 150, "color": (255, 100, 60), "speed": 1.5},
    "turret": {"hp": 4, "w": 28, "h": 28, "score": 250, "color": (160, 60, 255), "speed": 0},
}

# Boss属性
BOSS_CONFIG = {
    1: {"hp": 30, "name": "废弃机甲", "score": 2000},
    2: {"hp": 50, "name": "回响哨兵", "score": 3000},
    3: {"hp": 80, "name": "巨型工兵", "score": 5000},
    4: {"hp": 60, "name": "数据核心", "score": 7000},
    5: {"hp": 120, "name": "回响·残王", "score": 10000},
}

# 关卡长度（像素）
LEVEL_LENGTHS = [5000, 6000, 7000, 8000, 6000]

# 字体（复用主游戏）
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from game.config import get_font
