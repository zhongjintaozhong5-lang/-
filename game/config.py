"""游戏配置常量"""

# 窗口
WINDOW_WIDTH = 540
WINDOW_HEIGHT = 780
FPS = 60
TITLE = "银翼出击 - 战机射击游戏"

# 颜色
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

# 玩家
PLAYER_SPEED = 5
PLAYER_ACCELERATION = 0.35
PLAYER_FRICTION = 0.88
PLAYER_MAX_SPEED = 6.5
PLAYER_MAX_LIVES = 5
PLAYER_MAX_HP = 3
PLAYER_INVINCIBLE_TIME = 90
PLAYER_SHOOT_INTERVAL = 8
PLAYER_LASER_MAX_CHARGES = 30
PLAYER_LASER_DRAIN = 1
PLAYER_LASER_MIN = 5

# 子弹
BULLET_SPEED = 10
ENEMY_BULLET_SPEED = 4

# 关卡配置
LEVEL_SCORES = [0, 600, 1800, 3500, 6000, 12000, 99999]
LEVEL_NAMES = [
    "初展翼", "编队战", "暗云涌", "弹幕炼狱", "最终决战", "终焉降临"
]
LEVEL_DESCS = [
    "适应操作，熟悉战场",
    "敌机开始反击，小心躲避",
    "多重威胁，编队来袭",
    "密集弹幕，Boss出现",
    "最终Boss决战",
    "苗浩毁灭者降临，前所未有的挑战"
]

# 敌机基础属性
ENEMY_TYPES = {
    "scout": {
        "hp": 1, "speed": 1.5, "score": 100,
        "w": 28, "h": 28, "can_shoot": False, "color": (80, 160, 255)
    },
    "fighter": {
        "hp": 2, "speed": 2.0, "score": 200,
        "w": 34, "h": 34, "can_shoot": True, "color": (255, 100, 60),
        "shoot_interval": 90
    },
    "runner": {
        "hp": 1, "speed": 3.5, "score": 150,
        "w": 24, "h": 28, "can_shoot": False, "color": (255, 200, 50)
    },
    "tank": {
        "hp": 6, "speed": 0.8, "score": 400,
        "w": 42, "h": 42, "can_shoot": True, "color": (160, 60, 255),
        "shoot_interval": 100
    },
    "miniboss": {
        "hp": 30, "speed": 0.6, "score": 2000,
        "w": 60, "h": 60, "can_shoot": True, "color": (255, 40, 100),
        "shoot_interval": 40
    }
}

# 护盾
PLAYER_SHIELD_MAX = 3

# 道具类型
POWERUP_TYPES = {
    "S": {"color": (0, 255, 136), "label": "S", "name": "散弹升级"},
    "M": {"color": (255, 60, 60), "label": "M", "name": "追踪导弹"},
    "H": {"color": (255, 100, 180), "label": "H", "name": "生命恢复"},
    "P": {"color": (255, 180, 0), "label": "P", "name": "火力提升"},
    "L": {"color": (255, 0, 255), "label": "L", "name": "穿透激光"},
    "W": {"color": (255, 255, 0), "label": "W", "name": "僚机支援"},
    "B": {"color": (0, 200, 255), "label": "盾", "name": "能量护盾"}
}

# 字体管理
import os
import pygame

_FONT_CACHE = {}

def get_font(size, bold=False):
    """获取支持中文的字体"""
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    # 尝试多种中文字体路径
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/msyhl.ttc",
    ]

    font = None
    for path in font_paths:
        if os.path.exists(path):
            try:
                font = pygame.font.Font(path, size)
                break
            except:
                continue

    if font is None:
        font = pygame.font.Font(None, size)

    _FONT_CACHE[key] = font
    return font
