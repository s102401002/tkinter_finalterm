import tkinter as tk
from game import ElectricEyeGame

class GameLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("主選單")
        self.geometry("400x300")
        self.resizable(False, False)

        self.game_time = tk.IntVar(value=60)
        self.npc_count = tk.IntVar(value=7)

        tk.Label(self, text="電眼美女 遊戲選單", font=("Arial", 16)).pack(pady=10)

        tk.Button(self, text="開始遊戲", command=self.start_game).pack(pady=10)
        tk.Button(self, text="設定", command=self.open_settings).pack(pady=10)

    def start_game(self):
        self.destroy()
        game = ElectricEyeGame(game_time=self.game_time.get(), npc_count=self.npc_count.get())
        game.mainloop()

    def open_settings(self):
        settings = tk.Toplevel(self)
        settings.title("遊戲設定")
        settings.geometry("300x200")

        tk.Label(settings, text="遊戲時間（秒）:").pack()
        tk.Spinbox(settings, from_=30, to=300, textvariable=self.game_time).pack()

        tk.Label(settings, text="NPC 數量:").pack()
        tk.Spinbox(settings, from_=1, to=20, textvariable=self.npc_count).pack()

        tk.Button(settings, text="確定", command=settings.destroy).pack(pady=10)

if __name__ == '__main__':
    GameLauncher().mainloop()
