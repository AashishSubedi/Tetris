# pieces.py
import random
from settings import S

PIECES = ["I", "O", "T", "S", "Z", "J", "L"]
COLORS = dict(S.COLORS)

SHAPES = {
    "I": ["....", "####", "....", "...."],
    "O": [".##.", ".##.", "....", "...."],
    "T": [".#..", "###.", "....", "...."],
    "S": [".##.", "##..", "....", "...."],
    "Z": ["##..", ".##.", "....", "...."],
    "J": ["#...", "###.", "....", "...."],
    "L": ["..#.", "###.", "....", "...."],
}

def rotate_4x4(shape_rows):
    grid = [list(r) for r in shape_rows]
    rot = list(zip(*grid[::-1]))
    return ["".join(row) for row in rot]

def shape_to_blocks(shape_rows):
    blocks = []
    for y, row in enumerate(shape_rows):
        for x, c in enumerate(row):
            if c == "#":
                blocks.append((x, y))
    return blocks

ROTATIONS = {}
for k, base in SHAPES.items():
    rots = [base]
    for _ in range(3):
        rots.append(rotate_4x4(rots[-1]))
    ROTATIONS[k] = [shape_to_blocks(r) for r in rots]

# O-piece should not "wiggle"
ROTATIONS["O"] = [ROTATIONS["O"][0]] * 4

class Bag:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self._bag = []

    def next(self):
        if not self._bag:
            self._bag = PIECES[:]
            self.rng.shuffle(self._bag)
        return self._bag.pop()
