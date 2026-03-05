"""
╔══════════════════════════════════════════════════════════════════════╗
║                     EthyTool Python Library v3.0                     ║
║                                                                      ║
║  Talks to the injected DLL inside Ethyrial via named pipe.           ║
║  Every function reads or does ONE thing.                             ║
║                                                                      ║
║  PLAYER:                                                             ║
║    conn.get_hp()              → 85.5   (health %)                    ║
║    conn.get_mp()              → 92.3   (mana %)                      ║
║    conn.get_max_hp()          → 4785                                 ║
║    conn.get_max_mp()          → 1011                                 ║
║    conn.get_current_hp()      → 4067                                 ║
║    conn.get_current_mp()      → 933                                  ║
║    conn.get_gold()            → 54321                                ║
║    conn.get_position()        → (4718.0, 1306.0, 1.0)               ║
║    conn.get_x() / get_y() / get_z()                                 ║
║    conn.get_speed()           → 4.5                                  ║
║    conn.get_attack_speed()    → 1.0                                  ║
║    conn.get_direction()       → 2                                    ║
║    conn.get_food()            → 85.0                                 ║
║    conn.get_infamy()          → 0.0                                  ║
║    conn.get_physical_armor()  → 45.0                                 ║
║    conn.get_magical_armor()   → 30.0                                 ║
║    conn.get_job()             → "Mining"                             ║
║    conn.in_combat()           → True / False                         ║
║    conn.is_moving()           → True / False                         ║
║    conn.is_frozen()           → True / False                         ║
║    conn.in_safe_zone()        → True / False                         ║
║    conn.in_wildlands()        → True / False                         ║
║    conn.is_spectating()       → True / False                         ║
║    conn.is_alive()            → True / False                         ║
║    conn.is_full_hp()          → True / False                         ║
║    conn.is_low_hp(30)         → True if HP below 30%                ║
║    conn.is_low_mp(20)         → True if MP below 20%                ║
║    conn.distance_to(x, y)     → 42.5                                ║
║    conn.is_near(x, y, 10)    → True if within 10 units              ║
║                                                                      ║
║  TARGET:                                                             ║
║    conn.has_target()          → True / False                         ║
║    conn.get_target()          → {"name":"Wolf", "hp":60, ...}       ║
║    conn.get_target_hp()       → 60.5                                 ║
║    conn.get_target_name()     → "Wolf"                               ║
║    conn.is_target_boss()      → True / False                         ║
║    conn.is_target_elite()     → True / False                         ║
║    conn.is_target_dead()      → True / False                         ║
║    conn.get_friendly_target() → {"name":"Healer", ...}              ║
║                                                                      ║
║  NEARBY ENTITIES:                                                    ║
║    conn.get_nearby()          → [{"name":"Wolf", ...}]              ║
║    conn.get_nearby_count()    → 12                                   ║
║    conn.get_nearby_mobs()     → only living entities with HP         ║
║    conn.get_nearby_names()    → ["Wolf", "Bear", "Trader"]          ║
║    conn.find_nearby("Wolf")   → first match or None                  ║
║    conn.count_nearby("Wolf")  → 3                                    ║
║                                                                      ║
║  SCENE ENTITIES:                                                     ║
║    conn.get_scene()           → [{"name":"Door", ...}]              ║
║    conn.get_scene_count()     → 250                                  ║
║    conn.get_scene_corpses()   → [{"uid":1234, ...}]                 ║
║    conn.find_in_scene("Chest")→ first match or None                  ║
║    conn.find_all_in_scene("Ore") → all matches                      ║
║                                                                      ║
║  ENTITY SCANNING (DLL-side, class-aware):                            ║
║    conn.scan_nearby()         → [{"class":"Doodad", ...}]           ║
║    conn.scan_scene()          → [{"class":"NPC", ...}]              ║
║    conn.scan_doodads()        → only Doodad class entities           ║
║    conn.scan_harvestable()    → full (non-hidden) doodads only       ║
║                                                                      ║
║  GATHERING / ENTITY INTERACTION:                                     ║
║    conn.use_entity("Stone")   → True if interaction started          ║
║    conn.has_progress()        → True if gather/cast bar active       ║
║    conn.wait_progress()       → blocks until bar finishes            ║
║    conn.gather("Stone")       → use + wait (full gather cycle)       ║
║                                                                      ║
║  SPELLS & CASTING:                                                   ║
║    conn.get_spells()          → [{"name":"Fireball", ...}]          ║
║    conn.get_spell_count()     → 8                                    ║
║    conn.get_spell_names()     → ["Fireball", "Heal", ...]           ║
║    conn.get_spell_set()       → {"fireball", "heal", ...} (lower)   ║
║    conn.has_spell("Heal")     → True / False                         ║
║    conn.is_spell_ready("Heal")→ True if off cooldown                 ║
║    conn.cast("Fireball")      → True if it worked                    ║
║    conn.cast_first(["A","B"]) → casts first available, returns name  ║
║    conn.detect_class()        → "Warrior" (from spell categories)    ║
║                                                                      ║
║  INVENTORY:                                                          ║
║    conn.get_inventory()       → [{"name":"Iron Ore", ...}]          ║
║    conn.get_inv_count()       → 24                                   ║
║    conn.get_equipped()        → [{"name":"Iron Sword", ...}]        ║
║    conn.get_item_names()      → ["Iron Ore", "Potion", ...]         ║
║    conn.has_item("Potion")    → True / False                         ║
║    conn.count_item("Ore")     → 47                                   ║
║    conn.find_item("Sword")    → first match or None                  ║
║                                                                      ║
║  LOOT:                                                               ║
║    conn.has_loot_window()     → True / False                         ║
║    conn.get_loot_window_count() → 1                                  ║
║    conn.get_loot_window_items() → [{"name":"Gold", ...}]            ║
║    conn.get_last_corpse()     → {"uid":1234, ...}                   ║
║    conn.has_corpse()          → True / False                         ║
║    conn.loot()                → True if looted                       ║
║    conn.open_corpse()         → True if corpse opened                ║
║    conn.list_corpses()        → [{"corpseOf":1234, ...}]            ║
║    conn.auto_loot()           → open + loot in one call              ║
║    conn.loot_nearest()        → find + open + loot nearest           ║
║                                                                      ║
║  CAMERA:                                                             ║
║    conn.get_camera()          → {"distance":12, ...}                ║
║    conn.get_camera_distance() → 12.0                                 ║
║    conn.get_camera_angle()    → 180.0                                ║
║    conn.get_camera_pitch()    → 52.0                                 ║
║                                                                      ║
║  BULK:                                                               ║
║    conn.get_all()             → {"hp":85, "gold":54321, ...}        ║
║                                                                      ║
║  WAIT HELPERS:                                                       ║
║    conn.heal_if_low("Heal", 50)                                     ║
║    conn.wait_until_out_of_combat()                                   ║
║    conn.wait_until_hp_above(90)                                      ║
║    conn.wait_until_not_moving()                                      ║
║    conn.wait_until_target_dead()                                     ║
║    conn.wait_for_spell_ready("Fireball")                             ║
║                                                                      ║
║  SYSTEM:                                                             ║
║    conn.ping()                → True if DLL alive                    ║
║    conn.init()                → (True, "OK")                        ║
║    conn.is_initialized()      → True / False                         ║
║    conn.get_version()         → "3.0.0"                              ║
║    conn.get_last_error()      → "" or error string                   ║
║    conn.dump_offsets()        → debug offset string                  ║
║    conn.dump_fields("Entity") → field dump for a class               ║
║    conn.dump_methods("Entity")→ method dump for a class              ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import time
import math
import threading


class EthyToolConnection:

    PIPE_NAME = r"\\.\pipe\EthyToolPipe"

    def __init__(self):
        self._handle = None
        self._kernel32 = None
        self._lock = threading.Lock()

    # ══════════════════════════════════════════════════════════════
    #  CONNECTION
    # ══════════════════════════════════════════════════════════════

    def connect(self, timeout=30):
        import ctypes
        import ctypes.wintypes
        self._kernel32 = ctypes.windll.kernel32

        GENERIC_READ = 0x80000000
        GENERIC_WRITE = 0x40000000
        OPEN_EXISTING = 3
        INVALID_HANDLE = ctypes.wintypes.HANDLE(-1).value
        PIPE_READMODE_MESSAGE = 0x00000002

        start = time.time()
        while time.time() - start < timeout:
            handle = self._kernel32.CreateFileW(
                self.PIPE_NAME,
                GENERIC_READ | GENERIC_WRITE,
                0, None, OPEN_EXISTING, 0, None
            )
            if handle != INVALID_HANDLE:
                mode = ctypes.wintypes.DWORD(PIPE_READMODE_MESSAGE)
                self._kernel32.SetNamedPipeHandleState(handle, ctypes.byref(mode), None, None)
                self._handle = handle
                return True
            time.sleep(0.5)
        return False

    def disconnect(self):
        if self._handle and self._kernel32:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None

    def _send(self, command):
        if not self._handle:
            return None
        import ctypes
        import ctypes.wintypes

        with self._lock:
            try:
                data = command.encode("utf-8")
                written = ctypes.wintypes.DWORD(0)
                ok = self._kernel32.WriteFile(self._handle, data, len(data), ctypes.byref(written), None)
                if not ok:
                    return None

                buf = ctypes.create_string_buffer(65536)
                read = ctypes.wintypes.DWORD(0)
                ok = self._kernel32.ReadFile(self._handle, buf, 65536, ctypes.byref(read), None)
                if not ok:
                    return None

                return buf.value[:read.value].decode("utf-8")
            except Exception:
                return None

    @property
    def connected(self):
        return self._handle is not None

    # ══════════════════════════════════════════════════════════════
    #  HEALTH & MANA
    # ══════════════════════════════════════════════════════════════

    def get_hp(self):
        """Your health as a percentage. 100.0 = full, 0.0 = dead."""
        return self._float(self._send("PLAYER_HP"))

    def get_mp(self):
        """Your mana as a percentage. 100.0 = full."""
        return self._float(self._send("PLAYER_MP"))

    def get_max_hp(self):
        """Your maximum health points (the actual number, not %)."""
        return self._int(self._send("PLAYER_MAX_HP"))

    def get_max_mp(self):
        """Your maximum mana points (the actual number, not %)."""
        return self._int(self._send("PLAYER_MAX_MP"))

    def get_current_hp(self):
        """Your current HP as an integer (max_hp * hp_pct / 100)."""
        max_hp = self.get_max_hp()
        hp_pct = self.get_hp()
        return int(max_hp * hp_pct / 100) if max_hp > 0 else 0

    def get_current_mp(self):
        """Your current MP as an integer (max_mp * mp_pct / 100)."""
        max_mp = self.get_max_mp()
        mp_pct = self.get_mp()
        return int(max_mp * mp_pct / 100) if max_mp > 0 else 0

    def is_alive(self):
        """Are you alive?"""
        return self.get_hp() > 0

    def is_full_hp(self):
        """Is your HP full (>= 99.9%)?"""
        return self.get_hp() >= 99.9

    def is_low_hp(self, threshold=30):
        """Is your HP below the threshold %?"""
        return self.get_hp() < threshold

    def is_low_mp(self, threshold=20):
        """Is your MP below the threshold %?"""
        return self.get_mp() < threshold

    # ══════════════════════════════════════════════════════════════
    #  POSITION & MOVEMENT
    # ══════════════════════════════════════════════════════════════

    def get_position(self):
        """Where you are in the world. Returns (x, y, z)."""
        r = self._send("PLAYER_POS")
        if not r:
            return (0.0, 0.0, 0.0)
        p = r.split(",")
        if len(p) < 3:
            return (0.0, 0.0, 0.0)
        return (float(p[0]), float(p[1]), float(p[2]))

    def get_x(self):
        return self.get_position()[0]

    def get_y(self):
        return self.get_position()[1]

    def get_z(self):
        return self.get_position()[2]

    def is_moving(self):
        """Are you currently walking/running?"""
        return self._send("PLAYER_MOVING") == "1"

    def is_frozen(self):
        """Are your controls frozen? (cutscene, loading, etc)"""
        return self._send("PLAYER_FROZEN") == "1"

    def get_speed(self):
        """Your current movement speed."""
        return self._float(self._send("PLAYER_SPEED"))

    def get_direction(self):
        """Which direction you're facing (number)."""
        return self._int(self._send("PLAYER_DIRECTION"))

    def distance_to(self, x, y):
        """Distance from you to a point."""
        px, py, _ = self.get_position()
        return math.sqrt((x - px) ** 2 + (y - py) ** 2)

    def is_near(self, x, y, radius=5):
        """Are you within radius of a point?"""
        return self.distance_to(x, y) <= radius

    # ══════════════════════════════════════════════════════════════
    #  COMBAT
    # ══════════════════════════════════════════════════════════════

    def in_combat(self):
        """Are you currently in combat?"""
        return self._send("PLAYER_COMBAT") == "1"

    def get_attack_speed(self):
        """Your current attack speed."""
        return self._float(self._send("PLAYER_ATTACK_SPEED"))

    def get_physical_armor(self):
        """Your total physical armor."""
        return self._float(self._send("PLAYER_PHYS_ARMOR"))

    def get_magical_armor(self):
        """Your total magical armor."""
        return self._float(self._send("PLAYER_MAG_ARMOR"))

    def cast(self, spell_name):
        """Cast a spell by name. Returns True if it worked."""
        r = self._send(f"CAST_{spell_name}")
        return r is not None and r.startswith("OK")

    def cast_first(self, spell_list):
        """Try to cast spells in order, return name of first that worked or None."""
        for spell in spell_list:
            if self.cast(spell):
                return spell
        return None

    # ══════════════════════════════════════════════════════════════
    #  TARGET
    # ══════════════════════════════════════════════════════════════

    def has_target(self):
        """Do you have something targeted?"""
        r = self._send("HOSTILE_TARGET")
        return r is not None and r not in ("NONE", "NOT_INITIALIZED")

    def get_target(self):
        """Get your current hostile target. Returns dict or None."""
        r = self._send("HOSTILE_TARGET")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return None
        return self._parse_kv(r)

    def get_target_hp(self):
        """Quick way to get your target's HP %. Returns 0 if no target."""
        t = self.get_target()
        return t.get("hp", 0.0) if t else 0.0

    def get_target_name(self):
        """Quick way to get your target's name."""
        t = self.get_target()
        return t.get("name", "") if t else ""

    def is_target_boss(self):
        t = self.get_target()
        return t.get("boss", False) if t else False

    def is_target_elite(self):
        t = self.get_target()
        return t.get("elite", False) if t else False

    def is_target_dead(self):
        return self.has_target() and self.get_target_hp() <= 0

    def get_friendly_target(self):
        """Get your friendly target. Returns dict or None."""
        r = self._send("FRIENDLY_TARGET")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return None
        return self._parse_kv(r)

    # ══════════════════════════════════════════════════════════════
    #  NEARBY ENTITIES
    # ══════════════════════════════════════════════════════════════

    def get_nearby_count(self):
        return self._int(self._send("NEARBY_COUNT"))

    def get_nearby(self):
        """All nearby entities. Returns list of dicts."""
        r = self._send("NEARBY_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def get_nearby_mobs(self):
        """Only living entities with HP."""
        r = self._send("NEARBY_LIVING")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def get_nearby_names(self):
        return [e.get("name", "") for e in self.get_nearby() if e.get("name")]

    def find_nearby(self, name):
        """Find first nearby entity matching name (case-insensitive)."""
        name_lower = name.lower()
        for e in self.get_nearby():
            if name_lower in e.get("name", "").lower():
                return e
        return None

    def count_nearby(self, name=None):
        entities = self.get_nearby()
        if name is None:
            return len(entities)
        name_lower = name.lower()
        return sum(1 for e in entities if name_lower in e.get("name", "").lower())

    def find_closest_nearby(self, name=None):
        """Find closest nearby entity, optionally filtered by name."""
        entities = self.get_nearby()
        if name:
            name_lower = name.lower()
            entities = [e for e in entities if name_lower in e.get("name", "").lower()]
        if not entities:
            return None
        px, py, _ = self.get_position()
        best, best_dist = None, float("inf")
        for e in entities:
            d = math.sqrt((e.get("x", 0) - px) ** 2 + (e.get("y", 0) - py) ** 2)
            if d < best_dist:
                best_dist, best = d, e
        return best

    # ═══════════��══════════════════════════════════════════════════
    #  SCENE ENTITIES
    # ══════════════════════════════════════════════════════════════

    def get_scene_count(self):
        return self._int(self._send("SCENE_COUNT"))

    def get_scene(self):
        r = self._send("SCENE_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED", "NO_ENTITY_MANAGER"):
            return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def get_scene_corpses(self):
        r = self._send("SCENE_CORPSES")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def find_in_scene(self, name):
        name_lower = name.lower()
        for e in self.get_scene():
            if name_lower in e.get("name", "").lower():
                return e
        return None

    def find_all_in_scene(self, name):
        name_lower = name.lower()
        return [e for e in self.get_scene() if name_lower in e.get("name", "").lower()]

    def find_closest_in_scene(self, name=None):
        entities = self.get_scene()
        if name:
            name_lower = name.lower()
            entities = [e for e in entities if name_lower in e.get("name", "").lower()]
        if not entities:
            return None
        px, py, _ = self.get_position()
        best, best_dist = None, float("inf")
        for e in entities:
            if e.get("hidden"):
                continue
            d = math.sqrt((e.get("x", 0) - px) ** 2 + (e.get("y", 0) - py) ** 2)
            if d < best_dist:
                best_dist, best = d, e
        return best

    # ══════════════════════════════════════════════════════════════
    #  ENTITY SCANNING (DLL-side, class-aware)
    # ══════════════════════════════════════════════════════════════

    def _parse_scan(self, r):
        if not r or r.startswith("NO_") or r.startswith("BAD_") or r.startswith("IL2CPP"):
            return []
        parts = r.split("###")
        results = []
        for p in parts[1:]:
            d = {}
            for kv in p.split("|"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    if v in ("0", "1"):
                        d[k] = v == "1"
                    else:
                        d[k] = v
            if d:
                results.append(d)
        return results

    def scan_nearby(self):
        """All nearby entities via DLL scanner."""
        return self._parse_scan(self._send("SCAN_NEARBY"))

    def scan_scene(self):
        """All scene entities via DLL scanner."""
        return self._parse_scan(self._send("SCAN_SCENE"))

    def scan_doodads(self):
        """Only Doodad-class entities from nearby scan."""
        return [e for e in self.scan_nearby() if e.get("class") == "Doodad"]

    def scan_harvestable(self, skip=None):
        """Full (non-hidden) doodad nodes. Optionally skip names."""
        if skip is None:
            skip = {"calm fog", "magic enchantment", "gravestone", "bush"}
        return [e for e in self.scan_doodads()
                if not e.get("hidden") and e.get("name", "").lower() not in skip]

    # ══════════════════════════════════════════════════════════════
    #  GATHERING / ENTITY INTERACTION
    # ══════════════════════════════════════════════════════════════

    def use_entity(self, name):
        """Interact with a nearby entity by name."""
        r = self._send(f"USE_ENTITY_{name}")
        if not r or not r.startswith("OK_USED"):
            return False
        return "invoke=0" in r

    def has_progress(self):
        """Is there an active progress bar?"""
        return self._send("HAS_PROGRESS") == "1"

    def wait_progress(self, timeout=30):
        """Wait for progress bar to start then finish."""
        consecutive = 0
        for _ in range(8):
            if self.has_progress():
                consecutive += 1
                if consecutive >= 2:
                    break
            else:
                consecutive = 0
            time.sleep(0.5)

        if consecutive < 2:
            time.sleep(12)
            return True

        for _ in range(timeout * 2):
            if not self.has_progress():
                return True
            time.sleep(0.5)
        return False

    def gather(self, name, post_delay=3):
        """Full gather cycle: use entity + wait for progress bar + post delay."""
        if not self.use_entity(name):
            return False
        done = self.wait_progress()
        time.sleep(post_delay)
        return done

    # ══════════════════════════════════════════════════════════════
    #  SPELLS & CASTING
    # ══════════════════════════════════════════════════════════════

    def get_spell_count(self):
        return self._int(self._send("SPELL_COUNT"))

    def get_spells(self):
        """All spells. Each dict has: name, display, cd, cur_cd, mana, range, cast, cat."""
        r = self._send("SPELLS_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(s) for s in r.split("###") if s.strip()]

    def get_spell_names(self):
        """Display names of all spells."""
        return [s.get("display", s.get("name", "")) for s in self.get_spells()]

    def get_spell_set(self):
        """Set of all spell names (lowercased) for fast lookup."""
        names = set()
        for s in self.get_spells():
            n = s.get("name", "")
            d = s.get("display", "")
            if n:
                names.add(n)
                names.add(n.lower())
            if d:
                names.add(d)
                names.add(d.lower())
        return names

    def has_spell(self, name):
        name_lower = name.lower()
        return any(
            name_lower in s.get("display", "").lower() or
            name_lower in s.get("name", "").lower()
            for s in self.get_spells()
        )

    def is_spell_ready(self, name):
        name_lower = name.lower()
        for s in self.get_spells():
            if (name_lower in s.get("display", "").lower() or
                name_lower in s.get("name", "").lower()):
                return s.get("cur_cd", 0) <= 0
        return False

    def detect_class(self):
        """Detect player class from spell categories."""
        spells = self.get_spells()
        cat_count = {}
        skip_cats = {"Misc", "Pets", "Light", "Shadow", ""}
        for s in spells:
            cat = s.get("cat", "Misc")
            if cat not in skip_cats:
                cat_count[cat] = cat_count.get(cat, 0) + 1
        if cat_count:
            return max(cat_count, key=cat_count.get)
        return "Unknown"

    def filter_available(self, spell_list):
        """Filter a list of spell names to only ones the player has."""
        known = self.get_spell_set()
        return [s for s in spell_list if s in known]

    # ══════════════════════════════════════════════════════════════
    #  INVENTORY
    # ══════════════════════════════════════════════════════════════

    def get_inv_count(self):
        return self._int(self._send("INV_COUNT"))

    def get_inventory(self):
        r = self._send("INV_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(i) for i in r.split("###") if i.strip()]

    def get_equipped(self):
        r = self._send("EQUIPPED")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(i) for i in r.split("###") if i.strip()]

    def get_item_names(self):
        return [i.get("name", "") for i in self.get_inventory() if i.get("name")]

    def has_item(self, name):
        name_lower = name.lower()
        return any(name_lower in i.get("name", "").lower() for i in self.get_inventory())

    def count_item(self, name):
        name_lower = name.lower()
        total = 0
        for i in self.get_inventory():
            if name_lower in i.get("name", "").lower():
                total += i.get("stack", 1)
        return total

    def find_item(self, name):
        name_lower = name.lower()
        for i in self.get_inventory():
            if name_lower in i.get("name", "").lower():
                return i
        return None

    # ══════════════════════════════════════════════════════════════
    #  LOOT
    # ══════════════════════════════════════════════════════════════

    def get_loot_window_count(self):
        return self._int(self._send("LOOT_WINDOW_COUNT"))

    def get_loot_window_items(self):
        r = self._send("LOOT_WINDOW_ITEMS")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        return [self._parse_kv(i) for i in r.split("###") if i.strip()]

    def has_loot_window(self):
        return self.get_loot_window_count() > 0

    def get_last_corpse(self):
        r = self._send("LAST_CORPSE")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return None
        return self._parse_kv(r)

    def has_corpse(self):
        return self.get_last_corpse() is not None

    def loot(self):
        """Loot all open container windows."""
        r = self._send("LOOT_ALL")
        return r is not None and r.startswith("OK")

    def open_corpse(self):
        """Open the nearest corpse."""
        r = self._send("OPEN_CORPSE")
        return r is not None and r.startswith("OK")

    def list_corpses(self):
        r = self._send("LIST_CORPSES")
        if not r or r == "NONE":
            return []
        results = []
        for part in r.split("###"):
            d = {}
            for kv in part.split("|"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    try:
                        d[k] = int(v)
                    except ValueError:
                        d[k] = v
            if d:
                results.append(d)
        return results

    def auto_loot(self):
        """Open nearest corpse + loot all in one call."""
        r = self._send("AUTO_LOOT")
        return r is not None and "OK" in r

    def loot_nearest(self):
        """Find nearest corpse, open it, loot it."""
        r = self._send("LOOT_NEAREST")
        return r is not None and r.startswith("OK")

    # ══════════════════════════════════════════════════════════════
    #  GOLD & STATUS
    # ══════════════════════════════════════════════════════════════

    def get_gold(self):
        return self._int(self._send("PLAYER_GOLD"))

    def get_infamy(self):
        return self._float(self._send("PLAYER_INFAMY"))

    def get_food(self):
        return self._float(self._send("PLAYER_FOOD"))

    def get_job(self):
        r = self._send("PLAYER_JOB")
        return r if r and r != "NOT_INITIALIZED" else ""

    def in_safe_zone(self):
        return self._send("PLAYER_PZ_ZONE") == "1"

    def in_wildlands(self):
        return self._send("PLAYER_WILDLANDS") == "1"

    def is_spectating(self):
        return self._send("PLAYER_SPECTATOR") == "1"

    # ══════════════════════════════════════════════════════════════
    #  CAMERA
    # ══════════════════════════════════════════════════════════════

    def get_camera(self):
        r = self._send("CAMERA")
        if not r or r == "NOT_INITIALIZED":
            return {}
        p = r.split(",")
        if len(p) < 6:
            return {}
        return {
            "x": float(p[0]), "y": float(p[1]), "z": float(p[2]),
            "distance": float(p[3]), "angle": float(p[4]), "pitch": float(p[5]),
        }

    def get_camera_distance(self):
        return self._float(self._send("CAMERA_DISTANCE"))

    def get_camera_angle(self):
        return self._float(self._send("CAMERA_ANGLE"))

    def get_camera_pitch(self):
        return self._float(self._send("CAMERA_PITCH"))

    # ══════════════════════════════════════════════════════════════
    #  COUNTS (legacy compat)
    # ═════════════════════════���════════════════════════════════════

    def get_entity_count(self):
        return self._int(self._send("ENTITY_COUNT"))

    def get_inventory_count(self):
        return self.get_inv_count()

    # ══════════════════════════════════════════════════════════════
    #  BULK READ
    # ══════════════════════════════════════════════════════════════

    def get_all(self):
        r = self._send("PLAYER_ALL")
        if not r or r == "NOT_INITIALIZED":
            return {}
        data = {}
        INT_KEYS = {"gold", "max_hp", "max_mp", "dir", "uid"}
        STR_KEYS = {"name", "job"}
        BOOL_KEYS = {
            "combat", "moving", "frozen", "pz", "spectator", "wildlands",
            "boss", "elite", "critter", "rare", "static", "hidden", "spawned"
        }
        for pair in r.split("|"):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            if k in STR_KEYS:
                data[k] = v
            elif k in BOOL_KEYS:
                data[k] = v == "1"
            elif k in INT_KEYS:
                try:
                    data[k] = int(v)
                except ValueError:
                    data[k] = v
            else:
                try:
                    data[k] = float(v)
                except ValueError:
                    data[k] = v
        return data

    # ══════════════════════════════════════════════════════════════
    #  WAIT HELPERS
    # ══════════════════════════════════════════════════════════════

    def heal_if_low(self, spell_name="Heal", threshold=50):
        if self.get_hp() < threshold:
            return self.cast(spell_name)
        return False

    def wait_until_out_of_combat(self, timeout=60, poll=0.5):
        start = time.time()
        while time.time() - start < timeout:
            if not self.in_combat():
                return True
            time.sleep(poll)
        return False

    def wait_until_hp_above(self, threshold=90, timeout=60, poll=0.5):
        start = time.time()
        while time.time() - start < timeout:
            if self.get_hp() >= threshold:
                return True
            time.sleep(poll)
        return False

    def wait_until_not_moving(self, timeout=30, poll=0.3):
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_moving():
                return True
            time.sleep(poll)
        return False

    def wait_until_target_dead(self, timeout=120, poll=0.5):
        start = time.time()
        while time.time() - start < timeout:
            if not self.has_target() or self.get_target_hp() <= 0:
                return True
            time.sleep(poll)
        return False

    def wait_for_spell_ready(self, spell_name, timeout=30, poll=0.3):
        start = time.time()
        while time.time() - start < timeout:
            if self.is_spell_ready(spell_name):
                return True
            time.sleep(poll)
        return False

    # ══════════════════════════════════════════════════════════════
    #  SYSTEM
    # ══════════════════════════════════════════════════════════════

    def ping(self):
        return self._send("PING") == "PONG"

    def init(self):
        resp = self._send("INIT")
        return resp == "OK", resp or "No response"

    def is_initialized(self):
        return self._send("IS_INIT") == "1"

    def get_version(self):
        return self._send("VERSION") or "unknown"

    def get_last_error(self):
        return self._send("ERROR") or ""

    def dump_offsets(self):
        return self._send("DUMP_OFFSETS") or ""

    def dump_fields(self, class_name):
        return self._send(f"DUMP_FIELDS_{class_name}") or ""

    def dump_methods(self, class_name):
        return self._send(f"DUMP_METHODS_{class_name}") or ""

    # ══════════════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _float(r):
        try:
            return float(r) if r else 0.0
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _int(r):
        try:
            return int(r) if r and r not in ("NOT_INITIALIZED",) else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _parse_kv(r):
        data = {}
        for pair in r.split("|"):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            if k in ("name", "display", "cat", "job"):
                data[k] = v
                continue
            NUMERIC_KEYS = (
                "uid", "stack", "rarity", "equip", "quality", "mana",
                "of", "cont", "max_hp", "max_mp", "dir", "idx"
            )
            if v in ("0", "1") and k not in NUMERIC_KEYS:
                data[k] = v == "1"
                continue
            try:
                data[k] = int(v)
            except ValueError:
                try:
                    data[k] = float(v)
                except ValueError:
                    data[k] = v
        return data


def create_connection():
    """Create a new connection. Used by the dashboard."""
    return EthyToolConnection()