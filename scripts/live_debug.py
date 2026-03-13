"""
Live Debug Monitor — captures every player state change in real time.
Logs position, movement, combat, targets, interactions, buffs, nearby entities,
loot/inventory changes, animation states, and progress bars.
Run from EthyTool dashboard. Writes to both the dashboard log and a timestamped file.
"""
import time
import math
import os
import json
import threading
import tkinter as tk
from pathlib import Path

try:
    conn
    stop_event
except NameError:
    print("ERROR: Run from EthyTool dashboard.")
    raise SystemExit(1)

# #region agent log
_DBG_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "debug-158e73.log")
def _dbg(msg, data=None, hyp="", run="run1"):
    entry = {"sessionId":"158e73","runId":run,"hypothesisId":hyp,"location":"live_debug.py","message":msg,"data":data or {},"timestamp":int(time.time()*1000)}
    try:
        with open(_DBG_LOG, "a", encoding="utf-8") as _f: _f.write(json.dumps(entry)+"\n")
    except Exception: pass
# #endregion

# ═══════════════════════════════════════════════════════════════
#  Theme
# ═══════════════════════════════════════════════════════════════

BG       = "#0a0e14"
BG_CARD  = "#12161e"
TEXT     = "#e6edf3"
TEXT_DIM = "#6e7681"
ACCENT   = "#58a6ff"
GREEN    = "#3fb950"
RED      = "#f85149"
ORANGE   = "#d29922"
YELLOW   = "#e3b341"
PURPLE   = "#BC8CFF"
CYAN     = "#56d4dd"
BORDER   = "#21262d"
FONT     = "Segoe UI"
FONT_B   = "Segoe UI Semibold"
FONT_M   = "Cascadia Code"

# ═══════════════════════════════════════════════════════════════
#  Debug engine
# ═══════════════════════════════════════════════════════════════

