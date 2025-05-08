import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk

from animation import Animation
from player import Player

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
        self.canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT, bg="#000000", highlightthickness=0)
        self.canvas.pack()

        self.mouse_x = PLAYER_CENTER_X
        self.mouse_y = HEIGHT // 2
        self.bg_offset = 0
        self.max_offset = 0

        self.switching = False
        self.switch_steps = 0
        self.switch_dx_scr = 0
        self.switch_world_x = 0

        self._bind_events()
        self._load_assets()
        self._setup_world()

        self._loop()

    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)

    def _on_mouse_move(self, e):
        self.mouse_x, self.mouse_y = e.x, e.y

    def _load_assets(self):
        bg = Image.open(ASSETS_DIR / 'bg.png')
        nh = HEIGHT
        nw = int(bg.width * nh / bg.height)
        bg = bg.resize((nw, nh), Image.Resampling.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(bg)
        self.max_offset = nw - WIDTH

        imgs_rw = [Image.open(ASSETS_DIR / f'player/player_right_{i}.png') for i in range(7)]
        imgs_lw = [Image.open(ASSETS_DIR / f'player/player_left_{i}.png') for i in range(7)]
        imgs_rr = [Image.open(ASSETS_DIR / f'player/player_right_run_{i}.png') for i in range(9)]
        imgs_lr = [Image.open(ASSETS_DIR / f'player/player_left_run_{i}.png') for i in range(9)]

        def mk(img): return ImageTk.PhotoImage(img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS))

        self.anim_right_walk = Animation([mk(i) for i in imgs_rw], WALK_FPS, FPS)
        self.anim_left_walk  = Animation([mk(i) for i in imgs_lw], WALK_FPS, FPS)
        self.anim_right_run  = Animation([mk(i) for i in imgs_rr], RUN_FPS, FPS)
        self.anim_left_run   = Animation([mk(i) for i in imgs_lr], RUN_FPS, FPS)

    def _setup_world(self):
        self.bg_offset = (self.bg_img.width() - WIDTH) // 2
        self.canvas.create_image(-self.bg_offset, 0, image=self.bg_img, anchor='nw', tags='bg')

        self.player = Player(self.canvas, PLAYER_CENTER_X, HEIGHT - 120 + PLAYER_Y_ADJUST,
                             self.anim_right_walk, self.anim_left_walk,
                             self.anim_right_run, self.anim_left_run)

    def _determine_speed(self):
        if self.player.set_direction(self.mouse_x):
            tgt = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            self.switching = True
            self.switch_steps = SWITCH_STEPS
            self.switch_dx_scr = (tgt - self.player.x) / SWITCH_STEPS
            self.switch_world_x = self.bg_offset + self.player.x

        dx = self.mouse_x - self.player.x
        if abs(dx) < 10:
            return 0
        return RUN_SPEED if abs(dx) > WIDTH * 0.5 else WALK_SPEED

    def _update(self):
        pw = self.player.anim.frames[0].width()
        ph = self.player.anim.frames[0].height()
        self.player.hover = (abs(self.mouse_x - self.player.x) <= pw/2 and
                             abs(self.mouse_y - self.player.y) <= ph/2)

        if self.player.hover:
            self.player.idle = True
            self.player.update()
            return

        speed = self._determine_speed()
        self.player.set_speed(speed)

        if self.switching:
            dx = self.switch_dx_scr
            new_scr_x = self.player.x + dx
            desired_off = self.switch_world_x - new_scr_x
            new_off = min(max(desired_off, 0), self.max_offset)
            delta_off = new_off - self.bg_offset
            if delta_off:
                self.bg_offset = new_off
                self.canvas.move('bg', -delta_off, 0)
            self.player.x = new_scr_x
            self.switch_steps -= 1
            if self.switch_steps <= 0:
                self.switching = False
        else:
            bg_scale = BG_SPEED_MULT_RUN if self.player.running else 1.0
            scroll_vx = self.player.vx * bg_scale
            no = min(max(self.bg_offset + scroll_vx, 0), self.max_offset)
            d = no - self.bg_offset

            if d != 0:
                self.bg_offset = no
                self.canvas.move('all', -d, 0)
                self.player.x = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            else:
                nx = self.player.x + self.player.vx
                min_x = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
                max_x = PLAYER_CENTER_X
                if self.player.face_right:
                    self.player.x = min(max(nx, min_x), max_x)
                else:
                    self.player.x = max(min(nx, min_x), max_x)

        hit_right_edge = (self.player.face_right and self.bg_offset >= self.max_offset and
                          self.player.x >= PLAYER_CENTER_X and self.player.vx > 0)
        hit_left_edge = (not self.player.face_right and self.bg_offset <= 0 and
                         self.player.x <= PLAYER_CENTER_X and self.player.vx < 0)

        self.player.idle = self.player.hover or hit_right_edge or hit_left_edge
        self.player.update()

    def _loop(self):
        self._update()
        self.after(int(1000 / FPS), self._loop)


if __name__ == '__main__':
    ElectricEyeGame().mainloop()
