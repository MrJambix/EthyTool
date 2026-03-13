"""
Game Class Explorer — Full IL2CPP dump of every class, field, method, and address.
Scans all known + discovered classes. Highlights animation, progress, gather hits.
Saves results to a timestamped file. Run from EthyTool dashboard.
"""
import time
import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path

try:
    conn
    stop_event
except NameError:
    print("ERROR: Run from EthyTool dashboard.")
    raise SystemExit(1)

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
PINK     = "#ff79c6"
FONT     = "Segoe UI"
FONT_B   = "Segoe UI Semibold"
FONT_M   = "Cascadia Code"

HIGHLIGHT_KEYWORDS = [
    "progress", "gather", "harvest", "chop", "mine", "channel", "cast",
    "action", "interact", "frozen", "bar", "fill", "duration", "timer",
    "animation", "anim", "state", "active", "busy", "working", "crafting",
    "loot", "pickup", "corpse", "container", "inventory", "item",
    "movement", "moving", "speed", "position", "direction", "facing",
    "target", "combat", "health", "mana", "buff", "debuff", "effect",
    "spell", "cooldown", "quest", "skill", "experience", "level",
]

ALL_CLASSES = [
    "Entity", "LivingEntity", "PlayerEntity", "LocalPlayerEntity", "LocalPlayerInput",
    "EntityManager", "EntityModel", "EntityScript", "EntityPresetInformation",
    "EntityInfoBar", "LivingEntityModel", "HitboxDisplay",
    "Item", "ItemSlot", "ItemModel", "Container", "ContainerWindow", "ContainerSlot",
    "EquipContainer", "VirtualContainer", "InventoryWindow", "BankController",
    "Spell", "SpellSlot", "StatusEffect", "Projectile", "ProjectileTarget", "Corpse",
    "UIController", "GameUI", "Tooltip", "ComparisonTooltip", "UnitFrame", "FloatingText",
    "NotificationManager", "CursorManager", "LoadingScreen",
    "CameraController", "SpectatorModeCameraController",
    "WorldMap", "MinimapCamera",
    "Quest", "QuestManager", "QuestTracker", "QuestObjective",
    "Party", "PartyGroup", "GuildManager", "Guild", "CompanionPanel",
    "ChatController", "Chat",
    "NPC", "Conversation", "ActiveConversation",
    "QuickBar", "QuickSlot", "Keybind",
    "ClientSettings", "AudioSettings", "ControlSettings", "AudioManager",
    "Model", "MeshEffects", "MeshEffectScript", "PositionTask", "TargetableEntityOutline",
    "EntityMouseOverInfoBarOutline",
    "Doodad", "ResourceNode", "HarvestNode", "GatherableEntity",
    "InteractableEntity", "StaticEntity", "MonsterEntity", "NPCEntity",
    "ProgressBar", "ActionProgressBar", "GatherProgressBar", "CastBar",
    "ActionBar", "InteractionController", "GatherController", "ChannelBar",
    "Animator", "Animation", "AnimationController", "AnimationState",
    "ImplementedAnimation", "ActiveAnimationState",
    "FillBar", "ProgressInfoBar", "EntityProgressBar", "FoodFillBar",
    "PlayerAnimation", "EntityAnimation", "AnimatorController",
    "CraftingWindow", "GatherWindow", "HarvestController",
    "SkillController", "ActionController", "PlayerController",
    "NetworkEntity", "SyncEntity", "EntitySync",
    "RPGLibrary", "RPGActionProgress", "RPGProgress",
    "GatherAction", "InteractionProgress", "DoodadInteraction",
    "SkillManager", "SkillProgressBar", "ExperienceBar",
    "MainProgressBar", "InfoBar", "HealthBar", "ManaBar",
    "BuffBar", "DebuffBar", "StatusBar", "ActionSlot",
    "SpellBook", "SpellCategory", "SpellEffect",
    "Infobar", "EntityInfobar", "InfobarController",
    "LootWindow", "LootPanel", "LootSlot",
    "MapController", "NavigationController",
    "PartyMember", "PartyMemberData", "PartyWindow",
    "TradeWindow", "ShopWindow", "VendorWindow",
    "CombatLog", "DamageText", "HealText",
    "MountController", "PetController", "CompanionController",
    "WeatherController", "TimeController", "DayNightCycle",
    "TalentTree", "TalentNode", "TalentWindow",
    "AchievementManager", "AchievementWindow",
    "SettingsWindow", "OptionsWindow", "KeybindWindow",
    "CharacterWindow", "CharacterStats", "StatsWindow",
    "SocialWindow", "FriendList", "IgnoreList",
    "MailWindow", "MailController", "InboxWindow",
    "AuctionHouse", "Marketplace", "TradingPost",
    "Waypoint", "WaypointManager", "TeleportController",
]