class DebugEngine:
    POLL_RATE = 0.25

    def __init__(self, conn, stop_event, log_fn):
        self.conn = conn
        self.stop_event = stop_event
        self.log = log_fn
        self.monitoring = False
        self._thread = None
        self.event_count = 0

        self._prev = {
            "x": None, "y": None, "z": None,
            "moving": None, "frozen": None, "combat": None,
            "hp": None, "mp": None, "speed": None,
            "has_target": None, "target_name": None,
            "direction": None, "pz": None, "wildlands": None,
            "food": None,
            "gold": None,
            "has_progress": False,
            "_was_moving_before_freeze": False,
        }
        self._prev_buffs = set()
        self._prev_nearby_names = {}
        self._prev_loot_count = 0

        self._prev_inv_snapshot = {}
        self._prev_inv_count = None
        self._prev_anim_states = {}
        self._anim_start_times = {}

        self._progress_start_time = None
        self._progress_count = 0

        self._loot_items_received = []

        self._prev_scene_names = {}

        self._frozen_start_time = None
        self._frozen_start_pos = None
        self._frozen_count = 0
        self._action_phase = None

        self.ANIM_STATES = ["Gather", "Chop", "Mine", "Harvest", "Interact", "Use", "Channeling"]

        self.DISCOVERY_CLASSES = [
            "Entity", "LivingEntity", "LocalPlayerEntity", "LocalPlayerInput",
            "EntityInfoBar", "EntityModel", "LivingEntityModel", "EntityScript",
            "UIController", "GameUI", "UnitFrame",
            "Animator", "Animation", "AnimationController", "AnimationState",
            "ProgressBar", "ActionProgressBar", "GatherProgressBar", "CastBar",
            "ActionBar", "InteractionController", "GatherController",
            "RPGLibrary", "RPGActionProgress", "RPGProgress",
            "GatherAction", "InteractionProgress", "ChannelBar",
            "PlayerAnimation", "EntityAnimation", "AnimatorController",
            "CraftingWindow", "GatherWindow", "HarvestController",
            "Doodad", "DoodadInteraction", "ResourceNode",
            "SkillController", "ActionController", "PlayerController",
            "NetworkEntity", "SyncEntity", "EntitySync",
        ]
        self.PROGRESS_KEYWORDS = [
            "progress", "gather", "harvest", "chop", "mine", "channel",
            "cast", "action", "interact", "frozen", "bar", "fill",
            "duration", "timer", "cooldown", "animation", "anim",
            "state", "active", "busy", "working", "crafting",
        ]

        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        try:
            _here = Path(__file__).parent
        except NameError:
            _here = Path(".")
        self._log_dir = _here / "debugs"
        self._log_dir.mkdir(exist_ok=True)
        self._log_file = self._log_dir / f"live_debug_{ts}.log"

    def start(self):
        if self.monitoring:
            return
        self.monitoring = True
        self.event_count = 0
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self.monitoring = False

    def _emit(self, category, msg, data=""):
        self.event_count += 1
        ts = time.strftime("%H:%M:%S")
        ms = f"{time.time() % 1:.3f}"[1:]
        tag = f"[{ts}{ms}]"
        line = f"{tag} [{category:>10}] {msg}"
        if data:
            line += f"  |  {data}"
        self.log(line)
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def _run(self):
        self._emit("SYSTEM", "Live debug started",
                    f"file={self._log_file}")
        self._emit("SYSTEM", "Monitors: Position, Combat, Vitals, Target, Buffs, "
                              "Nearby, Scene, Loot, Progress, Animation, Inventory, Gold")
        self._emit("SYSTEM", "Scan schedule: Inventory+Gold @0  Nearby @+1s  Scene @+2s  (3s cycle)")

        offsets = self.conn.dump_offsets()
        if offsets:
            self._emit("OFFSETS", "Runtime offsets", offsets[:200])

        # ── ADDRESS & OFFSET DISCOVERY ─────────────────────────────
        self._player_addr = 0
        self._singleton_addrs = {}
        try:
            raw_addr = self.conn._send("PLAYER_ADDRESS")
            self._player_addr = int(raw_addr, 16) if raw_addr and raw_addr != "0x0" else 0
            self._emit("ADDRESS", f"Player ptr = {raw_addr}",
                       f"decimal={self._player_addr}")
        except Exception:
            self._emit("ADDRESS", "PLAYER_ADDRESS: not available")

        try:
            singletons = self.conn.dump_singletons()
            self._singleton_addrs = singletons
            for label, addr in singletons.items():
                self._emit("ADDRESS", f"  {label} = 0x{addr:X}")
            if not singletons:
                self._emit("ADDRESS", "DUMP_SINGLETONS: empty")
        except Exception:
            self._emit("ADDRESS", "DUMP_SINGLETONS: not available")

        MOVEMENT_FIELDS = {
            "Entity": ["_x", "_y", "_z", "_direction", "position", "rotation",
                       "transform", "moveSpeed", "facing", "heading"],
            "LivingEntity": ["_isMoving", "movementSpeed", "_attackSpeed",
                             "moveDirection", "velocity", "_frozen", "facing"],
            "LocalPlayerEntity": ["_frozen", "NearbyEntities"],
        }
        for cls, keywords in MOVEMENT_FIELDS.items():
            try:
                raw = self.conn._send(f"DUMP_FIELDS_{cls}")
                if raw and raw not in ("NOT_FOUND", "FIELD_ITERATION_NOT_AVAILABLE", "NO_FIELDS"):
                    fields = [f.strip() for f in raw.split("|") if f.strip()]
                    matches = []
                    for f in fields:
                        fl = f.lower()
                        if any(kw.lower() in fl for kw in keywords):
                            matches.append(f)
                    if matches:
                        self._emit("ADDRESS", f"  {cls} movement fields ({len(matches)}):")
                        for m in matches:
                            self._emit("ADDRESS", f"    {m}")
                    else:
                        self._emit("ADDRESS", f"  {cls}: no movement fields matched (total={len(fields)})")
                else:
                    self._emit("ADDRESS", f"  DUMP_FIELDS_{cls}: {raw!r}")
            except Exception:
                pass

        # #region agent log
        _dbg("address_discovery", {
            "player_addr": hex(self._player_addr) if self._player_addr else "0x0",
            "singletons": {k: hex(v) for k, v in self._singleton_addrs.items()},
        }, hyp="G")
        # #endregion

        # ── CLASS DISCOVERY — find progress/animation in game classes ──
        self._emit("SYSTEM", "Scanning game classes for progress/animation fields & methods...")
        discovery_hits = {}
        for cls in self.DISCOVERY_CLASSES:
            if self.stop_event.is_set():
                break
            hits_for_class = []
            try:
                raw_m = self.conn._send(f"DUMP_METHODS_{cls}")
                if raw_m and raw_m not in ("NOT_FOUND", "METHOD_FUNCTIONS_NOT_AVAILABLE",
                                           "NO_METHODS", "UNKNOWN_CMD"):
                    methods = [m.strip() for m in raw_m.split("|") if m.strip()]
                    for m in methods:
                        ml = m.lower()
                        for kw in self.PROGRESS_KEYWORDS:
                            if kw in ml:
                                hits_for_class.append(f"METHOD: {m}")
                                break
            except Exception:
                pass
            try:
                raw_f = self.conn._send(f"DUMP_FIELDS_{cls}")
                if raw_f and raw_f not in ("NOT_FOUND", "FIELD_ITERATION_NOT_AVAILABLE",
                                           "NO_FIELDS", "UNKNOWN_CMD"):
                    fields = [f.strip() for f in raw_f.split("|") if f.strip()]
                    for f in fields:
                        fl = f.lower()
                        for kw in self.PROGRESS_KEYWORDS:
                            if kw in fl:
                                hits_for_class.append(f"FIELD: {f}")
                                break
            except Exception:
                pass
            if hits_for_class:
                discovery_hits[cls] = hits_for_class
                self._emit("DISCOVER", f"  {cls} ({len(hits_for_class)} hits):")
                for h in hits_for_class:
                    self._emit("DISCOVER", f"    {h}")

        if not discovery_hits:
            self._emit("DISCOVER", "No progress/animation hits found in known classes")
            self._emit("DISCOVER", "Using FROZEN-state proxy for progress detection")
        else:
            total = sum(len(v) for v in discovery_hits.values())
            self._emit("DISCOVER", f"Discovery complete: {total} hits in {len(discovery_hits)} classes")

        # #region agent log
        _dbg("class_discovery", {
            "classes_searched": len(self.DISCOVERY_CLASSES),
            "classes_with_hits": len(discovery_hits),
            "hits": {k: v for k, v in discovery_hits.items()},
        }, hyp="H")
        # #endregion

        self._emit("SYSTEM", "Progress detection: FROZEN-state proxy (player frozen = action bar active)")
        self._emit("SYSTEM", f"Frozen baseline = {self.conn._send('PLAYER_FROZEN')!r}")

        try:
            inv = self.conn.get_inventory()
            for item in inv:
                name = item.get("name", "")
                if not name:
                    continue
                stack = item.get("stack", 1)
                if isinstance(stack, str):
                    try: stack = int(stack)
                    except ValueError: stack = 1
                self._prev_inv_snapshot[name] = self._prev_inv_snapshot.get(name, 0) + stack
            self._prev_inv_count = len(inv)
            gold = self.conn.get_gold()
            self._prev["gold"] = gold
            self._emit("SYSTEM", f"Inventory baseline: {len(inv)} slots, {len(self._prev_inv_snapshot)} unique items, {gold:,}g")
            # #region agent log
            _dbg("baseline_inventory", {"slots": len(inv), "unique": len(self._prev_inv_snapshot), "gold": gold}, hyp="C,E")
            # #endregion
        except Exception:
            self._emit("SYSTEM", "Inventory baseline: failed to read")

        while self.monitoring and not self.stop_event.is_set():
            try:
                self._poll()
            except Exception as e:
                self._emit("ERROR", f"Poll exception: {e}")
            time.sleep(self.POLL_RATE)

        self._emit("SYSTEM", f"Stopped — {self.event_count} events logged")

    def _changed(self, key, new_val):
        if self._prev[key] != new_val:
            old = self._prev[key]
            self._prev[key] = new_val
            return True, old
        return False, None

    def _poll(self):
        c = self.conn

        # Position + movement — grab raw pipe values, parse locally to avoid double-send
        try:
            raw_pos = c._send("PLAYER_POS")
            raw_moving = c._send("PLAYER_MOVING")
            raw_frozen = c._send("PLAYER_FROZEN")
            raw_speed = c._send("PLAYER_SPEED")
            raw_dir = c._send("PLAYER_DIRECTION")

            px, py, pz = 0.0, 0.0, 0.0
            if raw_pos:
                parts = raw_pos.split(",")
                if len(parts) >= 3:
                    px, py, pz = float(parts[0]), float(parts[1]), float(parts[2])
            moving = raw_moving == "1"
            frozen = raw_frozen == "1"
            speed = c._float(raw_speed)
            direction = c._int(raw_dir)
        except Exception:
            return

        ch, old = self._changed("moving", moving)
        if ch:
            state = "MOVING" if moving else "STOPPED"
            addr_info = f"player=0x{self._player_addr:X}" if self._player_addr else "player=?"
            self._emit("MOVEMENT", f"{state}  pos=({px:.1f}, {py:.1f}, {pz:.1f})  dir={direction}  spd={speed:.1f}",
                       f"{addr_info}  raw_moving={raw_moving!r}  raw_pos={raw_pos!r}  raw_spd={raw_speed!r}")

        ch, old = self._changed("frozen", frozen)
        if ch:
            state = "FROZEN" if frozen else "UNFROZEN"
            self._emit("STATE", f"{state}  pos=({px:.1f}, {py:.1f})",
                       f"raw_frozen={raw_frozen!r}")

        old_x, old_y = self._prev["x"], self._prev["y"]
        if old_x is not None:
            dx = px - old_x
            dy = py - old_y
            dist_moved = math.sqrt(dx * dx + dy * dy)
            if dist_moved > 2.0:
                self._emit("POSITION", f"Jumped {dist_moved:.1f}u  ({old_x:.1f},{old_y:.1f}) → ({px:.1f},{py:.1f})",
                           f"raw_pos={raw_pos!r}  player=0x{self._player_addr:X}" if self._player_addr else "")
        self._prev["x"] = px
        self._prev["y"] = py
        self._prev["z"] = pz

        ch, old = self._changed("direction", direction)
        if ch and old is not None:
            self._emit("DIRECTION", f"Turned {old} → {direction}",
                       f"raw_dir={raw_dir!r}  player=0x{self._player_addr:X}" if self._player_addr else f"raw_dir={raw_dir!r}")

        # Combat
        combat = c.in_combat()
        ch, old = self._changed("combat", combat)
        if ch:
            if combat:
                self._emit("COMBAT", "ENTERED COMBAT", f"pos=({px:.1f}, {py:.1f})")
            else:
                self._emit("COMBAT", "LEFT COMBAT", f"pos=({px:.1f}, {py:.1f})")

        # HP / MP
        hp = c.get_hp()
        mp = c.get_mp()
        ch_hp, old_hp = self._changed("hp", round(hp, 1))
        ch_mp, old_mp = self._changed("mp", round(mp, 1))
        if ch_hp and old_hp is not None:
            delta = round(hp - old_hp, 1)
            tag = "DAMAGE" if delta < 0 else "HEAL"
            self._emit("VITALS", f"{tag}: HP {old_hp}% → {hp:.1f}% ({delta:+.1f})")
        if ch_mp and old_mp is not None:
            delta = round(mp - old_mp, 1)
            if abs(delta) >= 1:
                self._emit("VITALS", f"MP {old_mp}% → {mp:.1f}% ({delta:+.1f})")

        # Speed changes
        ch, old = self._changed("speed", round(speed, 1))
        if ch and old is not None:
            self._emit("SPEED", f"Speed {old} → {speed:.1f}")

        # Target
        has_t = c.has_target()
        ch, old = self._changed("has_target", has_t)
        if ch:
            if has_t:
                tgt = c.get_target()
                if tgt:
                    tname = tgt.get("name", "?")
                    thp = tgt.get("hp", 0)
                    tdist = tgt.get("dist", 0)
                    self._prev["target_name"] = tname
                    self._emit("TARGET", f"ACQUIRED: {tname}  HP={thp:.0f}%  dist={tdist:.1f}m",
                               f"raw={tgt}")
                    try:
                        tanim = c.get_target_animation()
                        if tanim:
                            self._emit("TARGET", f"  anim state={tanim.get('state',0)}  "
                                       f"interrupting={tanim.get('interrupting',False)}  "
                                       f"active_count={tanim.get('active_anim_count',0)}")
                    except Exception:
                        pass
                else:
                    self._emit("TARGET", "ACQUIRED (no info)")
            else:
                old_name = self._prev.get("target_name", "?")
                self._prev["target_name"] = None
                self._emit("TARGET", f"LOST: {old_name}")

        if has_t:
            tgt = c.get_target()
            if tgt:
                new_name = tgt.get("name", "?")
                ch, _ = self._changed("target_name", new_name)
                if ch:
                    self._emit("TARGET", f"SWITCHED → {new_name}",
                               f"hp={tgt.get('hp',0):.0f}%  dist={tgt.get('dist',0):.1f}m")

        # Buffs
        try:
            buffs = c.get_player_buffs()
            buff_names = set(b.get("name", "") for b in buffs if b.get("name"))
            added = buff_names - self._prev_buffs
            removed = self._prev_buffs - buff_names
            for b in added:
                detail = next((x for x in buffs if x.get("name") == b), {})
                self._emit("BUFF", f"+GAINED: {b}", f"stacks={detail.get('stacks',1)}")
            for b in removed:
                self._emit("BUFF", f"-LOST: {b}")
            self._prev_buffs = buff_names
        except Exception:
            pass

        # Zone flags + extended data from PLAYER_ALL
        try:
            pd = c.get_all()
            if pd:
                pz_flag = pd.get("pz", False)
                wild_flag = pd.get("wildlands", False)
                ch, old = self._changed("pz", pz_flag)
                if ch:
                    self._emit("ZONE", f"Safe zone: {old} → {pz_flag}")
                ch, old = self._changed("wildlands", wild_flag)
                if ch:
                    self._emit("ZONE", f"Wildlands: {old} → {wild_flag}")
                food = pd.get("food", 0)
                ch, old = self._changed("food", round(food, 1) if isinstance(food, float) else food)
                if ch and old is not None:
                    self._emit("VITALS", f"Food: {old} → {food}")
        except Exception:
            pass

        # Loot windows
        try:
            loot_cnt = c.get_loot_window_count()
            if loot_cnt != self._prev_loot_count:
                if loot_cnt > self._prev_loot_count:
                    self._emit("LOOT", f"Loot window OPENED (count={loot_cnt})")
                    # #region agent log
                    _dbg("loot_window_opened", {"count": loot_cnt, "prev": self._prev_loot_count}, hyp="A")
                    # #endregion
                else:
                    self._emit("LOOT", f"Loot window CLOSED (count={loot_cnt})")
                self._prev_loot_count = loot_cnt
        except Exception:
            pass

        # ── ACTION / PROGRESS detection (frozen proxy + real animation/condition data) ──
        anim_data = {}
        condition_mask = 0
        try:
            anim_data = c.get_animation_data() or {}
            condition_mask = c.get_condition_mask()
        except Exception:
            pass

        if frozen and not self._frozen_start_time:
            self._frozen_start_time = time.time()
            self._frozen_start_pos = (px, py)
            self._frozen_count += 1
            was_moving = self._prev.get("_was_moving_before_freeze", False)
            anim_info = (f"anim_state={anim_data.get('state', '?')}  "
                         f"cond_mask=0x{condition_mask:X}  "
                         f"active_anims={anim_data.get('active_anim_count', 0)}")
            self._emit("PROGRESS", f"▶ ACTION STARTED (frozen)  #{self._frozen_count}",
                       f"pos=({px:.1f}, {py:.1f})  {anim_info}  combat={combat}")
            # #region agent log
            _dbg("action_started_frozen", {
                "count": self._frozen_count, "pos": [px, py],
                "was_moving": was_moving, "combat": combat,
                "raw_frozen": raw_frozen,
                "anim_state": anim_data.get("state"), "condition_mask": condition_mask,
            }, hyp="H")
            # #endregion

        elif not frozen and self._frozen_start_time:
            dur = time.time() - self._frozen_start_time
            start_pos = self._frozen_start_pos or (0, 0)
            dist_during = math.sqrt((px - start_pos[0])**2 + (py - start_pos[1])**2)
            action_type = "GATHER" if dur > 1.5 else "INTERACT" if dur > 0.3 else "BRIEF"
            anim_info = (f"anim_state={anim_data.get('state', '?')}  "
                         f"cond_mask=0x{condition_mask:X}")
            self._emit("PROGRESS", f"■ ACTION ENDED ({action_type})  dur={dur:.2f}s  #{self._frozen_count}",
                       f"pos=({px:.1f}, {py:.1f})  drift={dist_during:.1f}u  {anim_info}  combat={combat}")
            # #region agent log
            _dbg("action_ended_frozen", {
                "count": self._frozen_count, "duration_sec": round(dur, 3),
                "action_type": action_type, "drift": round(dist_during, 1),
                "combat": combat, "raw_frozen": raw_frozen,
                "anim_state": anim_data.get("state"), "condition_mask": condition_mask,
            }, hyp="H")
            # #endregion
            self._frozen_start_time = None
            self._frozen_start_pos = None

        self._prev["_was_moving_before_freeze"] = moving

        # ═══════════════════════════════════════════════════════════
        # STAGGERED HEAVY SCANS — spread across a 12-tick (~3s) cycle
        # so only ONE heavy pipe burst happens per poll tick.
        #   tick % 12 == 0  → Inventory + Gold
        #   tick % 12 == 4  → Nearby entity scan
        #   tick % 12 == 8  → Scene entity rescan
        # ═══════════════════════════════════════════════════════════
        tick_slot = self.event_count % 12

        # ── INVENTORY / LOOT RECEIVED (slot 0, every ~3s) ──────────
        if tick_slot == 0:
            # #region agent log
            _dbg("scan_tick", {"slot": "inventory", "event_count": self.event_count}, hyp="F")
            # #endregion
            try:
                inv_items = c.get_inventory()
                new_snapshot = {}
                for item in inv_items:
                    name = item.get("name", "")
                    if not name:
                        continue
                    stack = item.get("stack", 1)
                    if isinstance(stack, str):
                        try: stack = int(stack)
                        except ValueError: stack = 1
                    new_snapshot[name] = new_snapshot.get(name, 0) + stack

                if self._prev_inv_snapshot:
                    for name, count in new_snapshot.items():
                        old_count = self._prev_inv_snapshot.get(name, 0)
                        if count > old_count:
                            gained = count - old_count
                            self._loot_items_received.append((name, gained, time.time()))
                            self._emit("ITEM", f"+RECEIVED: {name} x{gained}",
                                       f"total={count}")
                            # #region agent log
                            _dbg("item_received", {"name": name, "gained": gained, "total": count, "old": old_count}, hyp="C")
                            # #endregion

                    for name, old_count in self._prev_inv_snapshot.items():
                        if name not in new_snapshot:
                            self._emit("ITEM", f"-LOST: {name} x{old_count}")
                        elif new_snapshot[name] < old_count:
                            lost = old_count - new_snapshot[name]
                            self._emit("ITEM", f"-USED: {name} x{lost}",
                                       f"remaining={new_snapshot[name]}")

                inv_count = len(inv_items)
                if self._prev_inv_count is not None and inv_count != self._prev_inv_count:
                    delta = inv_count - self._prev_inv_count
                    tag = "+" if delta > 0 else ""
                    self._emit("ITEM", f"Inventory slots: {self._prev_inv_count} → {inv_count} ({tag}{delta})")
                self._prev_inv_count = inv_count
                self._prev_inv_snapshot = new_snapshot
            except Exception:
                pass

            try:
                gold = c.get_gold()
                ch, old_gold = self._changed("gold", gold)
                if ch and old_gold is not None and old_gold != 0:
                    delta = gold - old_gold
                    tag = "GAINED" if delta > 0 else "SPENT"
                    self._emit("GOLD", f"{tag}: {abs(delta):,}g  ({old_gold:,} → {gold:,})")
                    # #region agent log
                    _dbg("gold_changed", {"old": old_gold, "new": gold, "delta": delta}, hyp="E")
                    # #endregion
            except Exception:
                pass

        # ── NEARBY ENTITY SCAN (slot 4, every ~3s) ────────────────
        elif tick_slot == 4:
            # #region agent log
            _dbg("scan_tick", {"slot": "nearby", "event_count": self.event_count}, hyp="F")
            # #endregion
            try:
                ents = c.scan_nearby()
                current = {}
                for e in ents:
                    name = e.get("name", "")
                    cls = e.get("class", "")
                    if not name or cls in ("WallEntity", "DoorEntity"):
                        continue
                    key = f"{name}|{int(float(e.get('x',0)))}|{int(float(e.get('y',0)))}"
                    current[key] = e

                if self._prev_nearby_names:
                    new_keys = set(current.keys()) - set(self._prev_nearby_names.keys())
                    gone_keys = set(self._prev_nearby_names.keys()) - set(current.keys())

                    for k in list(new_keys)[:5]:
                        e = current[k]
                        self._emit("NEARBY", f"+APPEARED: {e.get('name','?')} [{e.get('class','')}]",
                                   f"pos=({e.get('x',0)}, {e.get('y',0)})  uid={e.get('uid','?')}  ptr={e.get('ptr','?')}")
                    for k in list(gone_keys)[:5]:
                        e = self._prev_nearby_names[k]
                        self._emit("NEARBY", f"-LEFT: {e.get('name','?')} [{e.get('class','')}]",
                                   f"pos=({e.get('x',0)}, {e.get('y',0)})")

                self._prev_nearby_names = current
            except Exception:
                pass

        # ── SCENE ENTITY RESCAN (slot 8, every ~3s) ───────────────
        elif tick_slot == 8:
            # #region agent log
            _dbg("scan_tick", {"slot": "scene", "event_count": self.event_count}, hyp="F")
            # #endregion
            try:
                scene_ents = c.scan_scene()
                current_scene = {}
                for e in scene_ents:
                    name = e.get("name", "")
                    cls = e.get("class", "")
                    if not name or cls in ("WallEntity", "DoorEntity"):
                        continue
                    uid = e.get("uid", "")
                    key = f"{name}|{uid}" if uid else f"{name}|{int(float(e.get('x',0)))}|{int(float(e.get('y',0)))}"
                    current_scene[key] = e

                if self._prev_scene_names:
                    new_keys = set(current_scene.keys()) - set(self._prev_scene_names.keys())
                    gone_keys = set(self._prev_scene_names.keys()) - set(current_scene.keys())

                    for k in list(new_keys)[:5]:
                        e = current_scene[k]
                        self._emit("SCENE", f"+SPAWNED: {e.get('name','?')} [{e.get('class','')}]",
                                   f"pos=({e.get('x',0)}, {e.get('y',0)})  uid={e.get('uid','?')}")
                    for k in list(gone_keys)[:5]:
                        e = self._prev_scene_names[k]
                        self._emit("SCENE", f"-DESPAWNED: {e.get('name','?')} [{e.get('class','')}]",
                                   f"pos=({e.get('x',0)}, {e.get('y',0)})  uid={e.get('uid','?')}")

                    if new_keys or gone_keys:
                        self._emit("SCENE", f"Scene delta: +{len(new_keys)} -{len(gone_keys)}  total={len(current_scene)}")

                self._prev_scene_names = current_scene
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
#  UI
# ═══════════════════════════════════════════════════════════════

