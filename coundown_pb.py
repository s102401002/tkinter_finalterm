import time
import tkinter as tk

class CountdownProgressBar:
    """
    在指定的 canvas 上繪製一層覆蓋遮罩 + 灰底/紅前景倒數進度條，
    並在倒數結束後自動清理自身並呼叫 on_finish 。
    
    參數：
      - canvas:    要繪製在其上的 tk.Canvas
      - x0, y0:    進度條左上角座標
      - width:     進度條背景與前景的總寬度
      - height:    進度條高度
      - duration:  倒數總秒數（浮點數，單位：秒）
      - overlay_w: 整個遮罩矩形的寬度（通常需覆蓋血條區域）
      - overlay_h: 整個遮罩矩形的高度
      - on_finish: 倒數到 0 秒時要呼叫的函式 (callback)
    """
    def __init__(self,
                 canvas: tk.Canvas,
                 x0: int,
                 y0: int,
                 width: int,
                 height: int,
                 duration: float,
                 overlay_w: int,
                 overlay_h: int,
                 on_finish=None):
        self.canvas = canvas
        self.x0 = x0
        self.y0 = y0
        self.total_width = width
        self.height = height
        self.duration = duration
        self.on_finish = on_finish

        # 紀錄遮罩要覆蓋的區域大小
        self.overlay_w = overlay_w
        self.overlay_h = overlay_h

        # 以下屬性稍後會由 create() 設定
        self._overlay_id = None
        self._bar_bg_id = None
        self._bar_fg_id = None
        self._start_time = None
        self._job_id = None  # after() 會回傳的 job id

        # 立刻建立所有介面元件，並啟動倒數
        self._create()

    def _create(self):
        """
        繪製遮罩＋背景長條＋前景長條，並啟動倒數更新機制。
        """
        # 1. 畫一個半透明黑色遮罩，覆蓋左上的 overlay_w × overlay_h 區域
        self._overlay_id = self.canvas.create_rectangle(
            0, 0, self.overlay_w, self.overlay_h,
            fill="#000000",
            stipple="gray50",
            width=0,
        )

        # 2. 在 (x0, y0) 畫一條灰底長條，寬度 self.total_width、高度 self.height
        x1 = self.x0 + self.total_width
        y1 = self.y0 + self.height
        self._bar_bg_id = self.canvas.create_rectangle(
            self.x0, self.y0, x1, y1,
            fill="#444444", outline="#888888", width=1
        )

        # 3. 在灰底上方放一條紅色前景長條，初始也是 full width
        self._bar_fg_id = self.canvas.create_rectangle(
            self.x0, self.y0, x1, y1,
            fill="#FF4444", outline="", width=0
        )

        # 4. 記錄開始時間，啟動 _update_loop()
        self._start_time = time.time()
        self._job_id = self.canvas.after(50, self._update_loop)

    def _update_loop(self):
        """
        每隔一段時間（預設 50ms）更新一次前景長條的寬度。
        直到倒數完成，呼叫 on_finish() 並刪除所有圖元。
        """
        elapsed = time.time() - self._start_time
        fraction = min(elapsed / self.duration, 1.0)  # 0.0 ~ 1.0
        new_w = int(self.total_width * (1.0 - fraction))

        # 前景長條座標更新：x1 從 x0 + total_width → x0 + 0
        if new_w > 0:
            # 縮短前景長條的寬度
            self.canvas.coords(
                self._bar_fg_id,
                self.x0, self.y0,
                self.x0 + new_w, self.y0 + self.height
            )
            # 再次安排下一次更新
            self._job_id = self.canvas.after(50, self._update_loop)
        else:
            # 倒數結束，直接呼叫 end() 清理（同時觸發 callback）
            self.end()

    def end(self):
        """
        倒數結束後呼叫：取消排程、刪除所有圖元，並呼叫 on_finish()。
        """
        # 1. 取消尚未執行的 after job
        if self._job_id is not None:
            self.canvas.after_cancel(self._job_id)
            self._job_id = None

        # 2. 刪除前景、背景、遮罩
        if self._bar_fg_id is not None:
            self.canvas.delete(self._bar_fg_id)
            self._bar_fg_id = None
        if self._bar_bg_id is not None:
            self.canvas.delete(self._bar_bg_id)
            self._bar_bg_id = None
        if self._overlay_id is not None:
            self.canvas.delete(self._overlay_id)
            self._overlay_id = None

        # 3. 如果有提供 on_finish callback，就呼叫之
        if callable(self.on_finish):
            self.on_finish()

    def destroy(self):
        """
        外部如果要強制結束（不等待倒數完成），可以呼叫此方法。
        """
        self.end()
