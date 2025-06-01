# game.py

import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
import random
import subprocess
import sys
import time

from animation import Animation
from player import Player
from clock import Clock
from npc import NPC
from npc_girl import NPC_GIRL
from healthBar import HealthBar
from pk_bar_light import LaserBarRectApp
from heart import HeartFillClip
from laserBeam import LaserBeam
from hover_button import HoverButton

# ------------------- config -------------------
WIDTH, HEIGHT = 900, 400
FPS = 60
ASSETS_DIR = Path(__file__).with_suffix('').with_name("assets_aligned")

PLAYER_Y_ADJUST = -50
PLAYER_LEFT_X = WIDTH * 3 // 4
PLAYER_RIGHT_X = WIDTH // 4
PLAYER_CENTER_X = WIDTH // 2
BG_SPEED_MULT_RUN = 1.5
NPC_WALK_FPS = 16
WALK_FPS = 16
RUN_FPS = 32
WALK_SPEED = 3
RUN_SPEED = 10
NPC_WALK_SPEED = 2
LONGPRESS_MS = 200
EYE_OFFSET_Y = 65
EYE_OFFSET_X = 5

NORMAL_HEART_HEAL = 1.0
BIG_HEART_HEAL = 1.5
# ------------------- main game -------------------
class ElectricEyeGame(tk.Tk):
    def __init__(self, game_time=60, npc_count=7): 
        super().__init__()

        # --- 基本視窗與 Canvas 設定 ---
        self.game_time = game_time
        self.npc_count = npc_count
        self.title("電眼美女")
        self.resizable(False, False)
        self.geometry(f"{WIDTH}x{HEIGHT + 50}")  # 主視窗大小

        # 畫布：遊戲畫面
        self.canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT, bg="#000000", highlightthickness=0)
        self.canvas.place(x=0, y=50)

        # UI 畫布：放血條、分數、按鈕
        self.ui_canvas = tk.Canvas(self, width=WIDTH, height=50, bg="#007500", highlightthickness=0)
        self.ui_canvas.place(x=0, y=0)

        # 時鐘畫布：獨立放時鐘
        self.clock_canvas = tk.Canvas(self, width=50, height=50, bg="#007500", highlightthickness=0)
        self.clock_canvas.place(x=400, y=0)

        # 暫停狀態相關
        self.paused = False
        self.pause_menu_items = []
        
        # 結算模式（settlement mode）相關屬性
        self.in_settlement = False
        self.scored_npc_ids = set()  # 用於記錄已跳過 +1000 分的 dead NPC image id

        # --- 樓層管理變數 ---
        self.floor_data = {}       # 用來存放每一層的 {bg_img, npc_list, girl_list, bg_width}
        self.floor = 2            # 當前樓層 (1~3)
        self.total_floors = 3
        self.up_btn = None
        self.down_btn = None
        self.is_switching_floor = True
        self.id_black_canvas = None
        # 存放遊戲狀態用變數
        self.bg_img = None
        self.bg_offset = 0
        self.max_offset = 0

        # 切換樓層按鈕
        self.first_load = True

        # 角色(與個數)
        self.player = Player(
            self.canvas,
            PLAYER_CENTER_X,
            HEIGHT - 160,
            asset_dir = ASSETS_DIR,
            walk_fps = WALK_FPS,
            run_fps = RUN_FPS,
            fps = FPS
        )

        self.npc_list = []
        self.npc_girl_list = []
        self.hearts = {}
        self.score = 0
        self.beams = []
        self.followers = []
        # 游標追蹤
        self.mouse_x = PLAYER_CENTER_X
        self.mouse_y = HEIGHT // 2

        # 方向切換
        self.switching = False
        self.switch_steps = 0
        self.switch_dx_scr = 0
        self.switch_world_x = 0

        # 滯留、對話、PK 模式等
        self.hover_npc = None
        self.focus_npc = None
        self.clicked_npc = None
        self.dead_npc = None
        self.attack_npc_girl = []
        self._lp_after_id = None
        self._longpress = False
        self.in_pk_mode = False
        self.pk_bar = None

        # 綁定滑鼠事件
        self._bind_events()

       # 先載入所有樓層資料
        self._preload_all_floors()

        # 直接同步顯示一樓，省去黑幕
        #print(self.floor_data[1].keys(), self.floor_data[1]['bg_img'])
        self._activate_floor(self.floor,use_blackout=False)
        self.is_switching_floor = False   # 確保 _loop() 能正常更新

        # 預載完成後，先啟動「一樓」
        self._switch_down()

        # 設置 UI (血條、分數、暫停按鈕)
        self._setup_ui()

        # 啟動時鐘與主迴圈
        self.clock.update(paused=True)
        self.clock.start()
        self._loop()

    """
    自訂 destroy，自行清除畫布引用，避免錯誤
    """
    def destroy(self):
        self.canvas.delete("all")
        self.ui_canvas.delete("all")
        self.canvas = None
        self.ui_canvas = None
        self.bg_img = None
        super().destroy()

    # ========================================================
    # 事件綁定 (滑鼠移動 / 點擊)
    # ========================================================
    def _bind_events(self):
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _on_mouse_move(self, e):
        self.mouse_x, self.mouse_y = e.x, e.y
        # 判斷滑鼠是否在 NPC 上
        self.hover_npc = None
        for npc in self.npc_list:
            if npc.id is None:
                continue
            coords = self.canvas.coords(npc.id)
            if not coords:
                continue
            x1, y1 = coords
            img_w = npc.current_img.width()
            img_h = npc.current_img.height()
            if abs(e.x - x1) <= img_w // 2 and abs(e.y - y1) <= img_h // 2:
                self.hover_npc = npc
                if self.hover_npc != self.focus_npc:
                    if self.focus_npc is not None :
                        self.focus_npc._on_hover_leave()
                    self.focus_npc = self.hover_npc
                    self.focus_npc._on_hover_enter()
                return

        if self.hover_npc is None and self.focus_npc:
            self.focus_npc._on_hover_leave()
            self.focus_npc = None

        # 如果滑鼠按下後移開原本 NPC，視同放開
        if self.clicked_npc and self.hover_npc != self.clicked_npc:
            if not self.clicked_npc.is_attracted_PK:
                self._on_release(e)

    def _on_press(self, event):
        #print("press")
        if self.player.lose_pk:
            return
        if self.hover_npc and not self.in_pk_mode:
            self.clicked_npc = self.hover_npc
            if self.clicked_npc.is_dead:
                return
            self.dead_npc = self.clicked_npc
            self.player.attracting = True
            self.clicked_npc.is_focused = True
            self.clicked_npc.stopping = True
            self._longpress = False
            self._lp_after_id = self.after(LONGPRESS_MS, self._handle_long_press)

    def _handle_long_press(self):
        # 長按一秒後，若滑鼠仍在同一 NPC，就開始對話或 PK
        self._lp_after_id = None
        if not self.clicked_npc or self.clicked_npc.is_dead:
            return
        if self.hover_npc is None or self.hover_npc is not self.clicked_npc:
            return

        self._longpress = True
        self.attack_npc_girl = []
        # 找出所有在畫面內的 NPC_GIRL 進 PK
        for girl in self.npc_girl_list:
            if girl.is_win or girl.is_lose:
                continue
            scr_x = girl.world_x - self.bg_offset
            if 0 <= scr_x <= WIDTH:
                self.attack_npc_girl.append(girl)
                girl.notice()

        sx = self.player.x + (EYE_OFFSET_X * 2 if self.player.face_right else -EYE_OFFSET_X * 2)
        sy = self.player.y - EYE_OFFSET_Y
        ex = self.clicked_npc.world_x - self.bg_offset
        ey = self.clicked_npc.y - EYE_OFFSET_Y
        beam = LaserBeam(
            canvas     = self.canvas,
            start      = (sx, sy),
            end        = (ex, ey),
            image_path = str(ASSETS_DIR / 'effect' / 'laser_pink.png'),
            steps      = 8,
            delay      = 40,
        )
        self.beams.append(beam)

        if self.attack_npc_girl:
            # 進入 PK 模式
            if not self.in_pk_mode:
                self.in_pk_mode = True
                x = self.clicked_npc.world_x - self.bg_offset
                y = self.clicked_npc.y
                self.pk_bar = LaserBarRectApp(self.canvas,
                                              screen_x=x,
                                              y=y-120,
                                              anim_fps=10,
                                              fps=FPS,
                                              on_finish=self._on_pk_finished)
                for girl in self.attack_npc_girl:
                    girl.enter_pk_mode(x, self.bg_offset)
                    girl_on_canvas_x, girl_on_canvas_y = self.canvas.coords(girl.id_walk)
                    off_x = 30 if girl.face_right else -30
                    sx2 = girl_on_canvas_x + off_x
                    sy2 = girl.y - EYE_OFFSET_Y
                    beam2 = LaserBeam(
                        canvas    = self.canvas,
                        start     = (sx2, sy2),
                        end       = (x, y - EYE_OFFSET_Y),
                        image_path= str(ASSETS_DIR / 'effect' / 'laser_yellow.png'),
                        steps     = 8,
                        delay     = 40,
                    )
                    self.beams.append(beam2)
                self.dead_npc.enter_pk_mode()
        else:
            # 沒有 NPC_GIRL，就進行單純對話
            self.dead_npc = None
            self.clicked_npc.start_dialog(self)
            self.clicked_npc.update(self.bg_offset)

    def _on_pk_finished(self, success: bool):
        if not self.pk_bar:
            return
        self.pk_bar.destroy()
        self.pk_bar = None

        for beam in self.beams[:]:
            beam.destroy()
            if beam in self.beams:
                self.beams.remove(beam)

        if success:
            # 玩家贏
            self.dead_npc.exit_pk_mode(player_win=True)
            for girl in self.attack_npc_girl:
                girl.exit_pk_mode(player_win=True, player_face_r=self.player.face_right)
            self.player.add_dead_npc(self.dead_npc)
            self.dead_npc.follow_player = True
            self.attack_npc_girl.clear()

            heal = BIG_HEART_HEAL # 治癒的血量
            heart = HeartFillClip.instant_create(
                canvas         = self.canvas,
                cx             = self.clicked_npc.world_x,
                screen_x       = self.clicked_npc.world_x - self.bg_offset,
                cy             = self.clicked_npc.y - 120,
                scale          = 2.0,
                target_y       = HEIGHT - 120,
                on_fall_finish = None,
                heal_amount    = heal
            )
            self.hearts[heart.fill_id] = heart

        else:
            # 玩家輸
            self.dead_npc.exit_pk_mode(player_win=False)
            self.player.lose_pk_mode()
            for girl in self.attack_npc_girl:
                girl.exit_pk_mode(player_win=False, player_face_r=self.player.face_right)
            self.health_bar.lose_one_step()

        self.player.attracting = False
        self.in_pk_mode = False
        self.dead_npc = None
        self.attack_npc_girl.clear()
        self.health_bar.lose_one_step()

    def _on_release(self, event):
        #print("release")
        if self.player.lose_pk:
            return
        if self.pk_bar:
            self.pk_bar.on_click()
            self.health_bar.lose_one_step(0.15)
            #點一次加3分
            self._update_score_display(add=3)

        if not self._longpress:
            if self._lp_after_id:
                self.after_cancel(self._lp_after_id)
                self._lp_after_id = None
            if not self.in_pk_mode:
                self.player.attracting = False
        else:
            if not self.in_pk_mode:
                self.clicked_npc.stop_dialog()
                for beam in self.beams[:]:
                    beam.destroy()
                    if beam in self.beams:
                        self.beams.remove(beam)
                for girl in self.npc_girl_list:
                    if girl.shock:
                        girl.shock = False
                        girl.update(self.bg_offset)
                self.player.attracting = False

        if not self.in_pk_mode:
            self.clicked_npc = None
        self._longpress = False

    # ========================================================
    # 預載所有樓層 (背景＋NPC＋NPC_GIRL)
    # ========================================================
    def _preload_all_floors(self):
        for fl in range(1, self.total_floors + 1):
            # 載入背景
            bg_path = ASSETS_DIR / f"bg{fl}.png"
            bg = Image.open(bg_path)
            nh = HEIGHT
            nw = int(bg.width * nh / bg.height)
            bg = bg.resize((nw, nh), Image.Resampling.LANCZOS)
            bg_img_tk = ImageTk.PhotoImage(bg)


            # 用一個「暫時 Canvas」來建構 NPC 與 NPC_GIRL（不顯示）
            temp_canvas = tk.Canvas(self, width=WIDTH, height=HEIGHT)
            npc_list, girl_list = self._generate_npcs(temp_canvas, nw)

            # 儲存進 floor_data
            self.floor_data[fl] = {
                'bg_img': bg_img_tk,
                'npc_list': npc_list,
                'girl_list': girl_list,
                'bg_width': nw
            }

    # --------------------------------------------------------
    # 生成單層的 NPC / NPC_GIRL 列表
    # --------------------------------------------------------
    def _generate_npcs(self, canvas, bg_width):
        npc_list = []
        girl_list = []
        npc_asset_dir = ASSETS_DIR / 'npc'
        margin = 500
        spacing = (bg_width - 2 * margin) // (self.npc_count + 2)
        y_choices = [HEIGHT - 110, HEIGHT - 130, HEIGHT - 190, HEIGHT - 210]

        # 建立 NPC
        for i in range(self.npc_count):
            y = random.choice(y_choices)
            npc = NPC(
                canvas,
                npc_asset_dir,
                start_x = margin + i * spacing + random.randint(0, spacing // 2),
                y = y,
                walk_fps = NPC_WALK_FPS,
                fps = FPS,
                world_left = 300,
                world_right = bg_width - 300,
                npc_num = self.npc_count,
                player = None,  # 稍後再指派真實 player
                game = self 
            )
            npc_list.append(npc)

        # 建立 NPC_GIRL
        for i in range(4):
            y = random.choice(y_choices)
            girl = NPC_GIRL(
                canvas,
                npc_asset_dir,
                start_x = random.randint(1000 + i * 500, 1000 + (i + 1) * 500),
                y = y,
                walk_fps = NPC_WALK_FPS,
                fps = FPS,
                world_left = 300,
                world_right = bg_width - 300,
                game = self 
            )
            girl_list.append(girl)

        return npc_list, girl_list

    # ========================================================
    # 切換樓層：先顯示黑色遮罩，再延遲呼叫 _show_floor_content()
    # ========================================================
    def _activate_floor(self, floor ,use_blackout=True):
        if use_blackout:
            # 一定要把回傳的 id 存到 self.id_black_canvas
            self.id_black_canvas = self.canvas.create_rectangle(
                0, 0, WIDTH, HEIGHT,
                fill='black', tags='blackout'
            )
            # 改回用 after_idle 比較保險：確保在所有清畫布、貼場景完成後再 call _show_floor_content
            self.canvas.after_idle(
                lambda: self._show_floor_content(self.floor_data[floor])
            )
            self.canvas.tag_raise(self.player.id)
        else:
            # use_blackout=False 時就不用畫黑幕
            self._show_floor_content(self.floor_data[floor])
            self.canvas.tag_raise(self.player.id)

    def _show_floor_content(self, data):
        # 如果之前真的有 overlay，也一定要先把它刪掉
        if getattr(self, 'id_black_canvas', None) is not None:
            self.canvas.delete(self.id_black_canvas)   # 刪掉黑幕
            self.id_black_canvas = None
        new_floor = self.floor
        old_floor = getattr(self, 'prev_floor', None)


         # 1. Hide（或刪除）舊樓層的 NPC/Girl 圖片
        if old_floor is not None:
            # 只針對 NPC、NPC_GIRL tag 做刪除
            self.canvas.delete("npc")       
            self.canvas.delete("npc_girl") 
        
        # 設定背景
        self.bg_img = data['bg_img']
        if self.first_load:
            self.first_load = False
            self.bg_offset = (self.bg_img.width() - WIDTH) // 2 
        self.max_offset = data['bg_width'] - WIDTH
        self.canvas.create_image(-self.bg_offset, 0, image=self.bg_img, anchor='nw', tags='bg')
        self.canvas.tag_lower('bg')
        
        if old_floor is not None:
            for old_npc in self.floor_data[old_floor]['npc_list']:
                if old_npc.is_dead and old_npc.follow_player:
                    if old_npc not in self.followers:
                        self.followers.append(old_npc)
                old_npc.hide()
            for old_girl in self.floor_data[old_floor]['girl_list']:
                old_girl.hide()

       

        new_npc_list = data['npc_list']
        new_girl_list = data['girl_list']
        
        for npc in new_npc_list:
            if not npc.is_dead:
                npc.canvas = self.canvas
                npc.player = self.player
                npc.reset()

        for girl in new_girl_list:
            if not girl.is_lose and not girl.is_win:
                girl.canvas = self.canvas
                girl.reset()


        # 再把跨樓層「正在跟隨玩家」的 NPC 也 show() 一次
        #    self.followers 存的都是全遊戲裡所有 follow_player == True 的實例
        for follower in self.followers:
            self.player.add_dead_npc(follower)

            
        self.npc_list = new_npc_list + [f for f in self.followers if f not in new_npc_list]
        self.npc_girl_list = new_girl_list.copy()
        
        self.player.canvas = self.canvas
        self.player.face_right = False if self.player.face_right else True
       
        self.player.draw()

        self.prev_floor = new_floor
        

    # ========================================================
    # HoverButton 顯示與隱藏
    # ========================================================
    def _show_floor_button(self, hit_right_edge:bool):
        """
        根據 self.floor，目前是 1、2 還是 3，決定畫哪些按鈕：
          一樓 (1) → 只顯示「上樓」  
          二樓 (2) → 顯示「上樓」、「下樓」  
          三樓 (3) → 只顯示「下樓」
        """

        # 先把可能殘留的按鈕都刪掉
        self._hide_floor_button()

        x_center = WIDTH - 120 if hit_right_edge else 120
        y_center = HEIGHT // 2

        if self.floor == 1:
            # 一樓：只有「上樓」按鈕
            self.up_btn = HoverButton(
                canvas=self.canvas,
                x=x_center,
                y=y_center,
                img_normal_path=str(ASSETS_DIR / "up_button.png"),
                img_hover_path =str(ASSETS_DIR / "up_button_hover.png"),
                command=self._switch_up
            )
            self.down_btn = None

        elif self.floor == 2:
            # 二樓：上下樓各一個
            self.up_btn = HoverButton(
                canvas=self.canvas,
                x=x_center,
                y=y_center - 50,  # 比較靠上
                img_normal_path=str(ASSETS_DIR / "up_button.png"),
                img_hover_path =str(ASSETS_DIR / "up_button_hover.png"),
                command=self._switch_up
            )
            self.down_btn = HoverButton(
                canvas=self.canvas,
                x=x_center,
                y=y_center + 50,  # 比較靠下
                img_normal_path=str(ASSETS_DIR / "down_button.png"),
                img_hover_path =str(ASSETS_DIR / "down_button_hover.png"),
                command=self._switch_down
            )

        elif self.floor == 3:
            # 三樓：只有「下樓」按鈕
            self.up_btn = None
            self.down_btn = HoverButton(
                canvas=self.canvas,
                x=x_center,
                y=y_center,
                img_normal_path=str(ASSETS_DIR / "down_button.png"),
                img_hover_path =str(ASSETS_DIR / "down_button_hover.png"),
                command=self._switch_down
            )

    def _hide_floor_button(self):
        if hasattr(self, "up_btn") and self.up_btn:
            self.up_btn.destroy()
            self.up_btn = None
        if hasattr(self, "down_btn") and self.down_btn:
            self.down_btn.destroy()
            self.down_btn = None
      # --------------------- 上樓 / 下樓 的實作 ---------------------
    def _switch_up(self):
        """
        把 is_switching_floor 設成 True → 顯示黑布 → 在後台（after_idle）真正載入上一層
        """
        if self.floor >= self.total_floors:
            return  # 本來就是三樓，就不能再往上一樓
        
        self.is_switching_floor = True

        # 1) 畫個黑矩形遮住整個畫布
        self._overlay = self.canvas.create_rectangle(
            0, 0, WIDTH, HEIGHT,
            fill="black", outline=""
        )
        # 2) 等候 idle 時機再去做真正載入↓
        self.after_idle(self._do_switch_up)

    def _do_switch_up(self):
        # a) 刪除現有場景
        #self.canvas.delete("all")
        self.canvas.delete("bg")
        self.canvas.delete("npc")
        self.canvas.delete("npc_girl")
        self.canvas.delete("blackout")
        self.canvas.delete("player")
        # b) 把 floor + 1
        
        self.floor += 1
        # c) 重新把 floor 內容 activate
        self._activate_floor(self.floor)
        # d) 把黑布刪掉
        self.canvas.delete(self._overlay)
        self._overlay = None
        # e) 重新顯示對應層的「上下樓」按鈕
        self.is_switching_floor = False


    def _switch_down(self):
        """
        同理，把 is_switching_floor 設成 True → 畫黑布 → after_idle 載入下一層
        """
        if self.floor <= 1:
            return  # 本來就是一樓，就不能再往下一樓
        self.is_switching_floor = True

        self._overlay = self.canvas.create_rectangle(
            0, 0, WIDTH, HEIGHT,
            fill="black", outline=""
        )
        self.after_idle(self._do_switch_down)

    def _do_switch_down(self):
        self.canvas.delete("bg")
        self.canvas.delete("npc")
        self.canvas.delete("npc_girl")
        self.canvas.delete("blackout")
        self.canvas.delete("player")
        
        self.floor -= 1
        self._activate_floor(self.floor)
        self.canvas.delete(self._overlay)
        self._overlay = None
        self.is_switching_floor = False

   
    # --------------------------------------------------------
    # 每幀更新
    # --------------------------------------------------------
    def _update(self):
        # =====================================================
        # 0. 表示愛心已填滿，玩家可以開始移動，要同步更新愛心位置     
        # =====================================================
        # 收集要更新的 heart
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
        # 1-1.玩家跌倒中(無視所有滑鼠事件)
        # =====================================================
        if self.player.lose_pk:
            self._update_npcs() 
            self.player.update()
            return

        # =====================================================
        # 1-2. 如果滑鼠懸停在 NPC 上，或是在吸引模式，先讓玩家站立不動，然後只更新 NPC
        # =====================================================
        # hover_npc: 已由 _on_mouse_move 更新
        if (self.player.attracting) or (self.hover_npc and self.hover_npc.is_hovered):
            # player 切站立圖（需要在 Player 裡實作）
            y = self.clicked_npc if self.player.attracting else self.hover_npc
            if not self.in_pk_mode :
                self.player.set_stand_image(focus_npc=y , mouse_x=self.mouse_x)
            self._update_npcs()      
            return

        # =====================================================
        # 1-3. 否則，如果游標在 player 身上 → 靜止並顯示 idle/frame0
        # =====================================================
        pw = self.player.anim.frames[0].width()
        ph = self.player.anim.frames[0].height()
        self.player.hover = (abs(self.mouse_x - self.player.x) <= pw/2 and
                            abs(self.mouse_y - self.player.y) <= ph/2)

        if self.player.hover:
            self.player.idle = True
            self.player.update()    # 顯示 idle 動畫
            self._update_npcs()        
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
                max_x = PLAYER_LEFT_X if self.player.face_right else PLAYER_RIGHT_X
                if self.player.face_right:
                    self.player.x = min(max(nx, min_x), max_x-100)
                else:
                    self.player.x = max(min(nx, min_x), max_x+100)
                

        # ---------- 5. idle (玩家已無法再前進) 判斷 ----------
        # 右邊滾到底：背景在最右 + 玩家面向右 + 已站在畫面最右可顯示位置 (= CENTER_X)
        hit_right_edge = (
            self.player.face_right and
            self.bg_offset >= self.max_offset and
            self.player.x >= PLAYER_LEFT_X-100 and
            self.player.vx > 0                    # 還想往右
        )

        # 左推到底：背景在最左 + 玩家面向左 + 已站在畫面最左可顯示位置 (= CENTER_X)
        hit_left_edge = (
            (not self.player.face_right) and
            self.bg_offset <= 0 and
            self.player.x <= PLAYER_RIGHT_X+100 and
            self.player.vx < 0                    # 還想往左
        )

        self.player.idle = self.player.hover or hit_right_edge or hit_left_edge
        
        if self.player.idle and (hit_left_edge or hit_right_edge):
            # 如果一開始 up_btn/down_btn 都還沒定義，就呼叫顯示函式
            if self.up_btn is None and self.down_btn is None:
                self._show_floor_button(hit_right_edge)
        else:
            # 玩家離開邊界範圍 → 檢查哪個按鈕還存在，就先把它刪掉
            if self.up_btn:
                self.up_btn.destroy()
                self.up_btn = None
            if self.down_btn:
                self.down_btn.destroy()
                self.down_btn = None
        # ---------- 6. 更新影像、確認有沒有吃到愛心 ----------
        self._check_heart_collision()
        self.player.update()
       
        # ---------- 7. 更新影像 ----------
        self._update_npcs()    
        
        layers = []
        # 玩家
        coords = self.canvas.coords(self.player.id)
        if len(coords) == 2:
            px, py = coords
            layers.append((self.player.id, py))

        # NPC 每個 layer 都要排序
        for npc in self.npc_list:
            if npc.id is None: # npc.py->start_dialog->remove_npc方法中有npc.i=None的操作
                continue
            for cid in (npc.id_walk, npc.id_flash, npc.id_weak, npc.id_hover,npc.id_died):
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
            for dead_id in self.player.dead_npc_ids:
                try:
                    _, yy = self.canvas.coords(dead_id)
                except Exception:
                    continue
                layers.append((dead_id, yy))
        # 按 y 升冪排序：y 小的先 raise，y 大的在最上
        layers.sort(key=lambda t: t[1])
        for cid, _ in layers:
            self.canvas.tag_raise(cid)

    # --------------------------------------------------------
    # 判定速度與是否要切換方向（觸發「切換背景」的過程）
    # --------------------------------------------------------
    def _determine_speed(self) -> int:
        if self.player.set_direction(self.mouse_x):
            tgt = PLAYER_RIGHT_X if self.player.face_right else PLAYER_LEFT_X
            self.switching = True
            self.switch_steps = 15
            self.switch_dx_scr = (tgt - self.player.x) / 15
            self.switch_world_x = self.bg_offset + self.player.x

        dx = self.mouse_x - self.player.x
        if abs(dx) < 8:
            return 0
        return RUN_SPEED if abs(dx) > WIDTH * 0.3 else WALK_SPEED

    # --------------------------------------------------------
    # 判斷有沒有吃到愛心
    # --------------------------------------------------------
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
                
                self.health_bar.gain(heart.heal_amount)
                score_add = 1500 if heart.heal_amount == BIG_HEART_HEAL else 500
                self._update_score_display(add=score_add)
                # print("eat"+ str(heart.heal_amount))

    # --------------------------------------------------------
    # 更新所有 NPC 與 NPC_GIRL
    # --------------------------------------------------------
    def _update_npcs(self):
        for npc in self.npc_list:
            if npc.id is None:
                continue
            npc.update(self.bg_offset)
            if not npc.is_attracted_noPK and not npc.is_attracted_PK:
                npc.move(NPC_WALK_SPEED)

        for girl in self.npc_girl_list:
            if girl.id is None:
                continue
            girl.update(self.bg_offset)
            if not girl.stopping and not girl.shock and not girl.in_pk_mode:
                girl.move(NPC_WALK_SPEED)
            if girl.is_win or girl.is_lose:
                screen_x = girl.world_x - self.bg_offset
                if (screen_x < 0 or screen_x > WIDTH) or girl.y<0:
                    self.canvas.delete(girl.id_walk)
                    self.canvas.delete(girl.id_exclamation)
                    self.npc_girl_list.remove(girl)
                    
    # ========================================================
    # 建立 UI (血條、暫停按鈕、時鐘、分數)
    # ========================================================
    def _setup_ui(self):
        self.health_bar = HealthBar(self.ui_canvas, x=20, y=20, spacing=35, max_hearts=9, initial_full=4)

        # 暫停按鈕
        self.pause_btn = self.ui_canvas.create_oval(840, 5, 880, 45, fill="red", outline="white")
        self.pause_text = self.ui_canvas.create_text(860, 25, text="||", fill="white", font=("Arial", 14, "bold"))
        self.ui_canvas.tag_bind(self.pause_btn, "<Button-1>", self._toggle_pause)
        self.ui_canvas.tag_bind(self.pause_text, "<Button-1>", self._toggle_pause)

        # 時鐘
        self.clock = Clock(self.clock_canvas, center_x=25, center_y=25, radius=20, total_seconds=self.game_time)

        # 分數文字
        self.score_text = self.ui_canvas.create_text(650, 25, text=f"Score: {self.score}", fill="white", font=("Arial", 24))

    def _update_score_display(self, add=0):
        self.score += add
        self.ui_canvas.itemconfig(self.score_text, text=f"Score: {self.score}")

    # 暫停
    def _toggle_pause(self, event=None):
        self.paused = not self.paused
        if self.paused:
            self.ui_canvas.config(height=HEIGHT, bg="white")
            self._show_pause_menu()
        else:
            self._hide_pause_menu()
            self.ui_canvas.config(height=50, bg="#007500")

    def _show_pause_menu(self):
        overlay = self.ui_canvas.create_rectangle(300, 100, 600, 300, fill="white", outline="black")
        text_continue = self.ui_canvas.create_text(450, 160, text="繼續遊戲", font=("Arial", 14), fill="black")
        text_back = self.ui_canvas.create_text(450, 220, text="返回主頁面", font=("Arial", 14), fill="black")
        text_quit = self.ui_canvas.create_text(450, 280, text="結束遊戲", font=("Arial", 14), fill="black")

        self.pause_menu_items = [overlay, text_continue, text_back, text_quit]
        self.ui_canvas.tag_bind(text_continue, "<Button-1>", lambda e: self._toggle_pause())
        self.ui_canvas.tag_bind(text_back, "<Button-1>", lambda e: self._return_to_main_menu())
        self.ui_canvas.tag_bind(text_quit, "<Button-1>", lambda e: self.destroy())

    def _hide_pause_menu(self):
        for item in self.pause_menu_items:
            self.ui_canvas.delete(item)
        self.pause_menu_items.clear()

    def start_settlement(self):
        """
        啟動結算流程：讓 player 及其身後的 dead NPC 開始往右跑，
        並準備一個 set 來記錄哪些 dead NPC 已經跳過 +1000 分數。
        """
        self.in_settlement = True
        # ----------------------------------------------------
        # (A) 把所有「活著的 NPC」從畫布移除
        # ----------------------------------------------------
        for npc in self.npc_list:
            try:
                self.canvas.delete(npc.id)
            except:
                pass
        # ----------------------------------------------------
        # (B) 把所有「光束 (beams)」從畫布移除
        # ----------------------------------------------------
        for beam in self.beams:
            try:
                self.canvas.delete(beam.id)
            except:
                pass
        self.beams.clear()
        # 讓玩家面向右、改用「走路速度」
        self.player.face_right = True
        self.player.vx = WALK_SPEED    # 由 RUN_SPEED 改成 WALK_SPEED
        #把player移到左邊 開始動畫
        self.player.x = 150
        self.player.update()
        # 改用「走路動畫」，讓結算看起來更一致
        self.player.anim = (
            self.player.anim_right_walk if self.player.face_right
            else self.player.anim_left_walk
        )

        # 重置計分用資料結構
        self.scored_npc_ids.clear()

        # 停用所有滑鼠互動
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")

        # （選）可整個背景暫停不動或直接靜止
        # 不要再捲動背景了，所以不動 background
        # 你可以讓 bg_offset 固定住，或直接不在 settlement 中執行 _update() 的背景邏輯
        # 於是，在 settlement_update() 只移動 player 與 dead NPC
    def animate_score_text(self, text_id, steps=20, dy=2, fade_step=5):
        """
        讓剛出現的「+1000」文字在 steps 幀內往上移動 dy 像素，
        然後逐步變淡，最後刪掉。
        """
        def _step(count):
            if count <= 0:
                try:
                    self.canvas.delete(text_id)
                except:
                    pass
                return
            self.canvas.move(text_id, 0, -dy)
            if count < fade_step:
                if count <= fade_step // 2:
                    self.canvas.itemconfig(text_id, fill="#888888")
                else:
                    self.canvas.itemconfig(text_id, fill="#CCCCCC")
            self.after(int(1000 / FPS), lambda: _step(count - 1))

        _step(steps)
    def settlement_update(self):
        """
        結算模式每幀更新：
        1. 先讓 player 往右移動並更新畫布座標。
        2. 再依序把每隻 dead NPC 平移同樣的像素，然後檢查是否觸發 +1000、是否要刪除。
        3. 如果還有死 NPC，下一幀繼續；如果都跑完了，就等 5 秒後回主選單。
        """

        # --------------------------------------
        # （一）1) 移動 player
        # --------------------------------------
        self.player.x += self.player.vx
        self.player.update(in_settlement=self.in_settlement)  # 把 player.id 更新到 (self.player.x, self.player.y)

        # --------------------------------------
        # （二）2) 移動死掉的 NPC 並檢查跳分/刪除
        # --------------------------------------
        to_remove = []
        # 避免刪除跳號
        for dead_id in list(self.player.dead_npc_ids):
            # 先把 dead NPC 移動
            self.canvas.move(dead_id, self.player.vx, 0)

            coords = self.canvas.coords(dead_id)
            if not coords:
                continue
            dead_x, dead_y = coords

            # (a) 如果還沒跳過 +1000，且 dead_x >= WIDTH - 350，就觸發 +1000
            if dead_id not in self.scored_npc_ids and dead_x >= WIDTH - 350:
                text_id = self.canvas.create_text(
                    dead_x, dead_y - 50,
                    text="+1000",
                    fill="yellow",
                    font=("Arial", 18, "bold")
                )
                # 跳分動畫、加分
                self.animate_score_text(text_id)
                self._update_score_display(add=1000)
                self.scored_npc_ids.add(dead_id)

            # (b) 如果 dead NPC 已經完全跑出畫面右側 (dead_x > WIDTH + 150)，才加入待刪
            if dead_x > WIDTH + 150:
                to_remove.append(dead_id)

        # 將所有跑出畫面的 dead NPC 從列表與畫布刪除
        for dead_id in to_remove:
            if dead_id in self.player.dead_npc_ids:
                self.player.dead_npc_ids.remove(dead_id)
            try:
                self.canvas.delete(dead_id)
            except:
                pass

        # --------------------------------------
        # （三）3) 更新 player 動畫幀
        # --------------------------------------
        img = self.player.anim.next()
        self.canvas.itemconfig(self.player.id, image=img)

        # --------------------------------------
        # （四）4) 檢查是否所有 dead NPC 都跑完
        # --------------------------------------
        if not self.player.dead_npc_ids:
            # 全部跑完 → 讓畫面停留 5 秒，再回主選單(暫時這樣)
            self.after(5000, self._return_to_main_menu)
        else:
            # 還有 dead NPC 在畫面 → 下一幀繼續 settlement_update
            self.after(int(1000 / FPS), self.settlement_update)
    # --------------------------------------------------------
    # 返回主選單
    # --------------------------------------------------------
    def _return_to_main_menu(self):
        self.destroy()
        subprocess.Popen([sys.executable, "main_menu.py"])
    '''
 # ========================================================
    # 主迴圈 (定時呼叫 _update)
    # ========================================================
    def _loop(self):
        if self.health_bar.is_empty():
            self._return_to_main_menu()
            return
        
        # 如果還在切換樓層，就 skip _update()，直到切換流程做完
        if not self.is_switching_floor:
            # 正常遊戲更新
            if hasattr(self, 'clock'):
                self.clock.update(paused=self.paused)
            if not self.paused and not self.clock.finished:
                self._update()
            elif self.clock.finished:
                self._return_to_main_menu()
                return
            
        self.after(int(1000 / FPS), self._loop)
    '''
   
    def _loop(self):
        # 1. 如果血條歸零，或時間到，就進入結算
        if self.health_bar.is_empty():
            if not self.in_settlement:
                # 啟動一次結算（只做 start_settlement，然後直接跑第一個 settlement_update）
                self.start_settlement()
                self.settlement_update()   # 立刻呼叫 settlement_update
            # 既然已經啟動結算，就不再做其他一般邏輯
            return
        if not self.is_switching_floor:
            # 2. 時鐘更新（若有）
            if hasattr(self, 'clock'):
                self.clock.update(paused=self.paused)

            if not self.paused:
                # 時間到 → 同理進入結算
                if self.clock.finished:
                    if not self.in_settlement:
                        self.start_settlement()
                        self.settlement_update()  # <- 立刻呼叫 settlement_update
                    return

                # 3. 一般遊戲更新（只有在沒有進入結算時）
                self._update()

        # 4. 若不進入結算，就繼續下一個 _loop
        self.after(int(1000 / FPS), self._loop)

if __name__ == "__main__":
    ElectricEyeGame().mainloop()
