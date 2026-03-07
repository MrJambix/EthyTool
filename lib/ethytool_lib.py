"""
EthyTool Library — All data + combat + party logic.
Scripts import this directly or use create_connection().
"""

import time
import math
import threading
import ctypes
import ctypes.wintypes
import importlib.util
from pathlib import Path


# ══════════════════════════════════════════════════════════════
#  Win32 setup
# ══════════════════════════════════════════════════════════════

_GENERIC_READ       = 0x80000000
_GENERIC_WRITE      = 0x40000000
_OPEN_EXISTING      = 3
_INVALID_HANDLE     = ctypes.wintypes.HANDLE(-1).value
_PIPE_READMODE_MSG  = 0x00000002
_TH32CS_SNAPPROCESS = 0x00000002

_k32 = ctypes.windll.kernel32

_k32.CreateFileW.argtypes = [
    ctypes.wintypes.LPCWSTR, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
    ctypes.c_void_p, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
    ctypes.wintypes.HANDLE,
]
_k32.CreateFileW.restype = ctypes.wintypes.HANDLE

_k32.WriteFile.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.wintypes.DWORD,
    ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.c_void_p,
]
_k32.WriteFile.restype = ctypes.wintypes.BOOL

_k32.ReadFile.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.c_void_p, ctypes.wintypes.DWORD,
    ctypes.POINTER(ctypes.wintypes.DWORD), ctypes.c_void_p,
]
_k32.ReadFile.restype = ctypes.wintypes.BOOL

_k32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
_k32.CloseHandle.restype = ctypes.wintypes.BOOL

_k32.SetNamedPipeHandleState.argtypes = [
    ctypes.wintypes.HANDLE, ctypes.POINTER(ctypes.wintypes.DWORD),
    ctypes.c_void_p, ctypes.c_void_p,
]
_k32.SetNamedPipeHandleState.restype = ctypes.wintypes.BOOL

_k32.CreateToolhelp32Snapshot.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]
_k32.CreateToolhelp32Snapshot.restype = ctypes.wintypes.HANDLE

_k32.Process32FirstW.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_void_p]
_k32.Process32FirstW.restype = ctypes.wintypes.BOOL

_k32.Process32NextW.argtypes = [ctypes.wintypes.HANDLE, ctypes.c_void_p]
_k32.Process32NextW.restype = ctypes.wintypes.BOOL


class _PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.wintypes.DWORD),
        ("cntUsage", ctypes.wintypes.DWORD),
        ("th32ProcessID", ctypes.wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID", ctypes.wintypes.DWORD),
        ("cntThreads", ctypes.wintypes.DWORD),
        ("th32ParentProcessID", ctypes.wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * 260),
    ]


def _find_game_pids():
    pids = []
    snapshot = _k32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
    if snapshot == _INVALID_HANDLE:
        return pids
    entry = _PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
    if _k32.Process32FirstW(snapshot, ctypes.byref(entry)):
        while True:
            if "ethyrial" in entry.szExeFile.lower():
                pids.append(entry.th32ProcessID)
            if not _k32.Process32NextW(snapshot, ctypes.byref(entry)):
                break
    _k32.CloseHandle(snapshot)
    return pids


def _try_connect_pipe(name):
    handle = _k32.CreateFileW(
        name, _GENERIC_READ | _GENERIC_WRITE,
        0, None, _OPEN_EXISTING, 0, None
    )
    if handle == _INVALID_HANDLE:
        return None
    mode = ctypes.wintypes.DWORD(_PIPE_READMODE_MSG)
    _k32.SetNamedPipeHandleState(handle, ctypes.byref(mode), None, None)
    return handle


# ══════════════════════════════════════════════════════════════
#  IGNORED SPELLS — NEVER auto-cast
# ══════════════════════════════════════════════════════════════

IGNORED_SPELLS = {
    "Summon Hallowed Ghost",
    "Siphon Shadow Energies",
    "Earthglow",
    "Light of the Keeper",
    "Hurry",
    "Leyline Meditation",
    "Rest",
    "Furious Charge",
}


# ══════════════════════════════════════════════════════════════
#  Combat State  (pure state tracking — no I/O, no profiles)
# ══════════════════════════════════════════════════════════════

class CombatState:
    def __init__(self):
        self.stacks = 0
        self.max_stacks = 20
        self.stack_decay_time = 8.0
        self.last_combat_time = time.time()
        self.last_gcd = 0
        self.gcd = 0.5
        self.buff_timers = {}
        self.defensive_timers = {}
        self.cast_counts = {}
        self.total_casts = 0
        self.kills = 0
        self.deaths = 0
        self.pulls = 0
        self.session_start = time.time()

    def gain_stacks(self, n=1):
        self.stacks = min(self.max_stacks, self.stacks + n)
        self.last_combat_time = time.time()

    def spend_stacks(self, n):
        if n == -1:
            spent = self.stacks; self.stacks = 0; return spent
        spent = min(self.stacks, n)
        self.stacks = max(0, self.stacks - n)
        return spent

    def decay(self, in_combat):
        if in_combat:
            self.last_combat_time = time.time()
        elif self.stacks > 0:
            if time.time() - self.last_combat_time > self.stack_decay_time:
                self.stacks = max(0, self.stacks - 1)
                self.last_combat_time = time.time()

    def on_gcd(self):
        return time.time() - self.last_gcd < self.gcd

    def trigger_gcd(self):
        self.last_gcd = time.time()

    def track_cast(self, name):
        self.cast_counts[name] = self.cast_counts.get(name, 0) + 1
        self.total_casts += 1

    def buff_active(self, name, duration):
        if name not in self.buff_timers: return False
        if duration <= 0: return True
        return time.time() - self.buff_timers[name] < duration

    def buff_needs_refresh(self, name, duration, refresh_before=3.0):
        if name not in self.buff_timers: return True
        if duration <= 0: return False
        remaining = duration - (time.time() - self.buff_timers[name])
        return remaining < refresh_before

    def defensive_active(self, name, duration=10):
        if name not in self.defensive_timers: return False
        return time.time() - self.defensive_timers[name] < duration


# ══════════════════════════════════════════════════════════════
#  Connection
# ══════════════════════════════════════════════════════════════

