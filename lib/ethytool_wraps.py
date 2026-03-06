"""
╔══════════════════════════════════════════════════════════════════════╗
║                     EthyTool API — The Only File You Need            ║
║                                                                      ║
║  Every script starts with:                                           ║
║      from ethytool_wraps import *                                    ║
║                                                                      ║
║  That's it. Everything below just works.                             ║
║                                                                      ║
║  ═══════════════════════════════════════════════════════════════════  ║
║                                                                      ║
║  ─── COMBAT ───────────────────────────────────────────────────────  ║
║                                                                      ║
║    fight()              Auto-fight current target using class         ║
║                         rotation until it dies.                       ║
║                                                                      ║
║    fight_loop()         Fight → loot → rest → repeat forever.        ║
║                                                                      ║
║    pull()               Buff up + charge in. Opens the fight.        ║
║                                                                      ║
║    rotate()             Cast one spell from your rotation.           ║
║                         Call this in a loop for manual control.      ║
║                                                                      ║
║    cast("Fireball")     Cast a specific spell. True if it worked.    ║
║                                                                      ║
║    cast_first(["A","B"]) Cast first available from list.             ║
║                                                                      ║
║    nuke()               Dump all stacks into your nuke spell.        ║
║                                                                      ║
║    defend()             Pop defensive cooldowns.                     ║
║                                                                      ║
║    buff()               Apply all class buffs.                       ║
║                                                                      ║
║  ─── HEALTH & MANA ───────────────────────────────────────────────  ║
║                                                                      ║
║    hp()                 Your HP as %. 100 = full, 0 = dead.          ║
║    mp()                 Your MP as %.                                ║
║    max_hp()             Max HP number.                               ║
║    max_mp()             Max MP number.                               ║
║    alive()              True if alive.                               ║
║    low_hp(30)           True if HP below 30%.                        ║
║    low_mp(20)           True if MP below 20%.                        ║
║                                                                      ║
║  ─── TARGET ───────────────────────────────────────────────────────  ║
║                                                                      ║
║    target()             Target info dict or None.                    ║
║    target_hp()          Target HP %.                                 ║
║    target_name()        Target name string.                          ║
║    has_target()         True if you have a target.                   ║
║    target_dead()        True if target is dead.                      ║
║    target_boss()        True if target is a boss.                    ║
║    target_elite()       True if target is elite.                     ║
║                                                                      ║
║  ─── POSITION & MOVEMENT ─────────────────────────────────────────  ║
║                                                                      ║
║    pos()                (x, y, z) tuple.                             ║
║    x() / y() / z()      Individual coords.                          ║
║    speed()              Movement speed.                              ║
║    moving()             True if walking/running.                     ║
║    frozen()             True if controls locked.                     ║
║    combat()             True if in combat.                           ║
║    safe_zone()          True if in safe zone.                        ║
║    wildlands()          True if in wildlands.                        ║
║    dist(x, y)           Distance to a point.                        ║
║    near(x, y, 10)       True if within 10 units.                    ║
║                                                                      ║
║  ─── SPELLS ───────────────────────────────────────────────────────  ║
║                                                                      ║
║    spells()             List of all spell dicts.                     ║
║    spell_names()        List of spell display names.                 ║
║    has_spell("Heal")    True if you have it.                         ║
║    spell_ready("Heal")  True if off cooldown.                        ║
║    my_class()           Your class name ("Berserker", etc).          ║
║                                                                      ║
║  ─── LOOT ─────────────────────────────────────────────────────────  ║
║                                                                      ║
║    loot()               Loot everything nearby. One call.            ║
║    loot_nearest()       Find closest corpse + loot it.               ║
║    has_loot()           True if loot window is open.                 ║
║    loot_items()         Items in the loot window.                    ║
║                                                                      ║
║  ─── GATHERING ────────────────────────────────────────────────────  ║
║                                                                      ║
║    gather("Stone")      Full cycle: interact + wait + done.          ║
║    use("Stone")         Start interacting with something.            ║
║    progress()           True if progress bar active.                 ║
║    wait_progress()      Wait until bar finishes.                     ║
║    nodes()              All harvestable nodes nearby.                ║
║    closest_node(name)   Closest matching node.                       ║
║                                                                      ║
║  ─── NEARBY / ENTITIES ────────────────────────────────────────────  ║
║                                                                      ║
║    nearby()             All nearby entities.                         ║
║    nearby_mobs()        Only living mobs.                            ║
║    nearby_names()       Names of nearby entities.                    ║
║    find("Wolf")         First nearby match.                          ║
║    closest("Wolf")      Closest matching entity.                     ║
║    enemies()            Hostile living mobs near you.                ║
║    enemy_count()        How many enemies within range.               ║
║                                                                      ║
║  ─── INVENTORY ────────────────────────────────────────────────────  ║
║                                                                      ║
║    items()              All inventory items.                         ║
║    item_names()         List of item names.                          ║
║    has("Potion")        True if you have it.                         ║
║    count_item("Ore")    Total count of matching items.               ║
║    find_item("Sword")   First matching item.                         ║
║    equipped()           Equipped gear.                               ║
║                                                                      ║
║  ─── REST & RECOVERY ─────────────────────────────────────────────  ║
║                                                                      ║
║    rest()               Sit down and recover HP/MP.                  ║
║    meditate()           Meditate for faster MP regen.                ║
║    heal(50)             Cast heal if below threshold.                ║
║    recover(90, 80)      Rest until HP>90% and MP>80%.               ║
║                                                                      ║
║  ─── WAIT / FLOW CONTROL ─────────────────────────────────────────  ║
║                                                                      ║
║    wait(1.5)            Sleep 1.5 seconds.                           ║
║    wait_combat_end()    Block until out of combat.                   ║
║    wait_hp(90)          Block until HP above 90%.                    ║
║    wait_still()         Block until not moving.                      ║
║    wait_dead()          Block until target is dead.                  ║
║    wait_spell("Heal")   Block until spell is off CD.                ║
║                                                                      ║
║  ─── CAMERA ───────────────────────────────────────────────────────  ║
║                                                                      ║
║    camera()             Full camera info dict.                       ║
║    zoom()               Camera distance.                             ║
║    angle()              Camera angle.                                ║
║    pitch()              Camera pitch.                                ║
║                                                                      ║
║  ─── SYSTEM ───────────────────────────────────────────────────────  ║
║                                                                      ║
║    all_stats()          Everything about your character.             ║
║    gold()               Your gold count.                             ║
║    food()               Your food %.                                 ║
║    ping()               True if DLL is alive.                        ║
║    log("message")       Print to the dashboard log.                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import time as _time
import math as _math
import sys as _sys
import importlib.util as _importlib_util
from pathlib import Path as _Path

# ══════════════════════════════════════════════════════════════
#  Internal — profile loader + combat state
# ══════════════════════════════════════════════════════════════

class _CombatState:
    """Internal combat state tracker. Users never see this."""

    def __init__(self):
        self.profile = None
        self.profile_name = None
        self.stacks = 0
        self.max_stacks = 20
        self.stack_decay_time = 8.0
        self.last_combat_time = _time.time()
        self.last_gcd = 0
        self.gcd = 0.5
        self.buff_timers = {}       # name -> applied_time
        self.defensive_timers = {}  # name -> popped_time
        self.cast_counts = {}
        self.total_casts = 0
        self.kills = 0
        self.deaths = 0
        self.pulls = 0
        self.session_start = _time.time()

    def gain_stacks(self, n=1):
        self.stacks = min(self.max_stacks, self.stacks + n)
        self.last_combat_time = _time.time()

    def spend_stacks(self, n):
        if n == -1:
            spent = self.stacks
            self.stacks = 0
            return spent
        spent = min(self.stacks, n)
        self.stacks = max(0, self.stacks - n)
        return spent

    def decay(self, in_combat):
        if in_combat:
            self.last_combat_time = _time.time()
        elif self.stacks > 0:
            if _time.time() - self.last_combat_time > self.stack_decay_time:
                self.stacks = max(0, self.stacks - 1)
                self.last_combat_time = _time.time()

    def on_gcd(self):
        return _time.time() - self.last_gcd < self.gcd

    def trigger_gcd(self):
        self.last_gcd = _time.time()

    def track_cast(self, name):
        self.cast_counts[name] = self.cast_counts.get(name, 0) + 1
        self.total_casts += 1

    def buff_active(self, name, duration):
        if name not in self.buff_timers:
            return False
        if duration <= 0:
            return True
        return _time.time() - self.buff_timers[name] < duration

    def buff_needs_refresh(self, name, duration, refresh_before=3.0):
        if name not in self.buff_timers:
            return True
        if duration <= 0:
            return False
        remaining = duration - (_time.time() - self.buff_timers[name])
        return remaining < refresh_before

    def defensive_active(self, name, duration=10):
        if name not in self.defensive_timers:
            return False
        return _time.time() - self.defensive_timers[name] < duration


_state = _CombatState()


def _load_profile(name=None):
    """Load a class profile from builds/<name>.py"""
    if _state.profile and name and name == _state.profile_name:
        return _state.profile

    if not name:
        name = my_class().lower()
        if name == "unknown":
            return None

    script_dir = _Path(__file__).parent
    for path in [script_dir / "builds" / f"{name}.py", script_dir / f"{name}.py"]:
        if path.exists():
            spec = _importlib_util.spec_from_file_location(name, str(path))
            module = _importlib_util.module_from_spec(spec)
            spec.loader.exec_module(module)
            _state.profile = module
            _state.profile_name = name
            _state.max_stacks = getattr(module, "MAX_STACKS", 20)
            _state.stack_decay_time = getattr(module, "STACK_DECAY_TIME", 8.0)
            _state.gcd = getattr(module, "GCD", 0.5)
            return module

    return None


def _get_spell_info(name):
    """Get SPELL_INFO entry for a spell from the loaded profile."""
    p = _load_profile()
    if not p:
        return {}
    info = getattr(p, "SPELL_INFO", {})
    return info.get(name, {})


def _try_cast(name):
    """Internal: try to cast a spell with GCD + stack checks."""
    if _state.on_gcd():
        return False
    if not conn.is_spell_ready(name):
        return False

    info = _get_spell_info(name)
    min_stacks = info.get("min_stacks", 0)
    if min_stacks > 0 and _state.stacks < min_stacks:
        return False

    result = conn.cast(name)
    if not result:
        return False

    _state.trigger_gcd()
    _state.track_cast(name)

    # Stack management
    gen = info.get("generates_stacks", 0)
    cost = info.get("consumes_stacks", 0)
    if gen > 0:
        _state.gain_stacks(gen)
    if cost != 0:
        _state.spend_stacks(cost)

    # Buff tracking
    dur = info.get("duration", 0)
    if dur > 0:
        _state.buff_timers[name] = _time.time()

    return True


# ══════════════════════════════════════════════════════════════
#  PLAYER — Health, Mana, Status
# ══════════════════════════════════════════════════════════════

def hp():           return conn.get_hp()
def mp():           return conn.get_mp()
def max_hp():       return conn.get_max_hp()
def max_mp():       return conn.get_max_mp()
def alive():        return conn.is_alive()
def low_hp(t=30):   return conn.is_low_hp(t)
def low_mp(t=20):   return conn.is_low_mp(t)

# ══════════════════════════════════════════════════════════════
#  POSITION & MOVEMENT
# ══════════════════════════════════════════════════════════════

def pos():          return conn.get_position()
def x():            return conn.get_x()
def y():            return conn.get_y()
def z():            return conn.get_z()
def speed():        return conn.get_speed()
def moving():       return conn.is_moving()
def frozen():       return conn.is_frozen()
def combat():       return conn.in_combat()
def safe_zone():    return conn.in_safe_zone()
def wildlands():    return conn.in_wildlands()
def dist(x, y):     return conn.distance_to(x, y)
def near(x, y, r=5): return conn.is_near(x, y, r)

# ══════════════════════════════════════════════════════════════
#  TARGET
# ══════════════════════════════════════════════════════════════

def target():        return conn.get_target()
def target_hp():     return conn.get_target_hp()
def target_name():   return conn.get_target_name()
def has_target():    return conn.has_target()
def target_dead():   return conn.is_target_dead()
def target_boss():   return conn.is_target_boss()
def target_elite():  return conn.is_target_elite()
def friendly():      return conn.get_friendly_target()

# ══════════════════════════════════════════════════════════════
#  SPELLS — Info only, casting is in COMBAT section
# ══════════════════════════════════════════════════════════════

def spells():            return conn.get_spells()
def spell_names():       return conn.get_spell_names()
def spell_set():         return conn.get_spell_set()
def has_spell(name):     return conn.has_spell(name)
def spell_ready(name):   return conn.is_spell_ready(name)
def my_class():          return conn.detect_class()
def stacks():            return _state.stacks

# ══════════════════════════════════════════════════════════════
#  COMBAT — The good stuff
# ══════════════════════════════════════════════════════════════

def cast(name):
    """Cast a specific spell by name."""
    return _try_cast(name)


def cast_first(lst):
    """Cast the first available spell from a list."""
    for name in lst:
        if _try_cast(name):
            return name
    return None


def buff():
    """Apply all class buffs that need refreshing."""
    p = _load_profile()
    if not p:
        return False
    buffs = getattr(p, "BUFFS", [])
    info = getattr(p, "SPELL_INFO", {})
    casted = False
    for name in buffs:
        dur = info.get(name, {}).get("duration", 0)
        if _state.buff_needs_refresh(name, dur, 3.0):
            if _try_cast(name):
                _state.buff_timers[name] = _time.time()
                casted = True
    return casted


def pull():
    """
    Open a fight: apply buffs, gap close to target.
    Call this when you first engage.
    """
    p = _load_profile()
    if not p:
        return False

    _state.pulls += 1

    # Opener / buffs
    for name in getattr(p, "OPENER", getattr(p, "BUFFS", [])):
        _try_cast(name)
        _time.sleep(0.1)

    # Gap closer
    if has_target():
        for name in getattr(p, "GAP_CLOSERS", []):
            if _try_cast(name):
                break

    return True


def rotate():
    """
    Cast ONE spell from your rotation (priority order).
    Returns the spell name that was cast, or None.

    Use in a loop:
        while has_target() and not target_dead():
            rotate()
            wait(0.3)
    """
    p = _load_profile()
    if not p:
        return None

    # Update stack decay
    _state.decay(combat())

    # Refresh buffs
    buff()

    # Main rotation
    for name in getattr(p, "ROTATION", []):
        if _try_cast(name):
            return name

    return None


def nuke():
    """
    Dump all stacks into your nuke spell.
    For Berserker: Executioner's Blow at 20 stacks.
    Returns True if the nuke fired.
    """
    p = _load_profile()
    if not p:
        return False
    info = getattr(p, "SPELL_INFO", {})
    for name, data in info.items():
        if data.get("type") == "nuke":
            if _state.stacks >= data.get("min_stacks", 1):
                return _try_cast(name)
    return False


def defend():
    """
    Pop all defensive cooldowns.
    For Berserker: Undying Fury + Staggering Shout combo.
    Returns True if something was cast.
    """
    p = _load_profile()
    if not p:
        return False

    casted = False
    for name in getattr(p, "DEFENSIVE_SPELLS", []):
        if not _state.defensive_active(name):
            if _try_cast(name):
                _state.defensive_timers[name] = _time.time()
                info = _get_spell_info(name)
                extra = info.get("extra_damage_taken", 0)
                heal = info.get("heal_on_expiry", 0)
                if extra or heal:
                    log(f"🛡 {name} ACTIVE! +{extra*100:.0f}% dmg taken, heals {heal*100:.0f}% on expiry")
                casted = True

                # Defensive combo
                for combo_name in getattr(p, "DEFENSIVE_COMBO", []):
                    _try_cast(combo_name)
                break

    return casted


def fight():
    """
    Fight your current target until it dies.
    Handles rotation, buffs, defensives, stacks, everything.

        # Just select a target and call:
        fight()
    """
    if not has_target():
        return False

    p = _load_profile()
    if not p:
        # No profile — just spam whatever is ready
        while has_target() and not target_dead() and alive():
            for s in spell_names():
                if _try_cast(s):
                    break
            _time.sleep(0.3)
        return True

    tick = getattr(p, "TICK_RATE", 0.3)
    def_hp = getattr(p, "DEFENSIVE_HP", 40)
    def_trigger = getattr(p, "DEFENSIVE_TRIGGER_HP", 20)
    info = getattr(p, "SPELL_INFO", {})

    # Pull sequence
    pull()
    _time.sleep(tick)

    # Main fight loop
    while has_target() and not target_dead() and alive():
        _state.decay(combat())

        my_hp = hp()

        # Defensive check
        if my_hp < def_trigger:
            defend()
        elif my_hp < def_hp:
            # Try heals if we have them
            for name in getattr(p, "HEAL_SPELLS", []):
                if _try_cast(name):
                    break

        # Check for AoE mode
        aoe_thresh = getattr(p, "AOE_THRESHOLD", 3)
        if enemy_count() >= aoe_thresh:
            for name in getattr(p, "AOE_SPELLS", []):
                if _try_cast(name):
                    break
            else:
                rotate()
        else:
            # Normal rotation
            rotate()

        # Buff safety warnings
        for buff_name, safety in getattr(p, "BUFF_SAFETY", {}).items():
            warn_hp = safety.get("warn_hp_below", 0)
            warn_time = safety.get("warn_before_expiry", 2.0)
            dur = info.get(buff_name, {}).get("duration", 0)
            if dur > 0 and buff_name in _state.buff_timers:
                remaining = dur - (_time.time() - _state.buff_timers[buff_name])
                if 0 < remaining < warn_time and my_hp < warn_hp:
                    log(f"⚠ {buff_name} expiring! {safety.get('danger', '')}")

        _time.sleep(tick)

    # Target died
    if has_target() and target_dead():
        _state.kills += 1

    return True


def fight_loop(rest_after=True, loot_after=True):
    """
    Fight → loot → rest → repeat. Forever.
    Stop the script to stop fighting.

        fight_loop()
    """
    log(f"⚔ Fight loop started — {my_class()}")
    _state.session_start = _time.time()

    while alive():
        # Wait for target
        while not has_target() or target_dead():
            if not alive():
                return
            _time.sleep(0.5)

        # Fight
        fight()

        # Loot
        if loot_after:
            _time.sleep(0.5)
            loot()

        # Rest
        if rest_after:
            recover()

        _time.sleep(0.3)


# ══════════════════════════════════════════════════════════════
#  LOOT
# ══════════════════════════════════════════════════════════════

def loot():
    """Loot everything. Finds corpses, opens them, takes items."""
    return conn.auto_loot()

def loot_nearest():
    """Find the closest corpse and loot it."""
    return conn.loot_nearest()

def has_loot():
    """Is a loot window currently open?"""
    return conn.has_loot_window()

def loot_items():
    """What's in the loot window?"""
    return conn.get_loot_window_items()

