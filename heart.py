import tkinter as tk
import math
import time

class HeartFillClip:
    def __init__(self, canvas, cx, cy, scale, target_y = 280, on_fall_finish=None):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.scale = scale
        self.steps = 200
        self.fill_ratio = 0.0  # 從 0.0 到 1.0
        self.delay = 30
        self.increment = 0.02

        self.start_time = time.time()
        self.duration = 2.0  # sec，填滿所需時間

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
            self.outline_points, outline="black", fill="", width=2
        )

        self.fill_id = None #逐步填滿時，要先把上一幀的狀況刪掉
        self.stopped = False
        self.animate_fill()

    def compute_heart_points(self):
        points = []
        for i in range(self.steps):
            t = (i / self.steps) * 2 * math.pi
            x = 16 * math.sin(t)**3
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            x *= self.scale
            y *= -self.scale
            points.append((self.cx + x, self.cy + y))
        return points

    def animate_fill(self):
        if self.fill_id:
            self.canvas.delete(self.fill_id)
        if self.stopped:
            return  # 停止更新
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
                fill="red",
                outline="",
                tags='filled_heart' # 獨立愛心的tag避免被刪
            )

        # 更新比例
        self.fill_ratio += self.increment
        if self.fill_ratio <= 1.03: # 用1.0會缺一塊 可能是浮點數精度問題?
            self.canvas.after(self.delay, self.animate_fill)
        else:
            # 填滿後啟動掉落動畫
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
        def step():
            if not self.fill_id:
                return
            # 取得目前座標
            points = self.canvas.coords(self.fill_id)# 回傳愛心所有頂點的座標
            if not points:
                return
            xs = points[::2] # 從頭開始，每隔 2 個取一次：取出所有 x 值
            ys = points[1::2]# 從第 1 個開始，每隔 2 個取一次：取出所有 y 值
            if not xs or not ys:
                return
            x = float(sum(xs) / len(xs))
            y = float(sum(ys) / len(ys))

            dx = 1.5 # 往右速度
            dy = self.fall_vy + self.gravity * self.t # 往下
            self.canvas.move(self.fill_id, dx, dy)
            self.t += 1
            # 檢查是否到底
            if y + dy >= self.target_y:
                delta_y = self.target_y - y
                self.canvas.move(self.fill_id, 0, delta_y)
                if self.on_fall_finish:
                    self.on_fall_finish() # 為建立時傳入的remove_npc函式
                return
            self.canvas.after(30, step)
        step()
if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(root, width=500, height=500, bg="white")
    canvas.pack()

    HeartFillClip(canvas, cx=250, cy=280, scale=5)

    root.mainloop()
