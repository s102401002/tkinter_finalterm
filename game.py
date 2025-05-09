import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
import random 
from animation import Animation
from player import Player
from npc import NPC
# ------------------- config -------------------
WIDTH, HEIGHT = 900, 400
FPS = 60
ASSETS_DIR = Path(__file__).with_suffix('').with_name("assets_aligned")
PLAYER_Y_ADJUST = -20
PLAYER_LEFT_X = WIDTH * 3 // 4
PLAYER_RIGHT_X = WIDTH // 4
PLAYER_CENTER_X = WIDTH // 2
BG_SPEED_MULT_RUN = 1.5
SWITCH_STEPS = 15
WALK_FPS = 2
RUN_FPS = 2
WALK_SPEED = 4
RUN_SPEED = 6

# ------------------- main game -------------------
class ElectricEyeGame(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("電眼美女")
        self.resizable(False, False)
        # ---- 畫布 ----
        self.canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT,
                                bg="#000000", highlightthickness=0)
        self.canvas.pack()

        # ---- 狀態變數 ----
        self.mouse_x = PLAYER_CENTER_X
        self.mouse_y = HEIGHT // 2

        self.bg_offset = 0            # 背景目前已捲動多少 px
        self.max_offset = 0           # 背景最右能捲到多少

        # 方向切換用
        self.switching      = False
        self.switch_steps   = 0
        self.switch_dx_scr  = 0
        self.switch_world_x = 0

        # 隨機位置 (畫面左 or 右隨機一邊)
        start_x = random.choice([50, WIDTH - 50])
        y = HEIGHT - 120

        # assets 資料夾路徑
        npc_asset_dir = ASSETS_DIR / 'npc' / 'man'

        # 建立 NPC 物件
        self.npc_list = []
        npc_y = [HEIGHT-140, HEIGHT-150,  HEIGHT-190,  HEIGHT-210]
        for _ in range(3):  # 例如一次隨機生成 3 個
            npc = NPC(self.canvas, npc_asset_dir, start_x, HEIGHT-210, fps=FPS)
            self.npc_list.append(npc)
        # for _ in range(3):  # 例如一次隨機生成 3 個
        #     npc = NPC(self.canvas, npc_asset_dir, start_x, HEIGHT-150, fps=FPS)
        #     self.npc_list.append(npc)
        # for _ in range(3):  # 例如一次隨機生成 3 個
        #     npc = NPC(self.canvas, npc_asset_dir, start_x, y+10, fps=FPS)
        #     self.npc_list.append(npc)
        # for _ in range(3):  # 例如一次隨機生成 3 個
        #     npc = NPC(self.canvas, npc_asset_dir, start_x, y+20, fps=FPS)
        #     self.npc_list.append(npc)
        # ---- 事件與資源 ----
        self._bind_events()
        self._load_assets()
        self._setup_world()

        # ---- 主迴圈 ----
        self._loop()

    # --------------------------------------------------------
    # 事件綁定
    # --------------------------------------------------------
    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)

    def _on_mouse_move(self, e):
        self.mouse_x, self.mouse_y = e.x, e.y

    # --------------------------------------------------------
    # 載入背景與角色貼圖
    # --------------------------------------------------------
    def _load_assets(self):
        # ---- 背景 ----
        bg = Image.open(ASSETS_DIR / 'bg.png')
        nh = HEIGHT
        nw = int(bg.width * nh / bg.height)
        bg = bg.resize((nw, nh), Image.Resampling.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(bg)
        self.max_offset = nw - WIDTH

        # ---- 走路 / 跑步 貼圖 ----
        imgs_rw = [Image.open(ASSETS_DIR / f'player/player_right_{i}.png') for i in range(7)]
        imgs_lw = [Image.open(ASSETS_DIR / f'player/player_left_{i}.png')  for i in range(7)]
        imgs_rr = [Image.open(ASSETS_DIR / f'player/player_right_run_{i}.png') for i in range(9)]
        imgs_lr = [Image.open(ASSETS_DIR / f'player/player_left_run_{i}.png')  for i in range(9)]

        def mk(img):                  # 統一縮放 (×1/3)
            return ImageTk.PhotoImage(
                img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            )

        self.anim_right_walk = Animation([mk(i) for i in imgs_rw], WALK_FPS, FPS)
        self.anim_left_walk  = Animation([mk(i) for i in imgs_lw], WALK_FPS, FPS)
        self.anim_right_run  = Animation([mk(i) for i in imgs_rr], RUN_FPS, FPS)
        self.anim_left_run   = Animation([mk(i) for i in imgs_lr], RUN_FPS, FPS)

    # --------------------------------------------------------
    # 建立背景與玩家物件
    # --------------------------------------------------------
    def _setup_world(self):
        # 背景加 'bg' tag，之後只移動這個 tag
        self.bg_offset = (self.bg_img.width() - WIDTH) // 2
        self.canvas.create_image(-self.bg_offset, 0, image=self.bg_img,
                                 anchor='nw', tags='bg')
        
        self.canvas.tag_lower('bg')  # 背景放到最底
        
        # 玩家
        self.player = Player(self.canvas,
                             PLAYER_CENTER_X,
                             HEIGHT - 120 + PLAYER_Y_ADJUST,
                             self.anim_right_walk, self.anim_left_walk,
                             self.anim_right_run,  self.anim_left_run)

    # --------------------------------------------------------
    # 依滑鼠距離決定速度
    # --------------------------------------------------------
    def _determine_speed(self) -> int:
        if self.player.set_direction(self.mouse_x):
            # 方向改變 → 啟動切換流程
            tgt = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            self.switching = True
            self.switch_steps   = SWITCH_STEPS
            self.switch_dx_scr  = (tgt - self.player.x) / SWITCH_STEPS
            self.switch_world_x = self.bg_offset + self.player.x

        # 距離小於 10 px → 停
        dx = self.mouse_x - self.player.x
        if abs(dx) < 10:
            return 0
        return RUN_SPEED if abs(dx) > WIDTH * 0.5 else WALK_SPEED

    # --------------------------------------------------------
    # 每幀更新
    # --------------------------------------------------------
    def _update(self):
        # ---------- 1. 懸停檢查 ----------
        pw = self.player.anim.frames[0].width()
        ph = self.player.anim.frames[0].height()
        self.player.hover = (abs(self.mouse_x - self.player.x) <= pw/2 and
                             abs(self.mouse_y - self.player.y) <= ph/2)

        # 如果懸停 → 只更新靜止圖然後 return
        if self.player.hover:
            self.player.idle = True
            self.player.update()
            return

        # ---------- 2. 速度 / 動畫 切換 ----------
        speed = self._determine_speed()
        self.player.set_speed(speed)

        # ---------- 3. 方向切換中 ----------
        if self.switching:
            # 每步螢幕位移
            dx = self.switch_dx_scr
            new_scr_x = self.player.x + dx

            # 同步背景：bg_offset = world_x - screen_x
            desired_off = self.switch_world_x - new_scr_x
            new_off = min(max(desired_off, 0), self.max_offset)
            delta_off = new_off - self.bg_offset
            if delta_off:
                self.bg_offset = new_off
                self.canvas.move('bg', -delta_off, 0)

            # 更新玩家螢幕座標
            self.player.x = new_scr_x

            self.switch_steps -= 1
            if self.switch_steps <= 0:
                self.switching = False

        else:
            # ---------- 4. 正常滾動 / 玩家移動 ----------
            bg_scale   = BG_SPEED_MULT_RUN if self.player.running else 1.0
            scroll_vx  = self.player.vx * bg_scale

            no = min(max(self.bg_offset + scroll_vx, 0), self.max_offset)
            d  = no - self.bg_offset

            if d != 0:
                # 背景真的捲動
                self.bg_offset = no
                self.canvas.move('all', -d, 0)
                # npc也跟著背景一起動
                for npc in self.npc_list:
                    self.canvas.move(npc.id, -d, 0)
                # 玩家在畫面固定點
                self.player.x = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            else:
                # 背景不能再捲 → 玩家自己在畫面內移動
                nx = self.player.x + self.player.vx
                min_x = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
                max_x = PLAYER_CENTER_X
                if self.player.face_right:
                    self.player.x = min(max(nx, min_x), max_x)
                else:
                    self.player.x = max(min(nx, min_x), max_x)

        # ---------- 5. idle (玩家已無法再前進) 判斷 ----------
        # 右邊滾到底：背景在最右 + 玩家面向右 + 已站在畫面最右可顯示位置 (= CENTER_X)
        hit_right_edge = (
            self.player.face_right and
            self.bg_offset >= self.max_offset and
            self.player.x >= PLAYER_CENTER_X and
            self.player.vx > 0                    # 還想往右
        )

        # 左推到底：背景在最左 + 玩家面向左 + 已站在畫面最左可顯示位置 (= CENTER_X)
        hit_left_edge = (
            (not self.player.face_right) and
            self.bg_offset <= 0 and
            self.player.x <= PLAYER_CENTER_X and
            self.player.vx < 0                    # 還想往左
        )

        self.player.idle = self.player.hover or hit_right_edge or hit_left_edge

        # ---------- 6. 更新影像 ----------
        self.player.update()


        # ---------- 7. 更新影像 ----------
        for npc in self.npc_list:
            npc.update()
            # 如果要移動：
            dx = 2 if npc.face_right else -2
            npc.move(dx)

    # --------------------------------------------------------
    # 主迴圈
    # --------------------------------------------------------
    def _loop(self):
        self._update()
        self.after(int(1000 / FPS), self._loop)



if __name__ == '__main__':
    ElectricEyeGame().mainloop()