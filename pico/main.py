# ============================================================
# Pico Light Show
# 5 x NeoPixel strips on GP0-GP4, 20 LEDs each
# Strips 2 (GP2) and 4 (GP4) are physically REVERSED
#
# Buttons (active-low, internal pull-up):
#   GP16  Play/Pause      GP17  Prev track
#   GP18  Next track      GP19  Random color + effect
#   GP20  Volume down     GP21  Volume up
# Audio: DFPlayer Mini on UART1  GP8=TX  GP9=RX  GP5=BUSY
# ============================================================

from neopixel import NeoPixel   # type: ignore
from machine  import Pin, UART  # type: ignore
from time     import sleep, ticks_ms, ticks_diff
import math
import urandom

# =====================================================================
# HARDWARE
# =====================================================================

N       = 20
NSTRIPS = 5
REV     = {2, 4}   # physically reversed strips

strips  = [NeoPixel(Pin(i), N) for i in range(NSTRIPS)]
onboard = Pin("LED", Pin.OUT)
onboard.on()

_btns     = [Pin(p, Pin.IN, Pin.PULL_UP) for p in (16, 17, 18, 19, 20, 21)]
_bprev    = [True] * 6
_btime    = [0]    * 6
_DEBOUNCE = 50

# =====================================================================
# GLOBAL STATE
# =====================================================================

_brightness = 0.7
_eff_idx    = 0
_pat_idx    = 0
_theme_idx  = 0
_t_effect   = 0
_paused     = False

# =====================================================================
# DFPLAYER MINI
# =====================================================================

_DFPLAYER_VOLUME = 20    # 0-30
_track_count     = 2     # number of tracks on SD card
_track_idx       = 1     # currently playing track (1-indexed)
_busy_prev       = True  # last BUSY pin state (HIGH = idle)
_last_play_ms    = 0     # ticks_ms() when dfp_play() was last called

_uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
_busy = Pin(5, Pin.IN, Pin.PULL_UP)

def _dfp_send(cmd, p1=0, p2=0):
    inner = [0xFF, 0x06, cmd, 0x00, p1, p2]
    cs    = (-sum(inner)) & 0xFFFF
    _uart.write(bytes([0x7E] + inner + [(cs >> 8) & 0xFF, cs & 0xFF, 0xEF]))
    sleep(0.05)

def dfp_init():
    sleep(1.5)
    _dfp_send(0x0C)                        # reset
    sleep(1.5)
    _dfp_send(0x06, 0, _DFPLAYER_VOLUME)  # set volume

def dfp_play(n):   _dfp_send(0x03, 0, n)
def dfp_next():    _dfp_send(0x01)
def dfp_prev():    _dfp_send(0x02)
def dfp_pause():   _dfp_send(0x0E)
def dfp_resume():  _dfp_send(0x0D)
def dfp_vol_up():  _dfp_send(0x04)
def dfp_vol_dn():  _dfp_send(0x05)


# =====================================================================
# COLOR HELPERS
# =====================================================================

def _c(r, g, b, s=1.0):
    s = max(0.0, min(1.0, s)) * _brightness
    return (int(r * s), int(g * s), int(b * s))

def _add(a, b):
    return (min(255, a[0]+b[0]), min(255, a[1]+b[1]), min(255, a[2]+b[2]))

def _px(si, i):
    return (N - 1 - i) if si in REV else i

def _write_all():
    for s in strips: s.write()

def _fill_all(col):
    for s in strips: s.fill(col)
    _write_all()

def _fill_strip(si, col):
    strips[si].fill(col)
    strips[si].write()

def _set(si, i, col):
    strips[si][_px(si, i)] = col

def _h(n):
    s = int(n) & 0xFFFFFFFF
    s = ((s >> 16) ^ s) * 0x45d9f3b & 0xFFFFFFFF
    s = ((s >> 16) ^ s) * 0x45d9f3b & 0xFFFFFFFF
    return ((s >> 16) ^ s) & 0xFF

# =====================================================================
# COLOR THEMES
# =====================================================================
# Each theme: 6 colour values [c0..c5]
# c0=primary  c1=alt  c2=accent  c3=dark  c4=mid  c5=bright

