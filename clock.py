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
        self.elapsed = 0
        self.clock_face = self.canvas.create_oval(
            self.cx - radius, self.cy - radius, self.cx + radius, self.cy + radius,
            fill="white", outline="black"
        )
        self.hand = self.canvas.create_line(
            self.cx, self.cy,
            self.cx, self.cy - radius,
            fill="red", width=2
        )

    def update(self):
        self.elapsed += 1 / 60
        angle = 360 * (self.elapsed / self.total_seconds)
        if angle > 360:
            angle = 360
        rad = math.radians(angle - 90)
        x = self.cx + self.radius * math.cos(rad)
        y = self.cy + self.radius * math.sin(rad)
        self.canvas.coords(self.hand, self.cx, self.cy, x, y)

    def reset(self):
        self.elapsed = 0
        self.update()



if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(root, width=500, height=500, bg="white")
    canvas.pack()
    
    total_seconds = 10
    def update_loop():
        clock.update()
        root.after(1000 // 60, update_loop)  # 每秒 60 次更新（對應 FPS = 60）

    def start_clock():
        update_loop()
    
    clock = Clock(canvas, center_x=100, center_y=100, radius=50, total_seconds=total_seconds)

    btn = tk.Button(root, text="開始時鐘", command=start_clock)
    btn.pack(pady=10)

    root.mainloop()