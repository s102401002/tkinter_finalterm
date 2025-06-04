import tkinter as tk
import math
class Animation:
    def __init__(self, frames: list[tk.PhotoImage], cycle_fps: int, fps: int):
        self.frames = frames
        self.n = len(frames)
        # 每秒要播 cycle_fps 次完整循環 → 每張圖要停留幾個主迴圈frame
        loops = fps / cycle_fps            
        self.loops_per_frame = max(1, math.ceil(loops))
        self._loop_counter = 0

    def next(self) -> tk.PhotoImage:
        idx = (self._loop_counter // self.loops_per_frame) % self.n
        self._loop_counter += 1
        return self.frames[idx]
