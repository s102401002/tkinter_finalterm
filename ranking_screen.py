import tkinter as tk
from tkinter import ttk
from pathlib import Path
import subprocess
import sys
import math
class RankingScreen(tk.Tk):
    RANK_FILE = "ranking.txt"

    def __init__(self, master=None):
        super().__init__(master)
        self.title("排行榜")
        self.geometry("700x500")
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
                    # 由於現在存四個欄位，所以長度要是 4
                    if len(parts) != 4:
                        continue
                    name, score_s, time_s, npc_s = parts
                    try:
                        score = int(score_s)
                        game_time = int(time_s)
                        npc_count = int(npc_s)
                    except ValueError:
                        continue
                    # 每筆改成 (name, score, game_time, npc_count)
                    data.append((name, score, game_time, npc_count))
        # 由分數高到低排序（如分數相同，再看名字排序）
        data.sort(key=lambda x: (-x[1], x[0]))
        return data

    def _save_ranking(self):
        path = Path(self.RANK_FILE)
        with path.open("w", encoding="utf-8") as f:
            for name, score, game_time, npc_count in self.ranking:
                # 寫檔時也要輸出四個欄位
                f.write(f"{name},{score},{game_time},{npc_count}\n")
    def add_score(self, name: str, score: int, game_time: int, npc_count: int):
        # 1. 將新成績加入記憶體清單
        self.ranking.append((name, score, game_time, npc_count))
        # 2. 依照分數從高到低排序（若分數相同，則按名字排序）
        self.ranking.sort(key=lambda x: (-x[1], x[0]))
        # 3. 寫檔到 ranking.txt
        self._save_ranking()
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
            columns=("rank", "name", "score", "time", "npc"),
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

        # 設定五個欄位的標題與排序 callback
        self.tree.heading(
            "rank",
            text="排名",
            command=lambda: self.treeview_sort_column(self.tree, "rank", False),
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
        self.tree.heading(
            "time",
            text="遊戲時間",
            command=lambda: self.treeview_sort_column(self.tree, "time", False),
            anchor=tk.CENTER
        )
        self.tree.heading(
            "npc",
            text="NPC數量",
            command=lambda: self.treeview_sort_column(self.tree, "npc", False),
            anchor=tk.CENTER
        )

        # 調整每個欄位寬度
        self.tree.column("rank", width=60, anchor=tk.CENTER)
        self.tree.column("name", width=160, anchor=tk.W)
        self.tree.column("score", width=80, anchor=tk.CENTER)
        self.tree.column("time", width=100, anchor=tk.CENTER)
        self.tree.column("npc", width=80, anchor=tk.CENTER)

        # 交替底色（zebra stripe）
        self.tree.tag_configure("oddrow", background="#e0e0e0")
        self.tree.tag_configure("evenrow", background="#ffffff")

    def treeview_sort_column(self, tree, col, reverse):
        data_list = [(tree.set(k, col), k) for k in tree.get_children("")]
        if col in ("rank", "score", "time", "npc"):
            # 這些欄位都是整數，先嘗試轉 int
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

        # 把所有 ranking 資料插入：每筆資料現在是 (name, score, game_time, npc_count)
        for idx, (n, s, t, p) in enumerate(self.ranking):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            # 插入時多加兩格：遊戲時間 t、NPC數量 p
            self.tree.insert("", "end", values=(idx + 1, n, s, t, p), tags=(tag,))

        # 最後一個「關閉」按鈕
        btn_close = ttk.Button(self, text="回到主選單", command=self._return_to_main_menu)
        btn_close.pack(pady=10)
    def _return_to_main_menu(self):
        self.destroy()
        # 重新啟動 main_menu.py（需與game.py同資料夾）
        subprocess.Popen([sys.executable, "main_menu.py"])

    def add_score_and_animate(self, name: str, score: int, game_time: int, npc_count: int, on_complete=None):
        # 儲存舊的排名，用於顯示舊排名
        old_ranking = list(self.ranking)
        # 先將新成績加入並排序（四個欄位）
        self.ranking.append((name, score, game_time, npc_count))
        self.ranking.sort(key=lambda x: (-x[1], x[0]))
        self._save_ranking()

        # 找出新資料在新排名中的索引
        new_index = next((i for i, (n, s, t, p) in enumerate(self.ranking) if n == name and s == score and t == game_time and p == npc_count), None)
        if new_index is None:
            new_index = len(self.ranking) - 1

        # 建立 Canvas，先畫舊排名
        self.canvas = tk.Canvas(self, width=500, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.old_labels = []
        for idx, (n, s, t, p) in enumerate(old_ranking[:10]):
            y_pos = 50 + idx * 30
            txt = f"{idx + 1}. {n} - {s} (T:{t}s, N:{p})"
            lbl_id = self.canvas.create_text(250, y_pos, text=txt, font=("Arial", 14), fill="black")
            self.old_labels.append(lbl_id)

        # 建立新資料的 Label，起始位置在畫面底部
        new_y_start = 620
        new_txt = f"{new_index + 1}. {name} - {score} (T:{game_time}s, N:{npc_count})"
        self.new_label_id = self.canvas.create_text(250, new_y_start, text=new_txt, font=("Arial", 16), fill="red")

        # 目標位置的 y 座標
        target_y = 50 + new_index * 30

        def animate_new_entry():
            x, y = self.canvas.coords(self.new_label_id)
            if y > target_y:
                self.canvas.move(self.new_label_id, 0, -5)
                self.after(30, animate_new_entry)
            else:
                # 到達位置後顯示煙火動畫
                self.launch_firework(x, y)
                # 短暫延遲後切換到 Treeview
                self.after(800, finish_animation)

        def finish_animation():
            if on_complete:
                on_complete()
            self.canvas.destroy()
            self.show_treeview()

        # 開始動畫
        self.after(50, animate_new_entry)

    def launch_firework(self, x, y):
        dots = []
        # 建立 8 個方向的點
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            dx = math.cos(rad)
            dy = math.sin(rad)
            dot_id = self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="yellow", outline="")
            dots.append((dot_id, dx, dy))

        steps = 10

        def animate_firework(step=0):
            if step < steps:
                for dot_id, dx, dy in dots:
                    self.canvas.move(dot_id, dx * 5, dy * 5)
                self.after(50, lambda: animate_firework(step + 1))
            else:
                # 刪除所有點
                for dot_id, _, _ in dots:
                    self.canvas.delete(dot_id)

        animate_firework()

def test():
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
        # screen.add_score('p',9)
        screen.show_treeview()

    btn_frame = tk.Frame(root)
    btn_frame.pack(expand=True, pady=20)

    btn_anim = tk.Button(btn_frame, text="測試動畫", width=20, command=test_animation)
    btn_anim.pack(pady=5)

    btn_tree = tk.Button(btn_frame, text="測試 Treeview", width=20, command=test_treeview)
    btn_tree.pack(pady=5)

    root.mainloop()
if __name__ == '__main__':
    # test()
    screen = RankingScreen()
    screen.show_treeview()
    screen.mainloop()
    
