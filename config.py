from pathlib import Path

# ------------------- config -------------------
WIDTH, HEIGHT = 900, 400
FPS = 50
ASSETS_DIR = Path(__file__).with_suffix('').with_name("assets_aligned")
PLAYER_Y_ADJUST = -50
PLAYER_LEFT_X = WIDTH * 3 // 4
PLAYER_RIGHT_X = WIDTH // 4
PLAYER_CENTER_X = WIDTH // 2
BG_SPEED_MULT_RUN = 1.5
SWITCH_STEPS = 15
WALK_FPS = 2
RUN_FPS = 2
NPC_WALK_FPS = 1
WALK_SPEED = 3
RUN_SPEED = 10
NPC_WALK_SPEED = 2
ATTRACT_TIME = 5 # 吸引幾秒加分
LONGPRESS_MS = 200