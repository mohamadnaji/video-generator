"""Python port of src/games/slingshot-planets/sim.ts (same formulas and constants).
World units, star at the origin, y down. Used to get the real numbers a reel narrates."""
import math

MU = 1.2e7
STAR_R = 28
GIANT_ORBIT = 340
GIANT_R = 13
GIANT_MU_SHARE = 0.03
VIEW_R = 500
SYSTEM_R = VIEW_R * 1.15
ORBIT_TURNS = 2
SUBSTEP = 1 / 240
SOFT2 = 4


def star_mu(p):
    return MU * p.get('star_mass', 1)


def giant_pos(p, t):
    w = math.sqrt(star_mu(p) / GIANT_ORBIT ** 3)
    return GIANT_ORBIT * math.cos(-w * t), GIANT_ORBIT * math.sin(-w * t)


def orbit_speeds(p, r):
    c = math.sqrt(star_mu(p) / max(r, 1))
    return c, c * math.sqrt(2)


def accel(p, t, x, y):
    r2 = x * x + y * y + SOFT2
    k = -star_mu(p) / (r2 * math.sqrt(r2))
    ax, ay = k * x, k * y
    if p.get('giant'):
        gx, gy = giant_pos(p, t)
        dx, dy = x - gx, y - gy
        d2 = dx * dx + dy * dy + SOFT2
        kg = -star_mu(p) * GIANT_MU_SHARE / (d2 * math.sqrt(d2))
        ax += kg * dx
        ay += kg * dy
    return ax, ay


class Moon:
    def __init__(self, x, y, vx, vy, label=''):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.status, self.swept, self.label = 'flying', 0.0, label
        self.end_t = None  # time of crash / escape

    def advance(self, p, t, h):
        before = math.atan2(self.y, self.x)
        ax, ay = accel(p, t, self.x, self.y)
        self.vx += ax * h / 2; self.vy += ay * h / 2
        self.x += self.vx * h; self.y += self.vy * h
        ax, ay = accel(p, t + h, self.x, self.y)
        self.vx += ax * h / 2; self.vy += ay * h / 2
        d = math.atan2(self.y, self.x) - before
        if d > math.pi: d -= 2 * math.pi
        if d < -math.pi: d += 2 * math.pi
        self.swept += d


def outcome(p, t, m):
    r = math.hypot(m.x, m.y)
    if r < STAR_R:
        return 'crashed'
    if p.get('giant'):
        gx, gy = giant_pos(p, t)
        if math.hypot(m.x - gx, m.y - gy) < GIANT_R + 3:
            return 'crashed'
    if r > SYSTEM_R:
        return 'escaped'
    return None


def energy(p, m):
    """Specific orbital energy around the star alone (negative = bound)."""
    return (m.vx ** 2 + m.vy ** 2) / 2 - star_mu(p) / math.hypot(m.x, m.y)


def run(p, moons, seconds, fps=30, record=None):
    """Steps every moon; calls record(t, moons) once per video frame. Returns the frame count."""
    t, frames = 0.0, int(seconds * fps)
    steps = max(1, math.ceil((1 / fps) / SUBSTEP))
    h = (1 / fps) / steps
    for f in range(frames):
        if record:
            record(t, moons)
        for _ in range(steps):
            for m in moons:
                if m.status in ('crashed', 'escaped'):
                    continue
                m.advance(p, t, h)
                end = outcome(p, t + h, m)
                if end:
                    m.status, m.end_t = end, t + h
                elif m.status == 'flying' and abs(m.swept) >= ORBIT_TURNS * 2 * math.pi:
                    m.status = 'orbit'
            t += h
    return frames


def tangential_launch(p, r, mult, label=''):
    """Moon at the top (0, -r) moving sideways (counter-clockwise on screen) at mult × circular speed."""
    c, _ = orbit_speeds(p, r)
    return Moon(0, -r, -c * mult, 0, label or f'{mult:.2f}×')


if __name__ == '__main__':
    # Thresholds for a sideways launch from radius r: crash below, escape above (× circle speed).
    import sys
    r = float(sys.argv[1]) if len(sys.argv) > 1 else 230
    p = {}
    lo, hi = 0.05, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        m = tangential_launch(p, r, mid)
        run(p, [m], 15)
        lo, hi = (mid, hi) if m.status == 'crashed' else (lo, mid)
    c, e = orbit_speeds(p, r)
    print(f'r = {r:g}: circle speed {c:.1f}, escape {e:.1f} (×{e / c:.3f}), crashes below ×{lo:.3f}')