# ══════════════════════════════════════════════════════════════
#  GATHERING
# ══════════════════════════════════════════════════════════════

def gather(name, delay=3):
    """Full gather: interact + wait for bar + delay."""
    return conn.gather(name, delay)

def use(name):
    """Start interacting with something."""
    return conn.use_entity(name)

def progress():
    """Is a progress/gather bar active?"""
    return conn.has_progress()

def wait_progress(t=30):
    """Wait until the progress bar finishes."""
    return conn.wait_progress(t)

def nodes():
    """All harvestable nodes nearby."""
    return conn.scan_harvestable()

def closest_node(name=None):
    """Closest gathering node, optionally filtered by name."""
    all_nodes = nodes()
    if name:
        n = name.lower()
        all_nodes = [e for e in all_nodes if n in e.get("name", "").lower()]
    if not all_nodes:
        return None
    px, py, _ = pos()
    return min(all_nodes,
               key=lambda e: _math.sqrt((float(e.get("x", 0)) - px) ** 2 +
                                         (float(e.get("y", 0)) - py) ** 2))

# ══════════════════════════════════════════════════════════════
#  NEARBY / ENTITIES
# ══════════════════════════════════════════════════════════════

def nearby():           return conn.get_nearby()
def nearby_mobs():      return conn.get_nearby_mobs()
def nearby_names():     return conn.get_nearby_names()
def nearby_count():     return conn.get_nearby_count()
def find(name):         return conn.find_nearby(name)
def closest(name=None): return conn.find_closest_nearby(name)

