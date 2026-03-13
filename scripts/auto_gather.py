"""
Auto-Gather — pick which nodes to gather, hit Start, watch it work.
Uses USE_ENTITY + frozen-state detection. Run from EthyTool dashboard.
"""
import time
import math
import threading
import tkinter as tk

try:
    conn
    stop_event
except NameError:
    print("ERROR: Run from EthyTool dashboard.")
    raise SystemExit(1)

# ═══════════════════════════════════════════════════════════════
#  Node database (same as radar)
# ═══════════════════════════════════════════════════════════════

CATEGORIES = {
    "mining": {
        "label": "⛏ Mining", "color": "#AAAAAA", "gather_time": 15.0,
        "items": [
            "Copper Vein", "Iron Vein", "Silver Vein", "Coal Vein",
            "Gold Vein", "Ethyrite Vein", "Platinum Vein", "Palladium Vein",
            "Azurium Vein", "Mystril Vein", "Feygold Vein", "Crimsonite Vein",
            "Celestium Vein", "Drakonium Vein", "Leysilver Vein",
        ],
    },
    "harvest": {
        "label": "🌿 Herbs", "color": "#3fb950", "gather_time": 15.0,
        "items": [
            "Rinthistle", "Sunthistle", "Hemp Bush", "Redban Flower",
            "Dark Dragon Plant", "Flax Flower", "Lurker Fungus Mushroom",
            "Cleansing Wisteria", "Cotton Plant", "Ginshade",
            "Wispbloom Flower", "Spirit Wreath Flowers", "Duskthorn",
            "Oxbloom", "Champignon", "Reed", "Small Flower",
        ],
    },
    "woodcut": {
        "label": "🪓 Wood", "color": "#8B4513", "gather_time": 20.0,
        "items": [
            "Dead Tree", "Pine Tree", "Birch Tree", "Fir Tree",
            "Oak Tree", "Acacia Tree", "Wispwood Tree", "Spiritwood Tree",
            "Staroak Tree", "Moonwillow Tree", "Aetherbark Tree",
            "Mana Ash Tree", "Elystram Tree", "Shadewood Tree",
            "Duskroot Tree", "Primordial Tree",
            "Ancient Oak", "Aging Birch", "Ancient Birch",
            "Apple Tree", "Apple Sacks",
        ],
    },
}

_ITEM_TO_CATEGORY = {}
for _cat_key, _cat in CATEGORIES.items():
    for _item in _cat["items"]:
        _ITEM_TO_CATEGORY[_item.lower()] = _cat_key

DEFAULT_GATHER_TIME = 15.0

# ═══════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════

SCAN_INTERVAL   = 0.8
WALK_TIMEOUT    = 14.0
STOP_DETECT     = 5.0
MAX_NODE_DIST   = 45.0
WANDER_STEP     = 12.0
IDLE_WANDER     = 12
EMPTY_COOLDOWN  = 120.0

# ═══════════════════════════════════════════════════════════════
#  Theme
# ═══════════════════════════════════════════════════════════════

BG       = "#0a0e14"
BG_CARD  = "#12161e"
BG_INPUT = "#1a2030"
TEXT     = "#e6edf3"
TEXT_DIM = "#6e7681"
ACCENT   = "#58a6ff"
GREEN    = "#3fb950"
RED      = "#f85149"
ORANGE   = "#d29922"
BORDER   = "#21262d"
FONT     = "Segoe UI"
FONT_B   = "Segoe UI Semibold"
FONT_M   = "Cascadia Code"

# ═══════════════════════════════════════════════════════════════
#  Gather engine
# ═══════════════════════════════════════════════════════════════

