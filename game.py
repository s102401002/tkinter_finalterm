'''待修復或未完成項目:
1.npc和npc_girl初始投放要均勻分布分布,不可走到玩家拿不到愛心的地方
2.npc和npc_girl的走路範圍重新設定,盡量減少交錯的情形(這個可以有空再改)
3.pk贏的愛心掉落
4.bar需傳入有幾個npc_girl在畫面中,決定遞減倍數
5.bar的輸贏需callback(贏寫一半,輸完全沒開始)
6.攻擊時的扣血量先註解掉,長按與短按扣除方法不同


'''

import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
import random 
import subprocess
import sys
from animation import Animation
from player import Player
from clock import Clock
from npc import NPC
from npc_girl import NPC_GIRL
from healthBar import HealthBar
from pk_bar_light import LaserBarRectApp
from heart import HeartFillClip
# ------------------- config -------------------
WIDTH, HEIGHT = 900, 400
FPS = 50
ASSETS_DIR = Path(__file__).with_suffix('').with_name("assets_aligned")
PLAYER_Y_ADJUST = -50
PLAYER_LEFT_X = WIDTH * 3 // 4
PLAYER_RIGHT_X = WIDTH // 4
PLAYER_CENTER_X = WIDTH // 2
BG_SPEED_MULT_RUN = 1.5
SWITCH_STEPS = 15
WALK_FPS = 2
RUN_FPS = 2
NPC_WALK_FPS = 1
WALK_SPEED = 3
RUN_SPEED = 10
NPC_WALK_SPEED = 2
ATTRACT_TIME = 5 # 吸引幾秒加分
LONGPRESS_MS = 200
# ------------------- main game -------------------
class ElectricEyeGame(tk.Tk):
    def __init__(self, game_time=10, npc_count=7): # 由main_menu.py傳入參數
        super().__init__()
        self.game_time = game_time
        self.npc_count = npc_count
        self.title("電眼美女")
        self.resizable(False, False)
        
        self.geometry(f"{WIDTH}x{HEIGHT + 50}")  # 設定整個視窗高度
        # ---- 畫布 ----
        self.canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT, bg="#000000", highlightthickness=0)
        self.canvas.place(x=0, y=50)
        #第二個canvas放血條、記分板、時間
        self.ui_canvas = tk.Canvas(self, width=WIDTH, height=50, bg="#007500", highlightthickness=0)
        self.ui_canvas.place(x=0, y=0)
        # 第三個canvas放時鐘(因為會超出綠色的位置所以另外開一個canvas)
        self.clock_canvas = tk.Canvas(self, width=50, height=50, bg="#007500", highlightthickness=0)
        self.clock_canvas.place(x=400, y=0)
        # 暫停的相關參數
        self.paused = False
        self.pause_menu_items = []


        # ---- 狀態變數 ----
        self.mouse_x = PLAYER_CENTER_X
        self.mouse_y = HEIGHT // 2

        self.bg_offset = 0            # 背景目前已捲動多少 px
        self.max_offset = 0           # 背景最右能捲到多少

        # 方向切換用
        self.switching      = False
        self.switch_steps   = 0
        self.switch_dx_scr  = 0
        self.switch_world_x = 0

        # 存PK後掉落的愛心，一般吸引的愛心綁在npc裡
        self.hearts = {}
        #目前吃了幾個愛心
        self.score = 0

        # 隨機位置 (畫面左 or 右隨機一邊)
        start_x = random.choice([50, WIDTH - 50])
        y = HEIGHT - 120 # 280

        
        
        # ---- 事件與資源 ----
        self._bind_events()
        self._load_assets()
        self._setup_world()
        self._setup_ui() #建立血條、時間...
        
        self.hover_npc = None # 判斷紀錄按下滑鼠時在不在npc上
        self.clicked_npc = None  # 避免 _on_mouse_move 報錯
        self.attack_npc_girl = [] #現在screen中有幾個女生要攻擊
        self._lp_after_id = None   # long-press 計時器 after-id
        self._outline_id  = None   # 當前 outline polygon id
        self._longpress   = False  # 這次是否已被視為長按
        self.in_pk_mode = False
        self.lose_locked = False
        self.pk_bar = None
        # ---- 主迴圈、計時 ----
        self.clock.update(paused=True) # 避免一開始填滿時鐘的bug-3.0
        self.clock.start()
        self._loop()

    """
    自訂清除函式，避免結束時的錯誤訊息
    """
    def destroy(self):
        # 主動清除 canvas 與引用
        self.canvas.delete("all")
        self.ui_canvas.delete("all")
        self.canvas = None
        self.ui_canvas = None
        self.bg_img = None  # 避免 PIL 圖像殘留
        super().destroy()
    # --------------------------------------------------------
    # 事件綁定
    # --------------------------------------------------------
    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)
        # self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _on_mouse_move(self, e):
        self.mouse_x, self.mouse_y = e.x, e.y
        # ---- 判斷滑鼠是不是在npc上: 在這裡判斷好，再交給on_press和on_release處理----
        self.hover_npc = None
        for npc in self.npc_list:
            if npc.id is None: # npc.py->start_dialog->remove_npc方法中有npc.i=None的操作
                continue
            coords = self.canvas.coords(npc.id)
            if not coords:
                continue
            x1, y1 = coords
            img_w = npc.current_img.width()
            img_h = npc.current_img.height()
            if abs(e.x - x1) <= img_w // 2 and abs(e.y - y1) <= img_h // 2:
                self.hover_npc = npc
                return
        # 按到一半時滑鼠離開原本npc位置 視為放開滑鼠 
        if self.clicked_npc and self.hover_npc != self.clicked_npc:
            if not self.clicked_npc.is_attracted_PK:
                self._on_release(e)
   
    def _on_press(self, event):
        if self.lose_locked:
            return
        if self.hover_npc and not self.in_pk_mode:
            self.clicked_npc = self.hover_npc
            if self.clicked_npc.is_dead:
                return
            self.player.attracting = True
            self.clicked_npc.is_focused = True
            self.clicked_npc.stopping = True
            #for girl in self.npc_girl_list:
            #    screen_x = girl.world_x - self.bg_offset
            #    if 0 <= screen_x <= WIDTH:
            #        girl.notice()
                    #self.attack_npc_girl.append(girl.id)    
            
            #self.clicked_npc.start_dialog(self)
            #self.clicked_npc.update(self.bg_offset)
            self._longpress   = False
            
            self._lp_after_id = self.after(LONGPRESS_MS, self._handle_long_press)
            
   

    def _handle_long_press(self):
        """滿 1 秒觸發；若滑鼠仍停留在同一隻 NPC 上就進入對話"""
        self._lp_after_id = None
        if not self.clicked_npc or self.clicked_npc.is_dead:
            return
        # 確保滑鼠仍懸停同隻 NPC
        if self.hover_npc is None or self.hover_npc is not self.clicked_npc:
            return

        self._longpress = True
        self.attack_npc_girl = []
        # NPC girls notice…
        for girl in self.npc_girl_list:
            scr_x = girl.world_x - self.bg_offset
            if 0 <= scr_x <= WIDTH:
                self.attack_npc_girl.append(girl) 
                girl.notice()

        # 畫面中沒有npc_girl，長按向上填滿愛心
        if self.attack_npc_girl :
            if not self.in_pk_mode:
                self.in_pk_mode = True #第一次長按觸發對戰模式
                x=self.clicked_npc.world_x-self.bg_offset
                y=self.clicked_npc.y
                
                self.pk_bar = LaserBarRectApp(self.canvas,
                                            screen_x=x,
                                            y=y-120,
                                            anim_fps=10,
                                            fps=FPS,
                                            on_finish=self._on_pk_finished 
                                            )
                
                for girl in self.attack_npc_girl:
                    self
                    girl.enter_pk_mode(x,self.bg_offset)
                self.clicked_npc.enter_pk_mode()  #動畫與邏輯與start_dialog不一樣

        else: # 非PK 呼叫update時扣血
            self.clicked_npc.start_dialog(self)
            self.clicked_npc.update(self.bg_offset)
            # 扣一小段血
            # self.health_bar.lose_one_step()
            # print("扣血")
    def _on_pk_finished(self, success: bool):
        if self.pk_bar:
            self.pk_bar.destroy()
            self.pk_bar = None
        if success:
            print("玩家成功搶到NPC")
            
            self.clicked_npc.exit_pk_mode(player_win=True)
            #self.player.exit_pk_mode(player_win=True)
            #for girl in self.attack_npc_girl:
                #girl.exit_pk_mode(girl_win=False)
                #girl.update(self.bg_offset)
            self.clicked_npc.update(self.bg_offset)
            self.player.update()
            '''
            掉愛心
            '''
            heal = 2.5 # 治癒的血量
            heart = HeartFillClip.instant_create(
                canvas         = self.canvas,
                cx             = self.clicked_npc.world_x,
                screen_x       = self.clicked_npc.world_x - self.bg_offset,
                cy             = self.clicked_npc.y,
                scale          = 1.0,
                target_y       = HEIGHT - 120,
                on_fall_finish = None,
                heal_amount    = heal
            )
            self.hearts[heart.fill_id] = heart
            # print(self.hearts)
            #
            #self._update_score_display()
        else:
            print("被其他女孩搶走了")  # 
            self.clicked_npc.exit_pk_mode(player_win=False)
            #self.player.exit_pk_mode(player_win=False)
            for girl in self.attack_npc_girl:
                #girl.exit_pk_mode(girl_win=True)
                girl.update(self.bg_offset) # 可記錄勝利狀態
            self.health_bar.lose_one_step()
            self.lose_locked = True
        self.in_pk_mode = False
        self.clicked_npc = None
        self.attack_npc_girl.clear()        

            # 扣一小段血
        self.health_bar.lose_one_step()

    def _on_release(self, event):
        if self.lose_locked:
            return
        # 如果目前是 PK 模式 → 不處理任何短按或 stop_dialog
        if self.pk_bar:
            self.health_bar.lose_one_step(0.09)
            print("PK 模式 點擊，扣血")
            self.pk_bar.on_click()
            
        # ─── 短按：取消 long-press───
        if not self._longpress:
            if self._lp_after_id:
                self.after_cancel(self._lp_after_id)
                self._lp_after_id = None
            if not self.in_pk_mode:
                # 恢復玩家走路狀態            
                self.player.attracting = False

        # ─── 長按：照原本 stop_dialog 流程 ───
        else:
            if not self.in_pk_mode:
                self.clicked_npc.stop_dialog()
                for girl in self.npc_girl_list:
                    if girl.shock:
                        girl.shock = False
                        girl.update(self.bg_offset)
                if not self.in_pk_mode:
                    self.player.attracting = False
        if not self.in_pk_mode:
            self.clicked_npc  = None
        self._longpress   = False
    # --------------------------------------------------------
    # 載入背景與角色貼圖
    # --------------------------------------------------------
    def _load_assets(self):
        # ---- 背景 ----
        bg = Image.open(ASSETS_DIR / 'bg.png')
        nh = HEIGHT
        nw = int(bg.width * nh / bg.height)
        bg = bg.resize((nw, nh), Image.Resampling.LANCZOS)
        self.bg_img = ImageTk.PhotoImage(bg)
        self.max_offset = nw - WIDTH

        

    # --------------------------------------------------------
    # 建立背景與玩家物件
    # --------------------------------------------------------
    def _setup_world(self):
        # 背景加 'bg' tag，之後只移動這個 tag
        self.bg_offset = (self.bg_img.width() - WIDTH) // 2
        self.canvas.create_image(-self.bg_offset, 0, image=self.bg_img,
                                 anchor='nw', tags='bg')
        
        self.canvas.tag_lower('bg')  # 背景放到最底
        
        # 玩家
        self.player = Player(self.canvas,
                             PLAYER_CENTER_X,
                             HEIGHT - 190 ,
                             asset_dir=ASSETS_DIR,
                             walk_fps=WALK_FPS,
                             run_fps=RUN_FPS,
                             fps=FPS
                             )
        # assets 資料夾路徑
        npc_asset_dir = ASSETS_DIR / 'npc' 

        # 建立 NPC 物件
        self.npc_list = []
        
        bg_width = self.bg_img.width()
        margin = 500 #離走廊的邊界 避免一開始就出界
        npc_spacing = (bg_width - 2 * margin) // self.npc_count

        npc_y = [HEIGHT-140, HEIGHT-160,  HEIGHT-220,  HEIGHT-240] # 後面兩項靠近牆壁
        
        for ii in range(self.npc_count):  # 一次隨機生成 7 個
            idx = random.randrange(len(npc_y))
            y = npc_y[idx]
            npc = NPC(
                self.canvas,
                npc_asset_dir,
                start_x=margin + ii * npc_spacing + random.randint(0, npc_spacing // 2),# 改成多npc均勻分布(原本只能最多七個npc 不然會超出去)
                y=y,
                walk_fps=NPC_WALK_FPS,
                fps = FPS,
                world_left=300,
                world_right=self.bg_img.width() - 300,
                npc_num=self.npc_count
            )
            if idx == 2 or idx == 3:
                self.canvas.tag_raise(npc.id, 'bg') #在player之下，背景之上
            self.npc_list.append(npc)
       
        self.npc_girl_list = []
        for ii in range(4):  # 例如一次隨機生成 7 個
            idx = random.randrange(len(npc_y))
            y = npc_y[idx]
            npc = NPC_GIRL(
                self.canvas,
                npc_asset_dir,
                start_x=random.randint(1000+ii*500, 1000+(ii+1)*500),
                y=y,
                walk_fps=NPC_WALK_FPS,
                fps = FPS,
                world_left=300,
                world_right=self.bg_img.width() - 300
            )
            if idx == 2 or idx == 3:
                self.canvas.tag_raise(npc.id, 'bg') #在player之下，背景之上
            self.npc_girl_list.append(npc)
    def _setup_ui(self):
        self.health_bar = HealthBar(self.ui_canvas, x=20, y=20, spacing=35, max_hearts=9, initial_full=4)
        # 暫停按鈕
        self.pause_btn = self.ui_canvas.create_oval(840, 5, 880, 45, fill="red", outline="white")
        self.pause_text = self.ui_canvas.create_text(860, 25, text="||", fill="white", font=("Arial", 14, "bold"))
        self.ui_canvas.tag_bind(self.pause_btn, "<Button-1>", self._toggle_pause)
        self.ui_canvas.tag_bind(self.pause_text, "<Button-1>", self._toggle_pause)

        # 時鐘
        self.clock = Clock(self.clock_canvas, center_x=25, center_y=25, radius=20, total_seconds=self.game_time)
        # self.clock.reset()
        # 分數文字
        self.score_text = self.ui_canvas.create_text(650, 25, text=f"Score: {self.score}", fill="white", font=("Arial", 24))
    def _update_score_display(self):
        self.ui_canvas.itemconfig(self.score_text, text=f"Score: {self.score}")
    def _toggle_pause(self, event=None):
        self.paused = not self.paused
        if self.paused:
            # self.clock_canvas.config(height=HEIGHT, bg="white")
            self.ui_canvas.config(height=HEIGHT, bg="white") #暫時把ui_canva拉大 才能看到其他選項
            self._show_pause_menu()
        else:
            self._hide_pause_menu()
            self.ui_canvas.config(height=50, bg="#007500")  # 恢復原高度與樣式
            # self.clock_canvas.config(height=50, bg="#007500")
    def _show_pause_menu(self):
        overlay = self.ui_canvas.create_rectangle(300, 100, 600, 300, fill="white", outline="black")
        text_continue = self.ui_canvas.create_text(450, 160, text="繼續遊戲", font=("Arial", 14), fill="black")
        text_quit = self.ui_canvas.create_text(450, 220, text="結束遊戲", font=("Arial", 14), fill="black")

        self.pause_menu_items = [overlay, text_continue, text_quit]

        self.ui_canvas.tag_bind(text_continue, "<Button-1>", lambda e: self._toggle_pause())
        self.ui_canvas.tag_bind(text_quit, "<Button-1>", lambda e: self.destroy())

    def _hide_pause_menu(self):
        for item in self.pause_menu_items:
            self.ui_canvas.delete(item)
        self.pause_menu_items.clear()
    # --------------------------------------------------------
    # 依滑鼠距離決定速度
    # --------------------------------------------------------
    def _determine_speed(self) -> int:
        
        if self.player.set_direction(self.mouse_x):
            # 方向改變 → 啟動切換流程
            tgt = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            self.switching = True
            self.switch_steps   = SWITCH_STEPS
            self.switch_dx_scr  = (tgt - self.player.x) / SWITCH_STEPS
            self.switch_world_x = self.bg_offset + self.player.x

        # 距離小於 8 px → 停
        dx = self.mouse_x - self.player.x
        if abs(dx) < 8:
            return 0
        return RUN_SPEED if abs(dx) > WIDTH * 0.3 else WALK_SPEED

    '''
    判斷有沒有吃到愛心
    '''
    def _check_heart_collision(self):
        px, py = self.player.x, self.player.y
        pw = self.player.anim.frames[0].width()
        ph = self.player.anim.frames[0].height()

        # 收集要更新的 heart
        hearts = []
        # 1. 取出 npc_list 上綁的 hearts
        for npc in self.npc_list:
            if getattr(npc, 'heart', None):
                hearts.append(npc.heart)

        # 2. 再把 self.hearts dict 裡管理的 hearts 一起加進來
        # 把 self.hearts 裡的也包成一樣格式
        hearts.extend(self.hearts.values())

        # 3. 統一做碰撞檢測
        for heart in hearts:
            if not (heart.fill_id and heart.fall_finished):
                continue

            coords = self.canvas.coords(heart.fill_id)
            if not coords:
                continue
            xs, ys = coords[::2], coords[1::2]
            hx = sum(xs) / len(xs)
            hy = sum(ys) / len(ys)

            if abs(hx - px) < pw // 2 and abs(hy - py) < ph // 2:
                # 3. 碰撞成功：刪圖、清參考、補血、計分
                self.canvas.delete(heart.fill_id)

                # 如果這顆心是綁在某個 npc 上，清掉那個參考
                for npc in self.npc_list:
                    if getattr(npc, 'heart', None) is heart:
                        npc.heart = None
                # 如果你有用 self.hearts dict，也把它 pop 出來
                self.hearts.pop(heart.fill_id, None)

                # 分數與補血
                self.score += 1
                self._update_score_display()
                self.health_bar.gain(heart.heal_amount)
                # print("eat"+ str(heart.heal_amount))


    # --------------------------------------------------------
    # 每幀更新
    # --------------------------------------------------------
    def _update(self):
        # =====================================================
        # 0. 表示愛心已填滿，玩家可以開始移動，要同步更新愛心位置     
        # =====================================================
        # 收集要更新的 heart
        hearts = []
        # 1. 取出 npc_list 上綁的 hearts
        for npc in self.npc_list:
            if getattr(npc, 'heart', None):
                hearts.append(npc.heart)

        # 2. 再把 self.hearts dict 裡管理的 hearts 一起加進來
        hearts.extend(self.hearts.values())
        # print(hearts)
        # 統一更新
        for h in hearts:
            if h.fall_finished or h.if_startfall:
                h.update(self.bg_offset)
        
     # =====================================================
     # 1. 如果滑鼠懸停在 NPC 上，或是在吸引模式，先讓玩家站立不動，然後只更新 NPC
     # =====================================================
     # hover_npc: 已由 _on_mouse_move 更新
        if (self.player.attracting) or (self.hover_npc and self.hover_npc.is_hovered):
            # player 切站立圖（需要在 Player 裡實作）
            y = self.clicked_npc if self.player.attracting else self.hover_npc 
           
            self.player.set_stand_image(focus_npc=y , mouse_x=self.mouse_x)

            # update NPC
            for npc in self.npc_list:
                npc.update(self.bg_offset)
                if not npc.is_attracted_noPK and not npc.is_attracted_PK:
                    npc.move(NPC_WALK_SPEED)

            # update NPC_GIRL
            for girl in self.npc_girl_list:
                girl.update(self.bg_offset)
                if girl.walking:
                    girl.move(NPC_WALK_SPEED)      

            return

        # =====================================================
        # 2. 否則，如果游標在 player 身上 → 靜止並顯示 idle/frame0
        # =====================================================
        pw = self.player.anim.frames[0].width()
        ph = self.player.anim.frames[0].height()
        self.player.hover = (abs(self.mouse_x - self.player.x) <= pw/2 and
                            abs(self.mouse_y - self.player.y) <= ph/2)

        if self.player.hover:
            self.player.idle = True
            self.player.update()    # 顯示 idle 動畫
           
            for npc in self.npc_list:
                npc.update(self.bg_offset)
                if not npc.is_attracted_noPK and not npc.is_attracted_PK:
                    npc.move(NPC_WALK_SPEED)
            
            # update NPC_GIRL
            for girl in self.npc_girl_list:
                girl.update(self.bg_offset)
                if girl.walking:
                    girl.move(NPC_WALK_SPEED)     
            return
         # ---------- 2. 速度 / 動畫 切換 ----------
        speed = self._determine_speed()
        self.running = (speed == RUN_SPEED)
        self.player.set_speed(speed,self.running)
         
        # ---------- 3. 方向切換中 ----------
        if self.switching:
            # 每步螢幕位移
            dx = self.switch_dx_scr
            new_scr_x = self.player.x + dx

            # 同步背景：bg_offset = world_x - screen_x
            desired_off = self.switch_world_x - new_scr_x
            new_off = min(max(desired_off, 0), self.max_offset)
            delta_off = new_off - self.bg_offset
            if delta_off:
                self.bg_offset = new_off
                self.canvas.move('bg', -delta_off, 0)

            # 更新玩家螢幕座標
            self.player.x = new_scr_x

            self.switch_steps -= 1
            if self.switch_steps <= 0:
                self.switching = False

        else:
            # ---------- 4. 正常滾動 / 玩家移動 ----------
            bg_scale   = BG_SPEED_MULT_RUN if self.player.running else 1.0
            scroll_vx  = self.player.vx * bg_scale

            no = min(max(self.bg_offset + scroll_vx, 0), self.max_offset)
            d  = no - self.bg_offset

            if d != 0:
                # 背景真的捲動
                self.bg_offset = no
                self.canvas.move('all', -d, 0) 
                if self.pk_bar :
                    self.canvas.move('pk_bar', d, 0) 
                # npc也跟著背景一起動
                for npc in self.npc_list:
                    if npc.id is None: 
                        continue
                    self.canvas.move(npc.id, -d, 0)
                for girl in self.npc_girl_list:
                    if girl.id is None:
                        continue
                    self.canvas.move(girl.id, -d, 0)
                # 玩家在畫面固定點
                
                self.player.x = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            else:
                # 背景不能再捲 → 玩家自己在畫面內移動
                nx = self.player.x + self.player.vx
                min_x = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
                max_x = PLAYER_CENTER_X
                if self.player.face_right:
                    self.player.x = min(max(nx, min_x), max_x)
                else:
                    self.player.x = max(min(nx, min_x), max_x)
                 # 玩家移動後，也要立刻 align 心型
                

        # ---------- 5. idle (玩家已無法再前進) 判斷 ----------
        # 右邊滾到底：背景在最右 + 玩家面向右 + 已站在畫面最右可顯示位置 (= CENTER_X)
        hit_right_edge = (
            self.player.face_right and
            self.bg_offset >= self.max_offset and
            self.player.x >= PLAYER_CENTER_X and
            self.player.vx > 0                    # 還想往右
        )

        # 左推到底：背景在最左 + 玩家面向左 + 已站在畫面最左可顯示位置 (= CENTER_X)
        hit_left_edge = (
            (not self.player.face_right) and
            self.bg_offset <= 0 and
            self.player.x <= PLAYER_CENTER_X and
            self.player.vx < 0                    # 還想往左
        )

        self.player.idle = self.player.hover or hit_right_edge or hit_left_edge
       
        # ---------- 6. 更新影像、確認有沒有吃到愛心 ----------
        self._check_heart_collision()
        self.player.update()
       
        # ---------- 7. 更新影像 ----------
        for npc in self.npc_list:
            if npc.id is None: 
                continue
            npc.update(self.bg_offset)
            if not npc.is_attracted_noPK and not npc.is_attracted_PK:  # 正在對話的 NPC 不移動
                npc.move(NPC_WALK_SPEED)
        
        for girl in self.npc_girl_list:
            if girl.id is None: 
                continue
            girl.update(self.bg_offset)
            if  girl.walking:  # 正在對話的 NPC 不移動
                girl.move(NPC_WALK_SPEED)    
        
        layers = []
        # 玩家
        px, py = self.canvas.coords(self.player.id)
        layers.append((self.player.id, py))
        # NPC 每個 layer 都要排序
        for npc in self.npc_list:
            if npc.id is None: # npc.py->start_dialog->remove_npc方法中有npc.i=None的操作
                continue
            for cid in (npc.id_walk, npc.id_flash, npc.id_weak, npc.id_hover):
                # 取 y 座標，如果還沒 create 這層就跳過
                try:
                    _, yy = self.canvas.coords(cid)
                except Exception:
                    continue
                layers.append((cid, yy))
        
        for girl in self.npc_girl_list:
            if girl.id is None: 
                continue
            for cid in (girl.id_walk, girl.id_exclamation):
                # 取 y 座標，如果還沒 create 這層就跳過
                try:
                    _, yy = self.canvas.coords(cid)
                except Exception:
                    continue
                layers.append((cid, yy))

        # 按 y 升冪排序：y 小的先 raise，y 大的在最上
        layers.sort(key=lambda t: t[1])
        for cid, _ in layers:
            self.canvas.tag_raise(cid)
    def _return_to_main_menu(self):
        self.destroy()
        # 重新啟動 main_menu.py（需與game.py同資料夾）
        subprocess.Popen([sys.executable, "main_menu.py"])
    # --------------------------------------------------------
    # 主迴圈
    # --------------------------------------------------------
    def _loop(self):
        if self.health_bar.is_empty() == True:
            self._return_to_main_menu()
            return
        if hasattr(self, 'clock'):
            self.clock.update(paused=self.paused) # 如果現在是暫停狀態就會停止clock
        if not self.paused:
            # 時間結束:自動回主選單
            if self.clock.finished:
                self._return_to_main_menu()
                return
            self._update()
        self.after(int(1000 / FPS), self._loop)



if __name__ == '__main__':
    ElectricEyeGame().mainloop()