class DebugUI:
    TAG_COLORS = {
        "MOVEMENT": GREEN, "POSITION": GREEN, "DIRECTION": GREEN,
        "STATE": ORANGE, "COMBAT": RED, "VITALS": RED,
        "TARGET": PURPLE, "BUFF": CYAN, "SPEED": YELLOW,
        "NEARBY": ACCENT, "LOOT": YELLOW, "ZONE": ORANGE,
        "PROGRESS": "#ff79c6", "ANIMATION": "#bd93f9", "ITEM": "#50fa7b",
        "GOLD": "#f1fa8c", "SCENE": "#8be9fd",
        "ADDRESS": "#ffb86c", "DISCOVER": "#ff6e6e",
        "OFFSETS": TEXT_DIM, "SYSTEM": ACCENT, "ERROR": RED,
    }

    def __init__(self, conn, stop_event, script_print):
        self.conn = conn
        self.stop_event = stop_event
        self.engine = DebugEngine(conn, stop_event, self._log)

        self.win = tk.Toplevel()
        self.win.title("Live Debug Monitor")
        self.win.configure(bg=BG)
        self.win.geometry("750x550")
        self.win.resizable(True, True)
        self.win.wm_attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        x = (self.win.winfo_screenwidth() - 750) // 2
        y = (self.win.winfo_screenheight() - 550) // 2
        self.win.geometry(f"+{x}+{y}")

        hdr = tk.Frame(self.win, bg=BG_CARD, height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🔍", font=("Segoe UI Emoji", 14), bg=BG_CARD, fg=ACCENT
                 ).pack(side=tk.LEFT, padx=(10, 6))
        tk.Label(hdr, text="Live Debug Monitor", font=(FONT_B, 13), bg=BG_CARD, fg=TEXT
                 ).pack(side=tk.LEFT)
        tk.Frame(self.win, bg=ACCENT, height=2).pack(fill=tk.X)

        btn_bar = tk.Frame(self.win, bg=BG, padx=10, pady=6)
        btn_bar.pack(fill=tk.X)

        self.start_btn = tk.Button(
            btn_bar, text="▶  Start", font=(FONT_B, 10),
            bg="#1a3a2a", fg=GREEN, relief=tk.FLAT,
            activebackground=GREEN, activeforeground=BG,
            padx=14, pady=4, cursor="hand2", command=self._on_start,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = tk.Button(
            btn_bar, text="■  Stop", font=(FONT_B, 10),
            bg="#3a1a1a", fg=RED, relief=tk.FLAT,
            activebackground=RED, activeforeground=BG,
            padx=14, pady=4, cursor="hand2", command=self._on_stop,
            state=tk.DISABLED,
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            btn_bar, text="Clear", font=(FONT, 9),
            bg=BG_CARD, fg=TEXT_DIM, relief=tk.FLAT,
            padx=10, pady=4, cursor="hand2", command=self._clear,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            btn_bar, text="Copy", font=(FONT, 9),
            bg=BG_CARD, fg=TEXT_DIM, relief=tk.FLAT,
            padx=10, pady=4, cursor="hand2", command=self._copy,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.status = tk.Label(btn_bar, text="Idle", font=(FONT_M, 9), bg=BG, fg=TEXT_DIM)
        self.status.pack(side=tk.RIGHT)

        self.counter = tk.Label(btn_bar, text="0 events", font=(FONT_M, 8), bg=BG, fg=TEXT_DIM)
        self.counter.pack(side=tk.RIGHT, padx=(0, 10))

        log_frame = tk.Frame(self.win, bg=BG)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        self.log_box = tk.Text(
            log_frame, font=(FONT_M, 8), bg="#060a10", fg=TEXT_DIM,
            relief=tk.FLAT, highlightthickness=0, padx=8, pady=4,
            state=tk.DISABLED, wrap=tk.NONE,
        )
        y_scroll = tk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview,
                                bg=BG_CARD, troughcolor=BG, width=10)
        x_scroll = tk.Scrollbar(log_frame, orient="horizontal", command=self.log_box.xview,
                                bg=BG_CARD, troughcolor=BG, width=10)
        self.log_box.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.log_box.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        for tag, color in self.TAG_COLORS.items():
            self.log_box.tag_configure(tag, foreground=color)
        self.log_box.tag_configure("default", foreground=TEXT_DIM)

        self._auto_scroll = True
        self._update_counter()
        self._poll_stop()

    def _log(self, line):
        try:
            self.log_box.configure(state=tk.NORMAL)

            tag = "default"
            for t in self.TAG_COLORS:
                if f"[{t:>10}]" in line or f"[{t}]" in line:
                    tag = t
                    break

            self.log_box.insert(tk.END, line + "\n", tag)

            total = int(self.log_box.index("end-1c").split(".")[0])
            if total > 5000:
                self.log_box.delete("1.0", f"{total - 5000}.0")

            if self._auto_scroll:
                self.log_box.see(tk.END)
            self.log_box.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _copy(self):
        content = self.log_box.get("1.0", tk.END)
        if content.strip():
            self.win.clipboard_clear()
            self.win.clipboard_append(content)
            self.win.update()

    def _clear(self):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _on_start(self):
        self.engine.start()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status.configure(text="Monitoring", fg=GREEN)

    def _on_stop(self):
        self.engine.stop()
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status.configure(text="Stopped", fg=ORANGE)

    def _update_counter(self):
        if not self.win.winfo_exists():
            return
        self.counter.configure(text=f"{self.engine.event_count} events")
        if self.engine.monitoring:
            self.status.configure(text="Monitoring", fg=GREEN)
        self.win.after(500, self._update_counter)

    def _poll_stop(self):
        if not self.win.winfo_exists():
            return
        if self.stop_event.is_set():
            self.engine.stop()
            return
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

print("  Opening Live Debug Monitor...")
ui = DebugUI(conn, stop_event, print)
