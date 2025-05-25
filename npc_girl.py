from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
from pathlib import Path
from character import Character
EXCLAM_FPS = 4
EXCLAM_FRAME_NUM = 4
EXA_OFFSET = 140
class NPC_GIRL(Character):
    _id_counter = 0
    def __init__(self, canvas: tk.Canvas, asset_dir: Path, start_x: int, y: int, walk_fps: int,fps: int, world_left: int, world_right: int):
        self.canvas = canvas
       # 世界座標與原點
        self.origin = world_left
        self.max_range = int((world_right - world_left)/4) # 固定最大區間
        self.cur_range = random.randint(20, self.max_range) # 當前區間，初始等於最大
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
        def mk(img):                  
                    return ImageTk.PhotoImage(
                        img.resize((img.width, img.height), Image.Resampling.LANCZOS)
                    )
        # 載入圖片
        self.anim_walk_r = self._load_animation(asset_dir / 'woman/right/walk', walk_fps, fps, 12,1)
        self.anim_walk_l = self._load_animation(asset_dir / 'woman/left/walk', walk_fps, fps, 12,1)
       
        self.img_attack_r = mk(Image.open(asset_dir / f'woman/right/attack.png'))
        self.img_notice_r = mk(Image.open(asset_dir / f'woman/right/notice.png'))
        self.img_attack_l = mk(Image.open(asset_dir / f'woman/left/attack.png'))
        self.img_notice_l = mk(Image.open(asset_dir / f'woman/left/notice.png'))
        
        self.anim_exclamation = self._load_animation(asset_dir / 'woman/exclamation', EXCLAM_FPS, fps, 4,1)

        

        # 設定初始動畫
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]

        # 先放在正確位置
        screen_x = self.world_x  # 初始沒有 bg_offset，直接 world_x

        # 原本的走路圖層
        self.id_walk  = self.canvas.create_image(screen_x, self.y,
                                                 image=self.anim_walk_r.frames[0],
                                                 tags='npc_girl')
        # 驚嘆號圖層(隱藏)
        self.id_exclamation = self.canvas.create_image(screen_x, self.y-EXA_OFFSET,
                                                 image=self.anim_exclamation.frames[0],
                                                 tags='npc_girl',
                                                 state='hidden')

        self.id = self.id_walk
        self.walking = True
        self.shock = False
        self.is_attack = False #是否正在發射光波
        self.is_win = False
        
        # 驚嘆號動畫計數器，超出後停在最後一幀
        self.exa_loops_per_frame = max(1, (fps // EXCLAM_FPS) // EXCLAM_FRAME_NUM)
        self.exa_counter = self.exa_loops_per_frame * EXCLAM_FRAME_NUM

        # 把所有 layer 都加上同一組 tag： f"npc{self.npc_id}"
        self._tag = f"npc_girl{self.npc_id}"
        #for cid in (self.id_walk):
        #    self.canvas.addtag_withtag(self._tag, cid)
        self.canvas.addtag_withtag(self._tag, self.id_walk)
   
    def move(self, speed: int):
        if self.stopping or self.shock :
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

    def update(self, bg_offset: int):
        screen_x = self.world_x - bg_offset
        for cid in (self.id_walk, self.id_exclamation):
            if cid is not None:
                y = self.y - (EXA_OFFSET if cid == self.id_exclamation else 0)
                self.canvas.coords(cid, screen_x, y)
        # 停止模式：保持 current_img，隱藏其他
        if self.shock:
           

            # 播放驚嘆號動畫
            frame_idx = min(self.exa_counter // self.exa_loops_per_frame, EXCLAM_FRAME_NUM - 1)
            self.canvas.itemconfig(self.id_exclamation, image=self.anim_exclamation.frames[frame_idx])

            if self.exa_counter < self.exa_loops_per_frame * EXCLAM_FRAME_NUM:
                self.exa_counter += 1
                 # 持續顯示 notice 圖片
                img = self.img_notice_r if self.face_right else self.img_notice_l
                self.canvas.itemconfig(self.id_walk, state='normal', image=img)
            else:
                # 換成攻擊圖
                atk_img = self.img_attack_r if self.face_right else self.img_attack_l
                self.canvas.itemconfig(self.id_walk, state='normal', image=atk_img)
                self.canvas.itemconfig(self.id_exclamation, state='hidden')
                self.is_attack = True
                self.shock = False
            return
        if self.stopping:
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            #for cid in (self.id_exclamation, self.id_weak):
            #    self.canvas.itemconfig(cid, state='hidden')
            self.canvas.itemconfig(self.id_exclamation, state='hidden')

            return
        
        else:
        # 走路或懸停
            self.canvas.itemconfig(self.id_exclamation, state='hidden')
            # 一般走路動畫
            self.current_img = self.anim.next()
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)

    def notice(self):
        if not self.shock:
            self.shock = True
            self.exa_counter = 0 
        self.walking  =False    
        img = self.img_notice_r if self.face_right else self.img_notice_l
        self.canvas.itemconfig(self.id_walk, state='normal',image=img)
        self.canvas.itemconfig(self.id_exclamation, state='normal',image=self.anim_exclamation.frames[0])



