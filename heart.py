import tkinter as tk
import math

class HeartFillAnimation:
    def __init__(self, canvas, cx, cy, scale):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.scale = scale
        self.steps = 200
        self.fill_height = 0
        self.max_fill = 300  # 動畫最大高度
        self.delay = 30  # 毫秒
        self.heart_id = None
        self.mask_id = None

        self.draw_heart_outline()
        self.animate_fill()

    def heart_points(self):
        points = []
        for i in range(self.steps):
            t = (i / self.steps) * 2 * math.pi
            x = 16 * math.sin(t)**3
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            x *= self.scale
            y *= -self.scale
            points.append((self.cx + x, self.cy + y))
        return points

    def draw_heart_outline(self):
        points = self.heart_points()
        self.heart_id = self.canvas.create_polygon(
            points,
            fill="red",
            outline="black"
        )

    def animate_fill(self):
        if self.mask_id:
            self.canvas.delete(self.mask_id)

        # 建立一個遮罩矩形，從上往下遮住心形
        self.mask_id = self.canvas.create_rectangle(
            0, 0, 500, self.cy + self.scale * 17 - self.fill_height,
            fill="white",
            outline="white"
        )

        self.fill_height += 5  # 每次增加高度
        if self.fill_height <= self.max_fill:
            self.canvas.after(self.delay, self.animate_fill)

root = tk.Tk()
root.title("愛心從下填滿動畫")
canvas = tk.Canvas(root, width=500, height=500, bg="white")
canvas.pack()

HeartFillAnimation(canvas, cx=250, cy=280, scale=5)

root.mainloop()
