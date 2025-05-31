from animation import Animation
from PIL import Image, ImageTk
import random
import tkinter as tk
import math
from pathlib import Path
from character import Character
EXCLAM_FPS = 16
EXCLAM_FRAME_NUM = 4
EXA_OFFSET = 120
FLY_FPS = 16
EYE_OFFSET_Y = 70
EYE_OFFSET_X = 20
class NPC_GIRL(Character):
    _id_counter = 0
    def __init__(self, canvas: tk.Canvas, asset_dir: Path, start_x: int, y: int, walk_fps: int,fps: int, world_left: int, world_right: int):
        self.canvas = canvas
       # 世界座標與原點
        self.origin = world_left
        self.max_range = int((world_right - world_left)/7) # 固定最大區間
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
        def mk(img: Image.Image, scale: int):
            return ImageTk.PhotoImage(
                img.resize((img.width//scale, img.height//scale), Image.Resampling.LANCZOS)
            )
        # 載入圖片
        self.anim_walk_r = self._load_animation(asset_dir / 'woman/right/walk', walk_fps, fps, 12,1)
        self.anim_walk_l = self._load_animation(asset_dir / 'woman/left/walk', walk_fps, fps, 12,1)
        
        self.anim_win_r = self._load_animation(asset_dir / 'woman/right/win', walk_fps, fps, 7,1)
        self.anim_win_l = self._load_animation(asset_dir / 'woman/left/win', walk_fps, fps, 7,1)
        
        self.anim_fly_r = self._load_animation(asset_dir / 'woman/right/fly', FLY_FPS, fps, 4,1)
        self.anim_fly_l = self._load_animation(asset_dir / 'woman/left/fly', FLY_FPS, fps, 4,1)
        
        self.img_attack_r = mk(Image.open(asset_dir / f'woman/right/attack.png'),1)
        self.img_notice_r = mk(Image.open(asset_dir / f'woman/right/notice.png'),1)
        self.img_attack_l = mk(Image.open(asset_dir / f'woman/left/attack.png'),1)
        self.img_notice_l = mk(Image.open(asset_dir / f'woman/left/notice.png'),1)
        #self.img_eyestar = mk(Image.open("assets_aligned/effect/light.png").convert("RGBA"),3)

        self.anim_exclamation = self._load_animation(asset_dir / 'woman/exclamation', EXCLAM_FPS, fps, 4,1)

        

        # 設定初始動畫
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.current_img = self.anim.frames[0]
        self.atk_img = None
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
        '''
        self.id_eyestar = self.canvas.create_image(screen_x, self.y-EYE_OFFSET_Y,
                                                 image=self.img_eyestar,
                                                 tags='npc_girl',
                                                 state='hidden')
        '''
        
        

        self.id = self.id_walk
        self.shock = False
        self.in_pk_mode = False #是否正在發射光波
        self.is_win = False
        self.is_lose = False
        # 驚嘆號動畫計數器，超出後停在最後一幀
        loops = fps / EXCLAM_FPS
        self.exa_loops_per_frame = max(1, math.ceil(loops / EXCLAM_FRAME_NUM))
        self.exa_counter         = self.exa_loops_per_frame * EXCLAM_FRAME_NUM

        # 把所有 layer 都加上同一組 tag： f"npc{self.npc_id}"
        self._tag = f"npc_girl{self.npc_id}"
        #for cid in (self.id_walk):
        #    self.canvas.addtag_withtag(self._tag, cid)
        self.canvas.addtag_withtag(self._tag, self.id_walk)
   
    def move(self, speed: int):
        if self.stopping or self.shock or self.in_pk_mode:
            return
        dx = speed if self.face_right else -speed
        nxt = self.world_x + dx
        if self.is_win: #直接走向邊界
            self.world_x = nxt
            return
        if self.is_lose:
            self.world_x = nxt
            self.y = self.y - speed*2
            return
        else:    
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
        if self.in_pk_mode:
            return
        if self.is_win:
            self.current_img = self.anim.next()
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            return
        if self.is_lose:
            self.current_img = self.anim.next()
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            return
        # 驚訝模式
        if self.shock:
            # 播放驚嘆號動畫
            frame_idx = min(self.exa_counter // self.exa_loops_per_frame, EXCLAM_FRAME_NUM - 1)
            self.canvas.itemconfig(self.id_exclamation, image=self.anim_exclamation.frames[frame_idx])

            if self.exa_counter <= self.exa_loops_per_frame * EXCLAM_FRAME_NUM:
                self.exa_counter += 1
                 # 持續顯示 notice 圖片
                img = self.img_notice_r if self.face_right else self.img_notice_l
                self.canvas.itemconfig(self.id_walk, state='normal', image=img)
            else:
                # 換成攻擊圖
                self.canvas.itemconfig(self.id_walk, state='normal', image=self.atk_img)
                self.canvas.itemconfig(self.id_exclamation, state='hidden')
                #self.is_attack = True
                self.shock = False
                self.in_pk_mode=True
            return
        
        if self.stopping:
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)
            self.canvas.itemconfig(self.id_exclamation, state='hidden')
            return
        
        else:
        # 走路或懸停
            #self.canvas.itemconfig(self.id_exclamation, state='hidden')
            # 一般走路動畫
            self.current_img = self.anim.next()
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.current_img)

    def notice(self):
        if not self.shock:
            self.shock = True
            self.exa_counter = 0 
          
        img = self.img_notice_r if self.face_right else self.img_notice_l
        self.canvas.itemconfig(self.id_walk, state='normal',image=img)
        self.canvas.itemconfig(self.id_exclamation, state='normal',image=self.anim_exclamation.frames[0])

    def enter_pk_mode(self,x, bg_offset):
        if not self.in_pk_mode:
           screen_x = self.world_x-bg_offset
           self.face_right = True if screen_x<=x else False
           self.atk_img = self.img_attack_r if self.face_right else self.img_attack_l
        '''
            # 先計算「眼睛光點」要放在哪裡
            offsset = EYE_OFFSET_X if self.face_right else -EYE_OFFSET_X
            new_eyestar_x = screen_x + offsset
            new_eyestar_y = self.y - EYE_OFFSET_Y

            # 1) 用 coords() 來移動 id_eyestar 到 (new_eyestar_x, new_eyestar_y)
            self.canvas.coords(self.id_eyestar, new_eyestar_x, new_eyestar_y)
            # 2) 再用 itemconfig() 來把它打開 (state='normal')
            self.canvas.itemconfig(self.id_eyestar, state='normal')
            self.canvas.tag_raise(self.id_eyestar)
        '''
       
    def exit_pk_mode(self, player_win: bool, player_face_r: bool):
        if player_win:
            self.in_pk_mode = False
            self.is_lose = True
            self.face_right = player_face_r
            self.anim = self.anim_fly_r if self.face_right else  self.anim_fly_l
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.anim.frames[0])
            #self.id_eyestar = self.canvas.itemconfig(self.id_eyestar,state='hidden')
        else:    #女npc 贏
            self.in_pk_mode = False
            self.is_win = True
            self.face_right = player_face_r
            self.anim = self.anim_win_r if self.face_right else  self.anim_win_l
            self.canvas.itemconfig(self.id_walk, state='normal', image=self.anim.frames[0])
            #self.id_eyestar = self.canvas.itemconfig(self.id_eyestar,state='hidden')