class GatherEngine:
    def __init__(self, conn, stop_event, log_fn):
        self.conn = conn
        self.stop_event = stop_event
        self.log = log_fn
        self.targets = set()
        self.gathering = False
        self.combat_enabled = True
        self.loot_enabled = True
        self._thread = None
        self.stats = {"gathered": 0, "attempts": 0, "empty": 0, "cycle": 0, "kills": 0, "looted": 0}
        self._empty_cache = {}
        self._loot_baseline = 0
        self._profile = None
        self._combat_tick = 0.3
        self._def_trigger = 20
        self._def_hp = 40
        self._rest_hp = 70

    def set_targets(self, names):
        self.targets = set(n.lower() for n in names)

    def start(self):
        if self.gathering:
            return
        self.gathering = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.gathering = False

    def _sleep(self, secs):
        end = time.monotonic() + secs
        while time.monotonic() < end:
            if self.stop_event.is_set() or not self.gathering:
                return False
            time.sleep(min(0.1, end - time.monotonic()))
        return True

    def _dist(self, x1, y1, x2, y2):
        return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def _pos_key(self, x, y):
        return (round(x), round(y))

    def _is_empty(self, x, y):
        k = self._pos_key(x, y)
        if k in self._empty_cache:
            if time.time() - self._empty_cache[k] < EMPTY_COOLDOWN:
                return True
            del self._empty_cache[k]
        return False

    def _mark_empty(self, x, y):
        self._empty_cache[self._pos_key(x, y)] = time.time()

    def _find_node(self):
        try:
            entities = self.conn.scan_nearby()
        except Exception:
            entities = []
        if not entities:
            return None

        px, py = self.conn.get_x(), self.conn.get_y()
        best, best_dist = None, float("inf")

        for e in entities:
            name = e.get("name", "")
            if not name:
                continue
            if name.lower() not in self.targets:
                continue
            hid = e.get("hidden")
            if hid == "1" or hid is True:
                continue
            nx = float(e.get("x", 0))
            ny = float(e.get("y", 0))
            d = self._dist(px, py, nx, ny)
            if d > MAX_NODE_DIST:
                continue
            if self._is_empty(nx, ny):
                continue
            if d < best_dist:
                best_dist = d
                best = e

        return best

    def _try_use(self, node):
        name = node.get("name", "")
        resp = self.conn._send(f"USE_ENTITY_{name}")
        if resp and "OK_USED" in resp:
            return True
        return False

    def _get_gather_time(self, node_name):
        """Get the fixed gather duration for a node based on its category."""
        cat_key = _ITEM_TO_CATEGORY.get(node_name.lower())
        if cat_key:
            return CATEGORIES[cat_key].get("gather_time", DEFAULT_GATHER_TIME)
        return DEFAULT_GATHER_TIME

    def _wait_arrive(self):
        """Wait until the player stops moving — that means they arrived and started gathering."""
        time.sleep(0.4)
        if not self.conn.is_moving():
            return True

        deadline = time.time() + WALK_TIMEOUT
        while time.time() < deadline:
            if self.stop_event.is_set() or not self.gathering:
                return False
            if not self.conn.is_moving():
                return True
            time.sleep(0.25)

        self.conn.stop_moving()
        return False

    def _wait_gather(self, node):
        """Wait a fixed duration based on node category after player stops moving."""
        nx = float(node.get("x", 0))
        ny = float(node.get("y", 0))
        name = node.get("name", "")

        if self.conn.is_moving():
            poll_end = time.time() + STOP_DETECT
            while time.time() < poll_end:
                if self.stop_event.is_set() or not self.gathering:
                    return "gathered"
                if not self.conn.is_moving():
                    break
                time.sleep(0.15)
            else:
                cx, cy = self.conn.get_x(), self.conn.get_y()
                if self._dist(cx, cy, nx, ny) > 3.0:
                    self._mark_empty(nx, ny)
                    return "empty"

        gather_time = self._get_gather_time(name)
        cat_key = _ITEM_TO_CATEGORY.get(name.lower(), "?")
        self.log(f"    Gathering {name} ({cat_key}) — waiting {gather_time:.0f}s")

        if not self._sleep(gather_time):
            return "gathered"

        return "gathered"

    def _wander(self):
        px, py = self.conn.get_x(), self.conn.get_y()
        angle = (time.time() * 37) % 360
        wx = px + WANDER_STEP * math.cos(math.radians(angle))
        wy = py + WANDER_STEP * math.sin(math.radians(angle))
        self.log(f"  🚶 Wandering ({wx:.0f}, {wy:.0f})...")
        self.conn.move_to(wx, wy)
        self._sleep(3.0)
        self.conn.stop_moving()

    def _load_combat_profile(self):
        try:
            self._profile = self.conn.load_profile()
            if self._profile:
                self._combat_tick = getattr(self._profile, "TICK_RATE", 0.3)
                self._def_trigger = getattr(self._profile, "DEFENSIVE_TRIGGER_HP", 20)
                self._def_hp = getattr(self._profile, "DEFENSIVE_HP", 40)
                self._rest_hp = getattr(self._profile, "REST_HP", 70)
                cls = self.conn.detect_class()
                self.log(f"  ⚔ Combat profile: {cls}")
        except Exception:
            self._profile = None

    def _snapshot_loot_baseline(self):
        try:
            self._loot_baseline = self.conn.get_loot_window_count()
        except Exception:
            self._loot_baseline = 0

    def _try_loot(self):
        if not self.loot_enabled:
            return
        try:
            windows = self.conn.get_loot_window_count()
            if windows > self._loot_baseline:
                n, resp = self.conn.loot_all()
                if n > 0:
                    self.stats["looted"] += n
                    self.log(f"  💰 Looted {n} window(s)")
            self._loot_baseline = self.conn.get_loot_window_count()
        except Exception:
            pass

    def _handle_combat(self):
        if not self.combat_enabled:
            return
        if not self.conn.in_combat():
            return

        self.conn.stop_moving()
        self.log("  ⚔ COMBAT — pausing gather")

        if self._profile is None:
            self._load_combat_profile()

        self.conn.do_buff()
        was_fighting = False

        while self.conn.in_combat() and self.gathering and not self.stop_event.is_set():
            was_fighting = True
            hp = self.conn.get_hp()

            if hp < self._def_trigger:
                self.conn.do_defend()
            elif hp < self._def_hp:
                self.conn.do_defend()

            if self._profile:
                self.conn.do_rotation()
            else:
                for s in self.conn.get_class_spells():
                    if self.conn.try_cast(s):
                        break

            time.sleep(self._combat_tick)

        if was_fighting:
            self.stats["kills"] += 1
            hp = self.conn.get_hp()
            self.log(f"  ✓ Kill #{self.stats['kills']} (HP:{hp:.0f}%)")

            self._try_loot()

            if hp < self._rest_hp:
                self.log("  💊 Resting...")
                self.conn.do_recover(hp_target=90, mp_target=80, timeout=30)
                self.log("  ✓ Ready")

            self._sleep(0.3)

    def _run(self):
        self.log("▶ Gather started")
        if self.combat_enabled:
            self._load_combat_profile()
        misses = 0

        while self.gathering and not self.stop_event.is_set():
            self.stats["cycle"] += 1

            self._snapshot_loot_baseline()
            self._handle_combat()
            if not self.gathering:
                break

            node = self._find_node()

            if node:
                misses = 0
                name = node.get("name", "?")
                nx = float(node.get("x", 0))
                ny = float(node.get("y", 0))
                px, py = self.conn.get_x(), self.conn.get_y()
                d = self._dist(px, py, nx, ny)

                self.log(f"  → {name} ({d:.0f}m)")
                self._snapshot_loot_baseline()
                ok = self._try_use(node)

                if ok:
                    self.stats["attempts"] += 1
                    arrived = self._wait_arrive()
                    if not self.gathering:
                        break

                    self._handle_combat()
                    if not self.gathering:
                        break

                    if arrived:
                        result = self._wait_gather(node)
                        if result == "gathered" or result == "timeout":
                            self.stats["gathered"] += 1
                            self._mark_empty(nx, ny)
                            self._try_loot()
                            self.log(f"  ★ Gathered {name}  "
                                     f"({self.stats['gathered']}/{self.stats['attempts']})")
                            self._sleep(0.3)
                            continue
                        elif result == "empty":
                            self.stats["empty"] += 1
                            self.log(f"  ○ Empty ({self.stats['empty']})")
                            continue
                    else:
                        self.log(f"  ! Couldn't reach {name}")
                else:
                    self.log(f"  ! USE_ENTITY failed for {name}")

                self._sleep(0.3)
            else:
                misses += 1
                if misses >= IDLE_WANDER and misses % 5 == 0:
                    self._wander()
                elif misses % 15 == 0:
                    self.log(f"  ~ No targets nearby (miss: {misses})")

            if not self._sleep(SCAN_INTERVAL):
                break

        self.gathering = False
        s = self.stats
        self.log(f"■ Stopped — Gathered: {s['gathered']}  Kills: {s['kills']}  "
                 f"Looted: {s['looted']}  Empty: {s['empty']}")


