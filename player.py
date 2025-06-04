from PIL import Image, ImageTk
from pathlib import Path
from animation import Animation
from npc import NPC

# 播放跌倒動畫時的目標 FPS 和總幀數
FALL_DOWN_FPS = 8
FALL_DOWN_FRAME_NUM = 18
REINFORCE_FPS = 16
REINFORCE_FRAME_NUM = 32
EYE_OFFSET_Y = 65
EYE_OFFSET_X = 5

class Player:
    def __init__(self, canvas, x: int, y: int, asset_dir: Path,
                 walk_fps: int, run_fps: int, fps: int):
        self.canvas = canvas
        # 位置與速度
        self.x, self.y = x, y
        self.vx = 0

        # 載入素材
        rw_imgs = [Image.open(asset_dir / f'player/player_right_{i}.png') for i in range(7)]
        lw_imgs = [Image.open(asset_dir / f'player/player_left_{i}.png')  for i in range(7)]
        rr_imgs = [Image.open(asset_dir / f'player/player_right_run_{i}.png') for i in range(9)]
        lr_imgs = [Image.open(asset_dir / f'player/player_left_run_{i}.png')  for i in range(9)]
        fd_l = [Image.open(asset_dir / f'player/left/lose/{i}.png')  for i in range(1, FALL_DOWN_FRAME_NUM+1)]
        fd_r = [Image.open(asset_dir / f'player/right/lose/{i}.png') for i in range(1, FALL_DOWN_FRAME_NUM+1)]
        ref_l = [Image.open(asset_dir / f'player/left/reinforcing/{i}.png')  for i in range(1,REINFORCE_FRAME_NUM+1)]
        ref_r = [Image.open(asset_dir / f'player/right/reinforcing/{i}.png') for i in range(1,REINFORCE_FRAME_NUM+1)]
        # 縮放函式
        def mk(img: Image.Image, scale: int):
            return ImageTk.PhotoImage(
                img.resize((img.width // scale, img.height // scale), Image.Resampling.LANCZOS)
            )

        # 焦點圖（behind/front）
        self.img_foc_lb = mk(Image.open(asset_dir / 'player/focusing_left_behind.png'), 3)
        self.img_foc_lf = mk(Image.open(asset_dir / 'player/focusing_left_front.png'), 3)
        self.img_foc_rb = mk(Image.open(asset_dir / 'player/focusing_right_behind.png'), 3)
        self.img_foc_rf = mk(Image.open(asset_dir / 'player/focusing_right_front.png'), 3)

        # 走路 / 跑步 / 跌倒 動畫
        self.anim_right_walk = Animation([mk(i, 3) for i in rw_imgs], walk_fps, fps)
        self.anim_left_walk  = Animation([mk(i, 3) for i in lw_imgs], walk_fps, fps)
        self.anim_right_run  = Animation([mk(i, 3) for i in rr_imgs], run_fps, fps)
        self.anim_left_run   = Animation([mk(i, 3) for i in lr_imgs], run_fps, fps)
        self.anim_falldown_l = Animation([mk(i, 1) for i in fd_l], FALL_DOWN_FPS, fps)
        self.anim_falldown_r = Animation([mk(i, 1) for i in fd_r], FALL_DOWN_FPS, fps)
        self.anim_reinforcing_l = Animation([mk(i, 1) for i in ref_l], REINFORCE_FPS, fps)
        self.anim_reinforcing_r = Animation([mk(i, 1) for i in ref_r], REINFORCE_FPS, fps)

        # 初始狀態
        self.face_right     = True
        self.running        = False
        self.hover          = False
        self.attracting     = False
        self.idle           = False
        self.lose_pk        = False
        self.lose_pose_final = False
        self.is_transforming = False
        self.transforming_pose_final = False
        self.in_beauty_time = False

        # 使用右走動畫起始
        self.anim = self.anim_right_walk
        # 將首張影像繪出
        self.current_img = self.anim.frames[0]
        self.id = self.canvas.create_image(self.x, self.y, image=self.current_img, tags='player')

        # ───────────【 以下是死掉 NPC 的跟隨機制 】──────────
        # 用來記錄「已死亡且要跟隨玩家的 NPC 實例」
        # dead_npcs: store each NPC 實例；dead_npc_ids: store each的 Canvas item id
        self.dead_npcs    : list[NPC] = []
        self.dead_npc_ids : list[int] = []

        # 載入「死掉 NPC 向左」與「死掉 NPC 向右」的靜態貼圖
        try:
            self.dead_img_left  = mk(Image.open(asset_dir / "npc/man/left/died/6.png"), 3)
            self.dead_img_right = mk(Image.open(asset_dir / "npc/man/right/died/6.png"), 3)
        except Exception as e:
            raise RuntimeError(f"無法載入死掉 NPC 貼圖：{e}")

    
    def add_dead_npc(self, npc: NPC):
        """
        即便這隻 npc 已經在 dead_npcs 裡，只要它要跨樓層跟隨，
        就讓它「先刪掉舊的 image id，再重 new 一次 create_image」。
        """
        # 如果還沒記錄過，就把 npc 放入 dead_npcs，再在 dead_npc_ids 補一個 None
        if npc not in self.dead_npcs:
            self.dead_npcs.append(npc)
            self.dead_npc_ids.append(None)

        # 找到對應 dead_npc_ids 裡這隻 NPC 的 index
        idx = self.dead_npcs.index(npc)

        # 如果 dead_npc_ids 太短（之前的邏輯可能刪過 id），先把 dead_npc_ids 補齊
        if idx >= len(self.dead_npc_ids):
            for _ in range(len(self.dead_npcs) - len(self.dead_npc_ids)):
                self.dead_npc_ids.append(None)

        # （1）若該位置之前已經有一個舊的 canvas id，先刪掉
        old_id = self.dead_npc_ids[idx]
        if old_id is not None:
            try:
                self.canvas.delete(old_id)
            except Exception:
                pass


        # （2）根據當前面向，決定貼圖與 offset
        if self.face_right:
            img      = self.dead_img_right
            offset_x = -70 * (idx + 1)
        else:
            img      = self.dead_img_left
            offset_x =  70 * (idx + 1)

        new_x = self.x + offset_x
        new_y = self.y

        # （3）重新在 Canvas 上 create_image，並更新 dead_npc_ids[idx]
        new_id = self.canvas.create_image(new_x, new_y, image=img, state = "hidden",anchor="center", tags="dead_npc")
        #先hidden,等原地倒地動畫播完再顯示
        self.dead_npc_ids[idx] = new_id


    def set_direction(self, mouse_x: int) -> bool:
        """根據滑鼠 x 決定面向，若方向變動回傳 True"""
        new_face = mouse_x >= self.x
        if new_face != self.face_right:
            self.face_right = new_face
            return True
        return False

    def set_speed(self, speed: int, running: bool):
        """根據 speed 與 running 切換對應動畫"""
        self.vx = speed if self.face_right else -speed
        self.running = running
        if self.face_right:
            self.anim = self.anim_right_run if running else self.anim_right_walk
        else:
            self.anim = self.anim_left_run if running else self.anim_left_walk

    def update(self,in_settlement: bool = False):
        """每幀更新位置與動畫，含跌倒、hover、idle 邏輯"""
        # 更新玩家本體座標
        self.canvas.coords(self.id, self.x, self.y)

        # 跌倒模式優先
        if self.lose_pk:
            total = self.anim.loops_per_frame * self.anim.n
            if self.anim._loop_counter < total:
                img = self.anim.next()
            else:
                img = self.anim.frames[-1]
                self.lose_pk = False
                self.lose_pose_final = True
            self.canvas.itemconfig(self.id, image=img)
            return
        if self.is_transforming:
            total = self.anim.loops_per_frame * self.anim.n
            if self.anim._loop_counter < total:
                img = self.anim.next()
            else:
                img = self.anim.frames[-1]
                self.is_transforming = False
                self.transforming_pose_final = True
                self.in_beauty_time = True
            self.canvas.itemconfig(self.id, image=img)
            return
        # 靜止情況：hover / idle / attracting
        if self.hover or self.idle or self.attracting:
            img = self.anim.frames[0]
        else:
            img = self.anim.next()
        self.canvas.itemconfig(self.id, image=img)

        # ───────────【 更新死掉 NPC 的貼圖】──────────
        # 現在 dead_npcs 裡是 NPC 實例，要「每幀」都把它們畫／更新好
        # 2. 更新「死掉 NPC」的每個 Canvas item
        #    利用 dead_npcs[i] → dead_npc_ids[i] 對應關係。
        if not in_settlement:
            for idx, npc in enumerate(self.dead_npcs):
                canvas_id = self.dead_npc_ids[idx]

                # (a) 先更新死圖本身：如果玩家面向改變，要切換左右貼圖
                if self.face_right:
                    img = self.dead_img_right
                    offset_x = -70 * (idx + 1)
                else:
                    img = self.dead_img_left
                    offset_x = 70 * (idx + 1)
                self.canvas.itemconfig(canvas_id, image=img)

                # (b) 計算新座標：死 NPC 跟在玩家背後
                new_x = self.x + offset_x
                new_y = self.y
                self.canvas.coords(canvas_id, new_x, new_y)
                if npc.pose_final:
                    self.canvas.itemconfig(canvas_id, state = "normal") 


    def set_stand_image(self, focus_npc=None, mouse_x: int=None):
        """滑鼠在 NPC 上時，用對應焦點圖顯示"""
        if focus_npc is not None:
            if self.y < focus_npc.y:
                img = self.img_foc_rf if self.x >= mouse_x else self.img_foc_lf
            else:
                img = self.img_foc_rb if self.x >= mouse_x else self.img_foc_lb
        else:
            img = self.current_img
        self.canvas.itemconfig(self.id, image=img)

    def resume_move(self):
        """跳出 hover/attract 模式後，恢復先前走/跑動畫"""
        self.idle = False
        if self.vx == 0:
            self.set_stand_image()
        else:
            if self.running:
                self.anim = self.anim_right_run if self.face_right else self.anim_falldown_r
            else:
                self.anim = self.anim_left_run if self.face_right else self.anim_left_walk

    def lose_pk_mode(self):
        """進入跌倒動作，重設計數器"""
        self.lose_pk = True
        self.lose_pose_final = False
        self.anim = self.anim_falldown_r if self.face_right else self.anim_falldown_l
        self.anim._loop_counter = 0
        img = self.anim.frames[0]
        self.canvas.itemconfig(self.id, image=img)
    
    def enter_transforming_mode(self):
        if not self.is_transforming :
            self.is_transforming = True
            self.transforming_pose_final = False
            self.anim = self.anim_reinforcing_r if self.face_right else self.anim_reinforcing_l
            self.anim._loop_counter = 0
            img = self.anim.frames[0]
            self.canvas.itemconfig(self.id, image=img)
            
        
    def draw(self):
        """
        每次畫面需要重畫玩家時，就呼叫這個方法：
        1. 由於外層的 game.py 會 delete('all')，這裡直接 new 一個新的 Image。
        2. 最後把玩家自己的 image 放到最上層。
        """
        # （外層 delete('all') 之後，self.id 已經不存在在畫布上，這裡重新 create）
        self.id = self.canvas.create_image(
            self.x,
            self.y,
            image=self.current_img,
            anchor="center",
            tags="player"
        )
    
