import math
import tkinter as tk
from PIL import Image, ImageTk

class LaserBeam:
    def __init__(self, canvas, start, end, image_path, steps=3, delay=100, on_finish=None):
        """
        canvas: Tkinter canvas
        start, end: (x, y) 起點與終點
        image_path: 單張雷射圖片（橫向長度）
        steps: 分幾段發射
        delay: 每段間隔(ms)
        on_finish: 播完後的 callback
        """
        self.canvas = canvas
        self.start = start
        self.end = end
        self.steps = steps
        self.delay = delay
        self.on_finish = on_finish
        self.current_step = 1
        self.img_id = None
        self.img_light_id = None
        # 載入原圖
        self.base_img = Image.open(image_path).convert("RGBA")
        #self.light = mk(Image.open("assets_aligned/effect/light.png").convert("RGBA"))
        def mk(img):                  
            return ImageTk.PhotoImage(
                img.resize((img.width//4, img.height//4), Image.Resampling.LANCZOS)
            )
        self.light = mk(Image.open("assets_aligned/effect/light.png").convert("RGBA"))
        self.orig_w, self.orig_h = self.base_img.size

        # 計算角度和總長度
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        self.angle = math.degrees(math.atan2(dy, dx))

        # 用來鎖住 PhotoImage 的引用，避免被 GC
        self._images = []

        # 開始動畫
        self._draw_next()

    def _draw_next(self):
        if self.current_step <= self.steps:
            # 本階段長度比例
            ratio = self.current_step / self.steps

            # 目標終點
            sx, sy = self.start
            ex, ey = self.end
            tx = sx + (ex - sx) * ratio
            ty = sy + (ey - sy) * ratio

            # 線段中點（貼圖中心）
            cx = (sx + tx) / 2
            cy = (sy + ty) / 2

            # 計算這段長度，縮放寬度
            seg_len = math.hypot(tx - sx, ty - sy)
            scale = seg_len / self.orig_w

            # 縮放 + 旋轉
            resized = self.base_img.resize(
                (int(self.orig_w * scale), int(self.orig_h * 0.2)),
                Image.LANCZOS
            )
            rotated = resized.rotate(-self.angle, expand=True)

            # 生成 PhotoImage 並鎖定引用
            img = ImageTk.PhotoImage(rotated)
            self._images.append(img)

            # 刪除前一張（如果有）
            if self.img_id:
                self.canvas.delete(self.img_id)

            # 貼上新圖
            self.img_id = self.canvas.create_image(cx, cy, image=img, anchor='center')
            self.img_light_id = self.canvas.create_image(sx, sy, image=self.light, anchor='center')
            self.current_step += 1
            self.canvas.after(self.delay, self._draw_next)
        else:
            # 動畫結束 callback
            if self.on_finish:
                self.on_finish()

    def destroy(self):
        """手動刪除光束圖"""
        if self.img_id:
            self.canvas.delete(self.img_id)
            self.img_id = None
        # 清掉所有 Image 引用
        self._images.clear()


if __name__ == '__main__':
    root = tk.Tk()
    canvas = tk.Canvas(root, width=500, height=500, bg="white")
    canvas.pack()

    start = (100, 100)
    end   = (300, 300)

    # 畫紅點標記
    r = 5
    canvas.create_oval(start[0]-r, start[1]-r, start[0]+r, start[1]+r, fill='red', outline='')
    canvas.create_oval(end[0]-r, end[1]-r, end[0]+r, end[1]+r, fill='red', outline='')

    beam = LaserBeam(
        canvas=canvas,
        start=start,
        end=end,
        image_path="assets_aligned/effect/laser_yellow.png",
        steps=10,
        delay=50
    )

    # 3 秒後手動銷毀光束
    #root.after(3000, beam.destroy)

    root.mainloop()
