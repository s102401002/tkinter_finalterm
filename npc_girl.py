from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
from pathlib import Path
from character import Character
EFFECT_FPS = 8
class NPC_GIRL(Character):
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
        self.npc_id = NPC_GIRL._id_counter
        NPC_GIRL._id_counter += 1

        # 載入圖片
        self.anim_walk_r = self._load_animation(asset_dir / 'woman/right/walk', walk_fps, fps, 12,1)
        self.anim_walk_l = self._load_animation(asset_dir / 'woman/left/walk', walk_fps, fps, 12,1)
       
        img_shock_r = [Image.open(asset_dir / f'woman/right/attack.png')]
        img_notice_r = [Image.open(asset_dir / f'woman/right/notice.png')]
        img_shock_l = [Image.open(asset_dir / f'woman/left/attack.png')]
        img_notice_l = [Image.open(asset_dir / f'woman/left/notice.png')]
        
        self.anim_exclamation = self._load_animation(asset_dir / '/woman/exclamation', EFFECT_FPS, fps, 4,1)
        def mk(img):                  
            return ImageTk.PhotoImage(
                img.resize((img.width, img.height), Image.Resampling.LANCZOS)
            )

        # 設定初始動畫
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]

        # 先放在正確位置
        screen_x = self.world_x  # 初始沒有 bg_offset，直接 world_x

        # 原本的走路圖層
        self.id_walk  = self.canvas.create_image(screen_x, self.y,
                                                 image=self.anim_walk_r.frames[0],
                                                 tags='npc_girl')
      
        self.id_  = self.canvas.create_image(screen_x, self.y,
                                                 image=self.anim_walk_r.frames[0],
                                                 tags='npc_girl')

        self.id = self.id_walk
        self.walking = True
        self.is_attack = False ##
        self.is_win = False

       # 把所有 layer 都加上同一組 tag： f"npc{self.npc_id}"
        self._tag = f"npc_girl{self.npc_id}"
        #for cid in (self.id_walk):
        #    self.canvas.addtag_withtag(self._tag, cid)
        self.canvas.addtag_withtag(self._tag, self.id_walk)
   


    def update(self, bg_offset: int):
      
        screen_x = self.world_x - bg_offset
        if self.is_dead:
            self.canvas.coords(self.id_died, screen_x, self.y)
            if not self.pose_final:
                frame_idx = min(self._died_counter // self.died_loops_per_frame,DIED_FRAME_NUM - 1)
                if self._died_counter < self.died_loops_per_frame * DIED_FRAME_NUM:
                    
                    self._died_counter += 1
                    self.current_img = self.anim.next()
                    self.canvas.itemconfig(self.id_died,state='normal', image=self.current_img)
                else:
                    self.pose_final = True
            return

        for cid in (self.id_walk, self.id_flash, self.id_weak, self.id_hover):
            if cid is not None:
                y = self.y - (HOVER_OFFSET if cid == self.id_hover else 0)
                self.canvas.coords(cid, screen_x, y)
         # 停止模式：保持 current_img，隱藏其他
        if self.stopping:
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            for cid in (self.id_flash, self.id_weak):
                self.canvas.itemconfig(cid, state='hidden')
            if self.is_hovered:
                 # 懸停動畫
                frame_idx = min(self._hover_counter // self.hover_loops_per_frame, FOCUS_FRAME_NUM - 1)
                self.canvas.itemconfig(self.id_hover, image=self.anim_focus[frame_idx])
                if self._hover_counter < self.hover_loops_per_frame * FOCUS_FRAME_NUM:
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
                frame_idx = min(self._hover_counter // self.hover_loops_per_frame, FOCUS_FRAME_NUM - 1)
                self.canvas.itemconfig(self.id_hover, image=self.anim_focus[frame_idx])
                if self._hover_counter < self.hover_loops_per_frame * FOCUS_FRAME_NUM:
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
