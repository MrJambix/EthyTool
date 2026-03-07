# EthyTool

A modding and scripting toolkit for Ethyrial: Echoes of Yore. Read game data, interact with entities, build overlays, track stats, create custom tools — all through a simple Python API.

## Requirements

- **Windows 10/11**
- **Python 3.10+** — [Download here](https://www.python.org/downloads/)
  - During install, check **"Add Python to PATH"**
- **Ethyrial: Echoes of Yore**

## Setup

1. Download the latest release
2. Extract to any folder
3. Install Python if you haven't already
4. Launch the game
5. Run `EthyTool.exe`
6. Click **Inject**
7. Open the Scripts tab and run scripts

## What Can You Do?

### Read Game Data
Access any information the game client knows about — your character, targets, nearby entities, inventory, the entire scene.

```python
from ethytool_wraps import *

print(f"HP: {hp()}%  MP: {mp()}%")
print(f"Gold: {gold()}")
print(f"Position: {pos()}")
print(f"Target: {target_name()} at {target_hp()}% HP")
print(f"Nearby: {nearby_count()} entities")
```

### Entity Scanning
See everything around you — NPCs, monsters, players, gathering nodes, objects. Filter by type, check states, find specific things.

```python
from ethytool_wraps import *

for e in scan():
    print(f"  {e['class']:15s}  {e['name']}")

for node in harvestable():
    print(f"  {node['name']}  hidden={node['hidden']}")

chest = find_scene("Treasure Chest")
if chest:
    print(f"Chest at ({chest['x']}, {chest['y']})")
```

### Interact With the World
Cast spells, interact with entities, loot containers.

```python
from ethytool_wraps import *

cast("Fireball")
use("Campfire")
gather("Stone")
loot()
```

### Inventory and Equipment Tracking
Check what you have, count stacks, find specific items.

```python
from ethytool_wraps import *

for item in items():
    print(f"  {item['name']} x{item['stack']}")

ore = count_item("Iron Ore")
print(f"Iron Ore: {ore}")

if has("Health Potion"):
    print("Got potions")
```

### Build Custom Overlays and Tools
Use the data to build anything — stat trackers, map overlays, alert systems, damage logs.

```python
from ethytool_wraps import *

while True:
    data = all_stats()
    print(f"HP: {data['hp']:.0f}%  MP: {data['mp']:.0f}%  Gold: {data['gold']}")
    if data['combat']:
        print(f"  FIGHTING: {target_name()}")
    sleep(1)
```

### Camera Access
Read camera position, zoom level, rotation angle, pitch.

```python
from ethytool_wraps import *

cam = camera()
print(f"Zoom: {cam['distance']}  Angle: {cam['angle']}  Pitch: {cam['pitch']}")
```

## Writing Scripts

Scripts go in the `scripts/` folder. Two ways to use the API:

### Simple Mode (recommended)
```python
from ethytool_wraps import *

hp()              # your health %
cast("Fireball")  # cast a spell
gather("Stone")   # gather a node
loot()            # loot everything
sleep(1)          # wait 1 second
```

### Advanced Mode
```python
target = conn.get_target()
if target:
    print(f"Target: {target['name']} HP: {target['hp']}")

spells = conn.get_spells()
for s in spells:
    print(f"  {s['display']}  CD: {s['cur_cd']}s  Mana: {s['mana']}")
```

## Quick Reference

| Simple (wraps) | Advanced (lib) | What it does |
|---|---|---|
| `hp()` | `conn.get_hp()` | Your HP % |
| `mp()` | `conn.get_mp()` | Your MP % |
| `gold()` | `conn.get_gold()` | Your gold |
| `pos()` | `conn.get_position()` | Your (x, y, z) |
| `combat()` | `conn.in_combat()` | In combat? |
| `cast("Heal")` | `conn.cast("Heal")` | Cast a spell |
| `cast_first([...])` | `conn.cast_first([...])` | Cast first available |
| `has_target()` | `conn.has_target()` | Have a target? |
| `target_hp()` | `conn.get_target_hp()` | Target HP % |
| `target_name()` | `conn.get_target_name()` | Target name |
| `use("Stone")` | `conn.use_entity("Stone")` | Interact with entity |
| `gather("Stone")` | `conn.gather("Stone")` | Full gather cycle |
| `harvestable()` | `conn.scan_harvestable()` | List full nodes |
| `loot()` | `conn.loot()` | Loot all |
| `items()` | `conn.get_inventory()` | Your inventory |
| `has("Potion")` | `conn.has_item("Potion")` | Have an item? |
| `scan()` | `conn.scan_nearby()` | Nearby entities |
| `nearby_mobs()` | `conn.get_nearby_mobs()` | Living entities |
| `find("Wolf")` | `conn.find_nearby("Wolf")` | Find by name |
| `scene()` | `conn.get_scene()` | All scene entities |
| `my_class()` | `conn.detect_class()` | Your class |
| `spell_names()` | `conn.get_spell_names()` | All spell names |
| `sleep(1)` | `time.sleep(1)` | Wait |

Full reference: [docs/WRAPS.md](docs/WRAPS.md)

## Folder Structure

```
EthyTool/
├── EthyTool.exe              run this
├── EthyTool.dll              auto-injected
├── lib/
│   ├── ethytool_lib.py       low-level API
│   └── ethytool_wraps.py     simple API
├── scripts/                  your scripts go here
│   ├── combat.py
│   ├── harvest.py
│   ├── auto_loot.py
│   └── rotations/
│       ├── template.py       copy and rename for your class
│       └── ...
└── docs/
    ├── WRAPS.md              wraps reference
    ├── COMMANDS.md            raw DLL commands
    └── SCRIPTING.md           how to write scripts
```

## Combat Rotations

1. Copy `scripts/rotations/template.py`
2. Rename to your class (e.g. `warrior.py`)
3. Fill in your spell names
4. Run `combat.py` — it detects your class and loads the rotation

## Links

- [Wraps Reference](docs/WRAPS.md) — every simple function
- [Scripting Guide](docs/SCRIPTING.md) — how to write scripts
- [DLL Commands](docs/COMMANDS.md) — raw pipe commands
