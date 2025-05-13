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

        self.heart_outline_id = None
        self.heart_fill_id = None

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
        # if self.timer_label:
        #     self.timer_label.destroy()
        #     self.timer_label = None
        if self.heart_outline_id:
            self.canvas.delete(self.heart_outline_id)
            self.heart_outline_id = None
        if self.heart_fill_id:
            self.canvas.delete(self.heart_fill_id)
            self.heart_fill_id = None

    def _update_timer(self, root_window):
        if self.is_attracted:
            # self.timer_label.config(text=f"對話中：{self.timer_seconds:.1f} 秒")
            # self.timer_seconds += 0.1
            # root_window.after(100, lambda: self._update_timer(root_window))
            # 更新 timer
            self.timer_seconds += 0.1

            # 畫在 NPC 頭頂（根據 self.world_x 與 self.y 調整位置）
            screen_x = self.world_x  # 你也可以考慮 bg_offset
            screen_y = self.y - 60   # NPC 頭頂上方偏移
            self._draw_heart_progress(screen_x, screen_y)

            root_window.after(100, lambda: self._update_timer(root_window))
    
    def _draw_heart_progress(self, cx, cy, size=20):
        # 計算進度（最多 10 秒）
        progress = min(self.timer_seconds / 10, 1.0)
        print(progress)
        # 建立愛心輪廓座標（類似兩圓+三角）
        def heart_points(scale):
            return [
                cx, cy + scale * 0.4,                     # 下尖端
                cx - scale * 0.6, cy - scale * 0.2,       # 左下凹陷處
                cx - scale * 0.4, cy - scale * 0.8,       # 左上圓弧外側
                cx, cy - scale * 0.5,                     # 上中央凹陷
                cx + scale * 0.4, cy - scale * 0.8,       # 右上圓弧外側
                cx + scale * 0.6, cy - scale * 0.2,       # 右下凹陷處
            ]
        
        # 畫愛心填滿層
        points = heart_points(size)
        if self.heart_fill_id:
            self.canvas.delete(self.heart_fill_id)
        self.heart_fill_id = self.canvas.create_polygon(
            points,
            fill="red",
            stipple="gray50",  # 模擬半透明
            tags="npc"
        )
        self.canvas.itemconfig(self.heart_fill_id, state="normal")
        self.canvas.coords(self.heart_fill_id, points)

        # 遮住進度外的部分 (畫遮罩)
        clip_height = int((1 - progress) * size * 1.2)
        clip_y = cy - size * 0.8 + clip_height
        self.canvas.create_rectangle(cx - size, cy - size, cx + size, clip_y,
                                    fill=self.canvas["background"], width=0, tags="npc")

        # 畫愛心輪廓線
        if self.heart_outline_id:
            self.canvas.delete(self.heart_outline_id)
        self.heart_outline_id = self.canvas.create_polygon(
            points,
            outline="red", fill="",
            width=2,
            tags="npc"
        )