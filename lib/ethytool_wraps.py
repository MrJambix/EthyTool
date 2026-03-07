"""
EthyTool Wraps — Script-facing function calls only.
All logic lives in ethytool_lib.py.
"""

import math as _math
from pathlib import Path as _Path

conn = None  # Set by ScriptRunner or bootstrap

# ── PLAYER ────────────────────────────────────────────────
def hp():           return conn.get_hp()
def mp():           return conn.get_mp()
def max_hp():       return conn.get_max_hp()
def max_mp():       return conn.get_max_mp()
def alive():        return conn.is_alive()
def low_hp(t=30):   return conn.is_low_hp(t)
def low_mp(t=20):   return conn.is_low_mp(t)

# ── POSITION & MOVEMENT ──────────────────────────────────
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
def dist(tx, ty):   return conn.distance_to(tx, ty)
def near(tx, ty, r=5): return conn.is_near(tx, ty, r)

# ── TARGET ────────────────────────────────────────────────
def target():        return conn.get_target()
def target_hp():     return conn.get_target_hp()
def target_name():   return conn.get_target_name()
def has_target():    return conn.has_target()
def target_dead():   return conn.is_target_dead()
def target_boss():   return conn.is_target_boss()
def target_elite():  return conn.is_target_elite()
def friendly():      return conn.get_friendly_target()
def friendly_hp():   return conn.get_friendly_hp()

# ── PARTY ─────────────────────────────────────────────────
def party():            return conn.get_party()
def party_count():      return conn.get_party_count()
def in_party():         return conn.in_party()
def party_hp():         return conn.get_party_hp()
def party_alive():      return conn.get_party_alive()
def party_dead():       return conn.get_party_dead()
def party_in_range():   return conn.get_party_in_range()
def lowest_party(include_self=True): return conn.get_lowest_party(include_self)
def party_below(threshold):          return conn.get_party_below(threshold)
def target_party(name_or_index):     return conn.target_party(name_or_index)

# ── SPELLS ────────────────────────────────────────────────
def spells():            return conn.get_spells()
def spell_names():       return conn.get_class_spells()
def spell_set():         return conn.get_spell_set()
def has_spell(name):     return conn.has_spell(name)
def spell_ready(name):   return conn.is_spell_ready(name)
def stacks():            return conn.state.stacks
def my_class():          return conn.detect_class()
def class_spells():      return conn.get_class_spells()

# ── COMBAT ────────────────────────────────────────────────
def cast(name):          return conn.try_cast(name)
def cast_first(lst):
    for name in lst:
        if conn.try_cast(name): return name
    return None
def buff():              return conn.do_buff()
def pull():              return conn.do_pull()
def rotate():            return conn.do_rotate()
def nuke():              return conn.do_nuke()
def defend():            return conn.do_defend()
def fight():             return conn.do_fight()
def fight_loop(rest_after=True, loot_after=True):
    return conn.do_fight_loop(rest_after, loot_after)

# ── HEAL COMBAT ───────────────────────────────────────────
def heal_target():       return conn.do_heal_target()
def heal_party():        return conn.do_heal_party()
def shield_party():      return conn.do_shield_party()
def dps_weave():         return conn.do_dps_weave()
def heal_loop(dps_when_safe=True):
    return conn.do_heal_loop(dps_when_safe)

# ── LOOT ──────────────────────────────────────────────────
def loot():          return conn.auto_loot()
def loot_nearest():  return conn.loot_nearest()
def has_loot():      return conn.has_loot_window()
def loot_items():    return conn.get_loot_window_items()

# ── GATHERING ─────────────────────────────────────────────
def gather(name, delay=3): return conn.gather(name, delay)
def use(name):              return conn.use_entity(name)
def progress():             return conn.has_progress()
def wait_progress(t=30):    return conn.wait_progress(t)
def nodes():                return conn.scan_harvestable()
def closest_node(name=None):
    all_n = nodes()
    if name:
        n = name.lower()
        all_n = [e for e in all_n if n in e.get("name", "").lower()]
    if not all_n: return None
    px, py, _ = pos()
    return min(all_n, key=lambda e: _math.sqrt(
        (float(e.get("x", 0)) - px) ** 2 + (float(e.get("y", 0)) - py) ** 2))

# ── ENTITIES ──────────────────────────────────────────────
def nearby():           return conn.get_nearby()
def nearby_mobs():      return conn.get_nearby_mobs()
def nearby_names():     return conn.get_nearby_names()
def nearby_count():     return conn.get_nearby_count()
def find(name):         return conn.find_nearby(name)
def closest(name=None): return conn.find_closest_nearby(name)
def enemies(r=10):      return conn.get_enemies(r)
def enemy_count(r=10):  return conn.get_enemy_count(r)
def scene():            return conn.get_scene()
def scene_count():      return conn.get_scene_count()
def find_scene(name):   return conn.find_in_scene(name)
def corpses():          return conn.get_scene_corpses()

# ── INVENTORY ─────────────────────────────────────────────
def items():             return conn.get_inventory()
def item_count():        return conn.get_inv_count()
def item_names():        return conn.get_item_names()
def has(name):           return conn.has_item(name)
def count_item(name):    return conn.count_item(name)
def find_item(name):     return conn.find_item(name)
def equipped():          return conn.get_equipped()

# ── REST & RECOVERY ───────────────────────────────────────
def rest():              return conn.try_cast_ooc("Rest")
def meditate():          return conn.try_cast_ooc("Leyline Meditation")
def heal(threshold=50):
    if hp() >= threshold: return False
    p = conn.load_profile()
    if p:
        for name in getattr(p, "HEAL_SPELLS", []):
            if conn.try_cast(name): return True
    return False
def recover(hp_t=90, mp_t=80, t=60): return conn.do_recover(hp_t, mp_t, t)

# ── WAIT ──────────────────────────────────────────────────
def wait(s):                 import time; time.sleep(s)
def wait_combat_end(t=60):   return conn.wait_until_out_of_combat(t)
def wait_hp(t=90):           return conn.wait_until_hp_above(t)
def wait_still(t=30):        return conn.wait_until_not_moving(t)
def wait_dead(t=120):        return conn.wait_until_target_dead(t)
def wait_spell(name, t=30):  return conn.wait_for_spell_ready(name, t)

# ── CAMERA ────────────────────────────────────────────────
def camera():   return conn.get_camera()
def zoom():     return conn.get_camera_distance()
def angle():    return conn.get_camera_angle()
def pitch():    return conn.get_camera_pitch()

# ── SYSTEM ────────────────────────────────────────────────
def gold():      return conn.get_gold()
def food():      return conn.get_food()
def all_stats(): return conn.get_all()
def ping():      return conn.ping()
def log(msg):    print(msg, flush=True)

def stats():
    s = conn.get_stats()
    mins = max(s["elapsed"] / 60, 0.01)
    log("")
    log("═" * 45)
    log(f"  SESSION: {mins:.1f} min")
    log(f"  Kills: {s['kills']}  ({s['kills'] / mins:.1f}/min)")
    log(f"  Deaths: {s['deaths']}")
    log(f"  Casts: {s['total_casts']}")
    if s["cast_counts"]:
        log("")
        for name, count in sorted(s["cast_counts"].items(), key=lambda x: -x[1]):
            bar = "█" * min(count, 20)
            log(f"  {name:<22} {count:>4}x {bar}")
    log("═" * 45)