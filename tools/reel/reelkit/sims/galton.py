"""Python port of src/games/galton-board/sim.ts (same formulas, constants and seeded random numbers).
World units: one peg spacing = 1, y points down. Used to get the real numbers a reel narrates."""
import math

G = 30
MARBLE_R = 0.17
PEG_R = 0.1
ROW_DY = 0.866
BIN_DEPTH = 9
SUBSTEPS = 6
DRAG = 3.5
DEFAULT = dict(rows=12, tilt_deg=0.0, wind=0.0, bounce=0.45, rate=40, total=1000)


class Rng:
    """mulberry32, identical to src/shared/math/random.ts."""

    def __init__(self, seed):
        self.a = seed & 0xFFFFFFFF

    def next(self):
        self.a = (self.a + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.a
        t = _imul(t ^ (t >> 15), t | 1)
        t ^= (t + _imul(t ^ (t >> 7), t | 61)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    def range(self, lo, hi):
        return lo + self.next() * (hi - lo)


def _imul(a, b):
    return (a * b) & 0xFFFFFFFF


class Marble:
    __slots__ = ('x', 'y', 'vx', 'vy', 'bin', 'id')

    def __init__(self, x, y, vx, vy, mid):
        self.x, self.y, self.vx, self.vy, self.bin, self.id = x, y, vx, vy, -1, mid


class Board:
    def __init__(self, rows, seed=1):
        self.rows, self.bins = rows, rows + 1
        self.width = self.bins
        self.peg_top = 1.5
        self.pegs = []
        for i in range(rows):
            y = self.peg_top + i * ROW_DY
            x = 1.0 if (rows - 1 - i) % 2 == 0 else 0.5
            while x < self.width - 0.01:
                self.pegs.append((x, y))
                x += 1
        self.bin_top = self.peg_top + (rows - 1) * ROW_DY + 0.75
        self.floor = self.bin_top + BIN_DEPTH
        self.counts = [0] * self.bins
        self.marbles, self.released, self.landed, self.carry = [], 0, 0, 0.0
        self.landings = []  # (marble id, bin) in landing order
        self.rng = Rng(seed)

    def pile_scale(self):
        per = (2 * MARBLE_R) ** 2 * 0.9
        mx = max(1, *self.counts)
        return BIN_DEPTH * 0.95 / mx if mx * per > BIN_DEPTH * 0.95 else per

    def pile_height(self, b):
        return self.counts[b] * self.pile_scale()

    def release(self):
        r = self.rng
        self.marbles.append(Marble(self.width / 2 + r.range(-0.04, 0.04), 0.2, r.range(-0.3, 0.3), 0.0, self.released))
        self.released += 1

    def step(self, p, dt):
        self.carry += p['rate'] * dt
        while self.carry >= 1 and self.released < p['total']:
            self.release()
            self.carry -= 1
        if self.released >= p['total']:
            self.carry = 0
        tilt = math.radians(p['tilt_deg'])
        ax, ay = G * math.sin(tilt) + G * p['wind'], G * math.cos(tilt)
        h = dt / SUBSTEPS
        hit = MARBLE_R + PEG_R
        damp = math.exp(-DRAG * h)
        for _ in range(SUBSTEPS):
            for m in list(reversed(self.marbles)):
                m.vx = (m.vx + ax * h) * damp
                m.vy = (m.vy + ay * h) * damp
                m.x += m.vx * h
                m.y += m.vy * h
                if m.x < MARBLE_R:
                    m.x, m.vx = MARBLE_R, abs(m.vx) * p['bounce']
                if m.x > self.width - MARBLE_R:
                    m.x, m.vx = self.width - MARBLE_R, -abs(m.vx) * p['bounce']
                if m.y < self.bin_top:
                    row = round((m.y - self.peg_top) / ROW_DY)
                    if row < 0 or row >= self.rows:
                        continue
                    for px, py in self.pegs:
                        if abs(py - m.y) > hit or abs(px - m.x) > hit:
                            continue
                        dx, dy = m.x - px, m.y - py
                        d = math.hypot(dx, dy)
                        if d >= hit or d == 0:
                            continue
                        nx, ny = dx / d, dy / d
                        m.x, m.y = px + nx * hit, py + ny * hit
                        vn = m.vx * nx + m.vy * ny
                        if vn < 0:
                            m.vx -= (1 + p['bounce']) * vn * nx
                            m.vy -= (1 + p['bounce']) * vn * ny
                            j = self.rng.range(-0.25, 0.25)
                            m.vx += -ny * j
                            m.vy += nx * j
                else:
                    if m.bin < 0:
                        m.bin = min(self.bins - 1, max(0, math.floor(m.x)))
                    lo, hi = m.bin + MARBLE_R, m.bin + 1 - MARBLE_R
                    if m.x < lo:
                        m.x, m.vx = lo, abs(m.vx) * 0.3
                    if m.x > hi:
                        m.x, m.vx = hi, -abs(m.vx) * 0.3
                    if m.y + MARBLE_R >= self.floor - self.pile_height(m.bin):
                        self.counts[m.bin] += 1
                        self.landed += 1
                        self.landings.append((m.id, m.bin))
                        self.marbles.remove(m)

    def finished(self, p):
        return self.released >= p['total'] and not self.marbles

    def stats(self):
        if not self.landed:
            return 0.0, 0.0
        c = (self.bins - 1) / 2
        mean = sum(n * (i - c) for i, n in enumerate(self.counts)) / self.landed
        var = sum(n * (i - c - mean) ** 2 for i, n in enumerate(self.counts)) / self.landed
        return mean, math.sqrt(var)


def run(p, seed, record=None, fps=30, max_s=200):
    """Runs a whole drop; record(t, board) once per video frame. Returns the board."""
    b = Board(p['rows'], seed)
    t, f = 0.0, 0
    while not b.finished(p) and t < max_s:
        if record:
            record(t, b)
        b.step(p, 1 / fps)
        t += 1 / fps
        f += 1
    if record:
        record(t, b)
    return b


if __name__ == '__main__':
    import sys
    bounce = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT['bounce']
    for seed in (1, 2, 3):
        p = dict(DEFAULT, bounce=bounce, rate=300)
        b = run(p, seed)
        mean, sd = b.stats()
        print(f'seed {seed} bounce {bounce}: counts {b.counts} mean {mean:+.2f} sd {sd:.2f} (theory {math.sqrt(p["rows"]) / 2:.2f})')
