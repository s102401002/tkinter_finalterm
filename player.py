from PIL import Image, ImageTk
from pathlib import Path
from animation import Animation

class Player:
    def __init__(self, canvas, x, y, asset_dir: Path,walk_fps: int, run_fps: int, fps: int):
        self.canvas = canvas
       
        # ---- 走路 / 跑步 貼圖 ----
        imgs_rw = [Image.open(asset_dir / f'player/player_right_{i}.png') for i in range(7)]
        imgs_lw = [Image.open(asset_dir / f'player/player_left_{i}.png')  for i in range(7)]
        imgs_rr = [Image.open(asset_dir / f'player/player_right_run_{i}.png') for i in range(9)]
        imgs_lr = [Image.open(asset_dir / f'player/player_left_run_{i}.png')  for i in range(9)]

        self.img_foc_lb = [ImageTk.PhotoImage(Image.open(asset_dir / f'player/focusing_left_behind.png'))]
        self.img_foc_lf = [ImageTk.PhotoImage(Image.open(asset_dir / f'player/focusing_left_front.png'))]
        self.img_foc_rb = [ImageTk.PhotoImage(Image.open(asset_dir / f'player/focusing_right_behind.png'))]
        self.img_foc_rf = [ImageTk.PhotoImage(Image.open(asset_dir / f'player/focusing_right_front.png'))]

        def mk(img):                  # 統一縮放 (×1/3)
            return ImageTk.PhotoImage(
                img.resize((img.width//3, img.height//3), Image.Resampling.LANCZOS)
            )

        self.anim_right_walk = Animation([mk(i) for i in imgs_rw], walk_fps, fps)
        self.anim_left_walk  = Animation([mk(i) for i in imgs_lw], walk_fps, fps)
        self.anim_right_run  = Animation([mk(i) for i in imgs_rr], run_fps, fps)
        self.anim_left_run   = Animation([mk(i) for i in imgs_lr], run_fps, fps)

        self.anim = self.anim_right_walk
        self.face_right = True
        self.running = False
        self.hover = False
        self.attracting = False # 是否點著npc 後面可以連接不同的圖片
        self.idle = False
        self.x, self.y = x, y
        self.vx = 0
        self.id = canvas.create_image(x, y, image=self.anim.frames[0], tags='player')

    def set_direction(self, mouse_x):  ##根據滑鼠游標位置決定方向
        new_face = (mouse_x >= self.x)
        if new_face != self.face_right:
            self.face_right = new_face
            return True
        return False

    def set_speed(self, speed, running): ##根據滑鼠游標位置決定走/跑
        self.vx = speed if self.face_right else -speed
        self.running = running
        if self.face_right:
            self.anim = self.anim_right_run if self.running else self.anim_right_walk
        else:
            self.anim = self.anim_left_run if self.running else self.anim_left_walk

    def update(self):
        self.canvas.coords(self.id, self.x, self.y)
        if self.hover or self.idle or self.attracting:
            img = self.anim.frames[0]
        else:
            img = self.anim.next()
        self.canvas.itemconfig(self.id, image=img)

   
    def set_stand_image(self, focus_npc=None, mouse_x=None):
        """
        focus_npc: 如果傳入 NPC，就比對 y 值決定用 lb(在後) or lf(在前)；
        否則用預設 stand_frame。
        """
        if self.y < focus_npc.y:
            if self.x >= mouse_x:
                img = self.img_foc_rf
            else:
                img = self.img_foc_lf
        else:
            if self.x >= mouse_x:
                img = self.img_foc_rb
            else:
                img = self.img_foc_lb


        self.canvas.itemconfig(self.id, image=img)

    def resume_move(self):
        """當沒有 hover 或吸引時，恢復走路或跑步的動畫和速度"""
        self.idle = False
        # 依照先前設定的 vx/self.running 重新設定 anim
        if self.vx == 0:
            self.set_stand_image()  # 或許直接站著也可
        else:
            # 例如：
            if self.running:
                self.anim = self.anim_run_r if self.face_right else self.anim_run_l
            else:
                self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
