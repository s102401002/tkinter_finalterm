import tkinter as tk
from game import ElectricEyeGame

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
        tk.Button(btn_frame, text="結束程式", width=20, font=("Arial", 12), command=self.quit).pack(pady=5)

    def start_game(self):
        self.destroy()
        game = ElectricEyeGame(game_time=self.game_time.get(), npc_count=self.npc_count.get())
        game.mainloop()

    def open_settings(self):
        settings = tk.Toplevel(self)
        settings.title("遊戲設定")
        settings.geometry("300x200")
        settings.configure(bg="#fefefe")

        tk.Label(settings, text="遊戲時間（秒）:", bg="#fefefe", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Spinbox(settings, from_=30, to=300, textvariable=self.game_time, font=("Arial", 10)).pack()

        tk.Label(settings, text="NPC 數量:", bg="#fefefe", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Spinbox(settings, from_=1, to=20, textvariable=self.npc_count, font=("Arial", 10)).pack()

        tk.Button(settings, text="確定", command=settings.destroy).pack(pady=15)

if __name__ == '__main__':
    GameLauncher().mainloop()
