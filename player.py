from PIL import Image, ImageTk
from pathlib import Path
from animation import Animation

# 播放跌倒動畫時的目標 FPS 和總幀數
FALL_DOWN_FPS = 12
FALL_DOWN_FRAME_NUM = 18
EYE_OFFSET_Y = 65
EYE_OFFSET_X=5
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
          # 縮放函式
        def mk(img: Image.Image, scale: int):
            return ImageTk.PhotoImage(
                img.resize((img.width//scale, img.height//scale), Image.Resampling.LANCZOS)
            )
        #self.img_eyestar = mk(Image.open("assets_aligned/effect/light.png").convert("RGBA"),1)
        # 焦點圖（behind/front）
        self.img_foc_lb = mk(Image.open(asset_dir / 'player/focusing_left_behind.png'),3)
        self.img_foc_lf = mk(Image.open(asset_dir / 'player/focusing_left_front.png'),3)
        self.img_foc_rb = mk(Image.open(asset_dir / 'player/focusing_right_behind.png'),3)
        self.img_foc_rf = mk(Image.open(asset_dir / 'player/focusing_right_front.png'),3)


        # 走路 / 跑步 / 跌倒 動畫
        self.anim_right_walk = Animation([mk(i, 3) for i in rw_imgs], walk_fps, fps)
        self.anim_left_walk  = Animation([mk(i, 3) for i in lw_imgs], walk_fps, fps)
        self.anim_right_run  = Animation([mk(i, 3) for i in rr_imgs], run_fps, fps)
        self.anim_left_run   = Animation([mk(i, 3) for i in lr_imgs], run_fps, fps)
        self.anim_falldown_l = Animation([mk(i,1) for i in fd_l], FALL_DOWN_FPS, fps)
        self.anim_falldown_r = Animation([mk(i,1) for i in fd_r], FALL_DOWN_FPS, fps)

        # 初始狀態
        self.face_right = True
        self.running = False
        self.hover = False
        self.attracting = False
        self.idle = False
        self.lose_pk = False
        self.lose_pose_final = False
        # 使用右走動畫起始
        self.anim = self.anim_right_walk
        # 將首張影像繪出
        self.current_img = self.anim.frames[0]
        self.id = self.canvas.create_image(self.x, self.y, image=self.current_img, tags='player')
         # ───────────【 以下是死去NPC的跟隨機制 】──────────
        # 用來記錄「已死亡 NPC」有幾隻
        self.dead_npc_count = 0
        # 儲存這些死 NPC 在 Canvas 上的 image item id
        self.dead_npc_ids = []

        # 載入「死掉 NPC 向左」與「死掉 NPC 向右」的靜態貼圖
        try:
            #dead_left_img_path = asset_dir / "npc/man/left/died/6.png"
            #dead_right_img_path = asset_dir / "npc/man/right/died/6.png"
            self.dead_img_left = mk(Image.open(asset_dir / "npc/man/left/died/6.png"),3)
            self.dead_img_right = mk(Image.open(asset_dir / "npc/man/right/died/6.png"),3)
        except Exception as e:
            raise RuntimeError(f"無法載入死去 NPC 貼圖：{e}")
        # ────────────────────────────────────────────────────────────
        '''
        self.id_eye = self.canvas.create_image(self.x, 
                                               self.y-EYE_OFFSET_Y, 
                                               image=self.img_eyestar, 
                                               state="hidden", 
                                               tags='player')
        '''
        

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
    def add_dead_npc(self):
        """
        新增一隻死掉的 NPC 追隨者。每叫一次就多一個。
        1. dead_npc_count + 1
        2. 在 Canvas 上 create_image，先把它放在玩家身後一點
        3. 把 image_id 存到 dead_npc_ids
        """
        idx = self.dead_npc_count
        self.dead_npc_count += 1

        # 根據玩家朝向，決定要用哪張貼圖，以及放在哪邊
        if self.face_right:
            img = self.dead_img_right
            offset = -70 * (idx + 1)
        else:
            img = self.dead_img_left
            offset = 70 * (idx + 1)

        # 一開始的顯示位置：玩家當前座標 + offset
        init_x = self.x + offset
        init_y = self.y

        # 在 Canvas 上新增一張 image，並把 id 存起來
        new_id = self.canvas.create_image(init_x, init_y, image=img)
        self.dead_npc_ids.append(new_id)
    def update(self):
        """每幀更新位置與動畫，含跌倒、hover、idle 邏輯"""
        # 更新實際座標
        self.canvas.coords(self.id, self.x, self.y)
        #if not self.attracting:
            #self.canvas.itemconfig(self.id_eye, state="hidden")
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

        # 靜止情況：hover、idle、attracting
        if self.hover or self.idle or self.attracting:
            img = self.anim.frames[0]
        else:
            img = self.anim.next()

        self.canvas.itemconfig(self.id, image=img)
        # 上面都執行完之後，再把「死去 NPC 的貼圖」一個一個更新好
        for idx, npc_img_id in enumerate(self.dead_npc_ids):
            # (a) 根據玩家朝向決定該用哪張死圖
            if self.face_right:
                img = self.dead_img_right
                offset_x = -70 * (idx + 1)   # 玩家向右，死 NPC 應該出現在左邊
            else:
                img = self.dead_img_left
                offset_x = 70 * (idx + 1)    # 玩家向左，死 NPC 出現在右邊

            # (b) 更新畫布上的貼圖
            self.canvas.itemconfig(npc_img_id, image=img)

            # (c) 計算跟在玩家身後的位置
            new_x = (self.x + offset_x)
            new_y = self.y
            self.canvas.coords(npc_img_id, new_x, new_y)

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
        #if self.attracting:
        #    self.canvas.itemconfig(self.id_eye, state="normal")

    def resume_move(self):
        """跳出 hover/attract 模式後，恢復先前走/跑動畫"""
        self.idle = False
        if self.vx == 0:
            self.set_stand_image()
        else:
            # 依目前速度/方向重新設定 anim
            if self.running:
                self.anim = self.anim_right_run if self.face_right else self.anim_left_run
            else:
                self.anim = self.anim_right_walk if self.face_right else self.anim_left_walk

    def lose_pk_mode(self):
        """進入跌倒動作，重設計數器"""
        self.lose_pk = True
        self.lose_pose_final = False
        # 切換對應跌倒動畫
        self.anim = self.anim_falldown_r if self.face_right else self.anim_falldown_l
        # 重設動畫計數
        self.anim._loop_counter = 0
        # 顯示第一張
        img = self.anim.frames[0]
        self.canvas.itemconfig(self.id, image=img)