def enemies(range_limit=10):
    """Hostile living mobs within range."""
    mobs = nearby_mobs()
    if not mobs:
        return []
    px, py, _ = pos()
    return [m for m in mobs
            if m.get("hp", 0) > 0
            and not m.get("static")
            and _math.sqrt((float(m.get("x", 0)) - px) ** 2 +
                           (float(m.get("y", 0)) - py) ** 2) < range_limit]

def enemy_count(range_limit=10):
    """How many enemies within range."""
    return len(enemies(range_limit))

def scene():            return conn.get_scene()
def scene_count():      return conn.get_scene_count()
def find_scene(name):   return conn.find_in_scene(name)
def corpses():          return conn.get_scene_corpses()

# ══════════════════════════════════════════════════════════════
#  INVENTORY
# ══════════════════════════════════════════════════════════════

def items():             return conn.get_inventory()
def item_count():        return conn.get_inv_count()
def item_names():        return conn.get_item_names()
def has(name):           return conn.has_item(name)
def count_item(name):    return conn.count_item(name)
def find_item(name):     return conn.find_item(name)
def equipped():          return conn.get_equipped()

# ══════════════════════════════════════════════════════════════
#  REST & RECOVERY
# ══════════════════════════════════════════════════════════════

def rest():
    """Sit down and rest. Returns when done or interrupted."""
    if combat():
        return False
    return conn.cast("Rest")

