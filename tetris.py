# tetris.py
from settings import S
from pieces import Bag, ROTATIONS, COLORS

# SRS wall-kicks (y+ is down)
JLSTZ_KICKS = {
    (0, 1): [(0,0), (-1,0), (-1,-1), (0,2), (-1,2)],
    (1, 0): [(0,0), (1,0), (1,1), (0,-2), (1,-2)],

    (1, 2): [(0,0), (1,0), (1,1), (0,-2), (1,-2)],
    (2, 1): [(0,0), (-1,0), (-1,-1), (0,2), (-1,2)],

    (2, 3): [(0,0), (1,0), (1,-1), (0,2), (1,2)],
    (3, 2): [(0,0), (-1,0), (-1,1), (0,-2), (-1,-2)],

    (3, 0): [(0,0), (-1,0), (-1,1), (0,-2), (-1,-2)],
    (0, 3): [(0,0), (1,0), (1,-1), (0,2), (1,2)],
}

I_KICKS = {
    (0, 1): [(0,0), (-2,0), (1,0), (-2,1), (1,-2)],
    (1, 0): [(0,0), (2,0), (-1,0), (2,-1), (-1,2)],

    (1, 2): [(0,0), (-1,0), (2,0), (-1,-2), (2,1)],
    (2, 1): [(0,0), (1,0), (-2,0), (1,2), (-2,-1)],

    (2, 3): [(0,0), (2,0), (-1,0), (2,-1), (-1,2)],
    (3, 2): [(0,0), (-2,0), (1,0), (-2,1), (1,-2)],

    (3, 0): [(0,0), (1,0), (-2,0), (1,2), (-2,-1)],
    (0, 3): [(0,0), (-1,0), (2,0), (-1,-2), (2,1)],
}

def get_kicks(kind, fr, to):
    if kind == "I":
        return I_KICKS.get((fr, to), [(0, 0)])
    if kind == "O":
        return [(0, 0)]
    return JLSTZ_KICKS.get((fr, to), [(0, 0)])


class Piece:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.rot = 0
        self.x = x
        self.y = y

    def blocks(self, rot=None, x=None, y=None):
        r = self.rot if rot is None else rot
        px = self.x if x is None else x
        py = self.y if y is None else y
        return [(px + bx, py + by) for (bx, by) in ROTATIONS[self.kind][r]]


