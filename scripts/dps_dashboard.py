"""
╔══════════════════════════════════════════════════════════════════════╗
║                   EthyTool DPS Dashboard v1.0                        ║
║                                                                      ║
║  Modes:                                                              ║
║    live      — Capture real combat data from the game pipe           ║
║    simulate  — Estimate DPS from build profiles (offline)            ║
║    compare   — Load saved sessions and overlay charts                ║
║    view      — Open a saved .json session file                       ║
║                                                                      ║
║  Usage:                                                              ║
║    python dps_dashboard.py live                                      ║
║    python dps_dashboard.py simulate berserker spellblade             ║
║    python dps_dashboard.py compare session1.json session2.json       ║
║    python dps_dashboard.py view session1.json                        ║
║                                                                      ║
║  Charts:                                                             ║
║    1. DPS Over Time (1s samples)                                     ║
║    2. Estimated Total Damage Over Time                               ║
║    3. Rolling Sustain DPS (5s moving average)                        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import json
import time
import math
import threading
import importlib.util
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from typing import Optional

# ══════════════════════════════════════════════════════════════
#  Data Models
# ══════════════════════════════════════════════════════════════

@dataclass
class DamageEvent:
    timestamp: float
    spell_name: str
    damage: float
    is_crit: bool = False
    target: str = ""

@dataclass
class CombatSession:
    name: str
    profile: str
    start_time: float = 0.0
    duration: float = 60.0
    events: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_event(self, spell_name: str, damage: float,
                  is_crit: bool = False, target: str = ""):
        self.events.append({
            "t": time.time() - self.start_time,
            "spell": spell_name,
            "dmg": damage,
            "crit": is_crit,
            "target": target,
        })

    def add_event_at(self, t: float, spell_name: str, damage: float,
                     is_crit: bool = False):
        self.events.append({
            "t": t,
            "spell": spell_name,
            "dmg": damage,
            "crit": is_crit,
            "target": "",
        })

    # ── Time-series builders ─────────────────────────────────

    def dps_timeseries(self, bucket_size: float = 1.0):
        """DPS in fixed-width time buckets. Returns (times[], dps[])."""
        if not self.events:
            return [], []
        max_t = max(e["t"] for e in self.events)
        n_buckets = int(math.ceil(max_t / bucket_size)) + 1
        buckets = [0.0] * n_buckets
        for e in self.events:
            idx = min(int(e["t"] / bucket_size), n_buckets - 1)
            buckets[idx] += e["dmg"]
        times = [i * bucket_size for i in range(n_buckets)]
        dps = [b / bucket_size for b in buckets]
        return times, dps

    def cumulative_damage(self, bucket_size: float = 1.0):
        """Cumulative total damage over time. Returns (times[], totals[])."""
        times, dps = self.dps_timeseries(bucket_size)
        totals = []
        running = 0.0
        for d in dps:
            running += d * bucket_size
            totals.append(running)
        return times, totals

    def rolling_dps(self, window: float = 5.0, step: float = 1.0):
        """Rolling average DPS with a sliding window. Returns (times[], avg_dps[])."""
        if not self.events:
            return [], []
        max_t = max(e["t"] for e in self.events)
        times, avg = [], []
        t = 0.0
        while t <= max_t:
            window_dmg = sum(
                e["dmg"] for e in self.events
                if (t - window) < e["t"] <= t
            )
            effective_window = min(window, t) if t > 0 else step
            times.append(t)
            avg.append(window_dmg / effective_window if effective_window > 0 else 0)
            t += step
        return times, avg

    def spell_breakdown(self):
        """Damage and cast count per spell. Returns dict {spell: {casts, damage, pct}}."""
        totals = defaultdict(lambda: {"casts": 0, "damage": 0.0})
        for e in self.events:
            totals[e["spell"]]["casts"] += 1
            totals[e["spell"]]["damage"] += e["dmg"]
        grand = sum(v["damage"] for v in totals.values()) or 1
        for v in totals.values():
            v["pct"] = v["damage"] / grand * 100
        return dict(totals)

    def summary(self):
        total_dmg = sum(e["dmg"] for e in self.events)
        max_t = max((e["t"] for e in self.events), default=0)
        return {
            "name": self.name,
            "profile": self.profile,
            "total_damage": total_dmg,
            "duration": max_t,
            "avg_dps": total_dmg / max_t if max_t > 0 else 0,
            "total_casts": len(self.events),
            "spells": self.spell_breakdown(),
        }

    # ── Serialization ────────────────────────────────────────

    def save(self, path: str):
        data = {
            "name": self.name,
            "profile": self.profile,
            "start_time": self.start_time,
            "duration": self.duration,
            "events": self.events,
            "metadata": self.metadata,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Dashboard] Saved session → {path}")

    @staticmethod
    def load(path: str) -> "CombatSession":
        with open(path) as f:
            data = json.load(f)
        s = CombatSession(
            name=data.get("name", Path(path).stem),
            profile=data.get("profile", "unknown"),
            start_time=data.get("start_time", 0),
            duration=data.get("duration", 60),
        )
        s.events = data.get("events", [])
        s.metadata = data.get("metadata", {})
        return s


# ══════════════════════════════════════════════════════════════
#  Profile Loader — reads SPELL_INFO / ROTATION from build .py
# ══════════════════════════════════════════════════════════════

BUILDS_DIR = Path(__file__).parent / "builds"

def load_build_profile(name: str):
    candidates = [
        BUILDS_DIR / f"{name}.py",
        Path(__file__).parent / f"{name}.py",
    ]
    for path in candidates:
        if path.exists():
            spec = importlib.util.spec_from_file_location(name, str(path))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    return None


def list_profiles():
    if not BUILDS_DIR.exists():
        return []
    return [p.stem for p in BUILDS_DIR.glob("*.py") if p.stem != "_init_"]


# ══════════════════════════════════════════════════════════════
#  DPS Simulator — Offline estimation from build profiles
# ══════════════════════════════════════════════════════════════

class DPSSimulator:
    """
    Estimates DPS from a build profile's SPELL_INFO + ROTATION.

    Walks through time ticking GCD and cooldown timers, casting
    the highest-priority available spell each tick. Tracks DoT
    durations, buff windows, stack resources, and auto-attack filler.
    """

    DAMAGE_MULTIPLIERS = {
        "builder": 1.0,
        "spender": 2.0,
        "nuke": 3.5,
        "damage": 1.2,
        "aoe": 1.5,
        "dot": 0.8,
        "cc": 0.6,
        "gap_closer": 0.7,
        "buff": 0.0,
        "defensive": 0.0,
        "invulnerable": 0.0,
        "interrupt": 0.0,
        "escape": 0.0,
        "execute": 4.0,
        "utility": 0.0,
    }

    AUTO_ATTACK_DPS = 80.0
    AUTO_ATTACK_INTERVAL = 2.0

    def __init__(self, profile_name: str, duration: float = 60.0,
                 weapon_dps: float = 200.0):
        self.profile_name = profile_name
        self.duration = duration
        self.weapon_dps = weapon_dps
        self.mod = load_build_profile(profile_name)

    def _spell_damage(self, info, stype, stacks, max_stacks):
        mult = self.DAMAGE_MULTIPLIERS.get(stype, 1.0)
        if mult <= 0:
            return 0.0

        cd = info.get("cd", info.get("cooldown", 0))
        cd_scale = 1.0 + max(cd - 2, 0) * 0.12

        base = self.weapon_dps * (0.8 + mult * 0.6) * cd_scale

        if stype == "nuke" and max_stacks > 0:
            base *= 1.0 + (stacks / max_stacks) * 2.5
        elif stype == "execute":
            base *= 2.5
        elif stype == "dot":
            duration = info.get("duration", 10)
            base *= 0.3 + duration * 0.08

        return base

    def simulate(self) -> CombatSession:
        session = CombatSession(
            name=self.profile_name.replace("_", " ").title(),
            profile=self.profile_name,
            start_time=0,
            duration=self.duration,
            metadata={"mode": "simulated", "weapon_dps": self.weapon_dps},
        )

        if not self.mod:
            print(f"[Sim] No profile found for '{self.profile_name}'")
            return session

        spell_info = getattr(self.mod, "SPELL_INFO", {})
        rotation = getattr(self.mod, "ROTATION", [])
        opener = getattr(self.mod, "OPENER", [])
        gcd = getattr(self.mod, "GCD", 0.5)
        tick = getattr(self.mod, "TICK_RATE", 0.3)
        stack_enabled = getattr(self.mod, "STACK_ENABLED", False)
        max_stacks = getattr(self.mod, "MAX_STACKS", 20)

        cooldowns = {name: 0.0 for name in spell_info}
        dot_active = {}
        stacks = 0
        cast_locked_until = 0.0
        last_auto = -self.AUTO_ATTACK_INTERVAL
        t = 0.0
        opener_idx = 0

        while t < self.duration:
            dt = tick

            for name in cooldowns:
                cooldowns[name] = max(0, cooldowns[name] - dt)

            expired_dots = [n for n, exp in dot_active.items() if t >= exp]
            for n in expired_dots:
                del dot_active[n]

            if t < cast_locked_until:
                t += dt
                continue

            active_rotation = rotation
            if opener_idx < len(opener):
                active_rotation = opener[opener_idx:] + rotation

            cast_this_tick = False

            for name in active_rotation:
                if name not in spell_info:
                    continue
                info = spell_info[name]

                if cooldowns.get(name, 0) > 0:
                    continue

                stype = info.get("type", "damage")

                min_stacks = info.get("min_stacks", 0)
                if stack_enabled and min_stacks > 0 and stacks < min_stacks:
                    continue

                if stype == "dot" and name in dot_active:
                    continue

                mult = self.DAMAGE_MULTIPLIERS.get(stype, 1.0)

                if mult <= 0:
                    cd = info.get("cd", info.get("cooldown", 0))
                    cooldowns[name] = cd
                    dur = info.get("duration", 0)
                    if dur > 0:
                        dot_active[name] = t + dur
                    if stack_enabled:
                        stacks = min(max_stacks,
                                     stacks + info.get("generates_stacks", 0))
                    if name in opener[opener_idx:opener_idx + 1]:
                        opener_idx += 1
                    continue

                cast_time = info.get("cast_time", 0)
                cd = info.get("cd", info.get("cooldown", 0))
                lockout = max(gcd, cast_time)

                base_dmg = self._spell_damage(info, stype, stacks, max_stacks)
                variance = 0.9 + (hash(f"{name}{t}") % 200) / 1000.0
                damage = base_dmg * variance

                if stype == "dot":
                    dur = info.get("duration", 10)
                    dot_active[name] = t + dur
                    total_dot_dmg = damage * (dur / 3.0)
                    tick_count = max(1, int(dur / 3.0))
                    per_tick = total_dot_dmg / tick_count
                    for i in range(tick_count):
                        dot_t = t + (i + 1) * 3.0
                        if dot_t < self.duration:
                            session.add_event_at(dot_t, name, per_tick)
                else:
                    session.add_event_at(t + cast_time, name, damage)

                cooldowns[name] = max(cd, lockout)
                cast_locked_until = t + lockout

                if stack_enabled:
                    gen = info.get("generates_stacks", 0)
                    cost = info.get("consumes_stacks", 0)
                    stacks = min(max_stacks, stacks + gen)
                    if cost == -1:
                        stacks = 0
                    elif cost > 0:
                        stacks = max(0, stacks - cost)

                if name in opener[opener_idx:opener_idx + 1]:
                    opener_idx += 1

                cast_this_tick = True
                break

            if not cast_this_tick:
                if t - last_auto >= self.AUTO_ATTACK_INTERVAL:
                    aa_dmg = self.AUTO_ATTACK_DPS * self.AUTO_ATTACK_INTERVAL
                    variance = 0.85 + (hash(f"aa{t}") % 300) / 1000.0
                    session.add_event_at(t, "Auto Attack", aa_dmg * variance)
                    last_auto = t

            t += dt

        return session


# ══════════════════════════════════════════════════════════════
#  Live Capture — Record real combat from the game pipe
# ══════════════════════════════════════════════════════════════

class LiveCapture:
    """
    Connects to EthyTool pipe and records damage events in real-time.
    Monitors target HP changes to estimate damage dealt per cast.
    """

    def __init__(self, conn, session_name: str = "Live", duration: float = 60.0):
        self.conn = conn
        self.session = CombatSession(
            name=session_name,
            profile="live",
            duration=duration,
            metadata={"mode": "live"},
        )
        self.stop_event = threading.Event()
        self._last_target_hp = 0.0
        self._last_target_max = 0.0
        self._last_cast = ""
        self._cast_log = []

    def start(self):
        self.session.start_time = time.time()
        t = threading.Thread(target=self._capture_loop, daemon=True)
        t.start()
        return t

    def stop(self):
        self.stop_event.set()

    def _capture_loop(self):
        print("[Live] Capture started. Press Ctrl+C to stop.")
        poll = 0.2
        elapsed = 0.0

        while not self.stop_event.is_set() and elapsed < self.session.duration:
            try:
                self._tick()
            except Exception as e:
                print(f"[Live] Error: {e}")
            time.sleep(poll)
            elapsed = time.time() - self.session.start_time

        print(f"[Live] Capture ended. {len(self.session.events)} events recorded.")

    def _tick(self):
        if not self.conn.in_combat() and not self.conn.has_target():
            return

        target_hp_v2 = self.conn.get_target_hp_v2()
        if not target_hp_v2:
            return

        current_hp = target_hp_v2.get("hp", 0)
        max_hp = target_hp_v2.get("max", 0)

        if max_hp <= 0:
            target_hp_pct = self.conn.get_target_hp()
            if target_hp_pct > 0:
                max_hp = 10000
                current_hp = int(max_hp * target_hp_pct / 100)

        if self._last_target_max == max_hp and current_hp < self._last_target_hp:
            hp_lost = self._last_target_hp - current_hp
            if 0 < hp_lost < max_hp:
                spell = self._last_cast or "Auto Attack"
                self.session.add_event(spell, hp_lost, target=self.conn.get_target_name())

        self._last_target_hp = current_hp
        self._last_target_max = max_hp

        spells = self.conn.get_spells()
        for s in spells:
            cd = s.get("cur_cd", 0)
            name = s.get("display", s.get("name", ""))
            if name and cd > 0:
                if name not in [c[0] for c in self._cast_log[-5:]]:
                    self._cast_log.append((name, time.time()))
                    self._last_cast = name


# ══════════════════════════════════════════════════════════════
#  Dashboard Renderer — matplotlib charts
# ══════════════════════════════════════════════════════════════

COLORS = [
    "#2196F3",  # blue
    "#FF9800",  # orange
    "#4CAF50",  # green
    "#F44336",  # red
    "#9C27B0",  # purple
    "#00BCD4",  # cyan
    "#FF5722",  # deep orange
    "#8BC34A",  # light green
]


def render_dashboard(sessions: list, title: str = "EthyTool DPS Dashboard",
                     save_path: Optional[str] = None):
    try:
        import matplotlib
        matplotlib.use("TkAgg")
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec
    except ImportError:
        print("[Dashboard] matplotlib required: pip install matplotlib")
        return

    fig = plt.figure(figsize=(14, 16), facecolor="#1a1a2e")
    fig.suptitle(title, fontsize=18, fontweight="bold",
                 color="#e0e0e0", y=0.98)

    gs = GridSpec(4, 1, figure=fig, height_ratios=[3, 3, 3, 2],
                  hspace=0.35, top=0.94, bottom=0.05, left=0.10, right=0.95)

    style_kw = dict(facecolor="#16213e")

    # ── Chart 1: DPS Over Time (1s Samples) ──────────────────
    ax1 = fig.add_subplot(gs[0], **style_kw)
    for i, s in enumerate(sessions):
        times, dps = s.dps_timeseries(1.0)
        color = COLORS[i % len(COLORS)]
        ax1.plot(times, dps, color=color, linewidth=1.8,
                 label=s.name, alpha=0.9)
    _style_axis(ax1, "DPS Over Time (1s Samples)", "Time (seconds)", "DPS")
    ax1.legend(loc="upper right", fontsize=9, framealpha=0.7,
               facecolor="#16213e", edgecolor="#333",
               labelcolor="#e0e0e0")

    # ── Chart 2: Estimated Total Damage Over Time ────────────
    ax2 = fig.add_subplot(gs[1], **style_kw)
    for i, s in enumerate(sessions):
        times, totals = s.cumulative_damage(1.0)
        color = COLORS[i % len(COLORS)]
        ax2.plot(times, totals, color=color, linewidth=1.8,
                 label=s.name, alpha=0.9)
    _style_axis(ax2, "Estimated Total Damage Over Time",
                "Time (seconds)", "Total Damage")

    # ── Chart 3: Rolling Sustain DPS (5s Average) ────────────
    ax3 = fig.add_subplot(gs[2], **style_kw)
    for i, s in enumerate(sessions):
        times, avg = s.rolling_dps(window=5.0, step=1.0)
        color = COLORS[i % len(COLORS)]
        ax3.plot(times, avg, color=color, linewidth=1.8,
                 label=s.name, alpha=0.9)
    _style_axis(ax3, "Rolling Sustain DPS (5s Average)",
                "Time (seconds)", "DPS")

    # ── Chart 4: Summary Table ───────────────────────────────
    ax4 = fig.add_subplot(gs[3], **style_kw)
    ax4.axis("off")
    _render_summary_table(ax4, sessions)

    if save_path:
        fig.savefig(save_path, dpi=150, facecolor=fig.get_facecolor())
        print(f"[Dashboard] Chart saved → {save_path}")
    plt.show()


def _style_axis(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=13, fontweight="bold",
                 color="#e0e0e0", pad=10)
    ax.set_xlabel(xlabel, fontsize=10, color="#aaa")
    ax.set_ylabel(ylabel, fontsize=10, color="#aaa")
    ax.tick_params(colors="#888", which="both")
    ax.grid(True, alpha=0.15, color="#555")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#333")
    ax.spines["left"].set_color("#333")


def _render_summary_table(ax, sessions):
    if not sessions:
        return

    headers = ["Build", "Total Dmg", "Avg DPS", "Peak DPS", "Casts", "Duration"]
    rows = []
    for s in sessions:
        sm = s.summary()
        _, dps_vals = s.dps_timeseries(1.0)
        peak = max(dps_vals) if dps_vals else 0
        rows.append([
            sm["name"],
            f'{sm["total_damage"]:,.0f}',
            f'{sm["avg_dps"]:,.0f}',
            f"{peak:,.0f}",
            str(sm["total_casts"]),
            f'{sm["duration"]:.1f}s',
        ])

    cell_colors = [["#1a1a2e"] * len(headers) for _ in rows]
    header_colors = ["#0a3d62"] * len(headers)

    table = ax.table(
        cellText=rows, colLabels=headers,
        cellLoc="center", loc="center",
        colColours=header_colors,
        cellColours=cell_colors,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.6)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#333")
        if row == 0:
            cell.set_text_props(fontweight="bold", color="#e0e0e0")
        else:
            cell.set_text_props(color="#ccc")


def print_text_summary(sessions):
    print()
    print("=" * 70)
    print("  ETHYTOOL DPS DASHBOARD — SESSION SUMMARY")
    print("=" * 70)
    for s in sessions:
        sm = s.summary()
        _, dps_vals = s.dps_timeseries(1.0)
        peak = max(dps_vals) if dps_vals else 0
        print(f"\n  {sm['name']:<25} ({sm['profile']})")
        print(f"  {'─' * 45}")
        print(f"  Total Damage:   {sm['total_damage']:>12,.0f}")
        print(f"  Average DPS:    {sm['avg_dps']:>12,.0f}")
        print(f"  Peak DPS (1s):  {peak:>12,.0f}")
        print(f"  Total Casts:    {sm['total_casts']:>12}")
        print(f"  Duration:       {sm['duration']:>11.1f}s")
        print()
        breakdown = sm["spells"]
        if breakdown:
            print(f"  {'Spell':<22} {'Casts':>5}  {'Damage':>10}  {'%':>5}  Graph")
            print(f"  {'─' * 22} {'─' * 5}  {'─' * 10}  {'─' * 5}  {'─' * 15}")
            for name, info in sorted(breakdown.items(),
                                     key=lambda x: -x[1]["damage"]):
                bar = "█" * min(int(info["pct"] / 4), 20)
                print(f"  {name:<22} {info['casts']:>5}  "
                      f"{info['damage']:>10,.0f}  {info['pct']:>4.1f}%  {bar}")
    print()
    print("=" * 70)


# ══════════════════════════════════════════════════════════════
#  CLI Entry Points
# ══════════════════════════════════════════════════════════════

def cmd_simulate(args):
    no_chart = "--no-chart" in args
    save_png = None
    filtered = []
    for a in args:
        if a == "--no-chart":
            continue
        elif a.startswith("--save="):
            save_png = a.split("=", 1)[1]
        else:
            filtered.append(a)
    args = filtered

    profiles = args if args else list_profiles()
    if not profiles:
        print("[Dashboard] No profiles found. Available builds:")
        for p in list_profiles():
            print(f"  - {p}")
        return

    sessions = []
    for name in profiles:
        print(f"[Sim] Simulating {name}...")
        sim = DPSSimulator(name, duration=60.0)
        session = sim.simulate()
        sessions.append(session)

        out_dir = Path(__file__).parent / "sessions"
        out_dir.mkdir(exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        session.save(str(out_dir / f"sim_{name}_{ts}.json"))

    print_text_summary(sessions)
    if not no_chart:
        render_dashboard(sessions, title="EthyTool DPS Simulation",
                         save_path=save_png)


def cmd_live(args):
    sys.path.insert(0, str(Path(__file__).parent.parent))
    try:
        from ethytool_lib import create_connection
    except ImportError:
        print("[Dashboard] Cannot import ethytool_lib. "
              "Run from the EthyTool/dist directory.")
        return

    conn = create_connection()
    print("[Live] Connecting to game...")
    if not conn.connect(timeout=10):
        print("[Live] Failed to connect. Is the game running with EthyTool?")
        return
    print("[Live] Connected!")

    duration = float(args[0]) if args else 60.0
    label = args[1] if len(args) > 1 else conn.detect_class()

    capture = LiveCapture(conn, session_name=label, duration=duration)
    thread = capture.start()

    try:
        thread.join()
    except KeyboardInterrupt:
        capture.stop()
        thread.join(timeout=3)

    session = capture.session
    out_dir = Path(__file__).parent / "sessions"
    out_dir.mkdir(exist_ok=True)
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    session.save(str(out_dir / f"live_{label}_{ts}.json"))

    print_text_summary([session])
    render_dashboard([session], title=f"EthyTool Live — {label}")


def cmd_compare(args):
    if not args:
        session_dir = Path(__file__).parent / "sessions"
        if session_dir.exists():
            files = sorted(session_dir.glob("*.json"))[-8:]
            args = [str(f) for f in files]
        if not args:
            print("[Dashboard] Usage: dps_dashboard.py compare file1.json file2.json ...")
            return

    sessions = []
    for path in args:
        if not os.path.exists(path):
            candidate = Path(__file__).parent / "sessions" / path
            if candidate.exists():
                path = str(candidate)
            else:
                print(f"[Dashboard] File not found: {path}")
                continue
        sessions.append(CombatSession.load(path))
        print(f"[Dashboard] Loaded: {path}")

    if sessions:
        print_text_summary(sessions)
        render_dashboard(sessions, title="EthyTool DPS Comparison")


def cmd_view(args):
    if not args:
        print("[Dashboard] Usage: dps_dashboard.py view session.json")
        return
    cmd_compare(args[:1])


def cmd_list(_args):
    print("\n  Available Build Profiles:")
    print("  " + "─" * 30)
    for p in list_profiles():
        mod = load_build_profile(p)
        rotation = getattr(mod, "ROTATION", []) if mod else []
        print(f"  {p:<20} ({len(rotation)} spells in rotation)")
    print()

    session_dir = Path(__file__).parent / "sessions"
    if session_dir.exists():
        files = list(session_dir.glob("*.json"))
        if files:
            print(f"  Saved Sessions ({len(files)}):")
            print("  " + "─" * 30)
            for f in sorted(files)[-10:]:
                size = f.stat().st_size / 1024
                print(f"  {f.name:<40} ({size:.1f} KB)")
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("  Available commands:")
        print("    simulate [build1 build2 ...]  — Simulate DPS from profiles")
        print("    live [duration] [label]       — Capture live combat data")
        print("    compare [file1.json ...]      — Compare saved sessions")
        print("    view <file.json>              — View a single session")
        print("    list                          — Show profiles and sessions")
        print()
        print("  Available builds:", ", ".join(list_profiles()) or "(none found)")
        print()
        return

    cmd = sys.argv[1].lower()
    args = sys.argv[2:]

    commands = {
        "simulate": cmd_simulate,
        "sim": cmd_simulate,
        "live": cmd_live,
        "capture": cmd_live,
        "compare": cmd_compare,
        "view": cmd_view,
        "list": cmd_list,
        "ls": cmd_list,
    }

    handler = commands.get(cmd)
    if handler:
        handler(args)
    else:
        print(f"[Dashboard] Unknown command: {cmd}")
        print(f"  Available: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()
