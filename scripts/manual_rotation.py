"""
Manual control — rotate() in a loop with custom logic.
"""
from ethytool_wraps import *

while alive():
    if not has_target():
        wait(0.5)
        continue

    # Buff up
    buff()

    # Defensive if low
    if low_hp(20):
        defend()

    # Nuke if stacks are full
    if stacks() >= 20:
        log(f"🗡 NUKE! {stacks()} stacks!")
        nuke()
    else:
        # Normal rotation
        rotate()

    wait(0.3)