class Game:
    def __init__(self, effects=None):
        self.effects = effects
        self.reset()

    def reset(self):
        self.cols = S.COLS
        self.rows = S.ROWS
        self.hid = S.HIDDEN_ROWS
        self.grid = [[None for _ in range(self.cols)] for __ in range(self.rows + self.hid)]

        self.bag = Bag()
        self.queue = [self.bag.next() for _ in range(5)]
        self.hold_kind = None
        self.hold_used = False

        self.score = 0
        self.lines = 0
        self.level = 1

        self.gravity = S.GRAVITY_START
        self.drop_acc = 0.0

        self.lock_timer = 0.0
        self.dead = False
        self.paused = False

        # Input repeat
        self.left_held = False
        self.right_held = False
        self.das_t = 0.0
        self.arr_t = 0.0
        self.last_dir = 0

        self.soft_drop = False

        # Line clear animation state
        self.clearing_rows = []
        self.clear_anim_t = 0.0
        self.pending_clear_rows = []
        self.just_cleared_rows = []

        self.spawn()

    def toggle_pause(self):
        if self.dead:
            return
        self.paused = not self.paused
        self.drop_acc = 0.0
        self.das_t = 0.0
        self.arr_t = 0.0

    def _recalc_gravity(self):
        self.gravity = max(S.GRAVITY_MIN, S.GRAVITY_START * (S.GRAVITY_DECAY ** (self.level - 1)))

    def spawn(self):
        kind = self.queue.pop(0)
        self.queue.append(self.bag.next())
        self.cur = Piece(kind, 3, 0)
        self.hold_used = False
        self.lock_timer = 0.0
        if self._collides(self.cur):
            self.dead = True

    def _collides(self, piece, rot=None, x=None, y=None):
        for bx, by in piece.blocks(rot=rot, x=x, y=y):
            if bx < 0 or bx >= self.cols or by >= self.rows + self.hid:
                return True
            if by >= 0 and self.grid[by][bx] is not None:
                return True
        return False

    def _lock(self):
        col = COLORS[self.cur.kind]
        for bx, by in self.cur.blocks():
            if 0 <= by < self.rows + self.hid:
                self.grid[by][bx] = col

        cleared = self._start_clear_if_any()
        if not cleared:
            self.spawn()

    def _start_clear_if_any(self):
        full = []
        for y in range(self.rows + self.hid):
            if all(self.grid[y][x] is not None for x in range(self.cols)):
                full.append(y)

        if not full:
            return False

        self.clearing_rows = full
        self.pending_clear_rows = full[:]
        self.just_cleared_rows = full[:]
        self.clear_anim_t = S.CLEAR_ANIM_TIME

        n = len(full)
        base = {1: 100, 2: 300, 3: 500, 4: 800}[n]
        self.score += base * self.level
        self.lines += n
        self.level = 1 + (self.lines // 10)
        self._recalc_gravity()

        if self.effects:
            self.effects.shake.add(3 + 2 * n)

        return True

    def hard_drop(self):
        if self.dead or self.paused or self.clear_anim_t > 0:
            return
        dy = 0
        while not self._collides(self.cur, y=self.cur.y + dy + 1):
            dy += 1
        self.cur.y += dy
        self.score += 2 * dy
        self.lock_timer = 0.0
        self._lock()

    def hold(self):
        if self.dead or self.paused or self.hold_used or self.clear_anim_t > 0:
            return
        self.hold_used = True
        if self.hold_kind is None:
            self.hold_kind = self.cur.kind
            self.spawn()
        else:
            self.hold_kind, self.cur.kind = self.cur.kind, self.hold_kind
            self.cur.rot = 0
            self.cur.x, self.cur.y = 3, 0
            if self._collides(self.cur):
                self.dead = True

    def rotate(self, dir_):
        if self.dead or self.paused or self.clear_anim_t > 0:
            return

        fr = self.cur.rot
        nr = (fr + dir_) % 4

        if self.cur.kind == "O":
            self.cur.rot = nr
            self.lock_timer = 0.0
            return

        for ox, oy in get_kicks(self.cur.kind, fr, nr):
            nx = self.cur.x + ox
            ny = self.cur.y + oy
            if not self._collides(self.cur, rot=nr, x=nx, y=ny):
                self.cur.rot = nr
                self.cur.x, self.cur.y = nx, ny
                self.lock_timer = 0.0
                return

    def move(self, dx):
        if self.dead or self.paused or self.clear_anim_t > 0:
            return False
        nx = self.cur.x + dx
        if not self._collides(self.cur, x=nx):
            self.cur.x = nx
            self.lock_timer = 0.0
            return True
        return False

    def step_down(self, forced=False):
        if self.dead or self.paused or self.clear_anim_t > 0:
            return False
        ny = self.cur.y + 1
        if not self._collides(self.cur, y=ny):
            self.cur.y = ny
            if forced:
                self.score += 1
            return True
        return False

    def ghost_y(self):
        dy = 0
        while not self._collides(self.cur, y=self.cur.y + dy + 1):
            dy += 1
        return self.cur.y + dy

    def update(self, dt):
        if self.dead or self.paused:
            return

        # Line-clear animation
        if self.clear_anim_t > 0:
            self.clear_anim_t = max(0.0, self.clear_anim_t - dt)
            if self.clear_anim_t == 0.0 and self.pending_clear_rows:
                for y in sorted(self.pending_clear_rows):
                    del self.grid[y]
                    self.grid.insert(0, [None for _ in range(self.cols)])
                self.pending_clear_rows = []
                self.clearing_rows = []
                self.spawn()
            return

        # Gravity
        g = self.gravity * (S.SOFT_DROP_MULT if self.soft_drop else 1.0)
        self.drop_acc += dt
        while self.drop_acc >= g:
            self.drop_acc -= g
            moved = self.step_down()
            if not moved:
                break

        # Lock delay when grounded
        grounded = self._collides(self.cur, y=self.cur.y + 1)
        if grounded:
            self.lock_timer += dt
            if self.lock_timer >= S.LOCK_DELAY:
                self.lock_timer = 0.0
                self._lock()
        else:
            self.lock_timer = 0.0

        # DAS/ARR sideways
        dir_ = 0
        if self.left_held and not self.right_held:
            dir_ = -1
        elif self.right_held and not self.left_held:
            dir_ = 1

        if dir_ == 0:
            self.das_t = 0.0
            self.arr_t = 0.0
            self.last_dir = 0
            return

        if self.last_dir != dir_:
            self.last_dir = dir_
            self.das_t = 0.0
            self.arr_t = 0.0
            self.move(dir_)
            return

        self.das_t += dt
        if self.das_t < S.DAS:
            return

        self.arr_t += dt
        while self.arr_t >= S.ARR:
            self.arr_t -= S.ARR
            if not self.move(dir_):
                break
