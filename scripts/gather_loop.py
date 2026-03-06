"""
Auto-gather nearest nodes in a loop.
"""
from ethytool_wraps import *

TARGET = "Iron"  # Change to whatever you're farming

while alive():
    node = closest_node(TARGET)
    if node:
        name = node.get("name", TARGET)
        log(f"Gathering: {name}")
        gather(name)
    else:
        log("No nodes found, waiting...")
        wait(5)