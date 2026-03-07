"""
╔══════════════════════════════════════════════════════════════════════╗
║                    EthyTool Combat Engine v3.0                       ║
║                                                                      ║
║  100% GENERIC — all class logic lives in profile .py files.          ║
║                                                                      ║
║  Supports:                                                           ║
║    • Stack/resource tracking (configurable per class)                ║
║    • Buff duration tracking + safety warnings                        ║
║    • Defensive combos (e.g. Undying Fury → Staggering Shout)        ║
║    • Spender gating (min_stacks from SPELL_INFO)                    ║
║    • AoE detection + priority swap                                   ║
║    • Pull opener sequence                                            ║
║    • Gap closer logic                                                ║
║    • Kiting mode                                                     ║
║    • Auto-rest between fights                                        ║
║    • Full session stats                                              ║
║                                                                      ║
║  All class behavior comes from:                                      ║
║    scripts/builds/<classname>.py                                     ║
║                                                                      ║
║  Usage:                                                              ║
║    engine = CombatEngine(conn, "berserker")                          ║
║    engine = CombatEngine(conn, "cleric")                             ║
║    engine = CombatEngine(conn, "ranger")                             ║
║    engine.run()                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import time
import math
import threading
import importlib
import importlib.util
from pathlib import Path
from enum import Enum, auto


# ══════════════════════════════════════════════════════════════
#  Combat States
# ══════════════════════════════════════════════════════════════

class CombatState(Enum):
    IDLE = auto()
    PULLING = auto()
    COMBAT = auto()
    DEFENSIVE = auto()
    AOE = auto()
    KITING = auto()
    RESTING = auto()
    DEAD = auto()


# ══════════════════════════════════════════════════════════════
#  Stack Tracker — Generic resource system
# ══════════════════════════════════════════════════════════════

class StackTracker:
    """
    Estimates resource stacks from cast history.
    Works for any stack-based class (fury, combo points, etc).
    """

    def __init__(self, max_stacks=20, decay_time=8.0):
        self.max_stacks = max_stacks
        self.decay_time = decay_time
        self.stacks = 0
        self._last_combat = time.time()

    def gain(self, amount=1):
        self.stacks = min(self.max_stacks, self.stacks + amount)
        self._last_combat = time.time()

    def spend(self, amount):
        """Spend stacks. -1 = all."""
        if amount == -1:
            spent = self.stacks
            self.stacks = 0
            return spent
        spent = min(self.stacks, amount)
        self.stacks = max(0, self.stacks - amount)
        return spent

    def update(self, in_combat):
        if in_combat:
            self._last_combat = time.time()
        elif self.stacks > 0:
            if time.time() - self._last_combat > self.decay_time:
                self.stacks = max(0, self.stacks - 1)
                self._last_combat = time.time()

    def has(self, amount):
        return self.stacks >= amount

    @property
    def full(self):
        return self.stacks >= self.max_stacks

    @property
    def pct(self):
        return (self.stacks / self.max_stacks * 100) if self.max_stacks > 0 else 0


# ══════════════════════════════════════════════════════════════
#  Buff Tracker — Duration tracking + safety
# ══════════════════════════════════════════════════════════════

class BuffTracker:
    def __init__(self):
        self._buffs = {}

    def apply(self, name, duration=0):
        self._buffs[name] = {"applied": time.time(), "duration": duration}

    def is_active(self, name):
        if name not in self._buffs:
            return False
        info = self._buffs[name]
        if info["duration"] <= 0:
            return True
        return time.time() - info["applied"] < info["duration"]

    def remaining(self, name):
        if name not in self._buffs:
            return 0
        info = self._buffs[name]
        if info["duration"] <= 0:
            return 9999
        return max(0, info["duration"] - (time.time() - info["applied"]))

    def expiring_soon(self, name, threshold=2.0):
        r = self.remaining(name)
        return 0 < r < threshold

    def needs_refresh(self, name, before=3.0):
        if name not in self._buffs:
            return True
        return self.remaining(name) < before


# ══════════════════════════════════════════════════════════════
#  Spell Stats Tracker
# ══════════════════════════════════════════════════════════════

class SpellStats:
    def __init__(self):
        self._casts = {}
        self._total = 0

    def on_cast(self, name):
        self._casts[name] = self._casts.get(name, 0) + 1
        self._total += 1

    @property
    def total(self):
        return self._total

    @property
    def breakdown(self):
        return dict(self._casts)


# ══════════════════════════════════════════════════════════════
#  Profile Loader — Reads ANY class .py file
# ══════════════════════════════════════════════════════════════

class CombatProfile:
    """Loads all combat config from a class profile file."""

    def __init__(self):
        # Rotation
        self.rotation = []
        self.buffs = []
        self.rebuff_interval = 55.0
        self.aoe_spells = []
        self.aoe_threshold = 3
        self.opener = []
        self.gap_closers = []

        # Defensive
        self.defensive_spells = []
        self.defensive_hp = 40.0
        self.defensive_trigger_hp = 20
        self.defensive_combo = []

        # Healing
        self.heal_spells = []
        self.heal_hp = 50.0

        # Kiting
        self.kite_hp = 0
        self.kite_spells = []

        # Rest
        self.rest_spell = "Rest"
        self.rest_hp = 70
        self.rest_mp = 50
        self.meditation_spell = "Leyline Meditation"

        # Stacks
        self.stack_enabled = False
        self.max_stacks = 20
        self.stack_decay_time = 8.0

        # Spell metadata
        self.spell_info = {}

        # Buff config
        self.buff_durations = {}
        self.buff_safety = {}

        # Timing
        self.tick_rate = 0.3
        self.gcd = 0.5

    @staticmethod
    def load(name):
        p = CombatProfile()
        script_dir = Path(__file__).parent

        for path in [script_dir / "builds" / f"{name}.py", script_dir / f"{name}.py"]:
            if path.exists():
                spec = importlib.util.spec_from_file_location(name, str(path))
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)

                # Load everything the profile defines
                p.rotation = getattr(m, "ROTATION", [])
                p.buffs = getattr(m, "BUFFS", [])
                p.rebuff_interval = getattr(m, "REBUFF_INTERVAL", 55.0)
                p.aoe_spells = getattr(m, "AOE_SPELLS", [])
                p.aoe_threshold = getattr(m, "AOE_THRESHOLD", 3)
                p.opener = getattr(m, "OPENER", [])
                p.gap_closers = getattr(m, "GAP_CLOSERS", [])
                p.defensive_spells = getattr(m, "DEFENSIVE_SPELLS", [])
                p.defensive_hp = getattr(m, "DEFENSIVE_HP", 40.0)
                p.defensive_trigger_hp = getattr(m, "DEFENSIVE_TRIGGER_HP", 20)
                p.defensive_combo = getattr(m, "DEFENSIVE_COMBO", [])
                p.heal_spells = getattr(m, "HEAL_SPELLS", [])
                p.heal_hp = getattr(m, "HEAL_HP", 50.0)
                p.kite_hp = getattr(m, "KITE_HP", 0)
                p.kite_spells = getattr(m, "KITE_SPELLS", [])
                p.rest_spell = getattr(m, "REST_SPELL", "Rest")
                p.rest_hp = getattr(m, "REST_HP", 70)
                p.rest_mp = getattr(m, "REST_MP", 50)
                p.meditation_spell = getattr(m, "MEDITATION_SPELL", "Leyline Meditation")
                p.stack_enabled = getattr(m, "STACK_ENABLED", False)
                p.max_stacks = getattr(m, "MAX_STACKS", 20)
                p.stack_decay_time = getattr(m, "STACK_DECAY_TIME", 8.0)
                p.spell_info = getattr(m, "SPELL_INFO", {})
                p.buff_durations = getattr(m, "BUFF_DURATIONS", {})
                p.buff_safety = getattr(m, "BUFF_SAFETY", {})
                p.tick_rate = getattr(m, "TICK_RATE", 0.3)
                p.gcd = getattr(m, "GCD", 0.5)
                break

        return p

    def get_spell(self, name):
        """Get SPELL_INFO for a spell, or empty dict."""
        return self.spell_info.get(name, {})


# ══════════════════════════════════════════════════════════════
#  Combat Engine v3.0 — FULLY GENERIC
# ══════════════════════════════════════════════════════════════

class CombatEngine:

    def __init__(self, connection, profile_name="berserker",
                 log_fn=None, stop_event=None):
        self.conn = connection
        self.log = log_fn or print
        self.stop_event = stop_event or threading.Event()

        # Load profile
        self.profile = CombatProfile.load(profile_name)
        self.profile_name = profile_name

        # Systems
        self.stats = SpellStats()
        self.buffs = BuffTracker()
        self.stacks = None
        if self.profile.stack_enabled:
            self.stacks = StackTracker(
                max_stacks=self.profile.max_stacks,
                decay_time=self.profile.stack_decay_time,
            )

        # State
        self.state = CombatState.IDLE
        self._state_time = time.time()
        self._last_gcd = 0
        self._pull_count = 0
        self._kill_count = 0
        self._deaths = 0
        self._session_start = 0
        self._defensive_active = {}  # spell_name -> pop_time

        # Toggles
        self.auto_rest = True
        self.auto_buff = True
        self.auto_defensive = True
        self.auto_aoe = True
        self.log_casts = True
        self.log_states = True

        # Available spells (checked at start)
        self._available = set()

    # ══════════════════════════════════════
    #  Run
    # ══════════════════════════════════════

    def run(self):
        self._init()
        self._session_start = time.time()

        while not self.stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                self.log(f"[ERR] {e}")
            time.sleep(self.profile.tick_rate)

        self._report()

    def start(self):
        t = threading.Thread(target=self.run, daemon=True)
        t.start()
        return t

    def stop(self):
        self.stop_event.set()

    # ══════════════════════════════════════
    #  Init — Check available spells
    # ══════════════════════════════════════

    def _init(self):
        known = self.conn.get_spell_set()
        all_spells = set()

        for lst in [self.profile.rotation, self.profile.buffs,
                    self.profile.aoe_spells, self.profile.opener,
                    self.profile.gap_closers, self.profile.defensive_spells,
                    self.profile.heal_spells, self.profile.kite_spells,
                    self.profile.defensive_combo]:
            all_spells.update(lst)

        for spell in all_spells:
            if spell in known or spell.lower() in known:
                self._available.add(spell)
            else:
                self.log(f"[WARN] Missing spell: {spell}")

        self.log(f"")
        self.log(f"  ═══ {self.profile_name.upper()} COMBAT ENGINE ═══")
        self.log(f"  Spells: {len(self._available)}/{len(all_spells)}")
        self.log(f"  Rotation: {self.profile.rotation}")
        self.log(f"  Stacks: {'ON (max ' + str(self.profile.max_stacks) + ')' if self.stacks else 'OFF'}")
        self.log(f"")

    # ══════════════════════════════════════
    #  State Machine
    # ══════════════════════════════════════

    def _set_state(self, s):
        if s != self.state:
            old = self.state
            self.state = s
            self._state_time = time.time()
            if self.log_states:
                extra = ""
                if self.stacks:
                    extra = f" [{self.stacks.stacks}/{self.stacks.max_stacks}]"
                self.log(f"[STATE] {old.name} → {s.name}{extra}")

    # ══════════════════════════════════════
    #  Core Tick
    # ══════════════════════════════════════

    def _tick(self):
        hp = self.conn.get_hp()
        mp = self.conn.get_mp()
        in_combat = self.conn.in_combat()
        has_target = self.conn.has_target()
        target_hp = self.conn.get_target_hp() if has_target else 0
        alive = hp > 0

        # Update systems
        if self.stacks:
            self.stacks.update(in_combat)
        self._update_defensives()
        self._check_buff_safety(hp)

        # Dead
        if not alive:
            if self.state != CombatState.DEAD:
                self._deaths += 1
            self._set_state(CombatState.DEAD)
            return

        # Determine state
        if not in_combat and not has_target:
            if self.auto_rest and (hp < self.profile.rest_hp or mp < self.profile.rest_mp):
                self._set_state(CombatState.RESTING)
            else:
                self._set_state(CombatState.IDLE)

        elif in_combat or has_target:
            if self.state in (CombatState.IDLE, CombatState.RESTING):
                self._set_state(CombatState.PULLING)
                self._pull_count += 1

            elif self.auto_defensive and hp < self.profile.defensive_trigger_hp:
                if self.profile.kite_hp and hp < self.profile.kite_hp:
                    self._set_state(CombatState.KITING)
                else:
                    self._set_state(CombatState.DEFENSIVE)

            elif self.auto_defensive and hp < self.profile.defensive_hp:
                self._set_state(CombatState.DEFENSIVE)

            elif self.auto_aoe and self._count_enemies() >= self.profile.aoe_threshold:
                self._set_state(CombatState.AOE)

            else:
                self._set_state(CombatState.COMBAT)

        # Dispatch
        {
            CombatState.IDLE: self._do_idle,
            CombatState.RESTING: self._do_rest,
            CombatState.PULLING: self._do_pull,
            CombatState.COMBAT: self._do_combat,
            CombatState.DEFENSIVE: self._do_defensive,
            CombatState.AOE: self._do_aoe,
            CombatState.KITING: self._do_kite,
            CombatState.DEAD: self._do_dead,
        }.get(self.state, lambda: None)()

    # ══════════════════════════════════════
    #  Defensive Tracking (generic)
    # ══════════════════════════════════════

    def _update_defensives(self):
        """Track active defensive cooldowns by duration from SPELL_INFO."""
        for name, pop_time in list(self._defensive_active.items()):
            info = self.profile.get_spell(name)
            duration = info.get("duration", 10)
            if time.time() - pop_time > duration:
                del self._defensive_active[name]
                heal_pct = info.get("heal_on_expiry", 0)
                if heal_pct > 0:
                    self.log(f"[BUFF] {name} expired → healed {heal_pct * 100:.0f}% HP")
                else:
                    self.log(f"[BUFF] {name} expired")

    def _check_buff_safety(self, hp):
        """Check BUFF_SAFETY config for dangerous buff expirations."""
        for name, safety in self.profile.buff_safety.items():
            warn_hp = safety.get("warn_hp_below", 0)
            warn_time = safety.get("warn_before_expiry", 2.0)
            if self.buffs.expiring_soon(name, warn_time) and hp < warn_hp:
                danger = safety.get("danger", "Buff expiring!")
                self.log(f"[DANGER] {name} expiring! {danger}")

    # ══════════════════════════════════════
    #  State Handlers
    # ══════════════════════════════════════

    def _do_idle(self):
        if self.auto_buff:
            self._refresh_buffs()

    def _do_rest(self):
        if self.conn.in_combat():
            self._set_state(CombatState.COMBAT)
            return
        if self.conn.has_progress():
            return

        hp, mp = self.conn.get_hp(), self.conn.get_mp()

        if mp < self.profile.rest_mp:
            if self._try_cast(self.profile.meditation_spell):
                return
        if hp < self.profile.rest_hp:
            if self._try_cast(self.profile.rest_spell):
                return
        if hp >= 95 and mp >= 80:
            self._set_state(CombatState.IDLE)

    def _do_pull(self):
        # Opener buffs
        for spell in self.profile.opener:
            if self._try_cast(spell):
                self._apply_buff_if_needed(spell)
                return

        # Gap closer
        if self.profile.gap_closers and self.conn.has_target():
            target = self.conn.get_target()
            if target:
                px, py = self.conn.get_x(), self.conn.get_y()
                tx, ty = float(target.get("x", px)), float(target.get("y", py))
                if math.sqrt((tx - px) ** 2 + (ty - py) ** 2) > 3:
                    for closer in self.profile.gap_closers:
                        if self._try_cast(closer):
                            return

        self._set_state(CombatState.COMBAT)

    def _do_combat(self):
        # Refresh buffs
        if self.auto_buff:
            self._refresh_buffs()

        # Target dead = kill
        if self.conn.has_target() and self.conn.get_target_hp() <= 0:
            self._kill_count += 1
            return

        # Main rotation — gated by _can_cast (checks min_stacks)
        self._cast_rotation(self.profile.rotation)

    def _do_defensive(self):
        hp = self.conn.get_hp()

        # Heals first
        for spell in self.profile.heal_spells:
            if self._try_cast(spell):
                return

        # Pop defensive cooldowns
        for spell in self.profile.defensive_spells:
            if spell not in self._defensive_active:
                if self._try_cast(spell):
                    self._defensive_active[spell] = time.time()
                    info = self.profile.get_spell(spell)
                    extra_dmg = info.get("extra_damage_taken", 0)
                    msg = f"[DEF] 🛡 {spell} ACTIVE"
                    if extra_dmg > 0:
                        msg += f" (+{extra_dmg * 100:.0f}% dmg taken)"
                    self.log(msg)

                    # Defensive combo
                    for combo in self.profile.defensive_combo:
                        if self._try_cast(combo):
                            self.log(f"[DEF] → combo: {combo}")
                            break
                    return

        # Keep fighting
        self._cast_rotation(self.profile.rotation)

        if hp > self.profile.defensive_hp:
            self._set_state(CombatState.COMBAT)

    def _do_aoe(self):
        if self.auto_buff:
            self._refresh_buffs()
        self._cast_rotation(self.profile.aoe_spells)

    def _do_kite(self):
        for spell in self.profile.defensive_spells:
            if spell not in self._defensive_active:
                if self._try_cast(spell):
                    self._defensive_active[spell] = time.time()
                    return

        for spell in self.profile.kite_spells:
            if self._try_cast(spell):
                return

        if self.conn.get_hp() > self.profile.defensive_hp:
            self._set_state(CombatState.COMBAT)

    def _do_dead(self):
        if time.time() - self._state_time > 2 and self.conn.is_alive():
            self.log("[Combat] Resurrected!")
            self._set_state(CombatState.IDLE)

    # ══════════════════════════════════════
    #  Casting — Generic, reads SPELL_INFO
    # ══════════════════════════════════════

    def _cast_rotation(self, rotation):
        """Try to cast spells from a rotation list in priority order."""
        for spell in rotation:
            if self._can_cast(spell) and self._try_cast(spell):
                return True
        return False

    def _can_cast(self, name):
        """Check if spell can be cast based on SPELL_INFO min_stacks."""
        if name not in self._available:
            return False
        if not self.stacks:
            return True

        info = self.profile.get_spell(name)
        min_stacks = info.get("min_stacks", 0)
        if min_stacks > 0:
            return self.stacks.has(min_stacks)
        return True

    def _try_cast(self, name):
        if name not in self._available:
            return False
        if time.time() - self._last_gcd < self.profile.gcd:
            return False
        if not self.conn.is_spell_ready(name):
            return False

        result = self.conn.cast(name)
        if not result:
            return False

        self._last_gcd = time.time()
        self.stats.on_cast(name)

        # Stack management from SPELL_INFO
        info = self.profile.get_spell(name)
        if self.stacks:
            gen = info.get("generates_stacks", 0)
            cost = info.get("consumes_stacks", 0)
            if gen > 0:
                self.stacks.gain(gen)
            if cost != 0:
                self.stacks.spend(cost)

        # Buff tracking
        self._apply_buff_if_needed(name)

        # Log
        if self.log_casts:
            stype = info.get("type", "?")
            icons = {
                "builder": "⚔", "spender": "", "nuke": "🗡",
                "buff": "🛡", "cc": "", "gap_closer": "🏃",
                "defensive": "", "execute": "🗡", "utility": "🔧",
            }
            icon = icons.get(stype, "⚡")
            stk = f" [{self.stacks.stacks}/{self.stacks.max_stacks}]" if self.stacks else ""
            self.log(f"[{self.state.name[:4]}] {icon} {name}{stk}")

        return True

    def _apply_buff_if_needed(self, name):
        """If spell is a buff with duration, track it."""
        info = self.profile.get_spell(name)
        dur = info.get("duration", 0)
        if dur > 0:
            self.buffs.apply(name, dur)
        elif name in self.profile.buff_durations:
            dur = self.profile.buff_durations[name]
            if dur > 0:
                self.buffs.apply(name, dur)

    def _refresh_buffs(self):
        for buff in self.profile.buffs:
            dur = self.profile.buff_durations.get(buff,
                  self.profile.get_spell(buff).get("duration", 0))
            refresh_before = 3.0 if dur > 0 else self.profile.rebuff_interval

            if dur > 0:
                if self.buffs.needs_refresh(buff, 3.0):
                    if self._try_cast(buff):
                        return True
            else:
                if self.buffs.needs_refresh(buff, self.profile.rebuff_interval):
                    if self._try_cast(buff):
                        return True
        return False

    # ══════════════════════════════════════
    #  Helpers
    # ══════════════════════════════════════

    def _count_enemies(self):
        try:
            mobs = self.conn.get_nearby_mobs()
            if not mobs:
                return 0
            px, py = self.conn.get_x(), self.conn.get_y()
            return sum(1 for e in mobs
                       if e.get("hp", 0) > 0
                       and not e.get("static")
                       and math.sqrt((float(e.get("x", 0)) - px) ** 2 +
                                     (float(e.get("y", 0)) - py) ** 2) < 10)
        except Exception:
            return 0

    # ══════════════════════════════════════
    #  Stats Report
    # ══════════════════════════════════════

    def _report(self):
        elapsed = time.time() - self._session_start
        mins = max(elapsed / 60, 0.01)

        self.log("")
        self.log("═" * 55)
        self.log(f"  {self.profile_name.upper()} SESSION REPORT")
        self.log("═" * 55)
        self.log(f"  Duration:    {mins:.1f} min")
        self.log(f"  Kills:       {self._kill_count}  ({self._kill_count / mins:.1f}/min)")
        self.log(f"  Deaths:      {self._deaths}")
        self.log(f"  Pulls:       {self._pull_count}")
        self.log(f"  Casts:       {self.stats.total}  ({self.stats.total / mins:.1f}/min)")
        self.log("")

        bd = self.stats.breakdown
        if bd:
            self.log(f"  {'Spell':<25} {'Casts':>5}  {'Type':<8}  {'Graph'}")
            self.log(f"  {'─' * 25} {'─' * 5}  {'─' * 8}  {'─' * 20}")
            for name, count in sorted(bd.items(), key=lambda x: -x[1]):
                info = self.profile.get_spell(name)
                stype = info.get("type", "?")
                bar = "█" * min(count, 25)
                self.log(f"  {name:<25} {count:>5}  {stype:<8}  {bar}")

        self.log("═" * 55)