"""
Mob Detector — In-game overlay showing nearby hostile mobs. Click to move to mob.

Run from EthyTool dashboard. Shows a semi-transparent overlay with nearby
enemy/hostile targets only; click one to move your character to it.

Scans: NEARBY_ADDRESSES, SCENE_ADDRESSES (HostileEntity, MonsterEntity), SCAN_ENEMIES
All in single thread (root.after).
"""

import math
import tkinter as tk

# conn and stop_event injected by EthyTool dashboard
try:
    conn
    stop_event
except NameError:
    print("ERROR: Run from EthyTool dashboard (Load Script).")
    raise SystemExit(1)

# ═══════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════

DETECT_RANGE = 80.0
POLL_INTERVAL_MS = 500
OVERLAY_ALPHA = 0.92
OVERLAY_WIDTH = 280
OVERLAY_HEIGHT = 400

# Hostile/enemy entity classes only (excludes friendly NPCs)
HOSTILE_CLASSES = {"HostileEntity", "MonsterEntity"}
PLAYER_CLASSES = {"LocalPlayerEntity", "PlayerEntity"}

# Theme
BG = "#0a0e14"
BG_HEADER = "#12161e"
BG_ROW = "#0d1117"
BG_ROW_HOVER = "#161b22"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
FONT = "Segoe UI"
FONT_MONO = "Cascadia Code"


def get_mobs():
    """Scan for hostile/enemy entities only. All conn calls in caller thread."""
    px, py, _ = conn.get_position()
    seen = set()
    result = []

    def add_mob(name, x, y, dist, uid=None):
        key = (uid,) if uid else (name, round(x or 0, 1), round(y or 0, 1))
        if key in seen:
            return
        seen.add(key)
        if dist > DETECT_RANGE:
            return
        result.append({"name": name or "?", "dist": dist, "x": x, "y": y})

    # 1. NEARBY_ADDRESSES / SCENE_ADDRESSES — only HostileEntity, MonsterEntity
    for entities in [conn.get_nearby_addresses(), conn.get_scene_addresses()]:
        for e in entities or []:
            if e.get("hidden"):
                continue
            cls = e.get("class", "")
            if cls in PLAYER_CLASSES:
                continue
            if cls not in HOSTILE_CLASSES:
                continue
            name = e.get("name", "")
            if not name:
                continue
            try:
                x = float(e.get("x", 0))
                y = float(e.get("y", 0))
            except (ValueError, TypeError):
                continue
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            add_mob(name, x, y, dist, e.get("uid"))

    # 2. SCAN_ENEMIES — dedicated enemy scan (hostile targets only)
    for e in conn.scan_enemies() or []:
        name = e.get("name", "")
        if not name:
            continue
        try:
            dist = float(e.get("dist", 999))
        except (ValueError, TypeError):
            continue
        x = e.get("x")
        y = e.get("y")
        if x is not None and y is not None:
            try:
                x, y = float(x), float(y)
            except (ValueError, TypeError):
                x, y = None, None
        if x is not None and y is not None:
            add_mob(name, x, y, dist, e.get("uid"))
        elif dist < DETECT_RANGE and (name, "nopos") not in seen:
            seen.add((name, "nopos"))
            result.append({"name": name, "dist": dist, "x": None, "y": None})

    result.sort(key=lambda m: m["dist"])
    return result[:30]


class MobDetectorOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hostile Targets")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", OVERLAY_ALPHA)
        self.root.resizable(False, False)
        self.root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+50+50")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.mobs = []
        self.labels = []
        self.running = True
        self._build_ui()
        self._schedule_poll()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG_HEADER, height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🎯 Hostile Targets — Click to move", font=(FONT, 10, "bold"),
                 bg=BG_HEADER, fg=TEXT).pack(side=tk.LEFT, padx=10, pady=6)
        self.count_label = tk.Label(header, text="0 hostile", font=(FONT, 9), bg=BG_HEADER, fg=TEXT_DIM)
        self.count_label.pack(side=tk.RIGHT, padx=10, pady=6)

        canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg=BG)
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def _schedule_poll(self):
        """Poll for mobs in main thread via root.after (single-thread)."""
        if not self.running or not self.root.winfo_exists():
            return
        if stop_event.is_set():
            self.running = False
            self.root.destroy()
            return
        try:
            self.mobs = get_mobs()
            self._refresh_list()
        except Exception as e:
            try:
                conn.log(f"Mob detector error: {e}")
            except Exception:
                pass
        self.root.after(POLL_INTERVAL_MS, self._schedule_poll)

    def _check_stop(self):
        if stop_event.is_set():
            self.running = False
            self.root.destroy()
            return
        if self.root.winfo_exists():
            self.root.after(500, self._check_stop)

    def _refresh_list(self):
        if not self.root.winfo_exists():
            return
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.labels.clear()
        self.count_label.configure(text=f"{len(self.mobs)} hostile")
        for i, m in enumerate(self.mobs):
            row = tk.Frame(self.list_frame, bg=BG_ROW, cursor="hand2")
            row.pack(fill=tk.X, padx=2, pady=1)
            dist_str = f"{m['dist']:.1f}m" if m["dist"] < 999 else "?"
            name_short = (m["name"][:28] + "…") if len(m["name"]) > 28 else m["name"]
            lbl = tk.Label(row, text=f"  {name_short}  {dist_str}", font=(FONT_MONO, 9),
                          bg=BG_ROW, fg=TEXT, anchor="w", cursor="hand2")
            lbl.pack(fill=tk.X, padx=4, pady=4)
            lbl.bind("<Button-1>", lambda e, mob=m: self._on_click(mob))
            lbl.bind("<Enter>", lambda e, r=row: r.configure(bg=BG_ROW_HOVER))
            lbl.bind("<Leave>", lambda e, r=row: r.configure(bg=BG_ROW))
            row.bind("<Button-1>", lambda e, mob=m: self._on_click(mob))
            self.labels.append(lbl)

    def _on_click(self, mob):
        if mob["x"] is not None and mob["y"] is not None:
            conn.move_to(mob["x"], mob["y"])
            conn.log(f"Moving to {mob['name']} ({mob['dist']:.1f}m)")
        else:
            conn.log(f"Cannot move to {mob['name']} (no position)")

    def run(self):
        conn.log("Hostile target overlay started. Click an enemy to move.")
        self.root.after(500, self._check_stop)
        self.root.mainloop()


overlay = MobDetectorOverlay()
overlay.run()
