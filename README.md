# EthyTool

Hit that Star Button if you enjoy this!

Hit Pull Request to merge your scripts/updates!

Work in Progress

A modding and scripting toolkit for Ethyrial: Echoes of Yore. Read game data, interact with entities, build overlays, track stats, create custom tools — all through a simple Python API.

---

## TODO

- [ ] Review/fix pipe diagnostic (`check_pipe_block.bat`) if needed
- [ ] Improve or extend `auto_gather.py` template
- [ ] Update/maintain dump scripts (spells, doodad, monster codex)
- [ ] Add or refine EthyTool features
- [ ] Documentation / README updates
- [ ] Interrupt (combat/interrupt handling)
- [ ] Target skills

---

## Key Required

**A key is required to use EthyTool.** On first launch you will be prompted to enter your key. Reach out to **MrJambix** on Discord for a key.

Keys are validated locally inside the EXE — no internet connection or server required at launch.

---

## Requirements

- **Windows 10/11**
- **Python 3.10+** — [Download here](https://www.python.org/downloads/)
  - Use the **classic executable installer** — **do not use the new Python Installation Manager** (Store/WinGet). The new installer can cause compatibility issues.
  - During install, check **"Add Python to PATH"**
- **Ethyrial: Echoes of Yore**

---

## Setup

1. Download the latest release
2. Extract to any folder
3. **Run `install_all.bat`** (right-click → Run as administrator) — installs VC++ Redist, Defender exclusion, firewall rules, and optional Python packages
4. Or install manually:
   - Install Python if you haven't already (classic installer only)
   - Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. **Get a key** — reach out to **MrJambix** on Discord
6. Launch the game
7. Run `EthyTool.exe`
8. Enter your key when prompted
9. Click **Inject**
10. Open the Scripts tab and run scripts

---

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

---

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

---

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

---

## Global Hotkeys

Once the Dashboard is connected to the game, these hotkeys work system-wide — even while the game window is focused:

| Key | Action |
|-----|--------|
| **F5** | Stop all running scripts immediately |
| **F6** | Pause / Resume all running scripts |

Hotkeys are registered automatically on connect and unregistered cleanly when the Dashboard closes.

---

## Screen Reader & Computer Vision

`ScreenReader` lets scripts capture the game screen and do template matching — useful for reading UI elements the API doesn't expose directly.

```python
from ethytool_lib import ScreenReader

sr = ScreenReader()

# Screenshot the game window (uses mss for ~5ms capture)
frame = sr.screenshot()

# Find an image on screen — returns (x, y, confidence) or None
match = sr.find_image("templates/health_low.png", threshold=0.80)
if match:
    x, y, conf = match
    print(f"Found at ({x}, {y})  confidence={conf:.2f}")
```

**How it works:**
- Uses **mss** for ultra-fast screen capture (~5ms vs ~100ms with PIL)
- Uses **pywin32** to find and lock onto the Ethyrial game window automatically — captures only that window, not your whole screen
- Falls back to full-desktop capture if the game window isn't found
- Uses **OpenCV** for template matching

**Install dependencies** (already included in `requirements.txt`):
```bash
pip install mss pywin32 opencv-python Pillow
```

---

## Process Monitoring

EthyTool automatically watches the injected game process. If the game crashes or is closed:

- All running scripts are stopped immediately
- The Dashboard status updates to **"Game Closed"**
- A log entry is written with a timestamp

No manual cleanup needed — your scripts won't hang if the game dies unexpectedly.

Powered by **psutil**.

---

## DPS Dashboard

The built-in DPS Dashboard (`scripts/dps_dashboard.py`) tracks your damage output in real time and renders live charts.

```bash
# Run from the Scripts tab in EthyTool, or directly:
python scripts/dps_dashboard.py
```

Features:
- Live DPS graph per class/build
- Session recording — saves to `scripts/sessions/`
- Compare multiple sessions side-by-side
- Powered by **matplotlib** and **numpy**

---

## Combat Rotations

1. Copy `scripts/rotations/template.py`
2. Rename to your class (e.g. `warrior.py`)
3. Fill in your spell names
4. Run `combat.py` — it detects your class and loads the rotation

---

## Python Dependencies

All dependencies are bundled inside `EthyTool.exe`. If running scripts directly (not through the EXE), install with:

```bash
pip install -r requirements.txt
```

| Package | Version | Purpose |
|---------|---------|---------|
| `pyyaml` | ≥6.0 | Config file loading |
| `opencv-python` | ≥4.8 | Template matching / computer vision |
| `mss` | ≥9.0 | Fast screen capture (~5ms, multi-monitor) |
| `Pillow` | ≥10.0 | Image utilities, screenshot fallback |
| `numpy` | ≥1.24 | Array processing for screen capture & DPS charts |
| `matplotlib` | ≥3.7 | DPS Dashboard live charts |
| `pywin32` | ≥306 | Win32 API — reliable game window detection |
| `keyboard` | ≥0.13 | Global hotkeys (F5/F6) — work even in-game |
| `psutil` | ≥5.9 | Process monitoring — auto-stop on game crash |
| `pydantic` | ≥2.0 | Bot profile/config validation |
| `watchdog` | ≥3.0 | Hot reload — edit scripts without restarting |
| `rich` | ≥13.0 | CLI output formatting |
| `typer` | ≥0.9 | CLI command interface |

---

## Folder Structure

```
EthyTool/
├── EthyTool.exe              run this
├── EthyTool.dll              auto-injected
├── install_all.bat           full setup (VC++, Defender, firewall, deps)
├── install_firewall.ps1       used by install_all.bat
├── check_pipe_block.bat      pipe diagnostic if connection fails
├── server_config.yaml        token list (keys validated locally)
├── requirements.txt          Python dependencies
├── lib/
│   ├── ethytool_lib.py       low-level API + ScreenReader
│   └── ethytool_wraps.py     simple API
├── scripts/                  your scripts go here
│   ├── auto_rotation.py
│   ├── dps_dashboard.py      live DPS charts
│   ├── loot_all.py
│   ├── builds/               class rotations
│   ├── debugs/               debug utilities
│   ├── dumps/                dump scripts (spells, doodads, etc.)
│   ├── templates/            auto_gather, auto_farm, etc.
│   └── plugins/
└── docs/
    ├── WRAPS.md              wraps reference
    ├── COMMANDS.md           raw DLL commands
    └── SCRIPTING.md          how to write scripts
```

---

## Links

- [Wraps Reference](docs/WRAPS.md) — every simple function
- [Scripting Guide](docs/SCRIPTING.md) — how to write scripts
- [DLL Commands](docs/COMMANDS.md) — raw pipe commands
