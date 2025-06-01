# hover_button.py
from tkinter import *
from PIL import Image, ImageTk

class HoverButton():
    def __init__(self, canvas, x, y,
                 img_normal_path: str,
                 img_hover_path: str,
                 command=None):
        self.canvas = canvas

        # 拿到使用者指定的「一般狀態圖」與「滑鼠浮到上面時的圖」
        self.img_normal = ImageTk.PhotoImage(file=img_normal_path)
        self.img_hover  = ImageTk.PhotoImage(file=img_hover_path)
        self.command = command

        # 建立 image 物件，保留 id 以便之後變圖或刪掉
        self.btn_image = self.canvas.create_image(x, y,
                                                  image=self.img_normal,
                                                  tags="hover_btn")

        # 只要滑鼠進入這個 tag，就換 hover 圖、pointer cursor；滑鼠離開就換回 normal
        self.canvas.tag_bind(self.btn_image, "<Enter>", self.on_hover)
        self.canvas.tag_bind(self.btn_image, "<Leave>", self.on_leave)
        self.canvas.tag_bind(self.btn_image, "<Button-1>", self.on_click)

    def on_hover(self, event):
        # 換成滑鼠懸停的圖；改 cursor
        self.canvas.itemconfig(self.btn_image, image=self.img_hover)
        self.canvas.config(cursor="hand2")

    def on_leave(self, event):
        # 換回一般圖；restore cursor
        self.canvas.itemconfig(self.btn_image, image=self.img_normal)
        self.canvas.config(cursor="")

    def on_click(self, event):
        if self.command:
            self.command()

    def destroy(self):
        # 從 Canvas 上刪除這個按鈕、並把 cursor 還原
        self.canvas.delete(self.btn_image)
        self.canvas.config(cursor="")