def meditate():
    """Meditate for faster MP recovery."""
    if combat():
        return False
    return conn.cast("Leyline Meditation")

def heal(threshold=50):
    """Cast heal if HP below threshold. Uses profile heal spells."""
    if hp() >= threshold:
        return False
    p = _load_profile()
    if p:
        for name in getattr(p, "HEAL_SPELLS", []):
            if _try_cast(name):
                return True
    return False

def recover(hp_target=90, mp_target=80, timeout=60):
    """
    Rest until HP and MP are above targets.
    Handles meditation for MP, rest for HP.

        recover()           # Default: 90% HP, 80% MP
        recover(100, 100)   # Full recovery
    """
    if combat():
        conn.wait_until_out_of_combat(30)

    start = _time.time()
    while _time.time() - start < timeout:
        if hp() >= hp_target and mp() >= mp_target:
            return True
        if combat():
            return False

        # Don't interrupt existing channel
        if progress():
            _time.sleep(1)
            continue

        # MP first (meditation is faster)
        if mp() < mp_target:
            p = _load_profile()
            med = getattr(p, "MEDITATION_SPELL", "Leyline Meditation") if p else "Leyline Meditation"
            if spell_ready(med):
                conn.cast(med)
                _time.sleep(1)
                continue

        # HP
        if hp() < hp_target:
            p = _load_profile()
            rest_spell = getattr(p, "REST_SPELL", "Rest") if p else "Rest"
            if spell_ready(rest_spell):
                conn.cast(rest_spell)
                _time.sleep(1)
                continue

        _time.sleep(1)

    return hp() >= hp_target and mp() >= mp_target

