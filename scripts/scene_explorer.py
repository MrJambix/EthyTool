"""
Scene Explorer Dashboard — Browse all scene objects and game entities with full paths.
Hover over entities IN THE GAME to see them in the "Hover Target" panel.
Select any item to view its full game info.
Run from EthyTool dashboard.
"""
import tkinter as tk
from tkinter import ttk

try:
    conn
    stop_event
except NameError:
    print("ERROR: Run from EthyTool dashboard.")
    raise SystemExit(1)

HOVER_POLL_MS = 120

BG = "#0a0e14"
BG_CARD = "#12161e"
TEXT = "#e6edf3"
TEXT_DIM = "#6e7681"
ACCENT = "#58a6ff"
GREEN = "#3fb950"
ORANGE = "#d29922"
CYAN = "#56d4dd"
PINK = "#ff79c6"
FONT = "Segoe UI"
FONT_B = "Segoe UI Semibold"
FONT_M = "Cascadia Code"


def parse_kv(s):
    d = {}
    for part in (s or "").split("|"):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def parse_scene_dump(raw):
    """Parse SCENE_DUMP output into list of (path, name, depth)."""
    if not raw or raw.startswith("ERROR"):
        return []
    if "ROOTS=" not in raw:
        return []
    lines = raw.strip().split("\n")
    if not lines:
        return []
    result = []
    stack = []  # stack of (name, depth)
    for line in lines[1:]:
        if not line.strip() or "(truncated" in line:
            continue
        stripped = line.lstrip()
        depth = (len(line) - len(stripped)) // 2
        name = stripped
        while stack and stack[-1][1] >= depth:
            stack.pop()
        path_parts = [p[0] for p in stack] + [name]
        path = "/".join(path_parts)
        stack.append((name, depth))
        result.append({"path": path, "name": name, "depth": depth})
    return result


def parse_scene_all(raw):
    """Parse SCENE_ALL output into list of entity dicts."""
    if not raw or raw in ("NONE", "NO_ENTITY_MANAGER", "NOT_INITIALIZED"):
        return []
    return [parse_kv(e) for e in raw.split("###") if e.strip()]


def parse_scene_addresses(raw):
    """Parse SCENE_ADDRESSES output into list of entity dicts with ptr, class, etc."""
    if not raw or raw.startswith("NO_") or raw.startswith("ERROR"):
        return []
    result = []
    for part in raw.split("###"):
        if not part.strip():
            continue
        d = parse_kv(part)
        if d and ("ptr" in d or "uid" in d):
            result.append(d)
    return result