# ═══════════════════════════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════════════════════════

class GatherUI:
    def __init__(self, conn, stop_event, script_print):
        self.conn = conn
        self.stop_event = stop_event
        self.script_print = script_print
        self.engine = GatherEngine(conn, stop_event, self._log)
        self._item_vars = {}

        self.win = tk.Toplevel()
        self.win.title("Auto-Gather")
        self.win.configure(bg=BG)
        self.win.geometry("340x620")
        self.win.resizable(False, True)
        self.win.wm_attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        x = (self.win.winfo_screenwidth() - 340) // 2
        y = (self.win.winfo_screenheight() - 620) // 2
        self.win.geometry(f"+{x}+{y}")

        hdr = tk.Frame(self.win, bg=BG_CARD, height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⛏", font=("Segoe UI Emoji", 14), bg=BG_CARD, fg=ACCENT
                 ).pack(side=tk.LEFT, padx=(10, 6))
        tk.Label(hdr, text="Auto-Gather", font=(FONT_B, 13), bg=BG_CARD, fg=TEXT
                 ).pack(side=tk.LEFT)
        tk.Frame(self.win, bg=ACCENT, height=2).pack(fill=tk.X)

        btn_frame = tk.Frame(self.win, bg=BG, pady=8, padx=10)
        btn_frame.pack(fill=tk.X)

        self.start_btn = tk.Button(
            btn_frame, text="▶  Start", font=(FONT_B, 11),
            bg="#1a3a2a", fg=GREEN, relief=tk.FLAT,
            activebackground=GREEN, activeforeground=BG,
            padx=16, pady=6, cursor="hand2", command=self._on_start,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = tk.Button(
            btn_frame, text="■  Stop", font=(FONT_B, 11),
            bg="#3a1a1a", fg=RED, relief=tk.FLAT,
            activebackground=RED, activeforeground=BG,
            padx=16, pady=6, cursor="hand2", command=self._on_stop,
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT)

        self.status = tk.Label(btn_frame, text="Idle", font=(FONT_M, 9),
                               bg=BG, fg=TEXT_DIM)
        self.status.pack(side=tk.RIGHT)

        self.stats_label = tk.Label(self.win, text="", font=(FONT_M, 8),
                                    bg=BG, fg=TEXT_DIM, anchor=tk.W)
        self.stats_label.pack(fill=tk.X, padx=12, pady=(0, 4))

        opt_frame = tk.Frame(self.win, bg=BG, padx=10)
        opt_frame.pack(fill=tk.X, pady=(0, 4))
        self._combat_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opt_frame, text="⚔ Fight if attacked (auto-rotation)",
            variable=self._combat_var, font=(FONT_B, 9),
            bg=BG, fg=ORANGE, selectcolor=BG_CARD,
            activebackground=BG, activeforeground=ORANGE,
            highlightthickness=0, bd=0,
            command=self._toggle_combat,
        ).pack(anchor=tk.W)
        self._loot_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            opt_frame, text="💰 Auto-loot (loot all when window opens)",
            variable=self._loot_var, font=(FONT_B, 9),
            bg=BG, fg="#FFD700", selectcolor=BG_CARD,
            activebackground=BG, activeforeground="#FFD700",
            highlightthickness=0, bd=0,
            command=self._toggle_loot,
        ).pack(anchor=tk.W)

        tk.Frame(self.win, bg=BORDER, height=1).pack(fill=tk.X, padx=10)

        container = tk.Frame(self.win, bg=BG)
        container.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        cvs = tk.Canvas(container, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=cvs.yview,
                          bg=BG_CARD, troughcolor=BG, width=8)
        inner = tk.Frame(cvs, bg=BG)
        inner.bind("<Configure>", lambda e: cvs.configure(scrollregion=cvs.bbox("all")))
        cvs.create_window((0, 0), window=inner, anchor="nw")
        cvs.configure(yscrollcommand=sb.set)
        cvs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        cvs.bind_all("<MouseWheel>",
                      lambda e: cvs.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        for cat_key, cat in CATEGORIES.items():
            hdr_f = tk.Frame(inner, bg=BG_CARD, padx=6, pady=4)
            hdr_f.pack(fill=tk.X, pady=(8, 2), padx=4)

            tk.Label(hdr_f, text=cat["label"], font=(FONT_B, 10),
                     bg=BG_CARD, fg=cat["color"]).pack(side=tk.LEFT)

            all_b = tk.Label(hdr_f, text="All", font=(FONT, 8), bg=BG_CARD,
                             fg=GREEN, cursor="hand2", padx=4)
            all_b.pack(side=tk.RIGHT, padx=2)
            all_b.bind("<Button-1>", lambda e, k=cat_key: self._set_cat(k, True))

            none_b = tk.Label(hdr_f, text="None", font=(FONT, 8), bg=BG_CARD,
                              fg=RED, cursor="hand2", padx=4)
            none_b.pack(side=tk.RIGHT, padx=2)
            none_b.bind("<Button-1>", lambda e, k=cat_key: self._set_cat(k, False))

            for item_name in cat["items"]:
                var = tk.BooleanVar(value=False)
                self._item_vars[item_name] = var
                row = tk.Frame(inner, bg=BG)
                row.pack(fill=tk.X, padx=(16, 4))
                tk.Checkbutton(
                    row, text=item_name, variable=var,
                    font=(FONT, 9), bg=BG, fg=TEXT,
                    selectcolor=BG_CARD, activebackground=BG,
                    activeforeground=TEXT, highlightthickness=0, bd=0,
                ).pack(anchor=tk.W)

        log_frame = tk.Frame(self.win, bg=BG_CARD)
        log_frame.pack(fill=tk.X, padx=6, pady=(4, 6))
        tk.Label(log_frame, text="Log", font=(FONT_B, 8), bg=BG_CARD,
                 fg=TEXT_DIM).pack(anchor=tk.W, padx=6, pady=(4, 0))
        self.log_box = tk.Text(log_frame, font=(FONT_M, 7), bg="#060a10", fg=TEXT_DIM,
                               height=5, relief=tk.FLAT, highlightthickness=0,
                               padx=6, pady=4, state=tk.DISABLED, wrap=tk.WORD)
        self.log_box.pack(fill=tk.X, padx=4, pady=(0, 4))

        self._update_stats()
        self._poll_stop()

    def _set_cat(self, cat_key, state):
        for name in CATEGORIES[cat_key]["items"]:
            if name in self._item_vars:
                self._item_vars[name].set(state)

    def _get_selected(self):
        return [n for n, v in self._item_vars.items() if v.get()]

    def _log(self, msg):
        self.script_print(msg)
        try:
            self.log_box.configure(state=tk.NORMAL)
            ts = time.strftime("%H:%M:%S")
            self.log_box.insert(tk.END, f"[{ts}] {msg}\n")
            lines = int(self.log_box.index("end-1c").split(".")[0])
            if lines > 200:
                self.log_box.delete("1.0", f"{lines - 200}.0")
            self.log_box.see(tk.END)
            self.log_box.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _toggle_combat(self):
        self.engine.combat_enabled = self._combat_var.get()

    def _toggle_loot(self):
        self.engine.loot_enabled = self._loot_var.get()

    def _on_start(self):
        sel = self._get_selected()
        if not sel:
            self._log("⚠ No nodes selected!")
            return
        self.engine.set_targets(sel)
        self.engine.combat_enabled = self._combat_var.get()
        self.engine.loot_enabled = self._loot_var.get()
        self.engine.stats = {"gathered": 0, "attempts": 0, "empty": 0, "cycle": 0, "kills": 0, "looted": 0}
        self.engine.start()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status.configure(text="Running", fg=GREEN)
        self._log(f"Targets: {', '.join(sel)}")
        self._log(f"Combat: {'ON' if self.engine.combat_enabled else 'OFF'}  "
                  f"Loot: {'ON' if self.engine.loot_enabled else 'OFF'}")

    def _on_stop(self):
        self.engine.stop()
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status.configure(text="Stopped", fg=ORANGE)

    def _update_stats(self):
        if not self.win.winfo_exists():
            return
        s = self.engine.stats
        self.stats_label.configure(
            text=f"Gathered: {s['gathered']}   Kills: {s['kills']}   "
                 f"Looted: {s['looted']}   Empty: {s['empty']}"
        )
        if self.engine.gathering:
            if self.conn.in_combat():
                self.status.configure(text="⚔ Fighting", fg=RED)
            else:
                self.status.configure(text="Running", fg=GREEN)
        self.win.after(1000, self._update_stats)

    def _poll_stop(self):
        if not self.win.winfo_exists():
            return
        if self.stop_event.is_set():
            self.engine.stop()
            return
        if not self.engine.gathering and self.stop_btn["state"] == tk.NORMAL:
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)
            self.status.configure(text="Idle", fg=TEXT_DIM)
        self.win.after(500, self._poll_stop)

    def _on_close(self):
        self.engine.stop()
        try:
            self.win.destroy()
        except tk.TclError:
            pass


# ═══════════════════════════════════════════════════════════════
#  Entry
# ═══════════════════════════════════════════════════════════════

print("  Opening Auto-Gather UI...")
ui = GatherUI(conn, stop_event, print)
