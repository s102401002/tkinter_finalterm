import tkinter as tk
from tkinter import ttk
from pathlib import Path
import subprocess
import sys
class RankingScreen(tk.Toplevel):
    RANK_FILE = "ranking.txt"

    def __init__(self, master=None):
        super().__init__(master)
        self.title("排行榜")
        self.geometry("400x500")
        self.resizable(False, False)

        # 1. 先把資料讀進來
        self.ranking = self._load_ranking()

        # 2. 準備好 style、tree_frame、tree（還不顯示）
        self._setup_style()
        self._make_scrollbar()

        # **千萬不要在這裡呼 show_treeview()**

    def _load_ranking(self):
        data = []
        path = Path(self.RANK_FILE)
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",")
                    if len(parts) != 2:
                        continue
                    name, score_s = parts
                    try:
                        score = int(score_s)
                    except ValueError:
                        continue
                    data.append((name, score))
        # 由分數高到低排序
        data.sort(key=lambda x: (-x[1], x[0]))
        return data

    def _save_ranking(self):
        path = Path(self.RANK_FILE)
        with path.open("w", encoding="utf-8") as f:
            for name, score in self.ranking:
                f.write(f"{name},{score}\n")

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "Custom.Treeview",
            background="#ffffff",
            foreground="#333333",
            rowheight=28,
            fieldbackground="#ffffff",
            font=("Helvetica", 11)
        )
        style.map(
            "Custom.Treeview",
            background=[("active", "#f09af8")],
            foreground=[("active", "#ffffff")]
        )

        style.configure(
            "Custom.Treeview.Heading",
            background="#e48ce7",
            foreground="#000000",
            font=("Helvetica", 12, "bold"),
            relief="flat"
        )
        style.map(# 滑鼠移到 Header 時變色
            "Custom.Treeview.Heading",
            background=[("active", "#e55ae0")]
        )

        style.configure(
            "Custom.Vertical.TScrollbar",
            gripcount=0,
            background="#e0e0e0",
            darkcolor="#e0e0e0",
            troughcolor="#cccccc",
            lightcolor="#e0e0e0",
            bordercolor="#cccccc",
            arrowcolor="#555555"
        )

    def _make_scrollbar(self):
        # 建立一個 Frame，裡面放 Treeview + Scrollbar
        self.tree_frame = ttk.Frame(self)

        # 這裡建立 self.tree，並設定欄位與排序功能
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("rank", "name", "score"),
            show="headings",
            style="Custom.Treeview",
        )

        vsb = ttk.Scrollbar(
            self.tree_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Custom.Vertical.TScrollbar"
        )
        self.tree.configure(yscrollcommand=vsb.set)

        # 用 grid 排版：Treeview 在 (0,0)，Scrollbar 在 (0,1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        self.tree_frame.rowconfigure(0, weight=1)
        self.tree_frame.columnconfigure(0, weight=1)

        # 設定三個欄位的標題與排序 callback
        self.tree.heading(
            "rank",
            text="排名",
            command=lambda: self.treeview_sort_column(self.tree, "rank", False),# ttk.Treeview物件、排序的col、是否逆排序
            anchor=tk.CENTER
        )
        self.tree.heading(
            "name",
            text="名字",
            command=lambda: self.treeview_sort_column(self.tree, "name", False),
            anchor=tk.W
        )
        self.tree.heading(
            "score",
            text="分數",
            command=lambda: self.treeview_sort_column(self.tree, "score", False),
            anchor=tk.CENTER
        )

        self.tree.column("rank", width=60, anchor=tk.CENTER)
        self.tree.column("name", width=220, anchor=tk.W)
        self.tree.column("score", width=100, anchor=tk.CENTER)

        # 交替底色（zebra stripe）
        self.tree.tag_configure("oddrow", background="#f9f9f9")
        self.tree.tag_configure("evenrow", background="#ffffff")

    def treeview_sort_column(self, tree, col, reverse):
        data_list = [(tree.set(k, col), k) for k in tree.get_children("")]
        if col in ("rank", "score"):
            try:
                data_list.sort(key=lambda t: int(t[0]), reverse=reverse)
            except ValueError:
                data_list.sort(key=lambda t: t[0], reverse=reverse)
        else:
            data_list.sort(key=lambda t: t[0], reverse=reverse)

        for index, (val, k) in enumerate(data_list):
            tree.move(k, "", index)

        tree.heading(col, command=lambda: self.treeview_sort_column(tree, col, not reverse))

    def show_treeview(self):
        # 叫這個方法才會把排列表格 pack 出來
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 先刪掉原有列
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        # 把所有 ranking 資料插入
        for idx, (n, s) in enumerate(self.ranking):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=(idx + 1, n, s), tags=(tag,))

        # 最後一個「關閉」按鈕
        btn_close = ttk.Button(self, text="回到主選單", command=self._return_to_main_menu)
        btn_close.pack(pady=10)
    def _return_to_main_menu(self):
        self.destroy()
        # 重新啟動 main_menu.py（需與game.py同資料夾）
        subprocess.Popen([sys.executable, "main_menu.py"])
    def add_score_and_animate(self, name: str, score: int, on_complete=None):
        # 加入新成績、重新排序並儲存
        self.ranking.append((name, score))
        self.ranking.sort(key=lambda x: -x[1])
        self._save_ranking()

        # 把動畫先畫到 Canvas，動畫跑完再顯示 show_treeview()
        self.canvas = tk.Canvas(self, width=400, height=500, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.labels = []
        for idx, (n, s) in enumerate(self.ranking[:10]):
            y_start = 520 + idx * 40
            txt = f"{idx + 1}. {n} - {s}"
            lbl_id = self.canvas.create_text(
                200, y_start,
                text=txt,
                font=("Arial", 16),
                fill="black"
            )
            self.labels.append(lbl_id)

        def animate_step():
            finished = True
            for idx, lbl_id in enumerate(self.labels):
                x, y = self.canvas.coords(lbl_id)
                target_y = 50 + idx * 30
                if y > target_y:
                    self.canvas.move(lbl_id, 0, -5)
                    finished = False
            if not finished:
                self.after(30, animate_step)
            else:
                if on_complete:
                    on_complete()
                # 動畫結束之後把 Canvas 砍掉，改顯示 Treeview
                self.canvas.destroy()
                self.show_treeview()

        self.after(50, animate_step)


if __name__ == '__main__':
    # 這裡的 root 只會顯示兩個按鈕，點按鈕時才建立 RankingScreen
    root = tk.Tk()
    root.title("排行榜測試")
    root.geometry("300x150")
    root.resizable(False, False)

    def test_animation():
        screen = RankingScreen(root)
        screen.add_score_and_animate("Tester", 6088)

    def test_treeview():
        screen = RankingScreen(root)
        screen.show_treeview()

    btn_frame = tk.Frame(root)
    btn_frame.pack(expand=True, pady=20)

    btn_anim = tk.Button(btn_frame, text="測試動畫", width=20, command=test_animation)
    btn_anim.pack(pady=5)

    btn_tree = tk.Button(btn_frame, text="測試 Treeview", width=20, command=test_treeview)
    btn_tree.pack(pady=5)

    root.mainloop()