class SceneExplorerUI:
    def __init__(self):
        self.conn = conn
        self.win = tk.Toplevel()
        self.win.title("Scene Explorer")
        self.win.configure(bg=BG)
        self.win.geometry("1100x750")
        self.win.resizable(True, True)
        self.win.wm_attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        x = (self.win.winfo_screenwidth() - 1100) // 2
        y = (self.win.winfo_screenheight() - 750) // 2
        self.win.geometry(f"+{x}+{y}")

        # Header
        hdr = tk.Frame(self.win, bg=BG_CARD, height=44)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🌐", font=("Segoe UI Emoji", 16), bg=BG_CARD, fg=CYAN
                 ).pack(side=tk.LEFT, padx=(12, 8))
        tk.Label(hdr, text="Scene Explorer", font=(FONT_B, 14), bg=BG_CARD, fg=TEXT
                 ).pack(side=tk.LEFT)
        tk.Label(hdr, text="— All objects, paths & game info", font=(FONT, 10), bg=BG_CARD, fg=TEXT_DIM
                 ).pack(side=tk.LEFT, padx=(8, 0))
        tk.Frame(self.win, bg=CYAN, height=2).pack(fill=tk.X)

        # Hover Target — entity under mouse IN GAME
        self._hover_locked = False
        self._locked_entity = None  # {uid, name, class, x, y, z, ...} when locked
        hover_card = tk.Frame(self.win, bg="#0d1520", highlightbackground=CYAN, highlightthickness=1)
        hover_card.pack(fill=tk.X, padx=8, pady=(6, 4))
        hover_inner = tk.Frame(hover_card, bg="#0d1520", padx=10, pady=6)
        hover_inner.pack(fill=tk.X)
        tk.Label(hover_inner, text="🎯 Hover in-game → Lock to search:  |  F3 = dump to Log", font=(FONT_B, 9), bg="#0d1520", fg=CYAN
                 ).pack(side=tk.LEFT, padx=(0, 8))
        self.hover_label = tk.Label(
            hover_inner, text="Move mouse over entity in game...", font=(FONT_M, 9),
            bg="#0d1520", fg=TEXT_DIM,
        )
        self.hover_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lock_btn = tk.Button(
            hover_inner, text="📌 Lock", font=(FONT_B, 9),
            bg="#1a2a3a", fg=ACCENT, relief=tk.FLAT, padx=8, pady=2,
            cursor="hand2", command=self._toggle_lock,
        )
        self.lock_btn.pack(side=tk.LEFT, padx=(8, 0))

        # Toolbar
        toolbar = tk.Frame(self.win, bg=BG, padx=10, pady=8)
        toolbar.pack(fill=tk.X)

        tk.Button(
            toolbar, text="🔄 Refresh Unity Hierarchy", font=(FONT_B, 10),
            bg="#1a3a2a", fg=GREEN, relief=tk.FLAT,
            padx=12, pady=4, cursor="hand2", command=self._refresh_hierarchy,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(
            toolbar, text="🔄 Refresh Game Entities", font=(FONT_B, 10),
            bg="#1a2a3a", fg=ACCENT, relief=tk.FLAT,
            padx=12, pady=4, cursor="hand2", command=self._refresh_entities,
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(toolbar, text="Depth:", font=(FONT, 9), bg=BG, fg=TEXT_DIM
                 ).pack(side=tk.LEFT, padx=(12, 4))
        self.depth_var = tk.StringVar(value="6")
        depth_spin = tk.Spinbox(toolbar, from_=2, to=10, width=3, textvariable=self.depth_var,
                                font=(FONT_M, 9), bg=BG_CARD, fg=TEXT)
        depth_spin.pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(toolbar, text="Filter (name/class/uid):", font=(FONT, 9), bg=BG, fg=TEXT_DIM
                 ).pack(side=tk.LEFT, padx=(12, 4))
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *a: self._apply_filter())
        self.filter_entry = tk.Entry(
            toolbar, textvariable=self.filter_var, font=(FONT_M, 9),
            bg=BG_CARD, fg=TEXT, insertbackground=TEXT, relief=tk.FLAT, width=24,
        )
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 8))

        self.status = tk.Label(toolbar, text="Ready — Select an item to view details", font=(FONT_M, 9), bg=BG, fg=TEXT_DIM)
        self.status.pack(side=tk.RIGHT)

        # Main content: list + detail
        main = tk.Frame(self.win, bg=BG)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left: list with tabs
        left = tk.Frame(main, bg=BG)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(left)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_DIM, padding=[12, 6])
        style.map("TNotebook.Tab", background=[("selected", BG)])

        # Tab 1: Unity hierarchy
        self.tab_hierarchy = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_hierarchy, text=" Unity Hierarchy ")

        list_frame = tk.Frame(self.tab_hierarchy, bg=BG)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.hierarchy_list = tk.Listbox(
            list_frame, font=(FONT_M, 9), bg=BG_CARD, fg=TEXT,
            selectbackground=ACCENT, selectforeground=BG,
            relief=tk.FLAT, highlightthickness=0,
        )
        y_scroll = tk.Scrollbar(list_frame)
        self.hierarchy_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.hierarchy_list.configure(yscrollcommand=y_scroll.set)
        y_scroll.configure(command=self.hierarchy_list.yview)
        self.hierarchy_list.bind("<<ListboxSelect>>", self._on_select_hierarchy)
        self.hierarchy_list.bind("<Motion>", self._on_hover_hierarchy)
        self.hierarchy_list.bind("<Leave>", self._on_leave_hierarchy)

        # Tab 2: Game entities
        self.tab_entities = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_entities, text=" Game Entities ")

        list_frame2 = tk.Frame(self.tab_entities, bg=BG)
        list_frame2.pack(fill=tk.BOTH, expand=True)

        self.entities_list = tk.Listbox(
            list_frame2, font=(FONT_M, 9), bg=BG_CARD, fg=TEXT,
            selectbackground=ACCENT, selectforeground=BG,
            relief=tk.FLAT, highlightthickness=0,
        )
        y_scroll2 = tk.Scrollbar(list_frame2)
        self.entities_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll2.pack(side=tk.RIGHT, fill=tk.Y)
        self.entities_list.configure(yscrollcommand=y_scroll2.set)
        y_scroll2.configure(command=self.entities_list.yview)
        self.entities_list.bind("<<ListboxSelect>>", self._on_select_entity)
        self.entities_list.bind("<Motion>", self._on_hover_entity)
        self.entities_list.bind("<Leave>", self._on_leave_entity)

        # Right: detail panel
        right = tk.Frame(main, bg=BG_CARD, width=380)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 0))
        right.pack_propagate(False)

        tk.Label(right, text="Object Info", font=(FONT_B, 11), bg=BG_CARD, fg=TEXT
                 ).pack(anchor=tk.W, padx=10, pady=(10, 4))
        tk.Label(right, text="Click an item to view details", font=(FONT, 9), bg=BG_CARD, fg=TEXT_DIM
                 ).pack(anchor=tk.W, padx=10, pady=(0, 8))

        detail_frame = tk.Frame(right, bg=BG_CARD)
        detail_frame.pack(fill=tk.BOTH, expand=True)

        self.detail_text = tk.Text(
            detail_frame, font=(FONT_M, 9), bg="#060a10", fg=TEXT_DIM,
            relief=tk.FLAT, highlightthickness=0, padx=10, pady=8,
            wrap=tk.WORD, state=tk.DISABLED,
        )
        d_scroll = tk.Scrollbar(detail_frame)
        self.detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        d_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text.configure(yscrollcommand=d_scroll.set)
        d_scroll.configure(command=self.detail_text.yview)

        self.detail_text.tag_configure("key", foreground=CYAN)
        self.detail_text.tag_configure("val", foreground=TEXT)
        self.detail_text.tag_configure("path", foreground=ORANGE)
        self.detail_text.tag_configure("header", foreground=PINK, font=(FONT_B, 10))

        self._hierarchy_data = []
        self._entities_data = []
        self._pinned_entity = None
        self._tooltip_win = None
        self._hovered_hierarchy_item = None
        self._hovered_entity_item = None
        self.win.bind("<F3>", self._on_f3_dump)
        self._refresh_hierarchy()
        self._refresh_entities()
        self._poll_hover()

    def _toggle_lock(self):
        if not self._locked_entity:
            self.status.configure(text="Hover over an entity in-game first, then click Lock")
            return
        self._hover_locked = not self._hover_locked
        if self._hover_locked:
            self.lock_btn.configure(text="🔓 Unlock")
            self._update_hovered_entity_in_ui()
        else:
            self._hover_locked = False
            self._locked_entity = None
            self._pinned_entity = None
            self.lock_btn.configure(text="📌 Lock")
            self._populate_entities()
            self.hover_label.configure(text="Move mouse over entity in game...", fg=TEXT_DIM)
            self.status.configure(text="Unlocked — hover to select entity")

    def _update_hovered_entity_in_ui(self):
        """Highlight in list, add pinned if not found, show in detail."""
        if not self._locked_entity:
            return
        uid = self._locked_entity.get("uid", "")
        if not uid:
            return
        # Search entities list for matching UID
        found_idx = -1
        for i, item in enumerate(getattr(self.entities_list, "_data", [])):
            if str(item.get("uid", "")) == str(uid):
                found_idx = i
                break
        if found_idx >= 0:
            self.entities_list.selection_clear(0, tk.END)
            self.entities_list.selection_set(found_idx)
            self.entities_list.see(found_idx)
            self.entities_list.activate(found_idx)
            self.notebook.select(self.tab_entities)
            self._show_detail(self.entities_list._data[found_idx], source="entity")
            self.status.configure(text=f"Found uid={uid} in list")
        else:
            # Not in list — fetch via ENTITY_BY_UID and add as pinned
            raw = self.conn._send(f"ENTITY_BY_UID {uid}") or ""
            if raw and raw not in ("NOT_FOUND", "INVALID_UID", "NO_ENTITY_MANAGER"):
                d = parse_kv(raw)
                d["class"] = self._locked_entity.get("class", "")
                self._pinned_entity = d
                self._populate_entities()
                # Select the pinned entity (first item) and show details
                self.entities_list.selection_clear(0, tk.END)
                self.entities_list.selection_set(0)
                self.entities_list.see(0)
                self.notebook.select(self.tab_entities)  # Switch to Game Entities tab
                self._show_detail(d, source="entity")
                self.status.configure(text=f"Pinned entity uid={uid} (not in scene list — fetched by UID)")

    def _poll_hover(self):
        try:
            if not self.win.winfo_exists():
                return
            if self._hover_locked:
                try:
                    self.win.after(HOVER_POLL_MS, self._poll_hover)
                except tk.TclError:
                    pass
                return
            raw = self.conn._send("ENTITY_UNDER_MOUSE") or ""
            if raw in ("NONE", "NO_INPUT", "IL2CPP_NOT_AVAILABLE"):
                self.hover_label.configure(text="No entity under cursor", fg=TEXT_DIM)
                self._locked_entity = None
            elif raw and "uid=" in raw:
                d = parse_kv(raw)
                name = d.get("name") or d.get("class") or "?"
                cls = d.get("class", "")
                uid = d.get("uid", "")
                x, y, z = d.get("x", ""), d.get("y", ""), d.get("z", "")
                pos = f" @ ({x},{y},{z})" if x and y and z else ""
                txt = f"{name}  [{cls}]  uid={uid}{pos}"
                self.hover_label.configure(text=txt, fg=GREEN)
                self._locked_entity = d
            else:
                self.hover_label.configure(text="Move mouse over entity in game...", fg=TEXT_DIM)
                self._locked_entity = None
        except Exception:
            pass
        try:
            self.win.after(HOVER_POLL_MS, self._poll_hover)
        except tk.TclError:
            pass

    def _refresh_hierarchy(self):
        try:
            depth = int(self.depth_var.get())
        except ValueError:
            depth = 6
        depth = max(2, min(10, depth))
        self.status.configure(text="Loading Unity hierarchy...")
        self.win.update()
        raw = self.conn._send(f"SCENE_DUMP_{depth}") or ""
        self._hierarchy_data = parse_scene_dump(raw)
        self._populate_hierarchy()
        err = raw[:80] if raw and not self._hierarchy_data and "ROOTS=" not in raw else ""
        self.status.configure(text=f"Unity: {len(self._hierarchy_data)} objects" + (f" — {err}" if err else ""))

    def _refresh_entities(self):
        self.status.configure(text="Loading game entities...")
        self.win.update()
        raw = self.conn._send("SCENE_ADDRESSES") or ""
        self._entities_data = parse_scene_addresses(raw)
        if not self._entities_data:
            raw = self.conn._send("SCENE_ALL") or ""
            self._entities_data = parse_scene_all(raw)
        self._populate_entities()
        self.status.configure(text=f"Entities: {len(self._entities_data)}")

    def _populate_hierarchy(self):
        self.hierarchy_list.delete(0, tk.END)
        flt = (self.filter_var.get() or "").lower()
        for item in self._hierarchy_data:
            if flt and flt not in item["path"].lower() and flt not in item["name"].lower():
                continue
            indent = "  " * item["depth"]
            self.hierarchy_list.insert(tk.END, f"{indent}{item['name']}")
        self.hierarchy_list._data = [i for i in self._hierarchy_data
                                     if not flt or flt in i["path"].lower() or flt in i["name"].lower()]

    def _populate_entities(self):
        self.entities_list.delete(0, tk.END)
        flt = (self.filter_var.get() or "").lower()
        data = list(self._entities_data)
        # Prepend pinned entity when locked & not in scene list (fetched via ENTITY_BY_UID)
        if self._pinned_entity:
            pin_uid = str(self._pinned_entity.get("uid", ""))
            if not any(str(i.get("uid", "")) == pin_uid for i in self._entities_data):
                data = [self._pinned_entity] + data
        inserted_data = []
        for item in data:
            name = item.get("name") or item.get("class") or "?"
            if name == "?" and item.get("class"):
                name = item.get("class")
            uid = item.get("uid", "")
            cls = item.get("class", "")
            is_pinned = item is self._pinned_entity
            searchable = (item.get("name", "") + item.get("class", "") + str(uid)).lower()
            if flt and not is_pinned and flt not in searchable:
                continue
            if uid:
                display = f"{name}  (uid={uid})" if name != "?" else f"{cls}  (uid={uid})"
            else:
                display = name if name != "?" else cls or "?"
            prefix = "📌 " if item is self._pinned_entity else ""
            self.entities_list.insert(tk.END, prefix + display)
            inserted_data.append(item)
        self.entities_list._data = inserted_data

    def _apply_filter(self):
        if hasattr(self.hierarchy_list, "_data"):
            self._populate_hierarchy()
        if hasattr(self.entities_list, "_data"):
            self._populate_entities()

    def _on_select_hierarchy(self, evt):
        sel = self.hierarchy_list.curselection()
        if not sel or not hasattr(self.hierarchy_list, "_data"):
            return
        idx = sel[0]
        if idx >= len(getattr(self.hierarchy_list, "_data", [])):
            return
        item = self.hierarchy_list._data[idx]
        self._show_detail(item, source="unity")

    def _on_select_entity(self, evt):
        sel = self.entities_list.curselection()
        if not sel or not hasattr(self.entities_list, "_data"):
            return
        idx = sel[0]
        if idx >= len(getattr(self.entities_list, "_data", [])):
            return
        item = self.entities_list._data[idx]
        self._show_detail(item, source="entity")

    def _on_hover_hierarchy(self, evt):
        idx = self.hierarchy_list.nearest(evt.y)
        if idx < 0 or not hasattr(self.hierarchy_list, "_data") or idx >= len(self.hierarchy_list._data):
            self._hide_tooltip()
            self._hovered_hierarchy_item = None
            return
        item = self.hierarchy_list._data[idx]
        self._hovered_hierarchy_item = item
        self._show_tooltip(f"Path: {item.get('path', '')}\nName: {item.get('name', '')}", evt)

    def _on_hover_entity(self, evt):
        idx = self.entities_list.nearest(evt.y)
        if idx < 0 or not hasattr(self.entities_list, "_data") or idx >= len(self.entities_list._data):
            self._hide_tooltip()
            self._hovered_entity_item = None
            return
        item = self.entities_list._data[idx]
        self._hovered_entity_item = item
        lines = [f"{k}: {v}" for k, v in item.items() if v][:8]
        self._show_tooltip("\n".join(lines), evt)

    def _show_tooltip(self, text, evt):
        self._hide_tooltip()
        self._tooltip_win = tk.Toplevel(self.win)
        self._tooltip_win.wm_overrideredirect(True)
        self._tooltip_win.wm_geometry(f"+{evt.x_root + 12}+{evt.y_root + 12}")
        lbl = tk.Label(
            self._tooltip_win, text=text, font=(FONT_M, 9),
            bg=BG_CARD, fg=TEXT, relief=tk.SOLID, borderwidth=1,
            padx=8, pady=6,
        )
        lbl.pack()
        self._tooltip_win.after(3000, self._hide_tooltip)

    def _hide_tooltip(self, evt=None):
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except tk.TclError:
                pass
            self._tooltip_win = None

    def _on_leave_hierarchy(self, evt=None):
        self._hide_tooltip()
        self._hovered_hierarchy_item = None

    def _on_leave_entity(self, evt=None):
        self._hide_tooltip()
        self._hovered_entity_item = None

    def _on_f3_dump(self, evt=None):
        """F3: Dump whatever is hovered over into the Debug/Log window."""
        item = None
        source = ""
        try:
            tab_idx = self.notebook.index(self.notebook.select())
            if tab_idx == 0 and self._hovered_hierarchy_item:
                item = self._hovered_hierarchy_item
                source = "Unity Hierarchy"
            elif tab_idx == 1 and self._hovered_entity_item:
                item = self._hovered_entity_item
                source = "Game Entity"
            if not item and self._locked_entity:
                item = self._locked_entity
                source = "In-Game (entity under cursor)"
        except Exception:
            pass
        if not item:
            print("[Scene Explorer] F3: Nothing to dump — hover over a list item or an entity in-game.")
            return
        lines = [f"═══ F3 DUMP ({source}) ═══"]
        if source == "Unity Hierarchy":
            lines.append(f"Path: {item.get('path', '')}")
            lines.append(f"Name: {item.get('name', '')}")
            ptr = self.conn.scene_find(item.get("name", ""))
            if ptr and "PTR=" in ptr:
                lines.append(f"Pointer: {ptr.replace('PTR=', '')}")
        else:
            for k, v in sorted(item.items()):
                if v:
                    lines.append(f"{k}: {v}")
        lines.append("═" * 40)
        for line in lines:
            print(line)
        self.status.configure(text=f"Dumped to Log ({source})")

    def _show_detail(self, item, source="unity"):
        self.detail_text.configure(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)

        if source == "unity":
            self.detail_text.insert(tk.END, "Unity GameObject\n", "header")
            self.detail_text.insert(tk.END, "\nPath: ", "key")
            self.detail_text.insert(tk.END, item.get("path", ""), "path")
            self.detail_text.insert(tk.END, "\n\nName: ", "key")
            self.detail_text.insert(tk.END, item.get("name", ""), "val")
            ptr = self.conn.scene_find(item.get("name", ""))
            if ptr and "PTR=" in ptr:
                self.detail_text.insert(tk.END, "\n\nPointer: ", "key")
                self.detail_text.insert(tk.END, ptr.replace("PTR=", ""), "val")
        else:
            self.detail_text.insert(tk.END, "Game Entity\n", "header")
            for k, v in sorted(item.items()):
                if v:
                    self.detail_text.insert(tk.END, f"\n{k}: ", "key")
                    self.detail_text.insert(tk.END, str(v), "val")
            if item.get("name"):
                path = f"Entity/{item.get('name', '')}"
                if item.get("uid"):
                    path += f" (uid={item.get('uid')})"
                self.detail_text.insert(tk.END, "\n\nPath: ", "key")
                self.detail_text.insert(tk.END, path, "path")

        self.detail_text.configure(state=tk.DISABLED)

    def _on_close(self):
        self._tooltip_win = None
        try:
            self.win.destroy()
        except tk.TclError:
            pass


print("")
print("=" * 60)
print("  Scene Explorer — Opening dashboard...")
print("=" * 60)
print("")

ui = SceneExplorerUI()
print("  Dashboard open. Select items to view game info.")
print("")
