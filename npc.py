from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
from pathlib import Path

class NPC:
    def __init__(self, canvas: tk.Canvas, asset_dir: Path, start_x: int, y: int, walk_fps: int,fps: int, world_left: int, world_right: int):
        self.canvas = canvas
        self.world_x = start_x  # 世界座標
        self.y = y

        self.face_right = random.choice([True, False])
        self.world_left = world_left
        self.world_right = world_right

        # 載入圖片
        self.anim_walk_r = self._load_animation(asset_dir / 'right', walk_fps, fps)
        self.anim_walk_l = self._load_animation(asset_dir / 'left', walk_fps, fps)

        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]

        # 先放在正確位置
        screen_x = self.world_x  # 初始沒有 bg_offset，直接 world_x
        self.id = self.canvas.create_image(screen_x, self.y, image=self.current_img, tags='npc')

        self.walking = True

        self.is_attracted = False
        self.timer_seconds = 0
        self.timer_label = None  # 由主程式呼叫時設定

    def _load_animation(self, dir_path: Path, walk_fps: int, fps: int):
        frames = []
        for i in range(0, 13):  # 0.png ~ 13.png
            img = Image.open(dir_path / f'{i}.png')
            img = img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        return Animation(frames, walk_fps, fps)

    def move(self, speed: int):
        dx = speed if self.face_right else -speed
        next_world_x = self.world_x + dx

        # 檢查「下一個位置」是否超出邊界
        if next_world_x <= self.world_left:
            self.world_x = self.world_left
            self.face_right = True
            self.anim = self.anim_walk_r
            self.anim._loop_counter = 0
        elif next_world_x >= self.world_right:
            self.world_x = self.world_right
            self.face_right = False
            self.anim = self.anim_walk_l
            self.anim._loop_counter = 0
        else:
            # 沒撞牆 → 正常移動
            self.world_x = next_world_x

        # print(f"[move] face_right={self.face_right}, dx={dx}, world_x={self.world_x}")



    def update(self, bg_offset: int):
        # 計算畫面座標
        screen_x = self.world_x - bg_offset
        self.canvas.coords(self.id, screen_x, self.y)

        if self.walking:
            self.current_img = self.anim.next()
        if self.face_right and self.anim != self.anim_walk_r:
            self.anim = self.anim_walk_r
            self.anim._loop_counter = 0
        elif not self.face_right and self.anim != self.anim_walk_l:
            self.anim = self.anim_walk_l
            self.anim._loop_counter = 0
        self.canvas.itemconfig(self.id, image=self.current_img)
        # print(f"world_x={self.world_x}, bg_offset={bg_offset}, screen_x={self.world_x - bg_offset}, face_right={self.face_right}")
    
    def start_dialog(self, root_window):
        if not self.is_attracted:
            self.is_attracted = True
            self.timer_seconds = 0
            if not self.timer_label:
                self.timer_label = tk.Label(root_window, text="", font=("Arial", 14), fg="white", bg="black")
                self.timer_label.place(x=10, y=10)
            self._update_timer(root_window)

    def stop_dialog(self):
        self.is_attracted = False
        if self.timer_label:
            self.timer_label.destroy()
            self.timer_label = None

    def _update_timer(self, root_window):
        if self.is_attracted:
            self.timer_label.config(text=f"對話中：{self.timer_seconds} 秒")
            self.timer_seconds += 1
            root_window.after(1000, lambda: self._update_timer(root_window))