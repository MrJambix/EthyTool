"""
╔══════════════════════════════════════════════════════════════╗
║                    EthyTool Python Library                   ║
║                                                              ║
║  Talks to the injected DLL inside Ethyrial.                  ║
║  Every function reads or does ONE thing.                     ║
║                                                              ║
║  USAGE IN SCRIPTS:                                           ║
║    conn.get_hp()          → 85.5  (your health %)            ║
║    conn.get_mp()          → 92.3  (your mana %)              ║
║    conn.get_gold()        → 54321                            ║
║    conn.get_position()    → (150.0, 42.0, 300.0)            ║
║    conn.in_combat()       → True / False                     ║
║    conn.cast("Fireball")  → True if cast worked              ║
║    conn.loot()            → True if looted                   ║
║                                                              ║
║  SCRIPT TEMPLATE:                                            ║
║    import time                                               ║
║    while not stop_event.is_set():                            ║
║        hp = conn.get_hp()                                    ║
║        # do stuff                                            ║
║        time.sleep(0.5)                                       ║
╚══════════════════════════════════════════════════════════════╝
"""

import time
import threading


class EthyToolConnection:

    PIPE_NAME = r"\\.\pipe\EthyToolPipe"

    def __init__(self):
        self._handle = None
        self._kernel32 = None
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────
    # Connection (handled by dashboard — ignore this)
    # ──────────────────────────────────────────────

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

                buf = ctypes.create_string_buffer(8192)
                read = ctypes.wintypes.DWORD(0)
                ok = self._kernel32.ReadFile(self._handle, buf, 8192, ctypes.byref(read), None)
                if not ok:
                    return None

                return buf.value[:read.value].decode("utf-8")
            except Exception:
                return None

    @property
    def connected(self):
        return self._handle is not None

    # ══════════════════════════════════════════════
    #
    #   YOUR HEALTH / MANA
    #
    # ══════════════════════════════════════════════

    def get_hp(self):
        """Your health as a percentage. 100.0 = full, 0.0 = dead."""
        r = self._send("PLAYER_HP")
        return float(r) if r else 0.0

    def get_mp(self):
        """Your mana as a percentage. 100.0 = full."""
        r = self._send("PLAYER_MP")
        return float(r) if r else 0.0

    def get_max_hp(self):
        """Your maximum health points (the actual number, not %)."""
        r = self._send("PLAYER_MAX_HP")
        return int(r) if r else 0

    def get_max_mp(self):
        """Your maximum mana points (the actual number, not %)."""
        r = self._send("PLAYER_MAX_MP")
        return int(r) if r else 0

    # ══════════════════════════════════════════════
    #
    #   YOUR POSITION / MOVEMENT
    #
    # ══════════════════════════════════════════════

    def get_position(self):
        """Where you are in the world. Returns (x, y, z)."""
        r = self._send("PLAYER_POS")
        if not r:
            return (0.0, 0.0, 0.0)
        p = r.split(",")
        return (float(p[0]), float(p[1]), float(p[2]))

    def get_x(self):
        """Just your X coordinate."""
        return self.get_position()[0]

    def get_y(self):
        """Just your Y coordinate."""
        return self.get_position()[1]

    def get_z(self):
        """Just your Z coordinate."""
        return self.get_position()[2]

    def is_moving(self):
        """Are you currently walking/running?"""
        return self._send("PLAYER_MOVING") == "1"

    def is_frozen(self):
        """Are your controls frozen? (cutscene, loading, etc)"""
        return self._send("PLAYER_FROZEN") == "1"

    def get_speed(self):
        """Your current movement speed."""
        r = self._send("PLAYER_SPEED")
        return float(r) if r else 0.0

    def get_direction(self):
        """Which direction you're facing (number)."""
        r = self._send("PLAYER_DIRECTION")
        return int(r) if r else 0

    # ══════════════════════════════════════════════
    #
    #   COMBAT
    #
    # ══════════════════════════════════════════════

    def in_combat(self):
        """Are you currently in combat?"""
        return self._send("PLAYER_COMBAT") == "1"

    def get_attack_speed(self):
        """Your current attack speed."""
        r = self._send("PLAYER_ATTACK_SPEED")
        return float(r) if r else 0.0

    def get_physical_armor(self):
        """Your total physical armor."""
        r = self._send("PLAYER_PHYS_ARMOR")
        return float(r) if r else 0.0

    def get_magical_armor(self):
        """Your total magical armor."""
        r = self._send("PLAYER_MAG_ARMOR")
        return float(r) if r else 0.0

    # ══════════════════════════════════════════════
    #
    #   YOUR TARGET (who you're fighting / looking at)
    #
    # ═════════════════════════════════���════════════

    def get_target(self):
        """
        Get your current hostile target (the enemy you clicked on).
        Returns a dict or None if no target.

        Example:
            target = conn.get_target()
            if target:
                print(target["name"])  → "Wolf"
                print(target["hp"])    → 60.5
                print(target["boss"])  → False
        """
        r = self._send("HOSTILE_TARGET")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return None
        return self._parse_kv(r)

    def get_target_hp(self):
        """Quick way to get your target's HP %. Returns 0 if no target."""
        t = self.get_target()
        return t.get("hp", 0.0) if t else 0.0

    def get_target_name(self):
        """Quick way to get your target's name. Returns "" if no target."""
        t = self.get_target()
        return t.get("name", "") if t else ""

    def has_target(self):
        """Do you have something targeted?"""
        return self.get_target() is not None

    def get_friendly_target(self):
        """
        Get your friendly target (party member, NPC you clicked).
        Same format as get_target().
        """
        r = self._send("FRIENDLY_TARGET")
        if not r or r in ("NONE", "NOT_INITIALIZED"):
            return None
        return self._parse_kv(r)

    # ══════════════════════════════════════════════
    #
    #   GOLD / STATUS
    #
    # ══════════════════════════════════════════════

    def get_gold(self):
        """How much gold you have."""
        r = self._send("PLAYER_GOLD")
        return int(r) if r else 0

    def get_infamy(self):
        """Your current infamy level."""
        r = self._send("PLAYER_INFAMY")
        return float(r) if r else 0.0

    def in_safe_zone(self):
        """Are you in a PZ (safe) zone?"""
        return self._send("PLAYER_PZ_ZONE") == "1"

    def get_food(self):
        """Your current food level."""
        r = self._send("PLAYER_FOOD")
        return float(r) if r else 0.0

    def is_spectating(self):
        """Are you in spectator mode?"""
        return self._send("PLAYER_SPECTATOR") == "1"

    # ══════════════════════════════════════════════
    #
    #   ACTIONS (do stuff!)
    #
    # ══════════════════════════════════════════════

    def cast(self, spell_name):
        """
        Cast a spell by name. Returns True if it worked.

        Example:
            conn.cast("Fireball")
            conn.cast("Heal")
            conn.cast("Lightning Bolt")
        """
        r = self._send(f"CAST_{spell_name}")
        return r == "OK"

    def loot(self):
        """
        Loot all nearby corpses. Returns True if it worked.

        Example:
            conn.loot()
        """
        r = self._send("LOOT_ALL")
        return r == "OK"

    # ══════════════════════════════════════════════
    #
    #   CAMERA
    #
    # ══════════════════════════════════════════════

    def get_camera(self):
        """
        Get camera info. Returns a dict.

        Example:
            cam = conn.get_camera()
            print(cam["distance"])  → 12.5
            print(cam["angle"])     → 180.0
            print(cam["pitch"])     → 45.0
        """
        r = self._send("CAMERA")
        if not r or r == "NOT_INITIALIZED":
            return {}
        p = r.split(",")
        if len(p) < 6:
            return {}
        return {
            "x": float(p[0]),
            "y": float(p[1]),
            "z": float(p[2]),
            "distance": float(p[3]),
            "angle": float(p[4]),
            "pitch": float(p[5]),
        }

    def get_camera_distance(self):
        """How far the camera is zoomed out."""
        r = self._send("CAMERA_DISTANCE")
        return float(r) if r else 0.0

    def get_camera_angle(self):
        """Camera rotation angle."""
        r = self._send("CAMERA_ANGLE")
        return float(r) if r else 0.0

    # ══════════════════════════════════════════════
    #
    #   COUNTS
    #
    # ══════════════════════════════════════════════

    def get_entity_count(self):
        """How many entities (mobs, NPCs, players) are loaded."""
        r = self._send("ENTITY_COUNT")
        return int(r) if r and r != "NOT_INITIALIZED" else 0

    def get_spell_count(self):
        """How many spells you have."""
        r = self._send("SPELL_COUNT")
        return int(r) if r and r != "NOT_INITIALIZED" else 0

    def get_inventory_count(self):
        """How many items in your inventory."""
        r = self._send("INV_COUNT")
        return int(r) if r and r != "NOT_INITIALIZED" else 0

    # ══════════════════════════════════════════════
    #
    #   BULK READ (get everything at once — faster)
    #
    # ══════════════════════════════════════════════

    def get_all(self):
        """
        Get ALL your stats in ONE call. Way faster than calling each one.

        Returns a dict like:
        {
            "hp": 85.5,      "mp": 92.3,
            "max_hp": 1200,   "max_mp": 800,
            "gold": 54321,
            "x": 150.0,      "y": 42.0,      "z": 300.0,
            "dir": 2,
            "combat": False,  "moving": True,  "frozen": False,
            "speed": 5.5,     "atk_speed": 1.2,
            "phys_armor": 45.0, "mag_armor": 30.0,
            "infamy": 0.0,    "pz": False,
            "food": 85.0,     "spectator": False,
            "boss": False,    "elite": False,  "rare": False,
        }
        """
        r = self._send("PLAYER_ALL")
        if not r or r == "NOT_INITIALIZED":
            return {}
        data = {}
        for pair in r.split("|"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                # These are always numbers, not booleans
                if k in ("gold", "max_hp", "max_mp", "dir"):
                    try:
                        data[k] = int(v)
                    except ValueError:
                        data[k] = v
                elif v in ("0", "1"):
                    data[k] = v == "1"
                else:
                    try:
                        data[k] = float(v)
                    except ValueError:
                        data[k] = v
        return data

    # ══════════════════════════════════════════════
    #
    #   SYSTEM (you probably don't need these)
    #
    # ══════════════════════════════════════════════

    def ping(self):
        """Check if the DLL is alive. Returns True/False."""
        return self._send("PING") == "PONG"

    def init(self):
        """Initialize the game API. Returns (success, message)."""
        resp = self._send("INIT")
        return resp == "OK", resp or "No response"

    def is_initialized(self):
        """Is the game API ready?"""
        return self._send("IS_INIT") == "1"

    def get_version(self):
        """DLL version string."""
        return self._send("VERSION") or "unknown"

    def get_last_error(self):
        """Last error from the DLL."""
        return self._send("ERROR") or ""

    # ──────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────

    def _parse_kv(self, r):
        data = {}
        for pair in r.split("|"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                if v in ("0", "1") and k not in ("uid",):
                    data[k] = v == "1"
                else:
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