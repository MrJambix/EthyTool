"""
Auto-Rotation — YOU pull, it fights.
"""
import time

cls = conn.detect_class()
profile = conn.load_profile()

if not profile:
    conn.log(f"ERROR: No profile for '{cls}'")

conn.log(f"")
conn.log(f"  ⚔ AUTO-ROTATION — {cls}")

if profile:
    conn.log(f"  Rotation: {getattr(profile, 'ROTATION', [])}")
    conn.log(f"  Profile loaded OK")
else:
    conn.log(f"  No profile — generic mode")

conn.log(f"  Waiting for combat...")

was_in_combat = False
tick = getattr(profile, "TICK_RATE", 0.3) if profile else 0.3
def_trigger = getattr(profile, "DEFENSIVE_TRIGGER_HP", 20) if profile else 20
def_hp = getattr(profile, "DEFENSIVE_HP", 40) if profile else 40
rest_hp = getattr(profile, "REST_HP", 70) if profile else 70

while not stop_event.is_set() and conn.is_alive():

    in_combat = conn.in_combat()
    hp = conn.get_hp()

    if in_combat:
        if not was_in_combat:
            conn.log(f"  ⚔ Combat started!")
            conn.do_buff()
            conn.do_pull()
            was_in_combat = True

        if hp < def_trigger:
            conn.do_defend()
        elif hp < def_hp:
            conn.do_defend()

        if profile:
            conn.do_rotation()
        else:
            for s in conn.get_class_spells():
                if conn.try_cast(s):
                    break
    else:
        if was_in_combat:
            conn._state.kills += 1
            conn.log(f"  ✓ Kill #{conn._state.kills} (HP:{hp:.0f}%)")
            was_in_combat = False

            if hp < rest_hp:
                conn.log(f"  💊 Resting...")
                conn.do_recover(hp_target=90, mp_target=80, timeout=30)
                conn.log(f"  ✓ Ready")

    time.sleep(tick)

conn.print_stats()