"""
Node Teleport — In-game overlay showing nearby resource nodes. Click to move to node.

Run from EthyTool dashboard. Scans for HarvestNode, GatherableEntity, ResourceNode,
Doodad, etc. Click a node to move your character to it.

Uses conn.move_to(x, y) — pathfinding, not instant teleport.
Instant teleport would require a new SET_POSITION command in the injector.
All in single thread (root.after).
"""

import math
import tkinter as tk

# conn and stop_event injected by EthyTool dashboard
try:
    conn
    stop_event
except NameError:
    print("ERROR: Run from EthyTool dashboard (Load Script).")
    raise SystemExit(1)

# ═══════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════

DETECT_RANGE = 80.0
POLL_INTERVAL_MS = 500
OVERLAY_ALPHA = 0.92
OVERLAY_WIDTH = 300
OVERLAY_HEIGHT = 400

# Node/resource entity classes (from game IL2CPP)
NODE_CLASSES = {"Doodad", "HarvestNode", "GatherableEntity", "ResourceNode",
                "InteractableEntity", "StaticEntity"}
SKIP_CLASSES = {"LocalPlayerEntity", "PlayerEntity", "LivingEntity",
                "NPCEntity", "MonsterEntity", "HostileEntity"}

# Theme
BG = "#0a0e14"
BG_HEADER = "#12161e"
BG_ROW = "#0d1117"
BG_ROW_HOVER = "#161b22"
TEXT = "#e6edf3"
TEXT_DIM = "#8b949e"
FONT = "Segoe UI"
FONT_MONO = "Cascadia Code"


