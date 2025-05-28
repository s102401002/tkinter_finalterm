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
            fill="white", outline="black"
        )
        self.hand = self.canvas.create_line(
            self.cx, self.cy,
            self.cx, self.cy - radius,
            fill="red", width=2
        )
        self.fill_id = self.canvas.create_arc(
            self.cx - radius, self.cy - radius,
            self.cx + radius, self.cy + radius,
            start=90, extent=0,
            fill='pink', outline='pink'
        )

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
        if angle > 360:
            angle = 360
            self.finished = True
            self.running = False  # 自動停止
        # 更新 fill arc
        current_angle = angle - 90
        self.canvas.itemconfig(self.fill_id, extent=-angle)
        
        rad = math.radians(current_angle)
        x = self.cx + self.radius * math.cos(rad)
        y = self.cy + self.radius * math.sin(rad)
        self.canvas.coords(self.hand, self.cx, self.cy, x, y)

    def reset(self):
        self.elapsed = 0.0
        self.last_time = time.time()
        self.running = False
        self.finished = False
        self.prev_angle = -90

        self.canvas.coords(self.hand, self.cx, self.cy, self.cx, self.cy - self.radius)
        self.canvas.itemconfig(self.fill_id, extent=0)
        # self.update()

    def start(self):
        self.last_time = time.time()
        self.running = True
        self.finished = False

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