ANIM_PRIORITY_CLASSES = [
    "Entity", "LivingEntity", "LocalPlayerEntity", "EntityInfoBar",
    "Doodad", "InteractableEntity", "GatherableEntity",
    "ProgressBar", "ActionProgressBar", "CastBar",
    "Animator", "Animation", "PlayerAnimation", "AnimationState",
    "ImplementedAnimation", "FillBar", "ProgressInfoBar", "EntityProgressBar",
    "RPGLibrary", "GatherAction", "ActionController",
    "Infobar", "InfoBar", "MainProgressBar", "UnitFrame",
]


class DumpEngine:
    def __init__(self, conn, stop_event, log_fn, status_fn):
        self.conn = conn
        self.stop = stop_event
        self.log = log_fn
        self.set_status = status_fn
        self.results = {}
        self.total_fields = 0
        self.total_methods = 0
        self.total_hits = 0
        self._running = False

    def run_dump(self):
        if self._running:
            return
        self._running = True
        self.results = {}
        self.total_fields = 0
        self.total_methods = 0
        self.total_hits = 0

        self.log("=" * 80)
        self.log(f"  FULL GAME CLASS DUMP — {time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.log("=" * 80)

        self._dump_addresses()
        self._dump_offsets()
        self._dump_all_classes()
        self._save_report()

        self.log("")
        self.log("=" * 80)
        self.log(f"  DONE — {len(self.results)} classes found, "
                 f"{self.total_fields} fields, {self.total_methods} methods, "
                 f"{self.total_hits} keyword hits")
        self.log("=" * 80)
        self.set_status(f"Done — {len(self.results)} classes, {self.total_hits} hits")
        self._running = False

    def _dump_addresses(self):
        self.log("")
        self.log("─" * 80)
        self.log("  SECTION 1: RUNTIME ADDRESSES & SINGLETONS")
        self.log("─" * 80)

        raw = self.conn._send("PLAYER_ADDRESS")
        self.log(f"  Player ptr          = {raw}")

        raw = self.conn._send("DUMP_SINGLETONS")
        if raw and raw.strip():
            for pair in raw.split("|"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    self.log(f"  {k.strip():<22} = {v.strip()}")
        else:
            self.log("  DUMP_SINGLETONS: empty or unavailable")

    def _dump_offsets(self):
        self.log("")
        self.log("─" * 80)
        self.log("  SECTION 2: RUNTIME OFFSETS")
        self.log("─" * 80)

        raw = self.conn._send("DUMP_OFFSETS")
        if raw:
            for pair in raw.split("|"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    self.log(f"  {k.strip():<30} = {v.strip()}")
        else:
            self.log("  DUMP_OFFSETS: empty")

    def _dump_all_classes(self):
        self.log("")
        self.log("─" * 80)
        self.log("  SECTION 3: ALL CLASSES — FIELDS & METHODS")
        self.log("─" * 80)

        unique = list(dict.fromkeys(ALL_CLASSES))
        total = len(unique)

        for i, cls in enumerate(unique):
            if self.stop.is_set():
                break
            self.set_status(f"Scanning {i+1}/{total}: {cls}")
            self._dump_class(cls)

    def _dump_class(self, cls):
        fields = []
        methods = []

        raw_f = self.conn._send(f"DUMP_FIELDS_{cls}")
        if raw_f and raw_f not in ("NOT_FOUND", "FIELD_ITERATION_NOT_AVAILABLE",
                                    "NO_FIELDS", "UNKNOWN_CMD"):
            fields = [f.strip() for f in raw_f.split("|") if f.strip()]

        raw_m = self.conn._send(f"DUMP_METHODS_{cls}")
        if raw_m and raw_m not in ("NOT_FOUND", "METHOD_FUNCTIONS_NOT_AVAILABLE",
                                    "NO_METHODS", "UNKNOWN_CMD"):
            methods = [m.strip() for m in raw_m.split("|") if m.strip()]

        if not fields and not methods:
            return

        self.results[cls] = {"fields": fields, "methods": methods}
        self.total_fields += len(fields)
        self.total_methods += len(methods)

        is_priority = cls in ANIM_PRIORITY_CLASSES
        tag = " ◄◄ PRIORITY" if is_priority else ""

        self.log(f"\n  ╔══ {cls}{tag}")
        self.log(f"  ║   {len(fields)} fields, {len(methods)} methods")

        if fields:
            self.log(f"  ╠── FIELDS:")
            for f in fields:
                hit = self._check_highlight(f)
                marker = f"  ◄◄ {hit.upper()}" if hit else ""
                if hit:
                    self.total_hits += 1
                self.log(f"  ║     {f}{marker}")

        if methods:
            self.log(f"  ╠── METHODS:")
            for m in methods:
                hit = self._check_highlight(m)
                marker = f"  ◄◄ {hit.upper()}" if hit else ""
                if hit:
                    self.total_hits += 1
                self.log(f"  ║     {m}{marker}")

        self.log(f"  ╚══")

    def _check_highlight(self, text):
        tl = text.lower()
        for kw in HIGHLIGHT_KEYWORDS:
            if kw in tl:
                return kw
        return ""

    def _save_report(self):
        try:
            here = Path(__file__).parent
        except NameError:
            here = Path(".")
        out_dir = here
        out_dir.mkdir(exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H-%M-%S")
        path = out_dir / f"CLASS_DUMP_{ts}.txt"

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"FULL GAME CLASS DUMP — {ts}\n")
                f.write(f"Classes: {len(self.results)}  Fields: {self.total_fields}  "
                        f"Methods: {self.total_methods}  Hits: {self.total_hits}\n")
                f.write("=" * 80 + "\n\n")

                for cls, data in sorted(self.results.items()):
                    prio = " [PRIORITY]" if cls in ANIM_PRIORITY_CLASSES else ""
                    f.write(f"CLASS: {cls}{prio}\n")
                    if data["fields"]:
                        f.write(f"  FIELDS ({len(data['fields'])}):\n")
                        for field in data["fields"]:
                            hit = self._check_highlight(field)
                            marker = f"  <-- {hit.upper()}" if hit else ""
                            f.write(f"    {field}{marker}\n")
                    if data["methods"]:
                        f.write(f"  METHODS ({len(data['methods'])}):\n")
                        for method in data["methods"]:
                            hit = self._check_highlight(method)
                            marker = f"  <-- {hit.upper()}" if hit else ""
                            f.write(f"    {method}{marker}\n")
                    f.write("\n")

            self.log(f"\n  Report saved: {path}")
        except Exception as e:
            self.log(f"\n  Failed to save report: {e}")


class DumpUI:
    def __init__(self, conn, stop_event, script_print):
        self.conn = conn
        self.stop_event = stop_event

        self.win = tk.Toplevel()
        self.win.title("Game Class Explorer")
        self.win.configure(bg=BG)
        self.win.geometry("900x700")
        self.win.resizable(True, True)
        self.win.wm_attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        x = (self.win.winfo_screenwidth() - 900) // 2
        y = (self.win.winfo_screenheight() - 700) // 2
        self.win.geometry(f"+{x}+{y}")

        hdr = tk.Frame(self.win, bg=BG_CARD, height=40)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🔬", font=("Segoe UI Emoji", 14), bg=BG_CARD, fg=PINK
                 ).pack(side=tk.LEFT, padx=(10, 6))
        tk.Label(hdr, text="Game Class Explorer", font=(FONT_B, 13), bg=BG_CARD, fg=TEXT
                 ).pack(side=tk.LEFT)
        tk.Frame(self.win, bg=PINK, height=2).pack(fill=tk.X)

        btn_bar = tk.Frame(self.win, bg=BG, padx=10, pady=6)
        btn_bar.pack(fill=tk.X)

        self.dump_btn = tk.Button(
            btn_bar, text="▶  Dump All Classes", font=(FONT_B, 10),
            bg="#1a3a2a", fg=GREEN, relief=tk.FLAT,
            activebackground=GREEN, activeforeground=BG,
            padx=14, pady=4, cursor="hand2", command=self._on_dump,
        )
        self.dump_btn.pack(side=tk.LEFT, padx=(0, 6))

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

        tk.Label(btn_bar, text="Filter:", font=(FONT, 9), bg=BG, fg=TEXT_DIM
                 ).pack(side=tk.LEFT, padx=(12, 4))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", self._on_filter)
        self.filter_entry = tk.Entry(
            btn_bar, textvariable=self.filter_var, font=(FONT_M, 9),
            bg="#060a10", fg=TEXT, insertbackground=TEXT,
            relief=tk.FLAT, width=20,
        )
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 6))

        self.status = tk.Label(btn_bar, text="Ready", font=(FONT_M, 9), bg=BG, fg=TEXT_DIM)
        self.status.pack(side=tk.RIGHT)

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

        self.log_box.tag_configure("hit", foreground=PINK)
        self.log_box.tag_configure("priority", foreground=YELLOW)
        self.log_box.tag_configure("header", foreground=ACCENT)
        self.log_box.tag_configure("section", foreground=CYAN)
        self.log_box.tag_configure("addr", foreground=ORANGE)
        self.log_box.tag_configure("default", foreground=TEXT_DIM)
        self.log_box.tag_configure("found", background="#2a1a3a")

        self._all_lines = []
        self.engine = DumpEngine(conn, stop_event, self._log, self._set_status)

    def _log(self, line):
        self._all_lines.append(line)
        try:
            self.log_box.configure(state=tk.NORMAL)
            tag = "default"
            if "◄◄" in line:
                tag = "hit"
            elif "PRIORITY" in line:
                tag = "priority"
            elif line.startswith("  ╔") or line.startswith("  ╚"):
                tag = "header"
            elif "SECTION" in line or line.startswith("─"):
                tag = "section"
            elif "=" in line and ("0x" in line or "ptr" in line.lower()):
                tag = "addr"
            self.log_box.insert(tk.END, line + "\n", tag)
            self.log_box.see(tk.END)
            self.log_box.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def _set_status(self, text):
        try:
            self.status.configure(text=text)
            self.win.update_idletasks()
        except tk.TclError:
            pass

    def _on_dump(self):
        self.dump_btn.configure(state=tk.DISABLED, text="Scanning...")
        self._clear()
        t = threading.Thread(target=self._run_dump, daemon=True)
        t.start()

    def _run_dump(self):
        self.engine.run_dump()
        try:
            self.dump_btn.configure(state=tk.NORMAL, text="▶  Dump All Classes")
        except tk.TclError:
            pass

    def _on_filter(self, *_):
        term = self.filter_var.get().strip().lower()
        if not term:
            self._redraw_all()
            return
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        for line in self._all_lines:
            if term in line.lower():
                tag = "found" if "◄◄" in line else "default"
                self.log_box.insert(tk.END, line + "\n", tag)
        self.log_box.configure(state=tk.DISABLED)

    def _redraw_all(self):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        for line in self._all_lines:
            tag = "default"
            if "◄◄" in line:
                tag = "hit"
            elif "PRIORITY" in line:
                tag = "priority"
            elif line.startswith("  ╔") or line.startswith("  ╚"):
                tag = "header"
            self.log_box.insert(tk.END, line + "\n", tag)
        self.log_box.configure(state=tk.DISABLED)

    def _clear(self):
        self._all_lines = []
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.delete("1.0", tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def _copy(self):
        content = self.log_box.get("1.0", tk.END)
        if content.strip():
            self.win.clipboard_clear()
            self.win.clipboard_append(content)
            self.win.update()

    def _on_close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass


print("  Opening Game Class Explorer...")
ui = DumpUI(conn, stop_event, print)
