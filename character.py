from animation import Animation
from PIL import Image, ImageTk
from pathlib import Path
import random

class Character:
    def __init__(self, canvas, world_x, y):
        self.canvas = canvas
        self.world_x = world_x
        self.y = y
        self.face_right = random.choice([True, False])
        self.stopping = False
        self._end_hits = 0
        self.anim = None
        self.current_img = None

    def _load_animation(self, dir_path: Path, anim_fps: int, game_fps: int, frame_count: int, resize_ratio: int):
        frames = []
        for i in range(frame_count):
            img = Image.open(dir_path / f'{i}.png')
            img = img.resize((img.width // resize_ratio, img.height // resize_ratio), Image.Resampling.LANCZOS)
            frames.append(ImageTk.PhotoImage(img))
        return Animation(frames, anim_fps, game_fps)

    def move(self, speed: int):
        if self.stopping or getattr(self, 'is_attracted', False) or getattr(self, 'is_dead', False):
            return

        dx = speed if self.face_right else -speed
        nxt = self.world_x + dx

        if nxt <= self.bdr_left:
            self.world_x = self.bdr_left
            self._handle_boundary_hit(left=True)
        elif nxt >= self.bdr_right:
            self.world_x = self.bdr_right
            self._handle_boundary_hit(left=False)
        else:
            self.world_x = nxt

    def _handle_boundary_hit(self, left: bool):
        self.stopping = True
        self._end_hits += 1
        self.canvas.after(800, lambda left=left: self._resume_walk(left))

    def _resume_walk(self, left: bool):
        self.face_right = left
        self.anim = self.anim_walk_r if self.face_right else self.anim_walk_l
        self.anim._loop_counter = 0
        self.stopping = False

        if self._end_hits >= 2:
            self.cur_range = random.randint(20, self.max_range)
            self.bdr_left = self.world_x if self.face_right else self.world_x - int(self.cur_range / 2)
            self.bdr_right = self.world_x + int(self.cur_range / 2) if self.face_right else self.world_x
            self._end_hits = 0