class EthyToolConnection:

    PIPE_BASE = r"\\.\pipe\EthyToolPipe"

    def __init__(self, pid=None):
        self._handle = None
        self._lock = threading.Lock()
        self._pid = pid
        self._pipe_name = f"{self.PIPE_BASE}_{pid}" if pid else None
        self._state = CombatState()
        self._profile_cache = None
        self._log_fn = lambda msg: print(msg, flush=True)

    @property
    def pid(self):
        return self._pid

    @property
    def pipe_name(self):
        return self._pipe_name

    @property
    def state(self):
        return self._state

    def set_log(self, fn):
        self._log_fn = fn

    def log(self, msg):
        self._log_fn(msg)

    # ──────────────────────────────────────────────────────────
    #  connect / disconnect / reconnect
    # ──────────────────────────────────────────────────────────

    def connect(self, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            if self._pid:
                self._pipe_name = f"{self.PIPE_BASE}_{self._pid}"
                handle = _try_connect_pipe(self._pipe_name)
                if handle:
                    self._handle = handle
                    return True
            else:
                handle = _try_connect_pipe(self.PIPE_BASE)
                if handle:
                    self._handle = handle
                    self._pipe_name = self.PIPE_BASE
                    self._pid = 0
                    return True
                for game_pid in _find_game_pids():
                    pipe = f"{self.PIPE_BASE}_{game_pid}"
                    handle = _try_connect_pipe(pipe)
                    if handle:
                        self._handle = handle
                        self._pipe_name = pipe
                        self._pid = game_pid
                        return True
            time.sleep(0.5)
        return False

    def disconnect(self):
        if self._handle:
            _k32.CloseHandle(self._handle)
            self._handle = None

    def reconnect(self, timeout=10):
        self.disconnect()
        return self.connect(timeout)

    @property
    def connected(self):
        return self._handle is not None

    # ──────────────────────────────────────────────────────────
    #  send / receive
    # ──────────────────────────────────────────────────────────

    def _send(self, command):
        if not self._handle:
            return None
        with self._lock:
            try:
                data = command.encode("utf-8")
                written = ctypes.wintypes.DWORD(0)
                ok = _k32.WriteFile(self._handle, data, len(data), ctypes.byref(written), None)
                if not ok: return None
                buf = ctypes.create_string_buffer(65536)
                read_bytes = ctypes.wintypes.DWORD(0)
                ok = _k32.ReadFile(self._handle, buf, 65536, ctypes.byref(read_bytes), None)
                if not ok: return None
                return buf.value[:read_bytes.value].decode("utf-8")
            except Exception:
                return None

    @staticmethod
    def find_all_pipes():
        results = []
        base = EthyToolConnection.PIPE_BASE
        results.append((0, base))
        for pid in _find_game_pids():
            results.append((pid, f"{base}_{pid}"))
        return results

    # ══════════════════════════════════════════════════════════════
    #  HEALTH & MANA
    # ══════════════��═══════════════════════════════════════════════

    def get_hp(self):         return self._float(self._send("PLAYER_HP"))
    def get_mp(self):         return self._float(self._send("PLAYER_MP"))
    def get_max_hp(self):     return self._int(self._send("PLAYER_MAX_HP"))
    def get_max_mp(self):     return self._int(self._send("PLAYER_MAX_MP"))
    def get_hp_pct(self):     return self.get_hp()
    def get_current_hp(self):
        mh = self.get_max_hp(); hp = self.get_hp()
        return int(mh * hp / 100) if mh > 0 else 0
    def get_current_mp(self):
        mm = self.get_max_mp(); mp = self.get_mp()
        return int(mm * mp / 100) if mm > 0 else 0
    def is_alive(self):       return self.get_hp() > 0
    def is_full_hp(self):     return self.get_hp() >= 99.9
    def is_low_hp(self, t=30): return self.get_hp() < t
    def is_low_mp(self, t=20): return self.get_mp() < t

    # ══════════════════════════════════════════════════════════════
    #  POSITION & MOVEMENT
    # ═══════════════════════��══════════════════════════════════════

    def get_position(self):
        r = self._send("PLAYER_POS")
        if not r: return (0.0, 0.0, 0.0)
        p = r.split(",")
        if len(p) < 3: return (0.0, 0.0, 0.0)
        return (float(p[0]), float(p[1]), float(p[2]))

    def get_x(self):           return self.get_position()[0]
    def get_y(self):           return self.get_position()[1]
    def get_z(self):           return self.get_position()[2]
    def is_moving(self):       return self._send("PLAYER_MOVING") == "1"
    def is_frozen(self):       return self._send("PLAYER_FROZEN") == "1"
    def get_speed(self):       return self._float(self._send("PLAYER_SPEED"))
    def get_direction(self):   return self._int(self._send("PLAYER_DIRECTION"))

    def move_to_target(self):
        r = self._send("MOVE_TO_TARGET")
        return r is not None and "OK" in r

    def stop_moving(self):
        r = self._send("STOP_MOVEMENT")
        return r is not None and "OK" in r

    def distance_to(self, x, y):
        px, py, _ = self.get_position()
        return math.sqrt((x - px) ** 2 + (y - py) ** 2)

    def is_near(self, x, y, radius=5):
        return self.distance_to(x, y) <= radius

    # ══════════════════════════════════════════════════════════════
    #  COMBAT
    # ══════════════════════════════════════════════════════════════

    def in_combat(self):       return self._send("PLAYER_COMBAT") == "1"
    def get_attack_speed(self): return self._float(self._send("PLAYER_ATTACK_SPEED"))
    def get_physical_armor(self): return self._float(self._send("PLAYER_PHYS_ARMOR"))
    def get_magical_armor(self):  return self._float(self._send("PLAYER_MAG_ARMOR"))

    def cast(self, spell_name):
        r = self._send(f"CAST_{spell_name}")
        return r is not None and r.startswith("OK")

    def cast_first(self, spell_list):
        for spell in spell_list:
            if self.cast(spell): return spell
        return None

       # ══════════════════════════════════════════════════════════════
    #  TARGET  (dedicated DLL commands — with garbage value guards)
    # ══════════════════════════════════════════════════════════════

    def has_target(self):
        r = self._send("HAS_TARGET")
        return r == "1"

    def get_target(self):
        """Full target info from TARGET_INFO, guarded against garbage values."""
        r = self._send("TARGET_INFO")
        if not r or r in ("NO_TARGET", "NO_PLAYER"):
            return None
        d = self._parse_kv(r)
        # Guard garbage floats from DLL memory bugs
        for key in ("hp", "max_hp", "dist"):
            val = d.get(key, 0)
            if isinstance(val, (int, float)):
                if abs(val) > 1e7 or val < -1:
                    d[key] = 0.0
        return d if d.get("name") else None

    def get_target_hp(self):
        r = self._send("TARGET_HP")
        if not r or r in ("NO_TARGET", "NO_PLAYER"):
            return 0.0
        try:
            val = float(r)
            # Guard: real HP is 0-100 pct or 0-999999 flat. Garbage is 1e+30.
            if abs(val) > 1e7:
                return 0.0
            return val
        except (ValueError, TypeError):
            return 0.0

    def get_target_name(self):
        r = self._send("TARGET_NAME")
        if not r or r in ("NO_TARGET", "NO_PLAYER", "UNKNOWN"):
            return ""
        return r

    def get_target_distance(self):
        r = self._send("TARGET_DISTANCE")
        if not r or r in ("NO_TARGET", "NO_PLAYER"):
            return 999.0
        try:
            val = float(r)
            # Guard: real distance is 0-500. Garbage is -1e+29.
            if val < 0 or val > 1e6:
                return 999.0
            return val
        except (ValueError, TypeError):
            return 999.0

    def get_target_info(self):
        """TARGET_INFO with garbage guards."""
        return self.get_target()

    def is_target_boss(self):
        t = self.get_target()
        return t.get("boss", False) if t else False

    def is_target_elite(self):
        t = self.get_target()
        return t.get("elite", False) if t else False

    def is_target_dead(self):
        """Check if target is dead. Since DLL returns garbage HP,
        we can only reliably know target EXISTS via HAS_TARGET.
        We CANNOT determine dead vs alive from HP alone.
        Returns False if HP is garbage-guarded to 0."""
        if not self.has_target():
            return False
        # Raw HP from pipe — check if it's a real zero or garbage
        r = self._send("TARGET_HP")
        if not r or r in ("NO_TARGET", "NO_PLAYER"):
            return False
        try:
            val = float(r)
            # Garbage values are huge (1e+30) or hugely negative
            # If garbage, we can't tell — assume alive
            if abs(val) > 1e7:
                return False
            # Real zero = actually dead
            return val <= 0
        except (ValueError, TypeError):
            return False

    def target_nearest(self):
        r = self._send("TARGET_NEAREST")
        if not r or "OK" not in r:
            return None
        for part in r.split("|"):
            if part.startswith("name="):
                return part.split("=", 1)[1]
        return "targeted"

    def get_friendly_target(self):
        r = self._send("FRIENDLY_TARGET")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return None
        return self._parse_kv(r)

    def get_friendly_hp(self):
        ft = self.get_friendly_target()
        return ft.get("hp", 0) if ft else 0

    # ══════════════════════════════════════════════════════════════
    #  PARTY
    # ══════════════════════════════════════════════════════════════

    def get_party(self):
        r = self._send("PARTY_ALL")
        if not r or r in ("NOT_IN_PARTY", "NOT_INITIALIZED", "NO_ENTITIES"):
            return []
        return [self._parse_kv(b) for b in r.split("###") if b.strip()]

    def get_party_count(self):    return self._int(self._send("PARTY_COUNT"))
    def in_party(self):           return self.get_party_count() > 1

    def get_party_hp(self):
        return {m.get("name", ""): m.get("hp", 0) for m in self.get_party() if m.get("name")}

    def get_party_alive(self):    return [m for m in self.get_party() if not m.get("dead")]
    def get_party_dead(self):     return [m for m in self.get_party() if m.get("dead")]
    def get_party_in_range(self): return [m for m in self.get_party() if m.get("in_range") and not m.get("dead")]

    def get_lowest_party(self, include_self=True):
        members = self.get_party_in_range()
        if not include_self:
            members = [m for m in members if not m.get("is_self")]
        if not members: return None
        return min(members, key=lambda m: m.get("hp", 100))

    def get_party_below(self, threshold):
        members = self.get_party_in_range()
        hurt = [m for m in members if m.get("hp", 100) < threshold]
        return sorted(hurt, key=lambda m: m.get("hp", 100))

    def target_party_member(self, index):
        r = self._send(f"TARGET_PARTY {index}")
        return r is not None and r.startswith("OK")

    def target_friendly_by_name(self, name):
        r = self._send(f"TARGET_FRIENDLY {name}")
        return r is not None and r.startswith("OK")

    def target_party(self, name_or_index):
        if isinstance(name_or_index, int):
            return self.target_party_member(name_or_index)
        return self.target_friendly_by_name(str(name_or_index))

    def set_friendly_target(self, name):
        return self.target_friendly_by_name(name)

    # ═══════════════════════���══════════════════════════════════════
    #  NEARBY ENTITIES
    # ══════════════════════════════════════════════════════════════

    def get_nearby_count(self): return self._int(self._send("NEARBY_COUNT"))

    def get_nearby(self):
        r = self._send("NEARBY_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def get_nearby_mobs(self):
        r = self._send("NEARBY_LIVING")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def get_nearby_names(self):
        return [e.get("name", "") for e in self.get_nearby() if e.get("name")]

    def find_nearby(self, name):
        nl = name.lower()
        for e in self.get_nearby():
            if nl in e.get("name", "").lower(): return e
        return None

    def count_nearby(self, name=None):
        ents = self.get_nearby()
        if name is None: return len(ents)
        nl = name.lower()
        return sum(1 for e in ents if nl in e.get("name", "").lower())

    def find_closest_nearby(self, name=None):
        ents = self.get_nearby()
        if name:
            nl = name.lower()
            ents = [e for e in ents if nl in e.get("name", "").lower()]
        if not ents: return None
        px, py, _ = self.get_position()
        best, best_dist = None, float("inf")
        for e in ents:
            d = math.sqrt((float(e.get("x", 0)) - px) ** 2 + (float(e.get("y", 0)) - py) ** 2)
            if d < best_dist: best_dist, best = d, e
        return best

    def get_enemies(self, range_limit=10):
        mobs = self.get_nearby_mobs()
        if not mobs: return []
        px, py, _ = self.get_position()
        return [m for m in mobs
                if m.get("hp", 0) > 0 and not m.get("static")
                and math.sqrt((float(m.get("x", 0)) - px) ** 2 +
                              (float(m.get("y", 0)) - py) ** 2) < range_limit]

    def get_enemy_count(self, range_limit=10):
        return len(self.get_enemies(range_limit))

    def scan_enemies(self):
        """Dedicated SCAN_ENEMIES DLL command — guarded against garbage distances."""
        r = self._send("SCAN_ENEMIES")
        if not r or r == "NONE":
            return []
        parts = r.split("###")
        if parts and parts[0].startswith("count="):
            parts = parts[1:]
        results = []
        for p in parts:
            d = {}
            for kv in p.split("|"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    d[k] = v
            if not d:
                continue
            # Guard garbage distance
            if "dist" in d:
                try:
                    dist_val = float(d["dist"])
                    if dist_val < 0 or dist_val > 1e6:
                        d["dist"] = "999"
                except (ValueError, TypeError):
                    d["dist"] = "999"
            results.append(d)
        return results

    # ══════════════════════════════════════════════════════════════
    #  SCENE ENTITIES
    # ══════════════════════════════════════════════════════════════

    def get_scene_count(self): return self._int(self._send("SCENE_COUNT"))

    def get_scene(self):
        r = self._send("SCENE_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED", "NO_ENTITY_MANAGER"): return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def get_scene_corpses(self):
        r = self._send("SCENE_CORPSES")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(e) for e in r.split("###") if e.strip()]

    def find_in_scene(self, name):
        nl = name.lower()
        for e in self.get_scene():
            if nl in e.get("name", "").lower(): return e
        return None

    def find_all_in_scene(self, name):
        nl = name.lower()
        return [e for e in self.get_scene() if nl in e.get("name", "").lower()]

    def find_closest_in_scene(self, name=None):
        ents = self.get_scene()
        if name:
            nl = name.lower()
            ents = [e for e in ents if nl in e.get("name", "").lower()]
        if not ents: return None
        px, py, _ = self.get_position()
        best, best_dist = None, float("inf")
        for e in ents:
            if e.get("hidden"): continue
            d = math.sqrt((float(e.get("x", 0)) - px) ** 2 + (float(e.get("y", 0)) - py) ** 2)
            if d < best_dist: best_dist, best = d, e
        return best

    # ══════════════════════════════════════════════════════════════
    #  ENTITY SCANNING
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
                    d[k] = (v == "1") if v in ("0", "1") else v
            if d: results.append(d)
        return results

    def scan_nearby(self):     return self._parse_scan(self._send("SCAN_NEARBY"))
    def scan_scene(self):      return self._parse_scan(self._send("SCAN_SCENE"))
    def scan_doodads(self):    return [e for e in self.scan_nearby() if e.get("class") == "Doodad"]

    def scan_harvestable(self, skip=None):
        if skip is None:
            skip = {"calm fog", "magic enchantment", "gravestone", "bush"}
        return [e for e in self.scan_doodads()
                if not e.get("hidden") and e.get("name", "").lower() not in skip]

    # ══════════════════════════════════════════════════════════════
    #  GATHERING
    # ══════════════════════════════════════════════════════════════

    def use_entity(self, name):
        r = self._send(f"USE_ENTITY_{name}")
        if not r or not r.startswith("OK_USED"): return False
        return "invoke=0" in r

    def has_progress(self):    return self._send("HAS_PROGRESS") == "1"

    def wait_progress(self, timeout=30):
        consecutive = 0
        for _ in range(8):
            if self.has_progress():
                consecutive += 1
                if consecutive >= 2: break
            else: consecutive = 0
            time.sleep(0.5)
        if consecutive < 2:
            time.sleep(12); return True
        for _ in range(timeout * 2):
            if not self.has_progress(): return True
            time.sleep(0.5)
        return False

    def gather(self, name, post_delay=3):
        if not self.use_entity(name): return False
        done = self.wait_progress()
        time.sleep(post_delay)
        return done

    def closest_node(self, name=None):
        all_n = self.scan_harvestable()
        if name:
            nl = name.lower()
            all_n = [e for e in all_n if nl in e.get("name", "").lower()]
        if not all_n: return None
        px, py, _ = self.get_position()
        return min(all_n, key=lambda e: math.sqrt(
            (float(e.get("x", 0)) - px) ** 2 + (float(e.get("y", 0)) - py) ** 2))

    # ══════════════════════════════════════════════════════════════
    #  SPELLS
    # ══════════════════════════════════════════════════════════════

    def get_spell_count(self): return self._int(self._send("SPELL_COUNT"))

    def get_spells(self):
        r = self._send("SPELLS_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(s) for s in r.split("###") if s.strip()]

    def get_spell_names(self):
        return [s.get("display", s.get("name", "")) for s in self.get_spells()]

    def get_spell_set(self):
        names = set()
        for s in self.get_spells():
            n = s.get("name", ""); d = s.get("display", "")
            if n: names.add(n); names.add(n.lower())
            if d: names.add(d); names.add(d.lower())
        return names

    def has_spell(self, name):
        nl = name.lower()
        return any(nl in s.get("display", "").lower() or nl in s.get("name", "").lower()
                   for s in self.get_spells())

    def is_spell_ready(self, name):
        nl = name.lower()
        for s in self.get_spells():
            if nl in s.get("display", "").lower() or nl in s.get("name", "").lower():
                return s.get("cur_cd", 0) <= 0
        return False

    def detect_class(self):
        spells = self.get_spells()
        cat_count = {}
        skip_cats = {"Misc", "Pets", "Light", "Shadow", ""}
        for s in spells:
            cat = s.get("cat", "Misc")
            if cat not in skip_cats:
                cat_count[cat] = cat_count.get(cat, 0) + 1
        return max(cat_count, key=cat_count.get) if cat_count else "Unknown"

    def filter_available(self, spell_list):
        known = self.get_spell_set()
        return [s for s in spell_list if s in known]

    def get_class_spells(self):
        return [s for s in self.get_spell_names() if s not in IGNORED_SPELLS]

    # ══════════════════════════════════════════════════════════════
    #  BUFFS & STACKS (from game)
    # ══════════════════════════════════════════════════════════════

    def get_fury_stacks(self):
        r = self._send("PLAYER_STACKS")
        if not r or "stacks=" not in r:
            return 0
        for part in r.split("|"):
            if part.startswith("stacks="):
                try:
                    return int(float(part.split("=", 1)[1]))
                except (ValueError, IndexError):
                    return 0
        return 0

    def get_player_buffs(self):
        """Get active buffs. Skips count header and debug dumps."""
        r = self._send("PLAYER_BUFFS")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return []
        if r.startswith("DEEP_DEBUG") or "dictPtr=" in r:
            return []
        parts = r.split("###")
        # Skip the count=N header if present
        if parts and parts[0].strip().startswith("count="):
            parts = parts[1:]
        results = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            d = self._parse_kv(p)
            if d and d.get("name"):
                results.append(d)
        return results

    def get_player_stacks(self):
        """Get active stack effects. Returns empty list if DLL doesn't support."""
        r = self._send("PLAYER_STACK_EFFECTS")
        if not r or r in ("NONE", "NOT_INITIALIZED", "UNKNOWN_CMD"):
            return []
        return [self._parse_kv(s) for s in r.split("###") if s.strip()]

    def has_buff(self, name):
        for b in self.get_player_buffs():
            if b.get("id") == name or b.get("name") == name:
                return True
        return False

    def get_buff_duration(self, name):
        for b in self.get_player_buffs():
            if b.get("id") == name or b.get("name") == name:
                return float(b.get("dur", 0))
        return 0.0

    # ══════════════════════════════════════════════════════════════
    #  STACK & HP RULES
    # ══════════════════════════════════════════════════════════════

    def check_stack_rules(self, name, stacks):
        p = self.load_profile()
        if not p:
            return True

        stack_rules = getattr(p, "STACK_RULES", {})
        info = self.get_spell_info(name)

        if name in stack_rules:
            rule = stack_rules[name]
            min_req = rule.get("min", 0)
            max_req = rule.get("max", 999)
            override = rule.get("override_at", -1)

            if stacks < min_req:
                return False
            if stacks > max_req and stacks != override:
                return False
            return True

        if info.get("min_stacks", 0) > 0 and stacks < info["min_stacks"]:
            return False

        return True

    def check_hp_rules(self, name, hp_pct):
        p = self.load_profile()
        if not p:
            return True

        hp_rules = getattr(p, "HP_RULES", {})
        if name not in hp_rules:
            return True

        rule = hp_rules[name]
        use_below = rule.get("use_below_hp", 100)
        if hp_pct > use_below:
            return False

        return True

    def get_priority_spell(self, stacks, hp_pct):
        p = self.load_profile()
        if not p:
            return None

        stack_rules = getattr(p, "STACK_RULES", {})
        hp_rules = getattr(p, "HP_RULES", {})

        candidates = []

        for name, rule in stack_rules.items():
            if "priority" not in rule:
                continue
            min_req = rule.get("min", 0)
            if stacks < min_req:
                continue
            if not self.is_spell_ready(name):
                continue
            if not self.check_hp_rules(name, hp_pct):
                continue

            prio = rule["priority"]

            sweet = rule.get("sweet_spot", 0)
            if sweet > 0 and stacks >= sweet:
                prio -= 0.5

            candidates.append((prio, name))

        for name, rule in hp_rules.items():
            prio_below = rule.get("priority_below", None)
            prefer_hp = rule.get("prefer_below_hp", 0)
            if prio_below and hp_pct < prefer_hp:
                if self.is_spell_ready(name):
                    candidates.append((prio_below, name))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # ══════════════════════════════════════════════════════════════
    #  INVENTORY
    # ══════════════════════════════════════════════════════════════

    def get_inv_count(self): return self._int(self._send("INV_COUNT"))

    def get_inventory(self):
        r = self._send("INV_ALL")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(i) for i in r.split("###") if i.strip()]

    def get_equipped(self):
        r = self._send("EQUIPPED")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(i) for i in r.split("###") if i.strip()]

    def get_item_names(self):
        return [i.get("name", "") for i in self.get_inventory() if i.get("name")]

    def has_item(self, name):
        nl = name.lower()
        return any(nl in i.get("name", "").lower() for i in self.get_inventory())

    def count_item(self, name):
        nl = name.lower()
        return sum(i.get("stack", 1) for i in self.get_inventory() if nl in i.get("name", "").lower())

    def find_item(self, name):
        nl = name.lower()
        for i in self.get_inventory():
            if nl in i.get("name", "").lower(): return i
        return None

    # ══════════════════════════════════════════════════════════════
    #  LOOT
    # ══════════════════════════════════════════════════════════════

    def get_loot_window_count(self): return self._int(self._send("LOOT_WINDOW_COUNT"))

    def get_loot_window_items(self):
        r = self._send("LOOT_WINDOW_ITEMS")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return []
        return [self._parse_kv(i) for i in r.split("###") if i.strip()]

    def has_loot_window(self):  return self.get_loot_window_count() > 0

    def get_last_corpse(self):
        r = self._send("LAST_CORPSE")
        if not r or r in ("NONE", "NOT_INITIALIZED"): return None
        return self._parse_kv(r)

    def has_corpse(self):       return self.get_last_corpse() is not None

    def loot_all(self):
        r = self._send("LOOT_ALL")
        return r is not None and r.startswith("OK")

    def open_corpse(self):
        r = self._send("OPEN_CORPSE")
        return r is not None and r.startswith("OK")

    def loot_corpse_window(self):
        r = self._send("LOOT_CORPSE_WINDOW")
        return r is not None and "OK" in r

    def loot(self):
        """Loot corpse window if open, fallback to auto_loot."""
        if self.loot_corpse_window():
            return True
        return self.auto_loot()

    def list_corpses(self):
        r = self._send("LIST_CORPSES")
        if not r or r == "NONE": return []
        results = []
        for part in r.split("###"):
            d = {}
            for kv in part.split("|"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    try: d[k] = int(v)
                    except ValueError: d[k] = v
            if d: results.append(d)
        return results

    def auto_loot(self):
        r = self._send("AUTO_LOOT")
        return r is not None and "OK" in r

    def loot_nearest(self):
        r = self._send("LOOT_NEAREST")
        return r is not None and r.startswith("OK")

    # ══════════════════════════════════════════════════════════════
    #  GOLD & STATUS
    # ══════════════════════════════════════════════════════════════

    def get_gold(self):        return self._int(self._send("PLAYER_GOLD"))
    def get_infamy(self):      return self._float(self._send("PLAYER_INFAMY"))
    def get_food(self):        return self._float(self._send("PLAYER_FOOD"))

    def get_job(self):
        r = self._send("PLAYER_JOB")
        return r if r and r != "NOT_INITIALIZED" else ""

    def in_safe_zone(self):    return self._send("PLAYER_PZ_ZONE") == "1"
    def in_wildlands(self):    return self._send("PLAYER_WILDLANDS") == "1"
    def is_spectating(self):   return self._send("PLAYER_SPECTATOR") == "1"

    # ══════════════════════════════════════════════════════════════
    #  CAMERA
    # ══════════════════════════════════════════════════════════════

    def get_camera(self):
        r = self._send("CAMERA")
        if not r or r == "NOT_INITIALIZED": return {}
        p = r.split(",")
        if len(p) < 6: return {}
        return {"x": float(p[0]), "y": float(p[1]), "z": float(p[2]),
                "distance": float(p[3]), "angle": float(p[4]), "pitch": float(p[5])}

    def get_camera_distance(self): return self._float(self._send("CAMERA_DISTANCE"))
    def get_camera_angle(self):    return self._float(self._send("CAMERA_ANGLE"))
    def get_camera_pitch(self):    return self._float(self._send("CAMERA_PITCH"))

    # ══════════════════════════════════════════════════════════════
    #  BULK READ
    # ══════════════════════════════════════════════════════════════

    def get_all(self):
        r = self._send("PLAYER_ALL")
        if not r or r == "NOT_INITIALIZED": return {}
        data = {}
        INT_KEYS = {"gold", "max_hp", "max_mp", "dir", "uid"}
        STR_KEYS = {"name", "job"}
        BOOL_KEYS = {"combat", "moving", "frozen", "pz", "spectator", "wildlands",
                     "boss", "elite", "critter", "rare", "static", "hidden", "spawned"}
        for pair in r.split("|"):
            if "=" not in pair: continue
            k, v = pair.split("=", 1)
            if k in STR_KEYS: data[k] = v
            elif k in BOOL_KEYS: data[k] = v == "1"
            elif k in INT_KEYS:
                try: data[k] = int(v)
                except ValueError: data[k] = v
            else:
                try: data[k] = float(v)
                except ValueError: data[k] = v
        return data

    # ══════════════════════════════════════════════════════════════
    #  WAIT HELPERS
    # ══════════════════════════════════════════════════════════════

    def wait(self, s):
        time.sleep(s)

    def wait_until_out_of_combat(self, timeout=60, poll=0.5):
        start = time.time()
        while time.time() - start < timeout:
            if not self.in_combat(): return True
            time.sleep(poll)
        return False

    def wait_until_hp_above(self, threshold=90, timeout=60, poll=0.5):
        start = time.time()
        while time.time() - start < timeout:
            if self.get_hp() >= threshold: return True
            time.sleep(poll)
        return False

    def wait_until_not_moving(self, timeout=30, poll=0.3):
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_moving(): return True
            time.sleep(poll)
        return False

    def wait_until_target_dead(self, timeout=120, poll=0.5):
        start = time.time()
        while time.time() - start < timeout:
            if not self.has_target() or self.get_target_hp() <= 0: return True
            time.sleep(poll)
        return False

    def wait_for_spell_ready(self, spell_name, timeout=30, poll=0.3):
        start = time.time()
        while time.time() - start < timeout:
            if self.is_spell_ready(spell_name): return True
            time.sleep(poll)
        return False

    # ══════════════════════════════════════════════════════════════
    #  SYSTEM
    # ══════════════════════════════════════════════════════════════

    def ping(self):            return self._send("PING") == "PONG"
    def init(self):
        resp = self._send("INIT")
        return resp == "OK", resp or "No response"
    def is_initialized(self):  return self._send("IS_INIT") == "1"
    def get_version(self):     return self._send("VERSION") or "unknown"
    def get_last_error(self):  return self._send("ERROR") or ""
    def dump_offsets(self):    return self._send("DUMP_OFFSETS") or ""
    def dump_fields(self, cn): return self._send(f"DUMP_FIELDS_{cn}") or ""
    def dump_methods(self, cn): return self._send(f"DUMP_METHODS_{cn}") or ""

    # ══════════════════════════════════════════════════════════════
    #  PROFILE LOADER
    # ══════════════════════════════════════════════════════════════

    def load_profile(self):
        if self._profile_cache is not None:
            return self._profile_cache
        detected = self.detect_class().lower().replace(" ", "_")
        if not detected or detected == "unknown": return None
        search = [
            Path(__file__).parent / "builds" / f"{detected}.py",
            Path(__file__).parent.parent / "builds" / f"{detected}.py",
            Path(__file__).parent / f"{detected}.py",
        ]
        for path in search:
            if path.exists():
                try:
                    spec = importlib.util.spec_from_file_location(detected, str(path))
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self._profile_cache = mod
                    self.log(f"Loaded build: {detected} from {path.name}")
                    return mod
                except Exception as e:
                    self.log(f"Failed to load {path}: {e}")
        return None

    def get_spell_info(self, name):
        p = self.load_profile()
        if not p: return {}
        return getattr(p, "SPELL_INFO", {}).get(name, {})

    # ══════════════════════════════════════════════════════════════
    #  INTERNAL CAST HELPERS
    # ══════════════════════════════════════════════════════════════

    def try_cast(self, name):
        if name in IGNORED_SPELLS:
            return False

        p = self.load_profile()
        if p and name in getattr(p, "IGNORED_SPELLS", set()):
            return False

        if self._state.on_gcd():
            return False
        if not self.is_spell_ready(name):
            return False

        info = self.get_spell_info(name)

        stacks = 0
        if p and getattr(p, "STACK_ENABLED", False):
            stacks = self.get_fury_stacks()
            if not self.check_stack_rules(name, stacks):
                return False

        if p:
            hp_pct = self.get_hp_pct()
            if not self.check_hp_rules(name, hp_pct):
                return False

        if info.get("channel") and self.is_moving():
            return False

        result = self.cast(name)
        if not result:
            return False

        self._state.trigger_gcd()
        self._state.track_cast(name)

        if p and getattr(p, "STACK_ENABLED", False):
            self._state.stacks = stacks
            cost = info.get("consumes_stacks", 0)
            if cost == -1:
                self._state.stacks = 0
            elif cost > 0:
                self._state.stacks = max(0, self._state.stacks - cost)

        dur = info.get("duration", 0)
        if dur > 0:
            self._state.buff_timers[name] = time.time()

        if info.get("cast_time", 0) > 0:
            time.sleep(info["cast_time"] + 0.1)

        return True

    def try_cast_emergency(self, name):
        if name in IGNORED_SPELLS: return False
        if self._state.on_gcd(): return False
        if not self.is_spell_ready(name): return False
        result = self.cast(name)
        if not result: return False
        self._state.trigger_gcd()
        self._state.track_cast(name)
        info = self.get_spell_info(name)
        dur = info.get("duration", 0)
        if dur > 0: self._state.buff_timers[name] = time.time()
        return True

    def try_cast_ooc(self, name):
        if self._state.on_gcd(): return False
        if self.in_combat(): return False
        if not self.is_spell_ready(name): return False
        result = self.cast(name)
        if not result: return False
        self._state.trigger_gcd()
        return True

    # ══════════════════════════════════════════════════════════════
    #  ROTATION
    # ══════════════════════════════════════════════════════════════

    def do_rotation(self):
        p = self.load_profile()
        if not p:
            return False

        stacks = 0
        hp_pct = self.get_hp_pct()

        if getattr(p, "STACK_ENABLED", False):
            stacks = self.get_fury_stacks()

            prio_spell = self.get_priority_spell(stacks, hp_pct)
            if prio_spell:
                if self.try_cast(prio_spell):
                    return True

        rotation = getattr(p, "ROTATION", [])
        for name in rotation:
            if self.try_cast(name):
                return True

        return False

    # ══════════════════════════════════════════════════════════════
    #  COMBAT ACTIONS
    # ══════════════════════════════════════════════════════════════

    def do_buff(self):
        p = self.load_profile()
        if not p: return False
        buffs = getattr(p, "BUFFS", [])
        info = getattr(p, "SPELL_INFO", {})
        config = getattr(p, "BUFF_CONFIG", {})
        casted = False
        for name in buffs:
            if name in IGNORED_SPELLS: continue
            spell = info.get(name, {})
            cfg = config.get(name, {})
            if cfg.get("permanent") or spell.get("permanent"):
                if name in self._state.buff_timers: continue
                if self.try_cast(name):
                    self._state.buff_timers[name] = time.time()
                    self.log(f"✓ Permanent buff: {name}")
                    casted = True
                continue
            recast = cfg.get("recast_interval", 0)
            if recast > 0:
                if name in self._state.buff_timers and time.time() - self._state.buff_timers[name] < recast:
                    continue
                if self.try_cast(name):
                    self._state.buff_timers[name] = time.time()
                    casted = True
                continue
            dur = cfg.get("duration", spell.get("duration", 0))
            if self._state.buff_needs_refresh(name, dur, 3.0):
                if self.try_cast(name):
                    self._state.buff_timers[name] = time.time()
                    casted = True
        return casted

    def do_pull(self):
        p = self.load_profile()
        if not p: return False
        self._state.pulls += 1
        for name in getattr(p, "OPENER", []):
            if name not in IGNORED_SPELLS:
                self.try_cast(name); time.sleep(0.1)
        if self.has_target():
            for name in getattr(p, "GAP_CLOSERS", []):
                if name not in IGNORED_SPELLS and self.try_cast(name): break
        return True

    def do_rotate(self):
        p = self.load_profile()
        if not p: return None
        self._state.decay(self.in_combat())
        self.do_buff()
        for name in getattr(p, "ROTATION", []):
            if name in IGNORED_SPELLS: continue
            if self.try_cast(name): return name
        return None

    def do_nuke(self):
        p = self.load_profile()
        if not p: return False
        for name, data in getattr(p, "SPELL_INFO", {}).items():
            if data.get("type") == "nuke" and self._state.stacks >= data.get("min_stacks", 1):
                return self.try_cast(name)
        return False

    def do_defend(self):
        p = self.load_profile()
        if not p: return False
        casted = False
        for name in getattr(p, "DEFENSIVE_SPELLS", []):
            if name in IGNORED_SPELLS: continue
            if not self._state.defensive_active(name):
                if self.try_cast_emergency(name):
                    self._state.defensive_timers[name] = time.time()
                    casted = True
                    for combo in getattr(p, "DEFENSIVE_COMBO", []):
                        if combo not in IGNORED_SPELLS:
                            self.try_cast_emergency(combo)
                    break
        return casted

    def do_fight(self):
        if not self.has_target(): return False
        p = self.load_profile()
        if not p:
            while self.has_target() and not self.is_target_dead() and self.is_alive():
                for s in self.get_class_spells():
                    if self.try_cast(s): break
                time.sleep(0.3)
            return True
        tick = getattr(p, "TICK_RATE", 0.3)
        def_hp_val = getattr(p, "DEFENSIVE_HP", 40)
        def_trigger = getattr(p, "DEFENSIVE_TRIGGER_HP", 20)
        heal_threshold = getattr(p, "HEAL_HP", 0)
        heal_priority = getattr(p, "HEAL_PRIORITY", {})
        self.do_pull()
        time.sleep(tick)
        while self.has_target() and not self.is_target_dead() and self.is_alive():
            self._state.decay(self.in_combat())
            my_hp = self.get_hp()
            if my_hp < def_trigger: self.do_defend()
            if heal_threshold > 0 and my_hp < heal_threshold:
                for name in getattr(p, "HEAL_SPELLS", []):
                    if name not in IGNORED_SPELLS:
                        thresh = heal_priority.get(name, heal_threshold)
                        if my_hp < thresh and self.try_cast(name): break
                time.sleep(tick); continue
            elif my_hp < def_hp_val:
                for name in getattr(p, "HEAL_SPELLS", []):
                    if name not in IGNORED_SPELLS and self.try_cast(name): break
            aoe_thresh = getattr(p, "AOE_THRESHOLD", 3)
            if self.get_enemy_count() >= aoe_thresh:
                for name in getattr(p, "AOE_SPELLS", []):
                    if name not in IGNORED_SPELLS and self.try_cast(name): break
                else: self.do_rotate()
            else: self.do_rotate()
            time.sleep(tick)
        if self.has_target() and self.is_target_dead():
            self._state.kills += 1
        return True

    def recover_between_pulls(self):
        p = self.load_profile()
        rest_hp = getattr(p, "REST_HP", 80) if p else 80
        rest_mp = getattr(p, "REST_MP", 60) if p else 60
        if self.get_hp() >= rest_hp and self.get_mp() >= rest_mp: return
        start = time.time()
        while time.time() - start < 30:
            if self.get_hp() >= rest_hp and self.get_mp() >= rest_mp: return
            if self.in_combat(): return
            if self.get_mp() < rest_mp:
                med = getattr(p, "MEDITATION_SPELL", "Leyline Meditation") if p else "Leyline Meditation"
                self.try_cast_ooc(med); time.sleep(1); continue
            if self.get_hp() < rest_hp:
                rest_sp = getattr(p, "REST_SPELL", "Rest") if p else "Rest"
                self.try_cast_ooc(rest_sp); time.sleep(1); continue
            time.sleep(1)

    def do_recover(self, hp_target=90, mp_target=80, timeout=60):
        if self.in_combat(): self.wait_until_out_of_combat(30)
        start = time.time()
        while time.time() - start < timeout:
            if self.get_hp() >= hp_target and self.get_mp() >= mp_target: return True
            if self.in_combat(): return False
            if self.has_progress(): time.sleep(1); continue
            if self.get_mp() < mp_target:
                p = self.load_profile()
                med = getattr(p, "MEDITATION_SPELL", "Leyline Meditation") if p else "Leyline Meditation"
                self.try_cast_ooc(med); time.sleep(1); continue
            if self.get_hp() < hp_target:
                p = self.load_profile()
                rest_sp = getattr(p, "REST_SPELL", "Rest") if p else "Rest"
                self.try_cast_ooc(rest_sp); time.sleep(1); continue
            time.sleep(1)
        return self.get_hp() >= hp_target and self.get_mp() >= mp_target

    def do_fight_loop(self, rest_after=True, loot_after=True):
        p = self.load_profile()
        cls = self.detect_class()
        self.log(f"⚔ Fight loop started — {cls}")
        if p:
            self.log(f"  Rotation: {', '.join(getattr(p, 'ROTATION', []))}")
            self.log(f"  Buffs: {', '.join(getattr(p, 'BUFFS', []))}")
            self.log(f"  Defensives: {', '.join(getattr(p, 'DEFENSIVE_SPELLS', []))}")
        self._state.session_start = time.time()
        self.do_buff()
        while self.is_alive():
            while not self.has_target() or self.is_target_dead():
                if not self.is_alive(): return
                time.sleep(0.5)
            self.do_fight()
            if loot_after: time.sleep(0.5); self.auto_loot()
            if rest_after and not self.in_combat(): self.recover_between_pulls()
            time.sleep(0.3)

    # ══════════════════════════════════════════════════════════════
    #  HEAL LOOP — Party healing
    # ══════════════════════════════════════════════════════════════

    def do_heal_target(self):
        p = self.load_profile()
        if not p: return False
        ft_hp = self.get_friendly_hp()
        for name in getattr(p, "HEAL_SPELLS", []):
            if name in IGNORED_SPELLS: continue
            thresh = getattr(p, "HEAL_PRIORITY", {}).get(name, 80)
            if ft_hp < thresh and self.try_cast(name): return True
        return False

    def do_heal_party(self):
        p = self.load_profile()
        if not p: return None
        heal_threshold = getattr(p, "HEAL_HP", 70)
        hurt = self.get_party_below(heal_threshold)
        if not hurt: return None
        member = hurt[0]
        name = member.get("name", "")
        member_hp = member.get("hp", 100)
        if not member.get("in_range"): return None
        idx = member.get("index", -1)
        if idx >= 0: self.target_party(idx)
        else: self.target_party(name)
        time.sleep(0.1)
        for spell_name in getattr(p, "HEAL_SPELLS", []):
            if spell_name in IGNORED_SPELLS: continue
            thresh = getattr(p, "HEAL_PRIORITY", {}).get(spell_name, heal_threshold)
            if member_hp < thresh and self.try_cast(spell_name):
                self.log(f"💚 {spell_name} → {name} ({member_hp:.0f}%)")
                return name
        return None

    def do_shield_party(self):
        p = self.load_profile()
        if not p: return None
        def_hp_val = getattr(p, "DEFENSIVE_HP", 40)
        hurt = self.get_party_below(def_hp_val)
        if not hurt: return None
        member = hurt[0]
        name = member.get("name", "")
        idx = member.get("index", -1)
        if idx >= 0: self.target_party(idx)
        else: self.target_party(name)
        time.sleep(0.1)
        for spell_name in getattr(p, "DEFENSIVE_SPELLS", []):
            if spell_name in IGNORED_SPELLS: continue
            if self.try_cast_emergency(spell_name):
                self.log(f"🛡 {spell_name} → {name}")
                return name
        return None

    def do_dps_weave(self):
        p = self.load_profile()
        if not p: return None
        heal_threshold = getattr(p, "HEAL_HP", 70)
        mana_conserve = getattr(p, "MANA_CONSERVE", 30)
        if self.get_party_below(heal_threshold): return None
        if self.get_mp() < mana_conserve: return None
        if not self.has_target() or self.is_target_dead(): return None
        for name in getattr(p, "ROTATION", []):
            if name in IGNORED_SPELLS: continue
            if self.try_cast(name): return name
        return None

    def do_heal_loop(self, dps_when_safe=True):
        p = self.load_profile()
        cls = self.detect_class()
        self.log(f"💚 Heal loop started — {cls}")
        if p:
            self.log(f"  Heals: {', '.join(getattr(p, 'HEAL_SPELLS', []))}")
            self.log(f"  Defensives: {', '.join(getattr(p, 'DEFENSIVE_SPELLS', []))}")
            self.log(f"  DPS: {', '.join(getattr(p, 'ROTATION', []))}")
        self._state.session_start = time.time()
        self.do_buff()
        tick = getattr(p, "TICK_RATE", 0.3) if p else 0.3
        heal_threshold = getattr(p, "HEAL_HP", 70) if p else 70
        emergency_hp = getattr(p, "EMERGENCY_HP", 25) if p else 25
        def_hp_val = getattr(p, "DEFENSIVE_HP", 40) if p else 40
        while self.is_alive():
            if self.in_combat():
                critical = self.get_party_below(emergency_hp)
                if critical:
                    self.do_shield_party(); self.do_heal_party()
                    time.sleep(tick); continue
                danger = self.get_party_below(def_hp_val)
                if danger: self.do_shield_party()
                hurt = self.get_party_below(heal_threshold)
                if hurt: self.do_heal_party(); time.sleep(tick); continue
                if self.get_hp() < heal_threshold:
                    members = self.get_party()
                    for m in members:
                        if m.get("is_self"):
                            self.target_party(m.get("index", 0)); break
                    time.sleep(0.1); self.do_heal_target()
                    time.sleep(tick); continue
                self.do_buff()
                if dps_when_safe: self.do_dps_weave()
            else:
                self.auto_loot()
                if self.get_hp() < 90 or self.get_mp() < 80:
                    self.recover_between_pulls()
            time.sleep(tick)

    # ══════════════════════════════════════════════════════════════
    #  STATS
    # ══════════════════════════════════════════════════════════════

    def get_stats(self):
        s = self._state
        elapsed = time.time() - s.session_start
        return {
            "elapsed": elapsed,
            "kills": s.kills,
            "deaths": s.deaths,
            "total_casts": s.total_casts,
            "cast_counts": dict(s.cast_counts),
            "pulls": s.pulls,
            "stacks": s.stacks,
        }

    def print_stats(self):
        s = self.get_stats()
        mins = max(s["elapsed"] / 60, 0.01)
        self.log("")
        self.log("═" * 45)
        self.log(f"  SESSION: {mins:.1f} min")
        self.log(f"  Kills: {s['kills']}  ({s['kills'] / mins:.1f}/min)")
        self.log(f"  Deaths: {s['deaths']}")
        self.log(f"  Casts: {s['total_casts']}")
        if s["cast_counts"]:
            self.log("")
            for name, count in sorted(s["cast_counts"].items(), key=lambda x: -x[1]):
                bar = "█" * min(count, 20)
                self.log(f"  {name:<22} {count:>4}x {bar}")
        self.log("═" * 45)

    # ══════════════════════════════════════════════════════════════
    #  INTERNAL HELPERS
    # ═════════���════════════════════════════════════════════════════

    @staticmethod
    def _float(r):
        try: return float(r) if r else 0.0
        except (ValueError, TypeError): return 0.0

    @staticmethod
    def _int(r):
        try: return int(r) if r and r not in ("NOT_INITIALIZED",) else 0
        except (ValueError, TypeError): return 0

    @staticmethod
    def _parse_kv(r):
        data = {}
        for pair in r.split("|"):
            if "=" not in pair: continue
            k, v = pair.split("=", 1)
            if k in ("name", "display", "cat", "job"): data[k] = v; continue
            NUMERIC_KEYS = ("uid", "stack", "rarity", "equip", "quality", "mana",
                           "of", "cont", "max_hp", "max_mp", "dir", "idx")
            if v in ("0", "1") and k not in NUMERIC_KEYS:
                data[k] = v == "1"; continue
            try: data[k] = int(v)
            except ValueError:
                try: data[k] = float(v)
                except ValueError: data[k] = v
        return data


def create_connection(pid=None):
    return EthyToolConnection(pid=pid)