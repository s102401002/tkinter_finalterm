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
NPC_WALK_SPEED = 1
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
        npc_y = [HEIGHT-140, HEIGHT-170,  HEIGHT-220,  HEIGHT-240] # 後面兩項靠近牆壁
        # ---- 事件與資源 ----
        self._bind_events()
        self._load_assets()
        self._setup_world()
        for _ in range(7):  # 例如一次隨機生成 7 個
            idx = random.randrange(len(npc_y))
            y = npc_y[idx]
            npc = NPC(
                self.canvas,
                npc_asset_dir,
                start_x=random.randint(300, self.bg_img.width() - 300),
                y=y,
                walk_fps=NPC_WALK_FPS,
                fps = FPS,
                world_left=300,
                world_right=self.bg_img.width() - 300
            )
            if idx == 2 or idx == 3:
                self.canvas.tag_raise(npc.id, 'bg') #在player之下，背景之上
            self.npc_list.append(npc)
        
        self.hover_npc = None # 判斷紀錄按下滑鼠時在不在npc上
        # ---- 主迴圈 ----
        self._loop()

    # --------------------------------------------------------
    # 事件綁定
    # --------------------------------------------------------
    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)
        # self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _on_mouse_move(self, e):
        self.mouse_x, self.mouse_y = e.x, e.y
        # ---- 判斷滑鼠是不是在npc上: 在這裡判斷好，再交給on_press和on_release處理----
        self.hover_npc = None
        for npc in self.npc_list:
            x1, y1 = self.canvas.coords(npc.id)
            img_w = npc.current_img.width()
            img_h = npc.current_img.height()
            if abs(e.x - x1) <= img_w // 2 and abs(e.y - y1) <= img_h // 2:
                self.hover_npc = npc
                return
    def _on_click(self, event):
        pass
    def _on_press(self, event):
        if self.hover_npc:
            self.clicked_npc = self.hover_npc
            self.player.attracting = True
            self.clicked_npc.walking = False
            self.clicked_npc.start_dialog(self)

    def _on_release(self, event):
        if self.clicked_npc:
            self.clicked_npc.stop_dialog()
            self.clicked_npc.walking = True
            self.clicked_npc = None
            self.player.attracting = False
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
                             HEIGHT - 170 ,
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
        return RUN_SPEED if abs(dx) > WIDTH * 0.3 else WALK_SPEED

    # --------------------------------------------------------
    # 每幀更新
    # --------------------------------------------------------
    def _update(self):
        # ---------- 1. 懸停檢查 ----------
        pw = self.player.anim.frames[0].width()
        ph = self.player.anim.frames[0].height()
        self.player.hover = (abs(self.mouse_x - self.player.x) <= pw/2 and
                             abs(self.mouse_y - self.player.y) <= ph/2)

        # 如果player懸停或吸引中 → 只更新靜止圖然後 return
        if self.player.hover or self.player.attracting:
            self.player.idle = True
            self.player.update()
            
            # 在 return 前面補上 NPC 更新 不然NPC會跟著玩家一起停下來
            for npc in self.npc_list:
                npc.update(self.bg_offset)
                if not npc.is_attracted:  # 正在被勾引的 NPC 不移動
                    npc.move(NPC_WALK_SPEED)
            return

        # ---------- 2. 速度 / 動畫 切換 ----------
        speed = self._determine_speed()
        self.running = (speed == RUN_SPEED)
        self.player.set_speed(speed,self.running)

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
            npc.update(self.bg_offset)
            if not npc.is_attracted:  # 正在對話的 NPC 不移動
                npc.move(NPC_WALK_SPEED)

    # --------------------------------------------------------
    # 主迴圈
    # --------------------------------------------------------
    def _loop(self):
        self._update()
        self.after(int(1000 / FPS), self._loop)



if __name__ == '__main__':
    ElectricEyeGame().mainloop()