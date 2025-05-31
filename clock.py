import math
import tkinter as tk
import time

class Clock:
    def __init__(self, canvas, center_x, center_y, radius=20, total_seconds=60):
        self.canvas = canvas
        self.cx = center_x
        self.cy = center_y
        self.radius = radius
        self.total_seconds = total_seconds
        self.elapsed = 0.0
        self.last_time = time.time()
        self.running = False
        self.finished = False # 時間是否結束
        self.prev_angle = -90
        # 畫面元件
        self.clock_face = self.canvas.create_oval(
            self.cx - radius, self.cy - radius,
            self.cx + radius, self.cy + radius,
            fill="white", 
            outline="black"
        )
        # self.hand = self.canvas.create_line(
        #     self.cx, self.cy,
        #     self.cx, self.cy - radius,
        #     fill="red", width=2
        # )
        self.fill_id = self.canvas.create_arc(
            self.cx - radius, self.cy - radius,
            self.cx + radius, self.cy + radius,
            start=90, extent=0,
            fill='pink', outline='pink'
        )
        self.canvas.itemconfig(self.fill_id, extent=0) # 避免一開始就填滿的bug-2.0
    def update(self, paused=False):
        if not self.running or self.finished or paused:
            self.last_time = time.time()  # 更新last_time，避免暫停後開始繼續計時
            return

        now = time.time()
        delta = now - self.last_time
        self.last_time = now

        self.elapsed += delta

        # 限制最大角度
        angle = 360 * (self.elapsed / self.total_seconds)
        if angle >= 360:
            self.canvas.itemconfig(self.fill_id, extent=0)
            self.canvas.delete(self.fill_id)
            self.finished = True
            self.running  = False
            return 
        
        current_angle = angle - 90
        self.canvas.itemconfig(self.fill_id, extent=-angle)
        
        rad = math.radians(current_angle)
        x = self.cx + self.radius * math.cos(rad)
        y = self.cy + self.radius * math.sin(rad)
        # self.canvas.coords(self.hand, self.cx, self.cy, x, y)

    def reset(self):
        self.elapsed = 0.0
        self.last_time = time.time()
        self.running = False
        self.finished = False
        self.prev_angle = -90
        self.canvas.itemconfig(self.clock_face, fill='white')
        # self.canvas.coords(self.hand, self.cx, self.cy, self.cx, self.cy - self.radius)
        self.canvas.itemconfig(self.fill_id, extent=0)
        # self.update()
    def clear_fill(self):
        # 如果有 fill_id，才去刪
        if hasattr(self, 'fill_id') and self.fill_id is not None:
            try:
                self.canvas.delete(self.fill_id)
            except tk.TclError:
                # 若已被刪除，也不用理它
                pass
            finally:
                # 刪完把引用清掉，避免下次重複刪同一個 id
                self.fill_id = None
    def start(self):
        # 1. 重置內部狀態
        self.elapsed    = 0.0
        self.prev_angle = -90
        self.running    = True
        self.finished   = False
        
        # 2. 刪除舊的 arc（有就刪）
        self.clear_fill()
        # 3. 重新畫一個新的 arc
        self.fill_id = self.canvas.create_arc(
            self.cx - self.radius, self.cy - self.radius,
            self.cx + self.radius, self.cy + self.radius,
            start=90, extent=0, fill='pink', outline='pink'
        )
        # 4. 重置時間基準
        self.last_time = time.time()

# ------------------ 測試 ------------------
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Clock 測試")
    canvas = tk.Canvas(root, width=200, height=200, bg="white")
    canvas.pack()

    clock = Clock(canvas, center_x=100, center_y=100, radius=50, total_seconds=30)

    def update_loop():
        clock.update()
        root.after(1000 // 50, update_loop)  # 模擬 50 FPS

    update_loop()

    # 控制按鈕
    control_frame = tk.Frame(root)
    control_frame.pack(pady=10)

    start_btn = tk.Button(control_frame, text="開始", command=clock.start)
    start_btn.pack(side="left", padx=10)

    reset_btn = tk.Button(control_frame, text="重設", command=clock.reset)
    reset_btn.pack(side="left", padx=10)

    root.mainloop()