THEMES = [
    [(0,60,255),(168,0,255),(0,220,255),(0,20,80),(0,140,200),(200,200,255)],
    [(255,30,0),(255,130,0),(255,220,0),(80,0,0),(180,60,0),(255,200,80)],
    [(0,180,220),(0,80,200),(0,255,200),(0,20,60),(0,120,160),(180,240,255)],
    [(0,200,40),(0,140,60),(180,255,0),(0,40,10),(0,160,80),(200,255,120)],
    [(255,0,160),(200,0,255),(0,255,200),(60,0,60),(180,0,180),(255,180,255)],
    [(140,200,255),(200,240,255),(255,255,255),(10,30,60),(80,160,220),(220,240,255)],
    [(255,10,0),(255,80,0),(255,255,80),(50,0,0),(160,30,0),(255,160,40)],
    [(0,255,100),(0,200,255),(255,0,200),(0,40,20),(0,160,120),(180,255,200)],
    [(255,60,0),(255,0,100),(200,0,255),(60,0,20),(200,40,60),(255,180,120)],
    [(60,0,200),(200,0,255),(255,200,0),(10,0,40),(100,0,160),(220,180,255)],
]

def T(n): return THEMES[_theme_idx][n]

THEME_NAMES = ['Electric','Fire','Ocean','Forest','Neon',
               'Ice','Lava','Cyber','Sunset','Galaxy']

SNAKE_LEN = N * NSTRIPS   # 100


# =====================================================================
# EFFECTS  (0-9)
# Each function receives t_ms = time since pattern last started.
# _pat_idx (0-19) selects sub-parameters within the effect.
# =====================================================================