def get_nodes():
    """Scan for resource nodes from multiple sources. All conn calls in caller thread."""
    px, py, _ = conn.get_position()
    seen = set()
    result = []

    def add_node(name, x, y, dist, cls="", uid=None):
        key = (uid,) if uid else (name or "?", round(x or 0, 1), round(y or 0, 1))
        if key in seen:
            return
        seen.add(key)
        if dist > DETECT_RANGE:
            return
        result.append({"name": name or "?", "dist": dist, "x": x, "y": y, "class": cls})

    # 1. scan_doodads (NEARBY_ADDRESSES / SCENE_ADDRESSES filtered)
    for e in conn.scan_doodads() or []:
        if e.get("hidden"):
            continue
        name = e.get("name", "")
        try:
            x = float(e.get("x", 0))
            y = float(e.get("y", 0))
        except (ValueError, TypeError):
            continue
        dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
        add_node(name, x, y, dist, e.get("class", ""), e.get("uid"))

    # 2. NEARBY_ADDRESSES / SCENE_ADDRESSES — filter for nodes directly
    for entities in [conn.get_nearby_addresses(), conn.get_scene_addresses()]:
        for e in entities or []:
            if e.get("hidden"):
                continue
            cls = e.get("class", "")
            if cls in SKIP_CLASSES:
                continue
            if cls and cls not in NODE_CLASSES and not e.get("static"):
                continue
            name = e.get("name", "")
            try:
                x = float(e.get("x", 0))
                y = float(e.get("y", 0))
            except (ValueError, TypeError):
                continue
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            add_node(name or "?", x, y, dist, cls, e.get("uid"))

    # 3. SCAN_NEARBY / SCAN_SCENE raw — may have class=Doodad, static=1
    for raw in [conn._send("SCAN_NEARBY"), conn._send("SCAN_SCENE")]:
        if not raw or raw.startswith("NO_") or raw.startswith("BAD_"):
            continue
        for block in raw.split("###"):
            if block.startswith("count=") or not block.strip():
                continue
            d = {}
            for pair in block.split("|"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    d[k] = v
            cls = d.get("class", "")
            cls_upper = cls.upper() if cls else ""
            is_static = str(d.get("static", "")).lower() in ("1", "true")
            skip_upper = {c.upper() for c in SKIP_CLASSES}
            node_upper = {c.upper() for c in NODE_CLASSES}
            if cls_upper in skip_upper:
                continue
            if cls_upper not in node_upper and not is_static:
                continue
            name = d.get("name", "")
            try:
                x = float(d.get("x", 0))
                y = float(d.get("y", 0))
            except (ValueError, TypeError):
                continue
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            add_node(name or "?", x, y, dist, d.get("class", ""), d.get("uid"))

    # 4. get_nearby / get_scene — include static entities (often nodes)
    for entities in [conn.get_nearby(), conn.get_scene()]:
        for e in entities or []:
            if e.get("hidden"):
                continue
            if not e.get("static"):
                continue
            name = e.get("name", e.get("display", ""))
            try:
                x = float(e.get("x", 0))
                y = float(e.get("y", 0))
            except (ValueError, TypeError):
                continue
            dist = math.sqrt((x - px) ** 2 + (y - py) ** 2)
            add_node(name or "?", x, y, dist, e.get("class", ""), e.get("uid"))

    result.sort(key=lambda n: n["dist"])
    return result[:40]


class NodeTeleportOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Node Teleport")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", OVERLAY_ALPHA)
        self.root.resizable(False, False)
        self.root.geometry(f"{OVERLAY_WIDTH}x{OVERLAY_HEIGHT}+50+50")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.nodes = []
        self.labels = []
        self.running = True
        self._build_ui()
        self._schedule_poll()

    def _build_ui(self):
        header = tk.Frame(self.root, bg=BG_HEADER, height=36)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📦 Nodes — Click to move", font=(FONT, 10, "bold"),
                 bg=BG_HEADER, fg=TEXT).pack(side=tk.LEFT, padx=10, pady=6)
        self.count_label = tk.Label(header, text="0 nodes", font=(FONT, 9), bg=BG_HEADER, fg=TEXT_DIM)
        self.count_label.pack(side=tk.RIGHT, padx=10, pady=6)

        canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg=BG)
        self.list_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _on_close(self):
        self.running = False
        self.root.destroy()

    def _schedule_poll(self):
        """Poll for nodes in main thread via root.after (single-thread)."""
        if not self.running or not self.root.winfo_exists():
            return
        if stop_event.is_set():
            self.running = False
            self.root.destroy()
            return
        try:
            self.nodes = get_nodes()
            self._refresh_list()
        except Exception as e:
            try:
                conn.log(f"Node teleport error: {e}")
            except Exception:
                pass
        self.root.after(POLL_INTERVAL_MS, self._schedule_poll)

    def _check_stop(self):
        if stop_event.is_set():
            self.running = False
            self.root.destroy()
            return
        if self.root.winfo_exists():
            self.root.after(500, self._check_stop)

    def _refresh_list(self):
        if not self.root.winfo_exists():
            return
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.labels.clear()
        self.count_label.configure(text=f"{len(self.nodes)} nodes")
        for n in self.nodes:
            row = tk.Frame(self.list_frame, bg=BG_ROW, cursor="hand2")
            row.pack(fill=tk.X, padx=2, pady=1)
            dist_str = f"{n['dist']:.1f}m"
            name_short = (n["name"][:26] + "…") if len(n["name"]) > 26 else n["name"]
            cls_raw = n.get("class", "") or "node"
            cls_short = (cls_raw[:10] + "…") if len(cls_raw) > 10 else cls_raw
            lbl = tk.Label(row, text=f"  {name_short}  {dist_str}  [{cls_short}]", font=(FONT_MONO, 9),
                          bg=BG_ROW, fg=TEXT, anchor="w", cursor="hand2")
            lbl.pack(fill=tk.X, padx=4, pady=4)
            lbl.bind("<Button-1>", lambda e, node=n: self._on_click(node))
            lbl.bind("<Enter>", lambda e, r=row: r.configure(bg=BG_ROW_HOVER))
            lbl.bind("<Leave>", lambda e, r=row: r.configure(bg=BG_ROW))
            row.bind("<Button-1>", lambda e, node=n: self._on_click(node))
            self.labels.append(lbl)

    def _on_click(self, node):
        conn.move_to(node["x"], node["y"])
        conn.log(f"Moving to {node['name']} ({node['dist']:.1f}m)")

    def run(self):
        conn.log("Node Teleport overlay started. Click a node to move.")
        self.root.after(500, self._check_stop)
        self.root.mainloop()


overlay = NodeTeleportOverlay()
overlay.run()
