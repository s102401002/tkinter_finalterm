from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
from pathlib import Path

FLASH_FPS = 4
WEAK_FPS = 2

class NPC:
    _id_counter = 0
    def __init__(self, canvas: tk.Canvas, asset_dir: Path, start_x: int, y: int, walk_fps: int,fps: int, world_left: int, world_right: int):
        self.canvas = canvas
        self.world_x = start_x  # 世界座標
        self.y = y  ##畫面y座標(決定其在第幾道)

        self.face_right = random.choice([True, False])
        self.world_left = world_left  ## 世界座標左邊界
        self.world_right = world_right  ## 世界座標右邊界

         # 分配並遞增 npc_id
        self.npc_id = NPC._id_counter
        NPC._id_counter += 1

        # 載入圖片
        self.anim_walk_r = self._load_animation(asset_dir / 'man/right', walk_fps, fps, 13)
        self.anim_walk_l = self._load_animation(asset_dir / 'man/left', walk_fps, fps, 13)
        
        img_attr_flash = [Image.open(asset_dir / f'attracted/flash_{i}.png') for i in range(4)]
        img_attr_weak = [Image.open(asset_dir / f'attracted/weakening_{i}.png') for i in range(2)]
        def mk(img):                  # 統一縮放 (×1/3)
            return ImageTk.PhotoImage(
                img.resize((img.width//1, img.height//1), Image.Resampling.LANCZOS)
            )
        self.anim_attr_flash = Animation([mk(i) for i in img_attr_flash], FLASH_FPS, fps)
        self.anim_attr_weak = Animation([mk(i) for i in img_attr_weak], WEAK_FPS, fps)

        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]

        # 先放在正確位置
        screen_x = self.world_x  # 初始沒有 bg_offset，直接 world_x
        # 原本的走路圖層
        screen_x = self.world_x
        
        self.id_walk  = self.canvas.create_image(screen_x, self.y,
                                                 image=self.anim_walk_r.frames[0],
                                                 tags='npc')
        # 新增：閃光圖層（隱藏）
        self.id_flash = self.canvas.create_image(screen_x, self.y,
                                                 image=self.anim_attr_flash.frames[0],
                                                 state='hidden')
        # 新增：衰弱圖層（隱藏）
        self.id_weak  = self.canvas.create_image(screen_x, self.y,
                                                 image=self.anim_attr_weak.frames[0],
                                                 state='hidden')
        # 確保閃光在衰弱之下
        self.canvas.tag_lower(self.id_flash, self.id_weak)

        # 計數器：每兩次閃光更新一次衰弱
        self._flash_step = 0
        self.id = self.id_walk
        self.walking = True

        self.is_attracted = False
        self.timer_seconds = 0
        self.timer_label = None  # 由主程式呼叫時設定

        # 新增：hover 狀態旗標
        self.is_hovered = False

       # 把所有 layer 都加上同一組 tag： f"npc{self.npc_id}"
        self._tag = f"npc{self.npc_id}"
        for cid in (self.id_walk, self.id_flash, self.id_weak):
            self.canvas.addtag_withtag(self._tag, cid)
        # 綁事件：滑鼠移入／移出
        self.canvas.tag_bind(self._tag, "<Enter>",
                             lambda e, npc=self: npc._on_hover_enter())
        self.canvas.tag_bind(self._tag, "<Leave>",
                             lambda e, npc=self: npc._on_hover_leave())

    def _on_hover_enter(self):
        # 滑鼠游標進入任一 layer 時觸發
        if not self.is_attracted:
            self.is_hovered = True

    def _on_hover_leave(self):
        # 滑鼠游標離開 NPC 時觸發
        self.is_hovered = False

    def _load_animation(self, dir_path: Path, walk_fps: int, fps: int, range_id: int):
        frames = []
        for i in range(0, range_id):  # 0.png ~ 13.png
            img = Image.open(dir_path / f'{i}.png')
            img = img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        return Animation(frames, walk_fps, fps)

    def move(self, speed: int):
        dx = speed if self.face_right else -speed ## 速度：每frame位移量與方向 (右正左負)
        next_world_x = self.world_x + dx

        # 檢查「下一個位置」是否超出世界邊界
        if next_world_x <= self.world_left: ##碰到左邊界
            self.world_x = self.world_left
            self.face_right = True  ##掉頭
            self.anim = self.anim_walk_r
            self.anim._loop_counter = 0
        elif next_world_x >= self.world_right:  ##碰到右邊界
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
        for cid in (self.id_walk, self.id_flash, self.id_weak):
            self.canvas.coords(cid, screen_x, self.y)

        if self.is_attracted:
            # 1) 每幀都更新閃光
            img_f = self.anim_attr_flash.next()
            self.canvas.itemconfig(self.id_flash, image=img_f)
            self._flash_step += 1
            img_w = self.anim_attr_weak.next()
            self.canvas.itemconfig(self.id_weak, image=img_w)
            

        else:
            # 非吸引狀態 → 立刻恢復走路
            self.canvas.itemconfig(self.id_flash, state='hidden')
            self.canvas.itemconfig(self.id_weak,  state='hidden')
            self.canvas.itemconfig(self.id_walk,  state='normal')

            # 更新走路動畫
            self.current_img = self.anim.next()
            self.canvas.itemconfig(self.id_walk, image=self.current_img)
        # print(f"world_x={self.world_x}, bg_offset={bg_offset}, screen_x={self.world_x - bg_offset}, face_right={self.face_right}")
    
    def start_dialog(self, root_window):
        if not self.is_attracted:
            self.is_attracted = True
            # 隱藏走路、顯示特效
            self.canvas.itemconfig(self.id_walk,  state='hidden')
            self.canvas.itemconfig(self.id_flash, state='normal')
            self.canvas.itemconfig(self.id_weak,  state='normal')
            # 重置計數與動畫迴圈
            self._flash_step = 0
            self.anim_attr_flash._loop_counter = 0
            self.anim_attr_weak._loop_counter  = 0
            self.timer_seconds = 0
            if not self.timer_label:
                self.timer_label = tk.Label(root_window, text="", font=("Arial", 14), fg="white", bg="black")
                self.timer_label.place(x=10, y=10)
            self._update_timer(root_window)

    def stop_dialog(self):
        self.is_attracted = False
        # 隱藏特效、顯示走路
        self.canvas.itemconfig(self.id_flash, state='hidden')
        self.canvas.itemconfig(self.id_weak,  state='hidden')
        self.canvas.itemconfig(self.id_walk,  state='normal')
        # 重新設置為走路動畫
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        if self.timer_label:
            self.timer_label.destroy()
            self.timer_label = None

    def _update_timer(self, root_window):
        if self.is_attracted:
            self.timer_label.config(text=f"對話中：{self.timer_seconds} 秒")
            self.timer_seconds += 1
            root_window.after(1000, lambda: self._update_timer(root_window))