# ══════════════════════════════════════════════════════════════
#  WAIT / FLOW CONTROL
# ══════════════════════════════════════════════════════════════

def wait(s):             _time.sleep(s)
def wait_combat_end(t=60): return conn.wait_until_out_of_combat(t)
def wait_hp(t=90):       return conn.wait_until_hp_above(t)
def wait_still(t=30):    return conn.wait_until_not_moving(t)
def wait_dead(t=120):    return conn.wait_until_target_dead(t)
def wait_spell(name, t=30): return conn.wait_for_spell_ready(name, t)

# ══════════════════════════════════════════════════════════════
#  CAMERA
# ══════════════════════════════════════════════════════════════

def camera():   return conn.get_camera()
def zoom():     return conn.get_camera_distance()
def angle():    return conn.get_camera_angle()
def pitch():    return conn.get_camera_pitch()

# ═════════════════════════��════════════════════════════════════
#  SYSTEM
# ══════════════════════════════════════════════════════════════

def gold():      return conn.get_gold()
def food():      return conn.get_food()
def all_stats(): return conn.get_all()
def ping():      return conn.ping()

def log(msg):
    """Print to the dashboard log."""
    print(msg)

def stats():
    """Print combat session stats."""
    elapsed = _time.time() - _state.session_start
    mins = max(elapsed / 60, 0.01)
    log("")
    log("═" * 45)
    log(f"  SESSION: {mins:.1f} min")
    log(f"  Kills: {_state.kills}  ({_state.kills / mins:.1f}/min)")
    log(f"  Deaths: {_state.deaths}")
    log(f"  Casts: {_state.total_casts}")
    if _state.cast_counts:
        log("")
        for name, count in sorted(_state.cast_counts.items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            log(f"  {name:<22} {count:>4}x {bar}")
    log("═" * 45)