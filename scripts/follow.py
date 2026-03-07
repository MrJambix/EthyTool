"""
Follow Bot — Pick a party member and follow them automatically.
"""

import sys
import os
import time
import math
import threading
import tkinter as tk
from pathlib import Path

# Add scripts dir to path
scripts_dir = str(Path(__file__).parent)
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

# ══════════════════════════════════════════════════════════════
#  Theme (matches dashboard)
# ══════════════════════════════════════════════════════════════

BG          = "#0a0e14"
BG_CARD     = "#12161e"
BG_CARD_ALT = "#161c26"
BG_INPUT    = "#1a2030"
TEXT        = "#e6edf3"
TEXT_DIM    = "#6e7681"
TEXT_MID    = "#8b949e"
ACCENT      = "#58a6ff"
ACCENT_GLOW = "#1f6feb"
ACCENT_DIM  = "#1a3a5c"
GREEN       = "#3fb950"
GREEN_DIM   = "#1a3a2a"
RED         = "#f85149"
RED_DIM     = "#3a1a1a"
ORANGE      = "#d29922"
YELLOW      = "#e3b341"
PURPLE      = "#bc8cff"
CYAN        = "#56d4dd"
BORDER      = "#21262d"

FONT        = "Segoe UI"
FONT_BOLD   = "Segoe UI Semibold"
FONT_MONO   = "Cascadia Code"


# ══════════════════════════════════════════════════════════════
#  Follow Engine
# ══════════════════════════════════════════════════════════════

class FollowEngine:
    def __init__(self, connection):
        self.conn = connection
        self.target_name = None
        self.following = False
        self.stop_event = threading.Event()

        # Settings
        self.follow_distance = 3.0      # Stay this close
        self.max_distance = 50.0        # Stop if too far (probably zoned)
        self.tick_rate = 0.3
        self.fight_with_leader = True   # Join combat when leader fights
        self.auto_loot = True
        self.auto_rest = True
        self.rest_hp = 70
        self.rest_mp = 50

        # State
        self.last_leader_pos = None
        self.stuck_count = 0
        self.last_my_pos = None

    def get_party_members(self):
        """Get nearby entities that look like party members (players)."""
        nearby = self.conn.get_nearby()
        if not nearby:
            return []

        my_name = self._get_my_name()
        members = []

        for ent in nearby:
            name = ent.get("name", "")
            if not name:
                continue
            # Skip self
            if name == my_name:
                continue
            # Skip static entities (NPCs, objects)
            if ent.get("static"):
                continue
            # Skip entities without HP (decorations)
            if ent.get("max_hp", 0) <= 0 and not ent.get("hp"):
                continue
            # Players typically have HP and aren't static
            members.append({
                "name": name,
                "hp": ent.get("hp", 0),
                "x": float(ent.get("x", 0)),
                "y": float(ent.get("y", 0)),
                "uid": ent.get("uid", 0),
            })

        return members

    def _get_my_name(self):
        data = self.conn.get_all()
        return data.get("name", "")

    def find_leader(self):
        """Find the follow target in nearby entities."""
        if not self.target_name:
            return None
        nearby = self.conn.get_nearby()
        if not nearby:
            return None
        name_lower = self.target_name.lower()
        for ent in nearby:
            if name_lower in ent.get("name", "").lower():
                return ent
        return None

    def distance_to_leader(self):
        leader = self.find_leader()
        if not leader:
            return -1
        px, py, _ = self.conn.get_position()
        lx = float(leader.get("x", 0))
        ly = float(leader.get("y", 0))
        return math.sqrt((lx - px) ** 2 + (ly - py) ** 2)

    def start(self, name, log_fn=None):
        self.target_name = name
        self.following = True
        self.stop_event.clear()
        self.log = log_fn or print
        self.log(f"Following: {name}")

    def stop(self):
        self.following = False
        self.stop_event.set()
        if self.log:
            self.log("Follow stopped")

    def tick(self):
        """One tick of the follow loop. Returns status string."""
        if not self.following or not self.target_name:
            return "IDLE"

        leader = self.find_leader()
        if not leader:
            return "LOST"

        px, py, pz = self.conn.get_position()
        lx = float(leader.get("x", 0))
        ly = float(leader.get("y", 0))
        dist = math.sqrt((lx - px) ** 2 + (ly - py) ** 2)

        # Too far — leader probably zoned
        if dist > self.max_distance:
            return f"TOO_FAR ({dist:.0f})"

        # Close enough — stand still
        if dist <= self.follow_distance:
            self.stuck_count = 0

            # Fight with leader if they're in combat
            if self.fight_with_leader and self.conn.in_combat():
                return "FIGHTING"

            # Auto rest when idle and close
            if self.auto_rest and not self.conn.in_combat():
                if self.conn.get_hp() < self.rest_hp or self.conn.get_mp() < self.rest_mp:
                    return "RESTING"

            return f"FOLLOWING ({dist:.1f})"

        # Need to move — leader moved away
        # Stuck detection
        if self.last_my_pos:
            moved = math.sqrt((px - self.last_my_pos[0]) ** 2 +
                              (py - self.last_my_pos[1]) ** 2)
            if moved < 0.5:
                self.stuck_count += 1
            else:
                self.stuck_count = 0

        self.last_my_pos = (px, py)
        self.last_leader_pos = (lx, ly)

        if self.stuck_count > 10:
            return f"STUCK ({dist:.1f})"

        return f"MOVING ({dist:.1f})"


