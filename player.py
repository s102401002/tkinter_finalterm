class Player:
    def __init__(self, canvas, x, y, walk_r, walk_l, run_r, run_l):
        self.canvas = canvas
        self.walk_r, self.walk_l = walk_r, walk_l
        self.run_r,  self.run_l  = run_r,  run_l
        self.anim = walk_r
        self.face_right = True
        self.running = False
        self.hover = False
        self.idle = False
        self.x, self.y = x, y
        self.vx = 0
        self.id = canvas.create_image(x, y, image=self.anim.frames[0], tags='player')

    def set_direction(self, mouse_x):
        new_face = (mouse_x >= self.x)
        if new_face != self.face_right:
            self.face_right = new_face
            return True
        return False

    def set_speed(self, speed, running):
        self.vx = speed if self.face_right else -speed
        self.running = running
        if self.face_right:
            self.anim = self.run_r if self.running else self.walk_r
        else:
            self.anim = self.run_l if self.running else self.walk_l

    def update(self):
        self.canvas.coords(self.id, self.x, self.y)
        if self.hover or self.idle:
            img = self.anim.frames[0]
        else:
            img = self.anim.next()
        self.canvas.itemconfig(self.id, image=img)
