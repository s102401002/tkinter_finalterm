import tkinter as tk
import math
import time

class Heart:
    def __init__(self, canvas, cx, cy, scale):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.scale = scale
        self.steps = 30
        self.fill_ratio = 1.03
        self.decrement = 0.1
        self.delay = 30

        self.outline_points = self.compute_heart_points()
        self.outline_id = self.canvas.create_polygon(
            self.outline_points, outline="black", fill="", width=2, tags="health_ui"
        )
        self.fill_id = None
        self.fill_ratio = 0.0
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

    def draw(self):
        self.delete()
        y_values = [y for (_, y) in self.outline_points]
        min_y = min(y_values)
        max_y = max(y_values)
        threshold_y = max_y - (max_y - min_y) * self.fill_ratio
        clipped = [(x, y) for (x, y) in self.outline_points if y > threshold_y]
        if len(clipped) >= 3:
            self.fill_id = self.canvas.create_polygon(clipped, fill="red", outline="", tags="health_ui")

    def animate_reverse_step(self, reduce_by=None):
        if reduce_by == None:
            reduce_by = self.decrement
        self.fill_ratio -= reduce_by  # 每次呼叫扣多少
        if self.fill_ratio <= 0:
            self.fill_ratio = 0
            self.draw()
            # self.delete() 要保留黑色框所以先不刪
            return
        self.draw()

    def delete(self):
        if self.fill_id:
            self.canvas.delete(self.fill_id)
            self.fill_id = None
        # if self.outline_id:
        #     self.canvas.delete(self.outline_id)
        #     self.outline_id = None
class HealthBar:
    def __init__(self, canvas, x, y, spacing=50, max_hearts=9, initial_full=4):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.spacing = spacing
        self.max_hearts = max_hearts
        self.initial_full = initial_full
        self.loss_speed = 0.1 # 與Heart->self.decrement配合
        self.hearts = []

        for i in range(self.max_hearts):
            cx = x + i * spacing
            h = Heart(canvas, cx, y, scale=0.8)
            self.hearts.append(h)
        self._draw_initial()
    def is_empty(self):
        """如果所有愛心都已扣光，回傳 True"""
        return all(h.fill_ratio <= 0 for h in self.hearts)
    def _draw_initial(self):
        for i in range(self.initial_full):
            self.hearts[i].fill_ratio = 1.03
            self.hearts[i].draw()
    def lose_one_step(self, loss_speed=None):
        if loss_speed == None:
            loss_speed = self.loss_speed
        for idx, heart in reversed(list(enumerate(self.hearts))):
            if heart.fill_ratio > 0:
                # print(f"正在扣第 {idx} 顆愛心（從左數）目前 fill_ratio={heart.fill_ratio:.2f}")
                heart.animate_reverse_step(loss_speed)
                break
    def gain(self, increase):
        if increase == None or increase < 0:
            print(f'increase = {increase} is illegal')
            return
        increase *= 1.03  # 轉為 fill_ratio 單位
        for idx, heart in list(enumerate(self.hearts)):
            if increase <= 0:
                break
            if heart.fill_ratio < 1.03:
                diff = 1.03 - heart.fill_ratio
                if increase > diff:
                    heart.fill_ratio = 1.03
                    increase -= diff
                else:
                    heart.fill_ratio += increase
                    increase = 0
                heart.draw()

if __name__ == "__main__":
    root = tk.Tk()
    canvas = tk.Canvas(root, width=500, height=500, bg="white")
    canvas.pack()

    # h = Heart(canvas, cx=250, cy=280, scale=5)
    # h.draw()  # 先畫滿
    
    # def run_animation_until(threshold=0.5):
    #     if h.fill_ratio > threshold:
    #         h.animate_reverse_step()
    #         root.after(h.delay, lambda: run_animation_until(threshold))

    # root.after(1000, lambda: run_animation_until(0.5))
    hb = HealthBar(canvas, x=20, y=60, spacing=50, max_hearts=9, initial_full=4)

    # === 自動扣血區 ===
    loss_active = [False]  # 用 list 包裝以便修改閉包內狀態

    def trigger_loss():
        if loss_active[0]:
            hb.lose_one_step()
            root.after(200, trigger_loss)

    def start_loss():
        loss_active[0] = True
        trigger_loss()

    def stop_loss():
        loss_active[0] = False

    tk.Button(root, text="開始扣血", command=start_loss).pack(pady=5)
    tk.Button(root, text="停止扣血", command=stop_loss).pack(pady=5)

    # === 補血區 ===
    frame = tk.Frame(root)
    frame.pack(pady=10)

    entry = tk.Entry(frame, width=5)
    entry.pack(side="left")
    entry.insert(0, "1")  # 預設補1顆

    def gain_n():
        try:
            val = float(entry.get())
            if val > 0:
                hb.gain(val)
        except ValueError:
            pass  # 忽略非數字

    tk.Button(frame, text="補 N 顆", command=gain_n).pack(side="left", padx=5)

    root.mainloop()

