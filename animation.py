import tkinter as tk

class Animation:
    """簡易動畫輪播：依主迴圈 FPS 與 cycle fps 均勻切幀"""
    def __init__(self, frames: list[tk.PhotoImage], cycle_fps: int, fps: int):
        self.frames = frames
        self.n = len(frames)
        loops_per_cycle = fps // cycle_fps
        self.loops_per_frame = max(1, loops_per_cycle // self.n)
        self._loop_counter = 0

    def next(self) -> tk.PhotoImage:
        idx = (self._loop_counter // self.loops_per_frame) % self.n
        self._loop_counter += 1
        return self.frames[idx]
