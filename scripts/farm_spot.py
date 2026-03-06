"""
Farm a spot — fight + loot + rest. Print stats on stop.
"""
from ethytool_wraps import *

log(f"⚔ Farming as {my_class()} — {len(spell_names())} spells loaded")

while alive():
    # Wait for a target
    while not has_target():
        wait(0.5)

    # Fight it
    fight()

    # Loot
    wait(0.5)
    loot()

    # Rest up
    recover()

    wait(0.3)

stats()