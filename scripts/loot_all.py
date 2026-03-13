"""
Auto-Loot — loots NEW corpse windows when they appear.
⚠ Known issue: LOOT_ALL also hits quest bag panels (DLL limitation).
   Quest items may move to regular inventory. Toggle loot off if this bothers you.
Run from EthyTool dashboard. Stop the script to quit.
"""
import time

try:
    conn
    stop_event
except NameError:
    print("ERROR: Run this from the EthyTool dashboard.")
    raise SystemExit(1)

POLL_FAST = 0.15
POLL_IDLE = 0.4

looted_total = 0

print("")
print("=" * 60)
print("  Auto-Loot  (stop script to quit)")
print("=" * 60)
print("")
print("  ⚠ LOOT_ALL also affects quest bag panels (DLL limitation).")
print("  Quest items may move to regular inventory.")
print("")

try:
    baseline = int(conn._send("LOOT_WINDOW_COUNT") or "0")
except (ValueError, TypeError):
    baseline = 0

print(f"  Baseline: {baseline} window(s) — watching for NEW windows only")
print("")

prev = baseline
while not stop_event.is_set():
    try:
        raw = conn._send("LOOT_WINDOW_COUNT")
        current = int(raw) if raw else 0
    except (ValueError, TypeError):
        current = 0

    if current > prev and current > baseline:
        new_count = current - prev
        raw_loot = conn._send("LOOT_ALL")

        if raw_loot and raw_loot.startswith("OK"):
            looted_total += new_count
            print(f"  💰 Looted {new_count} new window(s)  [total: {looted_total}]")
        else:
            print(f"  ! LOOT_ALL: {raw_loot!r}")

        try:
            current = int(conn._send("LOOT_WINDOW_COUNT") or "0")
        except (ValueError, TypeError):
            pass

    if current < baseline:
        baseline = current

    prev = current
    time.sleep(POLL_FAST if conn.in_combat() else POLL_IDLE)

print("")
print("=" * 60)
print(f"  Stopped  —  Looted: {looted_total}")
print("=" * 60)
