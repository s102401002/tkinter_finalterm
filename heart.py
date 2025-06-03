import tkinter as tk
import math
import time

class HeartFillClip:
    global_duration = 2.0
    def __init__(self, canvas, cx, screen_x, cy, scale, target_y = 280, on_fall_finish=None,heal_amount=1.0):
        self.canvas = canvas
        self.world_x = cx  # 記錄真實世界座標
        self.bg_offset = cx-screen_x
        self.screen_x = screen_x  # 初始時等於畫面座標
        self.cy = cy
        self.scale = scale
        self.heal_amount=heal_amount
        self.steps = 100
        self.fill_ratio = 0.0  # 從 0.0 到 1.0
        self.if_startfall = False
        self.delay = 30
        self.increment = 0.02

        self.start_time = time.time()
        self.duration = HeartFillClip.global_duration    # sec，填滿所需時間
        self.fall_finished = False
        
        '''
        填滿後掉落所需參數
        '''
        self.t = 0
        self.fall_vy = -2   # 初速度（可調整）
        self.gravity = 0.5  # 重力加速度（可調整）
        self.target_y = target_y
        self.on_fall_finish = on_fall_finish
        

        self.outline_points = self.compute_heart_points()
        self.outline_id = self.canvas.create_polygon(
            self.outline_points, 
            outline="#FF299B", 
            fill="", 
            width=3,
            #joinstyle = round
        )

        self.fill_id = None #逐步填滿時，要先把上一幀的狀況刪掉
        self.stopped = False
        self.animate_fill()

    def compute_heart_points(self):
        points = []
        for i in range(self.steps):
            t = (i / self.steps) * 2 * math.pi
            x = 16 * math.sin(t)**3 * self.scale
            y = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)) * self.scale
           
            points.append((self.screen_x + x, self.cy + y))
        return points

    def animate_fill(self):
        # 每次 animate_fill 前，重建 outline
        if self.stopped:
            return  # 停止更新
        if self.outline_id:
            self.canvas.delete(self.outline_id)
        self.outline_points = self.compute_heart_points()
        self.outline_id = self.canvas.create_polygon(
            self.outline_points, outline="#FF299B", fill="", width=3
        )
        if self.fill_id:
            self.canvas.delete(self.fill_id)
        
        # 時間驅動的填滿比例
        elapsed = time.time() - self.start_time
        self.fill_ratio = elapsed / self.duration

        # 重新生成遮罩心形：只顯示低於某一高度的點
        y_values = [y for (_, y) in self.outline_points]
        min_y = min(y_values)
        max_y = max(y_values)
        threshold_y = max_y - (max_y - min_y) * self.fill_ratio
        clipped_points = [
            (x, y) for (x, y) in self.outline_points if y > threshold_y
        ]

        if len(clipped_points) >= 3:
            self.fill_id = self.canvas.create_polygon(
                clipped_points,
                fill="#FF99FF",
                outline="#FF299B", 
                tags=('filled_heart'),
                width = 5
            )

        # 更新比例
        self.fill_ratio += self.increment
        if self.fill_ratio <= 1.03: # 用1.0會缺一塊 可能是浮點數精度問題?
            self.canvas.after(self.delay, self.animate_fill)
        else:
            if self.on_fall_finish:
                self.on_fall_finish() ## call back通知npc
            # 填滿後啟動掉落動畫
            self.if_startfall = True
            self._start_fall()
            
    def stop(self):
        self.stopped = True
        # 不刪除已填滿的 fill_id
        if self.fill_ratio < 1.03:
            if self.fill_id:
                self.canvas.delete(self.fill_id)
        if self.outline_id:
            self.canvas.delete(self.outline_id)
    
    def _start_fall(self):
        if self.outline_id:
            self.canvas.delete(self.outline_id)
        self._fall_parabola()

    def _fall_parabola(self):
        """以拋物線 y = v0·t + ½gt² 掉落；整顆心用 move() 直移不重畫。"""
        # ① 若填滿階段留下殘影，先清掉再畫一顆完整心形
        if self.fill_id:
            self.canvas.delete(self.fill_id)
        self.fill_id = self.canvas.create_polygon(
            self.compute_heart_points(),
            fill="#FF99FF",outline="#FF299B", tags='filled_heart',width=3
        )

        self.t = 0                       # 時間步
        def step():
            dy  = self.fall_vy + self.gravity * self.t
            self.cy += dy                # 更新邏輯座標（若之後要碰撞可以用到）
            self.t  += 1

            # ② 只搬移，不重畫
            self.canvas.move(self.fill_id, 0, dy)

            # ③ 落地判斷 —— 取所有 y，計算中心點
            ys = self.canvas.coords(self.fill_id)[1::2]   # 每 2 個取一次 ➜ y 座標
            center_y = sum(ys) / len(ys)
            if center_y >= self.target_y:
                # 精準貼地
                self.canvas.move(self.fill_id, 0, self.target_y - center_y)
                self.fall_finished = True
                self.if_startfall = False
                return
            self.canvas.after(30, step)
        step()
    
    
    def update(self, bg_offset: int):
        """同步世界 → 螢幕座標"""
        self.bg_offset = bg_offset
        if not self.fill_id:      # 只要多邊形存在就更新，不管是否落地
            return
        self.screen_x = self.world_x - self.bg_offset
        pts = self.compute_heart_points()
        flat = [c for xy in pts for c in xy]
        self.canvas.coords(self.fill_id, *flat)
    @classmethod
    def instant_create(cls, canvas, cx, screen_x, cy, scale, target_y=280, on_fall_finish=None,heal_amount=1.0):
        """產生一顆立即填滿、直接掉落的愛心"""
        heart = cls.__new__(cls)  # 跳過 __init__
        heart.canvas = canvas
        heart.world_x = cx
        heart.bg_offset = cx - screen_x
        heart.screen_x = screen_x
        heart.cy = cy
        heart.scale = scale
        heart.target_y = target_y
        heart.on_fall_finish = on_fall_finish
        heart.heal_amount = heal_amount # 吃到愛心後的治癒量
        heart.fill_id = None
        heart.outline_id = None
        heart.fall_finished = False
        heart.if_startfall = True
        heart.steps = 30
        heart.outline_points = heart.compute_heart_points()
        
        # 直接畫出完整填滿的心形
        heart.fill_id = heart.canvas.create_polygon(
            heart.outline_points,
            fill="#FF99FF",
            outline="#FF299B", 
            tags='heart',
            width=3
        )

        # 立即啟動掉落
        heart.t = 0
        heart.fall_vy = -2
        heart.gravity = 0.5
        heart._fall_parabola()

        return heart
   
    
if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(root, width=300, height=500, bg="white")
    canvas.pack()

    # HeartFillClip(canvas, cx=250, cy=280, scale=5)
    HeartFillClip.instant_create(canvas, cx=250,screen_x=100, cy=280, scale=5)
    root.mainloop()