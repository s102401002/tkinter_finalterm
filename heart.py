import tkinter as tk
import math

class HeartFillClip:
    def __init__(self, canvas, cx, cy, scale):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.scale = scale
        self.steps = 200
        self.fill_ratio = 0.0  # 從 0.0 到 1.0
        self.delay = 30
        self.increment = 0.02

        self.outline_points = self.compute_heart_points()
        self.canvas.create_polygon(self.outline_points, outline="black", fill="", width=2)

        self.fill_id = None
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
                outline=""
            )

        # 更新比例
        self.fill_ratio += self.increment
        if self.fill_ratio <= 1.05: # 用1.0會缺一塊 可能是浮點數精度問題?
            self.canvas.after(self.delay, self.animate_fill)
if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(root, width=500, height=500, bg="white")
    canvas.pack()

    HeartFillClip(canvas, cx=250, cy=280, scale=5)

    root.mainloop()
