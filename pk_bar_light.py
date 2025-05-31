import tkinter as tk
from pathlib import Path
# 參數設定
BAR_WIDTH = 120           # 最大寬度
BAR_HEIGHT = 16
BAR_X = 50
BAR_Y = 30

y_increment = 5          # 每點擊增加
duration = 5_000         # 10 秒
update_interval = 16      # 60FPS：每 16ms 更新一次

class LaserBarRectApp:
    def __init__(self,canvas: tk.Canvas, 
                 screen_x: int, 
                 y: int, 
                 anim_fps: int,fps: int, 
                 on_finish: callable = None):
        
        self.canvas  = canvas
        self.current_value = 50  # 初始長度為 50（最大值為 100）
        self.max_value = 100
        self.running = True
        self.x0 = screen_x - int(BAR_WIDTH/2)
        self.x1 = screen_x + int(BAR_WIDTH/2)
        self.y0 = y - int(BAR_HEIGHT/2)
        self.y1 = y + int(BAR_HEIGHT/2)
        self.on_finish = on_finish  # 儲存 callback
        # 底色條（灰色背景）
        self.bar_bg = self.canvas.create_rectangle(
            self.x0-1, self.y0-1,
            self.x1+1, self.y1+1 ,
            fill="#EEC364", outline="#E54DF3",
            width=3,
            tags='pk_bar'
        )

        # 前景條（紅色進度）
        self.bar_fg = self.canvas.create_rectangle(
            self.x0, self.y0,
            self.x0 + self._scaled_width(), self.y1,
            fill="#E597F5", outline="",
            tags='pk_bar'
        )

        #self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.after(update_interval, self.update_bar)

    def _scaled_width(self):
        """目前長度（像素）"""
        ratio = min(self.current_value / self.max_value, 1.0)
        return int(BAR_WIDTH * ratio)

    def update_bar(self):
        if not self.running:
            return

        decrement = self.max_value / (duration / update_interval)
        self.current_value -= decrement
        if self.current_value <= 0:
            self.current_value = 0
            self.running = False
            if self.on_finish:
                self.on_finish(success=False)  # 點擊太慢，輸了

        self.redraw_bar()
        if self.running:
            self.canvas.after(update_interval, self.update_bar)

    def on_click(self):
        if not self.running:
            return
        self.current_value = min(self.current_value + y_increment, self.max_value)
        if self.current_value >= self.max_value:
            self.current_value = self.max_value
            self.running = False

        self.redraw_bar()

    def redraw_bar(self):
        new_w = self._scaled_width()
        self.canvas.coords(
            self.bar_fg,
            self.x0, self.y0,
            self.x0 + new_w, self.y1
        )
        if self.current_value >= self.max_value:
            if self.on_finish:
                self.on_finish(success=True)  # 提前填滿，獲勝
        if self.current_value <= 0:
            if self.on_finish:
                self.on_finish(success=False)  # 點擊太慢，輸了
    def destroy(self):
        for cid in [self.bar_bg, self.bar_fg]:
            if cid:
                self.canvas.delete(cid)
if __name__ == "__main__":
    root = tk.Tk()
    root.title("攻擊條（Rectangle 節能版）")
    app = LaserBarRectApp(root)
    root.mainloop()