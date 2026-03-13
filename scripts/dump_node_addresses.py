"""
Node Address & Offset Dump — memory pointers, UIDs, hidden/spawned state for all nearby resource nodes.
Run from EthyTool dashboard.
"""
import time

try:
    conn
except NameError:
    print("ERROR: Run from EthyTool dashboard.")
    raise SystemExit(1)

RESOURCE_CLASSES = {"Doodad", "HarvestNode", "GatherableEntity", "ResourceNode",
                    "InteractableEntity", "StaticEntity"}

SEP = "=" * 72

def dump():
    print(f"\n{SEP}")
    print(f"  Node Address & Offset Dump — {time.strftime('%H:%M:%S')}")
    print(SEP)

    px, py, pz = conn.get_position()
    print(f"\n  Player pos: ({px:.1f}, {py:.1f}, {pz:.1f})")

    # --- NEARBY_ADDRESSES (NearbyEntities list with raw pointers) ---
    nearby = conn.get_nearby_addresses()
    nearby_nodes = [e for e in nearby if e.get("class", "") in RESOURCE_CLASSES or e.get("static")]
    nearby_nodes.sort(key=lambda e: e.get("name", ""))

    print(f"\n{'─'*72}")
    print(f"  NEARBY ENTITIES — {len(nearby)} total, {len(nearby_nodes)} resource nodes")
    print(f"{'─'*72}")

    if nearby_nodes:
        for e in nearby_nodes:
            ptr = e.get("ptr", 0)
            uid = e.get("uid", 0)
            name = e.get("name", "(no name)")
            cls = e.get("class", "?")
            ex, ey, ez = e.get("x", 0), e.get("y", 0), e.get("z", 0)
            hid = e.get("hidden", False)
            spwn = e.get("spawned", False)
            static = e.get("static", False)

            import math
            dist = math.sqrt((float(ex) - px)**2 + (float(ey) - py)**2)
            tag = "HIDDEN" if hid else "VISIBLE"

            print(f"\n  [{tag:7s}] {name}")
            print(f"    ptr    = 0x{ptr:X}" if isinstance(ptr, int) else f"    ptr    = {ptr}")
            print(f"    uid    = {uid}")
            print(f"    class  = {cls}")
            print(f"    pos    = ({float(ex):.1f}, {float(ey):.1f}, {float(ez):.1f})  dist={dist:.1f}m")
            print(f"    hidden = {hid}  spawned = {spwn}  static = {static}")
    else:
        print("    (no resource nodes in NearbyEntities)")

    # --- Class breakdown of ALL nearby entities ---
    class_counts = {}
    for e in nearby:
        c = e.get("class", "?")
        class_counts[c] = class_counts.get(c, 0) + 1
    print(f"\n{'─'*72}")
    print(f"  NEARBY CLASS BREAKDOWN ({len(nearby)} entities)")
    print(f"{'─'*72}")
    for cls, cnt in sorted(class_counts.items(), key=lambda x: -x[1]):
        print(f"    x{cnt:3d}  {cls}")

    # --- SCENE_ADDRESSES (EntityManager — full scene) ---
    scene = conn.get_scene_addresses()
    scene_nodes = [e for e in scene if e.get("class", "") in RESOURCE_CLASSES or
                   (e.get("static") and e.get("class", "") not in
                    {"LocalPlayerEntity", "PlayerEntity", "LivingEntity",
                     "NPCEntity", "MonsterEntity", "HostileEntity", "WallEntity", "DoorEntity"})]
    scene_nodes.sort(key=lambda e: e.get("name", ""))

    print(f"\n{'─'*72}")
    print(f"  SCENE ENTITIES — {len(scene)} total, {len(scene_nodes)} resource nodes")
    print(f"{'─'*72}")

    node_summary = {}
    for e in scene_nodes:
        name = e.get("name", "(no name)")
        hid = e.get("hidden", False)
        key = (name, bool(hid))
        if key not in node_summary:
            node_summary[key] = {"name": name, "hidden": hid, "count": 0, "ptrs": []}
        node_summary[key]["count"] += 1
        ptr = e.get("ptr", 0)
        if len(node_summary[key]["ptrs"]) < 3:
            node_summary[key]["ptrs"].append(ptr)

    for entry in sorted(node_summary.values(), key=lambda x: (x["hidden"], x["name"])):
        tag = "HIDDEN" if entry["hidden"] else "VISIBLE"
        ptrs = ", ".join(f"0x{p:X}" if isinstance(p, int) else str(p) for p in entry["ptrs"])
        more = f" +{entry['count']-3} more" if entry["count"] > 3 else ""
        print(f"    [{tag:7s}] x{entry['count']:3d}  {entry['name']!r}")
        print(f"              ptrs: {ptrs}{more}")

    # --- SCAN_NEARBY raw fields (for nodes with full pipe data) ---
    print(f"\n{'─'*72}")
    print(f"  RAW SCAN_NEARBY — first 20 resource nodes (all fields)")
    print(f"{'─'*72}")

    raw = conn._send("SCAN_NEARBY")
    raw_nodes = []
    if raw and not raw.startswith("NO_") and not raw.startswith("BAD_"):
        for block in raw.split("###"):
            if block.startswith("count=") or not block.strip():
                continue
            d = {}
            for pair in block.split("|"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    d[k] = v
            if d.get("class") in ("Doodad",) or d.get("static") == "1":
                raw_nodes.append(d)

    for i, d in enumerate(raw_nodes[:20]):
        name = d.get("name", "?")
        print(f"\n  [{i}] {name}")
        for k, v in sorted(d.items()):
            print(f"      {k:15s} = {v}")

    # --- Corpses ---
    print(f"\n{'─'*72}")
    print(f"  CORPSES (SCENE_CORPSES)")
    print(f"{'─'*72}")
    corpses = conn.get_scene_corpses()
    if corpses:
        for c in corpses:
            print(f"    uid={c.get('uid')}  of={c.get('of')}  cont={c.get('cont')}  "
                  f"pos=({c.get('x',0):.1f}, {c.get('y',0):.1f}, {c.get('z',0):.1f})")
    else:
        print("    (no corpses)")

    print(f"\n{SEP}")
    print(f"  Done — {len(nearby)} nearby, {len(scene)} scene, {len(corpses)} corpses")
    print(SEP)


dump()