# ── Effect 0: Lightning Strike ─────────────────────────────────────
def eff_lightning(t):
    p   = _pat_idx
    fr  = t // 30
    for si in range(NSTRIPS):
        strips[si].fill(_c(*T(3), 0.25))
    leaders_tbl = [(0,4),(1,3),(0,1,3,4),(0,2,4),(1,2,3)]
    support_tbl = [(1,3),(0,2,4),(2,),(1,3),(0,4)]
    leaders  = leaders_tbl[p % 5]
    support  = support_tbl[p % 5]
    br_shift = (p // 5) * 0.15
    for si in leaders:
        head = _h(fr * 7 + si * 13) % N
        for i in range(N):
            dist = (i - head) % N
            if dist < 5:
                f   = ((5 - dist) / 5.0) ** 1.8 * (0.8 + br_shift)
                col = T(2) if _h(fr*3+i) > 200 else T(0)
                _set(si, i, _c(*col, f))
        for sp in range(6):
            sv = _h(fr * 19 + sp * 11 + si * 7)
            if sv > 190:
                pos = _h(fr * 23 + sp * 7 + si * 3) % N
                _set(si, pos, _c(*T(5), (sv-190)/65.0))
    for si in support:
        head2 = _h(fr * 5 + si * 17 + 50) % N
        for i in range(N):
            dist = (i - head2) % N
            if dist < 3:
                f = ((3 - dist) / 3.0) ** 2.0 * (0.45 + br_shift)
                _set(si, i, _c(*T(1), f))
    if _h(fr * 41) > 248:
        _fill_all(_c(*T(5), 1.0))
        sleep(0.018)
        return
    _write_all()


# ── Effect 1: Snake Chase ──────────────────────────────────────────
def eff_snake(t):
    p        = _pat_idx
    speed    = max(20, 80 - (p % 10) * 6)
    tail_len = 8 + (p // 10) * 6
    count    = 1 + (1 if p % 5 > 2 else 0)
    reverse  = (p % 4 >= 2)
    for si in range(NSTRIPS): strips[si].fill((0, 0, 0))
    for snake_n in range(count):
        offset   = (SNAKE_LEN // max(count, 2)) * snake_n
        head_pos = ((t // speed) + offset) % SNAKE_LEN
        if reverse: head_pos = (SNAKE_LEN - 1 - head_pos) % SNAKE_LEN
        for j in range(tail_len):
            pos = (head_pos - j) % SNAKE_LEN if not reverse else (head_pos + j) % SNAKE_LEN
            f   = ((tail_len - j) / tail_len) ** 1.6
            col = T(2) if j == 0 else (T(0) if j < tail_len // 2 else T(3))
            si2 = pos // N
            li  = pos % N
            px  = _px(si2, li)
            strips[si2][px] = _add(strips[si2][px], _c(*col, f))
    _write_all()


# ── Effect 2: Pulse Wave ───────────────────────────────────────────
def eff_pulse(t):
    p      = _pat_idx
    speed  = 800 + (p % 5) * 200
    width  = 0.3 + (p // 5) * 0.15
    invert = (p % 2 == 1)
    phase  = (t % speed) / speed
    for si in range(NSTRIPS):
        for i in range(N):
            norm   = i / (N - 1.0)
            dist   = abs(norm - 0.5)
            wave_d = abs(dist - phase)
            if wave_d < width:
                f = (1.0 - wave_d / width) ** 2
                if invert: f = 1.0 - f
            else:
                f = 0.02 if not invert else 0.9
            _set(si, i, _c(*(T(0) if i < N // 2 else T(1)), f))
        strips[si].write()
    af = math.sin((t % (speed*2))/(speed*2) * math.pi * 2) * 0.5 + 0.5
    for si in (0, 4):
        for i in range(N):
            px = _px(si, i)
            strips[si][px] = _add(strips[si][px], _c(*T(2), af * 0.4))
        strips[si].write()


# ── Effect 3: Meteor Shower ────────────────────────────────────────
def eff_meteor(t):
    p         = _pat_idx
    speed     = max(15, 35 + (p % 5) * 12)
    tail      = 7 + (p // 5) * 3
    n_meteors = 2 + (p % 3)
    paired    = (p % 2 == 1)
    for si in range(NSTRIPS): strips[si].fill((0, 0, 0))
    spacing = SNAKE_LEN // n_meteors
    for m in range(n_meteors):
        head = ((t // speed) + m * spacing) % SNAKE_LEN
        for j in range(tail):
            pos = (head - j) % SNAKE_LEN
            f   = ((tail - j) / tail) ** 2.0
            col = T(5) if j == 0 else (T(0) if j < 3 else T(3))
            si2 = pos // N
            li  = pos % N
            px  = _px(si2, li)
            strips[si2][px] = _add(strips[si2][px], _c(*col, f))
        if paired:
            mh = (SNAKE_LEN - 1 - ((t // speed) + m * spacing)) % SNAKE_LEN
            for j in range(tail):
                pos = (mh + j) % SNAKE_LEN
                f   = ((tail - j) / tail) ** 2.0
                si2 = pos // N
                li  = pos % N
                px  = _px(si2, li)
                strips[si2][px] = _add(strips[si2][px], _c(*T(1), f*0.6))
    _write_all()


# ── Effect 4: Fire ─────────────────────────────────────────────────
def eff_fire(t):
    p      = _pat_idx
    fr     = t // (18 + (p % 5) * 4)
    height = 0.5 + (p // 5) * 0.15
    c0, c1, c2 = T(0), T(1), T(2)
    for si in range(NSTRIPS):
        for i in range(N):
            bh   = max(0.0, height - (i / N) * 0.9)
            noise= _h(fr * 7 + i * 3 + si * 11) / 255.0 * 0.35
            heat = min(1.0, bh + noise)
            if heat > 0.75:   col = _c(*c2, heat)
            elif heat > 0.45: col = _c(*c1, heat)
            elif heat > 0.15: col = _c(*c0, heat * 0.8)
            else:             col = (0, 0, 0)
            _set(si, i, col)
        for sp in range(3):
            sv = _h(fr * 13 + sp * 17 + si * 5)
            if sv > 210:
                pos = N - 1 - (_h(fr * 23 + sp * 7 + si) % (N // 3))
                _set(si, pos, _c(*c2, (sv - 210) / 45.0))
        strips[si].write()


# ── Effect 5: Strobe ───────────────────────────────────────────────
_STROBE_PERIODS = (60,80,100,120,150,60,80,100,60,80,50,70,90,110,130,55,75,95,65,85)
_STROBE_GROUPS  = [
    (0,4),(1,3),(0,1,3,4),(0,2,4),(1,2,3),
    (0,4),(0,1,2,3,4),(1,3),(0,2,4),(0,1,2,3,4),
    (0,4),(1,3),(2,),(0,1,3,4),(0,2,4),
    (0,1,2,3,4),(0,4),(1,2,3),(0,1,3,4),(2,),
]

def eff_strobe(t):
    p      = _pat_idx
    period = _STROBE_PERIODS[p]
    on     = (t % period) < (period // 3)
    groups = _STROBE_GROUPS[p]
    rest   = [s for s in range(NSTRIPS) if s not in groups]
    c_on   = T(0) if (t // 500) % 2 == 0 else T(1)
    if on:
        for si in groups: _fill_strip(si, _c(*c_on, 1.0))
        for si in rest:   _fill_strip(si, _c(*T(3), 0.15))
    else:
        for si in rest:   _fill_strip(si, _c(*T(3), 0.08))
        for si in groups: _fill_strip(si, (0, 0, 0))


# ── Effect 6: Breathing ────────────────────────────────────────────
def eff_breathe(t):
    p      = _pat_idx
    period = 1200 + (p % 5) * 400
    if p % 5 == 2:
        groups  = [(0,1,2,3,4)]; offsets = [0.0]; cols = [T(0)]
    elif p % 5 in (0, 1):
        groups  = [(0,4),(1,3),(2,)]; offsets = [0.0,0.33,0.66]; cols = [T(0),T(1),T(2)]
    elif p % 5 == 3:
        groups  = [(0,4),(1,2,3)]; offsets = [0.0,0.5]; cols = [T(0),T(1)]
    else:
        groups  = [(0,2,4),(1,3)]; offsets = [0.0,0.5]; cols = [T(0),T(2)]
    for gi, grp in enumerate(groups):
        ph    = ((t % period) / period + offsets[gi]) % 1.0
        local = math.sin(ph * math.pi) ** 2
        col   = cols[gi % len(cols)]
        for si in grp:
            for i in range(N):
                _set(si, i, _c(*col, local * (1.0 - (i / N) * 0.45)))
            strips[si].write()


# ── Effect 7: Rainbow ──────────────────────────────────────────────
def eff_rainbow(t):
    p      = _pat_idx
    speed  = 2000 + (p % 5) * 600
    spread = 0.5 + (p // 5) * 0.17
    rev    = (p % 4 >= 2)
    phase  = (t % speed) / speed
    if rev: phase = 1.0 - phase
    def _hsv(h):
        h = h % 1.0; idx = int(h * 6); f = h*6 - idx; q = 1.0 - f
        segs = [(1,f,0),(q,1,0),(0,1,f),(0,q,1),(f,0,1),(1,0,q)]
        r,g,b = segs[idx % 6]; return (int(r*255), int(g*255), int(b*255))
    for pos in range(SNAKE_LEN):
        col = _hsv((pos / SNAKE_LEN * spread + phase) % 1.0)
        si  = pos // N; li = pos % N
        strips[si][_px(si, li)] = _c(*col, 1.0)
    _write_all()


# ── Effect 8: Sparkle ──────────────────────────────────────────────
def eff_sparkle(t):
    p       = _pat_idx
    fr      = t // 30
    density = 0.15 + (p % 5) * 0.08
    decay_f = 1.0 - 0.08 * (1 + (p // 5) * 0.7)
    for si in range(NSTRIPS):
        for i in range(N):
            seed = fr * 7 + i * 3 + si * 11
            if _h(seed) / 255.0 < density:
                _set(si, i, _c(*T(_h(seed * 3) % 3), 1.0))
            else:
                px = _px(si, i)
                r,g,b = strips[si][px]
                strips[si][px] = (int(r*decay_f), int(g*decay_f), int(b*decay_f))
        strips[si].write()


# ── Effect 9: Cascade Fill / Drain ────────────────────────────────
def eff_cascade(t):
    p      = _pat_idx
    period = 1500 + (p % 5) * 300
    phase  = (t % (period * 2)) / (period * 2)
    frac   = min(1.0, phase*2) if phase < 0.5 else max(0.0, 1.0-(phase-0.5)*2)
    ftop   = (p % 2 == 1)
    for si in range(NSTRIPS):
        fc  = int(frac * N)
        col = T(0) if si in (0, 2, 4) else T(1)
        for i in range(N):
            lit = (i >= N - fc) if ftop else (i < fc)
            if lit:
                edge = (N - fc) if ftop else (fc - 1)
                near = abs(i - edge) if fc > 0 else N
                _set(si, i, _c(*(T(2) if near == 0 else col), 1.0 if near < 2 else 0.75))
            else:
                _set(si, i, _c(*T(3), _h(t//80 + i*3 + si*7)/255.0 * 0.06))
        strips[si].write()
    for si in (0, 4):
        fc   = int(frac * N)
        edge = (N - fc) if ftop else (fc - 1)
        if 0 <= edge < N:
            _set(si, edge, _c(*T(5), 1.0))
        strips[si].write()


# =====================================================================
# EFFECT TABLE
# =====================================================================

EFFECTS = [
    (eff_lightning, "Lightning"),
    (eff_snake,     "Snake Chase"),
    (eff_pulse,     "Pulse Wave"),
    (eff_meteor,    "Meteor"),
    (eff_fire,      "Fire"),
    (eff_strobe,    "Strobe"),
    (eff_breathe,   "Breathe"),
    (eff_rainbow,   "Rainbow"),
    (eff_sparkle,   "Sparkle"),
    (eff_cascade,   "Cascade"),
]
N_EFFECTS  = len(EFFECTS)
N_PATTERNS = 20


# =====================================================================
# BUTTONS
# =====================================================================

def _poll_buttons():
    global _brightness, _eff_idx, _pat_idx, _theme_idx, _t_effect
    now    = ticks_ms()
    action = None
    for idx in range(6):
        state = bool(_btns[idx].value())
        if (not state) and _bprev[idx]:
            if ticks_diff(now, _btime[idx]) > _DEBOUNCE:
                _btime[idx] = now
                action = ('play_pause','prev_track','next_track',
                          'rand_color_eff','vol_dn','vol_up')[idx]
        _bprev[idx] = state
    return action


def _apply_action(action):
    global _paused, _eff_idx, _pat_idx, _theme_idx, _t_effect, _track_idx
    if action == 'play_pause':
        if _paused:
            dfp_resume()
            _paused = False
            print("Resumed")
        else:
            dfp_pause()
            _paused = True
            print("Paused")
    elif action == 'prev_track':
        _track_idx = (_track_idx - 2) % _track_count + 1
        dfp_play(_track_idx)
        _paused = False
        _last_play_ms = ticks_ms()
        print("Track:", _track_idx)
    elif action == 'next_track':
        _track_idx = (_track_idx % _track_count) + 1
        dfp_play(_track_idx)
        _paused = False
        _last_play_ms = ticks_ms()
        print("Track:", _track_idx)
    elif action == 'rand_color_eff':
        _theme_idx = urandom.randint(0, len(THEMES) - 1)
        _eff_idx   = urandom.randint(0, N_EFFECTS - 1)
        _pat_idx   = urandom.randint(0, N_PATTERNS - 1)
        _t_effect  = ticks_ms()
        print("Random:", THEME_NAMES[_theme_idx], "+", EFFECTS[_eff_idx][1])
    elif action == 'vol_dn':
        dfp_vol_dn()
        print("Vol -")
    elif action == 'vol_up':
        dfp_vol_up()
        print("Vol +")


# =====================================================================
# MAIN LOOP
# =====================================================================

PAT_DURATION = 8000   # ms before pattern auto-advances

_t_effect = ticks_ms()

print("Pico Light Show -- starting audio")
dfp_init()
dfp_play(_track_idx)
_last_play_ms = ticks_ms()
print("Playing track", _track_idx)

print("Pico Light Show -- ready")
print("Effect:", EFFECTS[_eff_idx][1],
      "| Pattern:", _pat_idx,
      "| Color:", THEME_NAMES[_theme_idx])

while True:
    now  = ticks_ms()
    t_ms = ticks_diff(now, _t_effect)

    if t_ms >= PAT_DURATION:
        _pat_idx  = (_pat_idx + 1) % N_PATTERNS
        _t_effect = now
        t_ms      = 0

    EFFECTS[_eff_idx][0](t_ms)

    act = _poll_buttons()
    if act:
        _apply_action(act)

    # Auto-advance when current track ends (BUSY goes HIGH).
    # Guard: skip if paused, or within 3s of a play command (race condition
    # -- some DFPlayer firmware briefly pulls BUSY HIGH on track change).
    busy_now = bool(_busy.value())
    if (busy_now and not _busy_prev
            and not _paused
            and ticks_diff(now, _last_play_ms) > 3000):
        _track_idx = (_track_idx % _track_count) + 1
        dfp_play(_track_idx)
        _last_play_ms = ticks_ms()
        print("Auto-next track:", _track_idx)
    _busy_prev = busy_now

    sleep(0.016)

