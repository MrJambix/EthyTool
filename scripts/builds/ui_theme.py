"""
Investigate map fog removal — what controls explored/unexplored areas.
"""
def send(cmd):
    return conn._send(cmd)

print()
print("+" + "-" * 58 + "+")
print("|  MAP FOG INVESTIGATION                                    |")
print("+" + "-" * 58 + "+")
print()

# WorldMap is resolved — read its instance fields
print("  === WorldMap Instance Data ===")
print()

# WorldMap has a static Instance field at 0x020
# Read key fields from the instance
r = send("DUMP_FIELDS_WorldMap")
if r:
    print("  Fields:")
    for f in r.split("|"):
        print(f"    {f}")
print()

# Key fields from WorldMap:
# 0x028 mapParts    — ConcurrentDictionary<Position, MinimapPart>
# 0x038 textureCount — int
# 0x03C HasLoadedFiles — bool
# 0x040 lastMap      — Map
# 0x0A0 saveTimer    — float
# 0x0A4 textureApplyTimer — float

# Methods that matter:
# get_DrawRange() — how many tiles around player are visible
# MapPartLoaded(Position) — is a tile explored?
# HasMapTexture(Position) — does a tile have texture data?
# GetMapTexture(Position) — get the actual texture
# _loadAllMapFiles(Map) — loads_*
