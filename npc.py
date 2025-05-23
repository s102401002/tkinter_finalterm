from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
from pathlib import Path
from heart import HeartFillClip
FLASH_FPS = 4
WEAK_FPS = 2
HOVER_FPS = 10  # 每秒顯示懸停動畫的幀率
HOVER_FRAMES = 3  # 懸停動畫的總幀數
HOVER_OFFSET = 70  # 懸停動畫相對於 NPC 的垂直偏移量
HOVER_OFFSET_X = 30
class NPC:
    _id_counter = 0
    def __init__(self, canvas: tk.Canvas, asset_dir: Path, start_x: int, y: int, walk_fps: int,fps: int, world_left: int, world_right: int):
        self.canvas = canvas
       # 世界座標與原點
        self.origin = world_left
        self.max_range = int((world_right - world_left)/4) # 固定最大區間
        self.cur_range = random.randint(20, self.max_range)            # 當前區間，初始等於最大
        self.world_x = start_x
        self.y = y
        # 動態邊界
        self.bdr_left = self.world_x - self.cur_range
        self.bdr_right = self.world_x + self.cur_range
        # 停止狀態與計數
        self.stopping = False
        self._end_hits = 0
        # 隨機初始方向
        self.face_right = random.choice([True, False])

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
        
         # 載入懸停動畫
        img_hover = [Image.open(asset_dir / f'focus//focus_{i}.png') for i in range(3)]
        self.hover_frames = [
            ImageTk.PhotoImage(
                img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            ) for img in img_hover
        ]
         # 計算每幀在主迴圈中持續的次數
        loops_per_cycle = fps // HOVER_FPS
        self.hover_loops_per_frame = max(1, loops_per_cycle // HOVER_FRAMES)
        # 懸停動畫計數器，超出後停在最後一幀
        self._hover_counter = self.hover_loops_per_frame * HOVER_FRAMES

        # 設定初始動畫
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]

        # 先放在正確位置
        screen_x = self.world_x  # 初始沒有 bg_offset，直接 world_x

        # 原本的走路圖層
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
        
         # 懸停動畫，隱藏並置於走路圖層上方
        self.id_hover = self.canvas.create_image(screen_x-HOVER_OFFSET_X, self.y-HOVER_OFFSET,
                                                 image=self.hover_frames[0],
                                                 state='hidden')
        
        # 確保閃光在衰弱之下
        self.canvas.tag_lower(self.id_flash, self.id_weak)
        
        # 確保懸停動畫在最上層
        self.canvas.tag_raise(self.id_hover)

        # 計數器：每兩次閃光更新一次衰弱
        self._flash_step = 0
        self.id = self.id_walk
        self.walking = True

        self.is_attracted = False
        self.timer_seconds = 0
        # self.timer_label = None  # 由主程式呼叫時設定
        self.heart = None  # 存放 HeartFillClip 物件

        # 新增：hover 狀態旗標
        self.is_hovered = False

       # 把所有 layer 都加上同一組 tag： f"npc{self.npc_id}"
        self._tag = f"npc{self.npc_id}"
        for cid in (self.id_walk, self.id_flash, self.id_weak, self.id_hover):
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
        # 重置懸停瞄準計數，從第一幀開始
        self._hover_counter = 0
        self.canvas.itemconfig(self.id_hover, state='normal')

    def _on_hover_leave(self):
        # 滑鼠游標離開 NPC 時觸發
        self.is_hovered = False
        # 隱藏懸停瞄準圖層，並停在初始狀態
        self.canvas.itemconfig(self.id_hover, state='hidden')

    def _load_animation(self, dir_path: Path, walk_fps: int, fps: int, range_id: int):
        frames = []
        for i in range(0, range_id):  # 0.png ~ 13.png
            img = Image.open(dir_path / f'{i}.png')
            img = img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        return Animation(frames, walk_fps, fps)
    
    def move(self, speed: int):
        if self.stopping or self.is_attracted:
            return
        dx = speed if self.face_right else -speed
        nxt = self.world_x + dx
        # 使用動態邊界
        if nxt <= self.bdr_left:
            self.world_x = self.bdr_left
            self._handle_boundary_hit(left=True)
        elif nxt >= self.bdr_right:
            self.world_x = self.bdr_right
            self._handle_boundary_hit(left=False)
        else:
            self.world_x = nxt
    '''
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
    '''
    



    def update(self, bg_offset: int):
        screen_x = self.world_x - bg_offset
        # 更新位置
        for cid in (self.id_walk, self.id_flash, self.id_weak, self.id_hover):
            y = self.y - (HOVER_OFFSET if cid == self.id_hover else 0)
            self.canvas.coords(cid, screen_x, y)
         # 停止模式：保持 current_img，隱藏其他
        if self.stopping:
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            for cid in (self.id_flash, self.id_weak):
                self.canvas.itemconfig(cid, state='hidden')
            if self.is_hovered:
                 # 懸停動畫
                frame_idx = min(self._hover_counter // self.hover_loops_per_frame, HOVER_FRAMES - 1)
                self.canvas.itemconfig(self.id_hover, image=self.hover_frames[frame_idx])
                if self._hover_counter < self.hover_loops_per_frame * HOVER_FRAMES:
                    self._hover_counter += 1
                # 確保懸停圖層在最上層
                self.canvas.tag_raise(self.id_hover)
                self.canvas.itemconfig(self.id_walk, state='normal')
                self.current_img = self.anim.next()
                self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            return
        if self.is_attracted:
            # 吸引特效
            img_f = self.anim_attr_flash.next()
            img_w = self.anim_attr_weak.next()
            self.canvas.itemconfig(self.id_flash, state='normal', image=img_f)
            self.canvas.itemconfig(self.id_weak, state='normal', image=img_w)
            self.canvas.itemconfig(self.id_walk, state='hidden')
            self.canvas.itemconfig(self.id_hover, state='hidden')
        else:
            # 走路或懸停
            self.canvas.itemconfig(self.id_flash, state='hidden')
            self.canvas.itemconfig(self.id_weak, state='hidden')
            if self.is_hovered:
                 # 懸停動畫
                frame_idx = min(self._hover_counter // self.hover_loops_per_frame, HOVER_FRAMES - 1)
                self.canvas.itemconfig(self.id_hover, image=self.hover_frames[frame_idx])
                if self._hover_counter < self.hover_loops_per_frame * HOVER_FRAMES:
                    self._hover_counter += 1
                # 確保懸停圖層在最上層
                self.canvas.tag_raise(self.id_hover)
                self.canvas.itemconfig(self.id_walk, state='normal')
                self.current_img = self.anim.next()
                self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)

            else:
                # 一般走路動畫
                self.canvas.itemconfig(self.id_hover, state='hidden')
                self.current_img = self.anim.next()
                self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)

    def _handle_boundary_hit(self, left: bool):
        # 進入停止模式，記錄碰撞次數
        self.stopping = True
        self._end_hits += 1
        # 1秒後恢復
        self.canvas.after(800, lambda left=left: self._resume_walk(left))

    def _resume_walk(self, left: bool):
        # 反向並切換動畫
        self.face_right = left
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.anim._loop_counter = 0
        self.stopping = False
        # 若完成一次來回 (2 次碰撞)，重新隨機區間
        if self._end_hits >= 2:
            self.cur_range = random.randint(20, self.max_range)
            self.bdr_left = self.world_x if self.face_right else self.world_x - int(self.cur_range/2)
            self.bdr_right = self.world_x + int(self.cur_range/2) if self.face_right else self.world_x
            self._end_hits = 0

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

            def remove_npc():
                self.canvas.delete(self.id_walk)
                self.canvas.delete(self.id_flash)
                self.canvas.delete(self.id_weak)
                self.id = None # 把NPC的id拿掉，不再更新
            # 加入愛心圖形 (顯示在 NPC 上方)
            screen_x = self.canvas.coords(self.id_walk)[0]
            heart_cx = screen_x
            heart_cy = self.y - 80  # 調整位置顯示在 NPC 上方
            player_y = root_window.player.y
            player_h = root_window.player.anim.frames[0].height()
            player_foot_y = player_y + player_h // 2 - 35
            self.heart = HeartFillClip(
                self.canvas,
                heart_cx,
                heart_cy,
                scale=1.2,
                target_y=player_foot_y, # 愛心填滿後，落下的目標y座標
                on_fall_finish=remove_npc  # 愛心填滿後，把這個npc刪掉
            )
            # if not self.timer_label:
            #     self.timer_label = tk.Label(root_window, text="", font=("Arial", 14), fg="white", bg="black")
            #     self.timer_label.place(x=10, y=10)
            # self._update_timer(root_window)

    def stop_dialog(self):
        self.is_attracted = False
        # 隱藏特效、顯示走路
        self.canvas.itemconfig(self.id_flash, state='hidden')
        self.canvas.itemconfig(self.id_weak,  state='hidden')
        self.canvas.itemconfig(self.id_walk,  state='normal')
        # 重新設置為走路動畫
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l

        # 若愛心還沒填滿，刪除愛心
        if self.heart:
            if self.heart.fill_ratio < 1.03:
                self.heart.stop()  
                self.heart = None
            else:
                # 已經填滿，讓它自然掉下來
                pass

        # if self.timer_label:
        #     self.timer_label.destroy()
        #     self.timer_label = None

    def _update_timer(self, root_window):
        if self.is_attracted:
            self.timer_label.config(text=f"對話中：{self.timer_seconds} 秒")
            self.timer_seconds += 1
            root_window.after(1000, lambda: self._update_timer(root_window))