import tkinter as tk
import tkinter.ttk as ttk
import threading
from game import ElectricEyeGame
from ranking_screen import RankingScreen 
import subprocess, sys
class GameLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("主選單")
        self.geometry("400x320")
        self.configure(bg="#f0f0f0") 
        self.resizable(False, False)

        self.game_time = tk.IntVar(value=60)
        self.npc_count = tk.IntVar(value=7)

        tk.Label(self, text="電眼美女 遊戲選單", font=("Helvetica", 18, "bold"), bg="#f0f0f0").pack(pady=20)

        btn_frame = tk.Frame(self, bg="#f0f0f0")
        btn_frame.pack()

        tk.Button(btn_frame, text="開始遊戲", width=20, font=("Arial", 12), command=self.start_game).pack(pady=5)
        tk.Button(btn_frame, text="設定", width=20, font=("Arial", 12), command=self.open_settings).pack(pady=5)
        tk.Button(btn_frame, text="查看排行榜", width=20, font=("Arial", 12), command=self.open_leaderboard).pack(pady=5)
        tk.Button(btn_frame, text="結束程式", width=20, font=("Arial", 12), command=self.quit).pack(pady=5)

    def start_game(self):
        # 顯示 Loading 畫面
        LoadingScreen(self, self.game_time.get(), self.npc_count.get())

    def open_settings(self):
        settings = tk.Toplevel(self)
        settings.title("遊戲設定")
        settings.geometry("400x200")
        settings.configure(bg="#fefefe")

        tk.Label(settings, text="遊戲時間（秒）:", bg="#fefefe", font=("Arial", 10)).pack(pady=(10, 0))
        time_choices = [60, 90, 120, 150, 180]
        # time_combo = ttk.Combobox(settings, values=time_choices, textvariable=self.game_time, state="readonly", font=("Arial", 10), width=10)
        # time_combo.set(self.game_time.get())  # 預設顯示目前值
        # time_combo.pack()
        radio_frame = ttk.Frame(settings)
        radio_frame.pack(padx=10, pady=5)
        for t in time_choices:
            rb = ttk.Radiobutton(
                radio_frame,
                text=f"{t} 秒",
                value=t,
                variable=self.game_time,
                # 當選項改變時不需要額外動作，故不指定 command
            )
            rb.pack(side="left", padx=5, pady=2)
        tk.Label(settings, text="NPC 數量:", bg="#fefefe", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Spinbox(settings, from_=1, to=20, textvariable=self.npc_count, font=("Arial", 10)).pack()

        tk.Button(settings, text="確定", command=settings.destroy).pack(pady=15)
    def open_leaderboard(self):
        self.destroy()  # 關掉主選單，確保沒有 Tk 實例殘留
        subprocess.Popen([sys.executable, "ranking_screen.py"])
# -------------------------------
# 載入動畫用的 Loading 視窗
# -------------------------------
class LoadingScreen(tk.Toplevel):
    def __init__(self, parent, game_time, npc_count):
        super().__init__(parent)
        self.title("Loading...")
        self.geometry("400x200")
        self.configure(bg="#222222")
        self.resizable(False, False)

        tk.Label(self, text="遊戲載入中，請稍候...", font=("Arial", 16),
                 fg="white", bg="#222222").pack(pady=40)

        self.progress = ttk.Progressbar(self, mode='indeterminate', length=250)
        self.progress.pack(pady=10)
        self.progress.start()

        # 背景 thread 中載入遊戲
        threading.Thread(
            target=self.load_game,
            args=(game_time, npc_count),
            daemon=True
        ).start()

    def load_game(self, game_time, npc_count):
        import time
        time.sleep(1.5)  # 可刪除：模擬載入時間

        # 在主執行緒中啟動遊戲畫面
        self.after(0, self.start_game_ui, game_time, npc_count)

    def start_game_ui(self, game_time, npc_count):
        self.progress.stop()  # 先停止動畫
        self.destroy()  # 關掉 loading 畫面
        self.master.destroy()  # 關掉主選單
        game = ElectricEyeGame(game_time=game_time, npc_count=npc_count)
        game.mainloop()

# -------------------------------
if __name__ == '__main__':
    GameLauncher().mainloop()
