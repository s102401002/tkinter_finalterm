from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
from pathlib import Path

class NPC:
    def __init__(self, canvas: tk.Canvas, asset_dir: Path, start_x: int, y: int, fps: int):
        self.canvas = canvas
        self.x = start_x
        self.y = y
        self.world_x = start_x
        # 隨機決定初始方向
        self.face_right = random.choice([True, False])

        # 載入圖片
        self.anim_walk_r = self._load_animation(asset_dir / 'right', fps)
        self.anim_walk_l = self._load_animation(asset_dir / 'left', fps)
        # self.stand_r = ImageTk.PhotoImage(Image.open(asset_dir / 'right' / 'stand.bmp'))
        # self.stand_l = ImageTk.PhotoImage(Image.open(asset_dir / 'left' / 'stand.bmp'))

        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]

        # 在 canvas 畫出 npc
        self.id = self.canvas.create_image(self.x, self.y, image=self.current_img, tags='npc')

        self.walking = True  # 是否在移動

    def _load_animation(self, dir_path: Path, fps: int):
        frames = []
        for i in range(0, 14):  # 0.bmp ~ 13.png
            img = Image.open(dir_path / f'{i}.png')
            img = img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        return Animation(frames, fps, fps)

    def update(self):
        # 每幀更新動畫
        if self.walking:
            self.current_img = self.anim.next()
        # else:
        #     self.current_img = self.stand_r if self.face_right else self.stand_l

        self.canvas.itemconfig(self.id, image=self.current_img)

    def move(self, dx: int):
        self.x += dx
        self.canvas.move(self.id, dx, 0)
