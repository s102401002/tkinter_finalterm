import tkinter as tk

# ----------------------------
# 全域參數設定
BAR_WIDTH        = 120       # 進度條完整寬度
BAR_HEIGHT       = 16        # 進度條高度
duration         = 5_000     # 倒數完整時間 (ms)
update_interval  = 16        # 每次更新間隔 (ms)
# ----------------------------

class LaserBarRectApp:
    def __init__(self, canvas: tk.Canvas, screen_x: int, y: int,
                 anim_fps: int, fps: int, on_finish: callable = None,
                 num_girls: int = 1):
        """
        建構子只負責：
        1. 初始化參數 (current_value, max_value, running)
        2. 把「背景框」與「前景框」畫到 Canvas（初始時用 full width）
        3. 暫時不排程 update_bar，等呼叫 start() 才開始遞減
        """
        self.canvas = canvas
        self.current_value = 100
        self.max_value     = 200
        # 一開始先把 running 設成 False，不讓它自動倒數
        self.running = False      

        # 計算倒數條要畫的位置
        self.x0 = screen_x - BAR_WIDTH // 2
        self.x1 = screen_x + BAR_WIDTH // 2
        self.y0 = y - BAR_HEIGHT // 2
        self.y1 = y + BAR_HEIGHT // 2
        self.on_finish = on_finish

        # 點擊一次要加的量 = max_value / (base_clicks + num_girls * extra_per_girl)
        base_clicks = 15
        extra_per_girl = 10
        total_required_clicks = base_clicks + num_girls * extra_per_girl
        self.y_increment = self.max_value / total_required_clicks 

        # 1. 畫「背景框」 (金黃色 + 紫色邊框)
        self.bar_bg = self.canvas.create_rectangle(
            self.x0 - 1, self.y0 - 1,
            self.x1 + 1, self.y1 + 1,
            fill="#EEC364", outline="#E54DF3",
            width=3,
            tags='pk_bar'
        )

        # 2. 畫「前景框」 (粉色)，初始寬度用 full scale
        self.bar_fg = self.canvas.create_rectangle(
            self.x0, self.y0,
            self.x0 + self._scaled_width(), self.y1,
            fill="#E597F5", outline="",
            tags='pk_bar'
        )

        # *【移除】* 這行：不要在 __init__ 裡面就開始呼叫 update_bar
        # self.canvas.after(update_interval, self.update_bar)

    def _scaled_width(self):
        """計算前景條依照 current_value 的寬度 (0~BAR_WIDTH)"""
        ratio = min(self.current_value / self.max_value, 1.0)
        return int(BAR_WIDTH * ratio)

    def start(self):
        """
        按下「開始」按鈕後才呼叫這個方法，才能讓 running=True，
        並立刻排程第一次更新 (16ms 後執行 update_bar)
        """
        if not self.running:
            self.running = True
            # 立刻呼叫第一次 update_bar (16ms 後)
            self.canvas.after(update_interval, self.update_bar)

    def update_bar(self):
        """
        只有在 running==True 時才會繼續遞減 current_value。
        如果倒數到 0，或被點擊加值到滿值，就呼叫 callback。
        """
        if not self.running:
            return

        # 每次扣掉的量 = max_value / (duration / update_interval)
        decrement = self.max_value / (duration / update_interval)
        self.current_value -= decrement

        # 倒到底就停止
        if self.current_value <= 0:
            self.current_value = 0
            self.running = False
            if self.on_finish:
                self.on_finish(success=False)

        self.redraw_bar()

        # 只要還在 running，就每 16ms 再執行一次自己
        if self.running:
            self.canvas.after(update_interval, self.update_bar)

    def on_click(self):
        """
        玩家點擊一次，就把 current_value 往上加一段 y_increment。
        如果加到滿值，就判定為成功。
        """
        if not self.running:
            # 如果還沒 start，就點也不會有任何效果
            return

        self.current_value = min(self.current_value + self.y_increment, self.max_value)
        if self.current_value >= self.max_value:
            self.current_value = self.max_value
            self.running = False

        self.redraw_bar()

    def redraw_bar(self):
        """重新計算前景條寬度，並更新在 Canvas 上"""
        new_w = self._scaled_width()
        self.canvas.coords(
            self.bar_fg,
            self.x0, self.y0,
            self.x0 + new_w, self.y1
        )
        # 如果到頂或歸零，都呼叫 callback
        if self.current_value >= self.max_value:
            if self.on_finish:
                self.on_finish(success=True)
        if self.current_value <= 0:
            if self.on_finish:
                self.on_finish(success=False)

    def destroy(self):
        """刪除這條進度條的所有畫面元素"""
        for cid in (self.bar_bg, self.bar_fg):
            if cid:
                self.canvas.delete(cid)


# ================================
# 以下為「獨立執行測試」的 __main__ 範例
# ================================
if __name__ == "__main__":
    # 1. 建立主視窗
    root = tk.Tk()
    root.title("PK Bar 獨立測試 – 按開始才倒數")
    # 調整視窗大小，留下面給按鈕
    root.geometry("300x140")

    # 2. 建立 Canvas (300×100)
    canvas = tk.Canvas(root, width=300, height=100, bg="white")
    canvas.pack(side="top", fill="x", pady=(5, 0))

    # 3. 建立 LaserBarRectApp 物件 (不會馬上倒數)
    app = LaserBarRectApp(
        canvas    = canvas,
        screen_x  = 150,
        y         = 50,
        anim_fps  = 10,
        fps       = 60,
        on_finish = lambda success: print("PK 結束：", "贏" if success else "輸"),
        num_girls = 1
    )

    # 4. 建立一顆「開始」按鈕，按下後觸發 app.start()
    btn_start = tk.Button(
        root,
        text="開始倒數",
        command=app.start
    )
    btn_start.pack(side="top", pady=(10, 0))

    # 5. 建立一顆「加分」按鈕，只有在倒數已經啟動後，才能讓 on_click 有效果
    btn_click = tk.Button(
        root,
        text="加分 (on_click)",
        command=app.on_click
    )
    btn_click.pack(side="top", pady=5)

    # 6. 啟動 Tkinter 主迴圈
    root.mainloop()