# ══════════════════════════════════════════════════════════════
#  Follow Bot UI
# ══════════════════════════════���═══════════════════════════════

class FollowBotUI:
    def __init__(self, connection, stop_event=None, log_fn=None):
        self.conn = connection
        self.external_stop = stop_event
        self.external_log = log_fn or print
        self.engine = FollowEngine(connection)
        self.running = True

        # Build window
        self.root = tk.Toplevel()
        self.root.title("EthyTool — Follow Bot")
        self.root.geometry("380x620")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.attributes("-topmost", True)

        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 380) // 2
        y = (self.root.winfo_screenheight() - 620) // 2
        self.root.geometry(f"+{x}+{y}")

        self._build_ui()
        self._refresh_party()
        self._update_loop()

    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=BG_CARD, height=44)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="  Follow Bot", font=(FONT_BOLD, 13),
                 bg=BG_CARD, fg=ACCENT).pack(side=tk.LEFT, padx=10)

        self.status_dot = tk.Label(header, text="--", font=(FONT_MONO, 9),
                                    bg=BG_CARD, fg=TEXT_DIM)
        self.status_dot.pack(side=tk.RIGHT, padx=12)

        tk.Frame(self.root, bg=ACCENT_GLOW, height=2).pack(fill=tk.X)

        # ── Party List ──
        party_frame = tk.Frame(self.root, bg=BG, padx=12, pady=8)
        party_frame.pack(fill=tk.X)

        party_header = tk.Frame(party_frame, bg=BG)
        party_header.pack(fill=tk.X, pady=(0, 6))
        tk.Label(party_header, text="PARTY MEMBERS", font=(FONT_BOLD, 9),
                 bg=BG, fg=TEXT_MID).pack(side=tk.LEFT)

        tk.Button(party_header, text="Refresh", font=(FONT, 8),
                  bg=BG_CARD, fg=TEXT_DIM, relief=tk.FLAT,
                  activebackground=BG_CARD_ALT, activeforeground=TEXT,
                  padx=8, pady=2, cursor="hand2",
                  command=self._refresh_party).pack(side=tk.RIGHT)

        self.party_count = tk.Label(party_header, text="0", font=(FONT_MONO, 8),
                                     bg=BG, fg=TEXT_DIM)
        self.party_count.pack(side=tk.RIGHT, padx=(0, 8))

        # Party member list (scrollable)
        list_outer = tk.Frame(party_frame, bg=BG_CARD, highlightbackground=BORDER,
                              highlightthickness=1)
        list_outer.pack(fill=tk.X)

        self.party_list = tk.Frame(list_outer, bg=BG_CARD, padx=4, pady=4)
        self.party_list.pack(fill=tk.X)

        self.no_party_label = tk.Label(self.party_list,
            text="No party members found\nMake sure you're near other players",
            font=(FONT, 9), bg=BG_CARD, fg=TEXT_DIM, justify=tk.CENTER, pady=16)
        self.no_party_label.pack()

        # ── Currently Following ──
        follow_frame = tk.Frame(self.root, bg=BG, padx=12, pady=4)
        follow_frame.pack(fill=tk.X)

        follow_card = tk.Frame(follow_frame, bg=BG_CARD, highlightbackground=BORDER,
                               highlightthickness=1, padx=12, pady=10)
        follow_card.pack(fill=tk.X)

        tk.Label(follow_card, text="FOLLOWING", font=(FONT_BOLD, 9),
                 bg=BG_CARD, fg=TEXT_MID).pack(anchor=tk.W)

        self.follow_name = tk.Label(follow_card, text="Nobody", font=(FONT_BOLD, 16),
                                     bg=BG_CARD, fg=TEXT_DIM)
        self.follow_name.pack(anchor=tk.W, pady=(4, 0))

        # Status row
        status_row = tk.Frame(follow_card, bg=BG_CARD)
        status_row.pack(fill=tk.X, pady=(6, 0))

        self.follow_status = tk.Label(status_row, text="Idle", font=(FONT, 10),
                                       bg=BG_CARD, fg=TEXT_DIM)
        self.follow_status.pack(side=tk.LEFT)

        self.follow_dist = tk.Label(status_row, text="", font=(FONT_MONO, 9),
                                     bg=BG_CARD, fg=TEXT_DIM)
        self.follow_dist.pack(side=tk.RIGHT)

        # Leader HP bar
        hp_row = tk.Frame(follow_card, bg=BG_CARD)
        hp_row.pack(fill=tk.X, pady=(6, 0))
        tk.Label(hp_row, text="HP", font=(FONT_BOLD, 8), bg=BG_CARD,
                 fg=RED, width=3).pack(side=tk.LEFT)
        self.leader_hp_bar = tk.Canvas(hp_row, height=10, bg=BG,
                                        highlightthickness=0)
        self.leader_hp_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 4))
        self.leader_hp_text = tk.Label(hp_row, text="--", font=(FONT_MONO, 8),
                                        bg=BG_CARD, fg=TEXT_DIM, width=5)
        self.leader_hp_text.pack(side=tk.RIGHT)

        # ── Settings ──
        settings_frame = tk.Frame(self.root, bg=BG, padx=12, pady=4)
        settings_frame.pack(fill=tk.X)

        settings_card = tk.Frame(settings_frame, bg=BG_CARD, highlightbackground=BORDER,
                                  highlightthickness=1, padx=12, pady=10)
        settings_card.pack(fill=tk.X)

        tk.Label(settings_card, text="SETTINGS", font=(FONT_BOLD, 9),
                 bg=BG_CARD, fg=TEXT_MID).pack(anchor=tk.W, pady=(0, 6))

        # Follow distance
        dist_row = tk.Frame(settings_card, bg=BG_CARD)
        dist_row.pack(fill=tk.X, pady=2)
        tk.Label(dist_row, text="Follow Distance", font=(FONT, 9),
                 bg=BG_CARD, fg=TEXT).pack(side=tk.LEFT)
        self.dist_var = tk.DoubleVar(value=3.0)
        self.dist_slider = tk.Scale(dist_row, from_=1, to=15, resolution=0.5,
                                     orient=tk.HORIZONTAL, variable=self.dist_var,
                                     bg=BG_CARD, fg=TEXT, troughcolor=BG_INPUT,
                                     highlightthickness=0, sliderrelief=tk.FLAT,
                                     font=(FONT_MONO, 8), length=140,
                                     command=self._update_distance)
        self.dist_slider.pack(side=tk.RIGHT)

        # Checkboxes
        self.fight_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_card, text="Fight with leader", font=(FONT, 9),
                        bg=BG_CARD, fg=TEXT, selectcolor=BG_CARD_ALT,
                        activebackground=BG_CARD, activeforeground=TEXT,
                        variable=self.fight_var,
                        command=self._update_settings).pack(anchor=tk.W, pady=1)

        self.loot_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_card, text="Auto-loot corpses", font=(FONT, 9),
                        bg=BG_CARD, fg=TEXT, selectcolor=BG_CARD_ALT,
                        activebackground=BG_CARD, activeforeground=TEXT,
                        variable=self.loot_var,
                        command=self._update_settings).pack(anchor=tk.W, pady=1)

        self.rest_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_card, text="Auto-rest when idle", font=(FONT, 9),
                        bg=BG_CARD, fg=TEXT, selectcolor=BG_CARD_ALT,
                        activebackground=BG_CARD, activeforeground=TEXT,
                        variable=self.rest_var,
                        command=self._update_settings).pack(anchor=tk.W, pady=1)

        # ── Control Buttons ──
        btn_frame = tk.Frame(self.root, bg=BG, padx=12, pady=8)
        btn_frame.pack(fill=tk.X)

        self.stop_btn = tk.Button(btn_frame, text="Stop Following", font=(FONT_BOLD, 11),
                                   bg=RED_DIM, fg=RED, relief=tk.FLAT,
                                   activebackground=RED, activeforeground=TEXT,
                                   padx=16, pady=8, cursor="hand2",
                                   command=self._stop_follow, state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X)

        # ── Log ──
        log_frame = tk.Frame(self.root, bg=BG, padx=12, pady=(0, 8))
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="LOG", font=(FONT_BOLD, 8),
                 bg=BG, fg=TEXT_DIM).pack(anchor=tk.W, pady=(0, 2))

        self.log_box = tk.Text(log_frame, font=(FONT_MONO, 7), bg=BG_CARD, fg=TEXT_DIM,
                                relief=tk.FLAT, highlightthickness=1,
                                highlightbackground=BORDER, padx=6, pady=4,
                                height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.log_box.pack(fill=tk.BOTH, expand=True)

        self.log_box.tag_configure("ok", foreground=GREEN)
        self.log_box.tag_configure("warn", foreground=ORANGE)
        self.log_box.tag_configure("err", foreground=RED)
        self.log_box.tag_configure("info", foreground=TEXT_DIM)

    # ── Party Management ──

    def _refresh_party(self):
        for w in self.party_list.winfo_children():
            w.destroy()

        members = self.engine.get_party_members()
        self.party_count.configure(text=str(len(members)))

        if not members:
            self.no_party_label = tk.Label(self.party_list,
                text="No party members found\nMake sure you're near other players",
                font=(FONT, 9), bg=BG_CARD, fg=TEXT_DIM, justify=tk.CENTER, pady=16)
            self.no_party_label.pack()
            return

        for member in members:
            name = member["name"]
            hp_val = member.get("hp", 0)

            row = tk.Frame(self.party_list, bg=BG_CARD_ALT, padx=8, pady=6,
                          highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill=tk.X, pady=(0, 3))

            # Left: name + hp
            left = tk.Frame(row, bg=BG_CARD_ALT)
            left.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(left, text=name, font=(FONT_BOLD, 10),
                     bg=BG_CARD_ALT, fg=TEXT).pack(anchor=tk.W)

            hp_color = GREEN if hp_val > 50 else ORANGE if hp_val > 25 else RED
            tk.Label(left, text=f"HP: {hp_val:.0f}%", font=(FONT_MONO, 8),
                     bg=BG_CARD_ALT, fg=hp_color).pack(anchor=tk.W)

            # Right: follow button
            follow_btn = tk.Button(row, text="Follow", font=(FONT_BOLD, 9),
                                    bg=ACCENT_DIM, fg=ACCENT, relief=tk.FLAT,
                                    activebackground=ACCENT_GLOW, activeforeground=TEXT,
                                    padx=12, pady=4, cursor="hand2",
                                    command=lambda n=name: self._start_follow(n))
            follow_btn.pack(side=tk.RIGHT, padx=(8, 0))

            # Hover
            def on_enter(e, r=row):
                r.configure(highlightbackground=ACCENT_DIM)
            def on_leave(e, r=row):
                is_following = self.engine.target_name and \
                    self.engine.target_name.lower() in name.lower()
                r.configure(highlightbackground=GREEN if is_following else BORDER)
            row.bind("<Enter>", on_enter)
            row.bind("<Leave>", on_leave)

    def _start_follow(self, name):
        self._log(f"Following: {name}", "ok")
        self.external_log(f"[follow] Following: {name}")
        self.engine.start(name, log_fn=lambda m: self._log(m, "info"))
        self.engine.follow_distance = self.dist_var.get()
        self.engine.fight_with_leader = self.fight_var.get()
        self.engine.auto_loot = self.loot_var.get()
        self.engine.auto_rest = self.rest_var.get()

        self.follow_name.configure(text=name, fg=GREEN)
        self.stop_btn.configure(state=tk.NORMAL)

        # Highlight in party list
        self._refresh_party()

    def _stop_follow(self):
        self.engine.stop()
        self.follow_name.configure(text="Nobody", fg=TEXT_DIM)
        self.follow_status.configure(text="Idle", fg=TEXT_DIM)
        self.follow_dist.configure(text="")
        self.stop_btn.configure(state=tk.DISABLED)
        self._log("Stopped following", "warn")
        self.external_log("[follow] Stopped")

    def _update_distance(self, val):
        self.engine.follow_distance = float(val)

    def _update_settings(self):
        self.engine.fight_with_leader = self.fight_var.get()
        self.engine.auto_loot = self.loot_var.get()
        self.engine.auto_rest = self.rest_var.get()

    # ── Update Loop ──

    def _update_loop(self):
        if not self.running:
            return

        # Check external stop
        if self.external_stop and self.external_stop.is_set():
            self._on_close()
            return

        if self.engine.following:
            status = self.engine.tick()
            self._update_status(status)

        self.root.after(300, self._update_loop)

    def _update_status(self, status):
        # Parse status
        if status.startswith("FOLLOWING"):
            self.follow_status.configure(text="Following", fg=GREEN)
            self.status_dot.configure(text="FOLLOWING", fg=GREEN)
        elif status.startswith("MOVING"):
            self.follow_status.configure(text="Moving to leader", fg=ACCENT)
            self.status_dot.configure(text="MOVING", fg=ACCENT)
        elif status.startswith("FIGHTING"):
            self.follow_status.configure(text="In Combat", fg=RED)
            self.status_dot.configure(text="COMBAT", fg=RED)
        elif status.startswith("RESTING"):
            self.follow_status.configure(text="Resting", fg=CYAN)
            self.status_dot.configure(text="REST", fg=CYAN)
        elif status.startswith("LOST"):
            self.follow_status.configure(text="Leader not found!", fg=ORANGE)
            self.status_dot.configure(text="LOST", fg=ORANGE)
        elif status.startswith("TOO_FAR"):
            self.follow_status.configure(text="Too far away!", fg=RED)
            self.status_dot.configure(text="TOO FAR", fg=RED)
        elif status.startswith("STUCK"):
            self.follow_status.configure(text="Stuck!", fg=ORANGE)
            self.status_dot.configure(text="STUCK", fg=ORANGE)
        else:
            self.follow_status.configure(text=status, fg=TEXT_DIM)
            self.status_dot.configure(text="--", fg=TEXT_DIM)

        # Distance
        dist = self.engine.distance_to_leader()
        if dist >= 0:
            self.follow_dist.configure(text=f"{dist:.1f}m")
        else:
            self.follow_dist.configure(text="--")

        # Leader HP bar
        leader = self.engine.find_leader()
        if leader:
            leader_hp = float(leader.get("hp", 0))
            self._draw_hp_bar(leader_hp)
            self.leader_hp_text.configure(text=f"{leader_hp:.0f}%")
        else:
            self._draw_hp_bar(0)
            self.leader_hp_text.configure(text="--")

    def _draw_hp_bar(self, pct):
        c = self.leader_hp_bar
        c.delete("all")
        w = c.winfo_width() or 200
        h = 10
        c.create_rectangle(0, 0, w, h, fill=BG, outline="")
        bw = int(w * pct / 100)
        if bw > 0:
            color = GREEN if pct > 50 else ORANGE if pct > 25 else RED
            c.create_rectangle(0, 0, bw, h, fill=color, outline="")
        c.create_rectangle(0, 0, w - 1, h - 1, outline=BORDER, width=1)

    # ── Log ──

    def _log(self, msg, tag="info"):
        def _do():
            self.log_box.configure(state=tk.NORMAL)
            ts = time.strftime("%H:%M:%S")
            self.log_box.insert(tk.END, f"[{ts}] {msg}\n", tag)

            lines = int(self.log_box.index('end-1c').split('.')[0])
            if lines > 200:
                self.log_box.delete("1.0", f"{lines - 200}.0")

            self.log_box.see(tk.END)
            self.log_box.configure(state=tk.DISABLED)

        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.root.after(0, _do)

    def _on_close(self):
        self.running = False
        self.engine.stop()
        try:
            self.root.destroy()
        except Exception:
            pass


# ══════��═══════════════════════════════════════════════════════
#  Entry — launched by dashboard script runner
# ══════════════════════════════════════════════════════════════

# The dashboard injects 'conn' and 'stop_event' before running
bot = FollowBotUI(
    connection=conn,
    stop_event=stop_event,
    log_fn=print,
)

# Keep alive until closed
while bot.running:
    if stop_event and stop_event.is_set():
        bot._on_close()
        break
    time.sleep(0.5)