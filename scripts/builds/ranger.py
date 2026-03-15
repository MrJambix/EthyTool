"""
╔══════════════════════════════════════════════════════════════╗
║               RANGER — Pet / Bow Build                       ║
║                                                              ║
║  Playstyle: Ranged DPS with spirit pet — arrows + pet wrath  ║
║  Spirit Shot, Spiritbeast's Wrath, Linked Rejuvenation heal   ║
║  Spiritualism discipline level checks (lv 5,10,15,20,25)      ║
╚══════════════════════════════════════════════════════════════╝
"""

# Spiritualism discipline level required for each skill.
# Attack has no requirement (always usable).
# Set your level here if the game doesn't expose it (e.g. SPIRITUALISM_LEVEL = 10).
SPIRITUALISM_LEVEL = 10   # Spiritburst + Spiritlife Arrow unlocked

SKILL_LEVEL_REQUIREMENTS = {
    "Spiritroot Arrow": 5,
    "Verdant Barrage": 5,
    "Spiritlife Arrow": 10,
    "Spiritburst Arrow": 10,
    "Linked Rejuvenation": 15,
    "Nature's Swiftness": 15,
    "Spiritbeast's Wrath": 20,
}

# Spells to skip — built from level (blocks Spiritbeast's Wrath until lv 20, etc.)
# Nature Arrows: toggle spell, not a rotation filler — ignore globally in ethytool_lib too
# Summons: never auto-cast in combat
IGNORED_SPELLS = {
    s for s, req in SKILL_LEVEL_REQUIREMENTS.items() if SPIRITUALISM_LEVEL < req
} | {"Nature Arrows", "Summon Spirit Alpha", "Summon Spirit Cub", "Summon Spirit Wolf"}

HEAL_HP        = 70
DEFENSIVE_HP   = 40
EMERGENCY_HP   = 25
REST_HP        = 70
REST_MP        = 80

TICK_RATE = 0.3
GCD       = 0.3

BUFFS = [
    "Nature's Swiftness",        # Self buff (30s CD)
]

# Don't cast if already active (detected via PLAYER_BUFFS)
BUFF_CONFIG = {
    "Nature's Swiftness": {
        "detect_buff": True,
        "buff_ids": ["Nature's Swiftness", "NaturesSwiftness"],
    },
}

PET_SPELLS = [
    "Attack",                     # Send pet to attack target (pull start)
]
PET_ROTATION = [
    "Attack",                     # Re-send pet to target when switching
    "Spiritbeast's Wrath",        # Pet damage ability
]

# Tried first every tick when ready — before pet, before rotation
MANA_BUILDER_PRIORITY = [
    "Spiritburst Arrow",          # Restores mana; use whenever off CD
]

OPENER = [
    "Nature's Swiftness",
    "Spiritburst Arrow",         # Mana builder — use first
    "Spiritbeast's Wrath",
    "Spirit Shot",
]

ROTATION = [
    "Spiritbeast's Wrath",       # Big hit (30s CD)
    "Spiritroot Arrow",          # (16s CD)
    "Spirit Shot",               # (10s CD)
    "Spiritlife Arrow",          # CC/damage (10s CD)
    "Verdant Barrage",           # Short CD (4s, 0.5s cast)
]
# Spiritburst Arrow in MANA_BUILDER_PRIORITY — tried before this rotation

HEAL_SPELLS = [
    "Linked Rejuvenation",      # Self heal (30s CD, 1s cast)
]

DEFENSIVE_SPELLS = []            # Ranger has no shield; Nature's Swiftness in buffs

DEFENSIVE_TRIGGER_HP = 20

REST_SPELL = "Rest"
REST_ENABLED = False             # Don't auto-use Rest; use manually
MEDITATION_SPELL = "Rest"
MEDITATION_MANA_PCT = 0

SPELL_INFO = {
    "Attack": {"type": "damage", "cast_time": 0, "cooldown": 1, "mana_cost": 0, "range": 25},
    "Linked Rejuvenation": {"type": "heal", "cast_time": 1.0, "cooldown": 30, "mana_cost": 8, "range": 1, "targets_self": True},
    "Nature's Swiftness": {"type": "buff", "cast_time": 0, "cooldown": 30, "mana_cost": 10, "range": 0, "targets_self": True},
    "Rest": {"type": "utility", "cast_time": 0, "cooldown": 10, "mana_cost": 0, "range": 2, "channel_time": 20, "targets_self": True},
    "Spirit Shot": {"type": "damage", "cast_time": 0, "cooldown": 10, "mana_cost": 5, "range": 12},
    "Spiritbeast's Wrath": {"type": "damage", "cast_time": 0, "cooldown": 30, "mana_cost": 6, "range": 12},
    "Spiritburst Arrow": {"type": "damage", "cast_time": 1.0, "cooldown": 12, "mana_cost": 6, "range": 12},
    "Spiritlife Arrow": {"type": "damage", "cast_time": 0, "cooldown": 10, "mana_cost": 4, "range": 12},
    "Spiritroot Arrow": {"type": "damage", "cast_time": 0, "cooldown": 16, "mana_cost": 4, "range": 12},
    "Summon Spirit Alpha": {"type": "pet", "cast_time": 5.0, "cooldown": 10, "mana_cost": 20, "range": 4, "targets_self": True},
    "Summon Spirit Cub": {"type": "pet", "cast_time": 5.0, "cooldown": 10, "mana_cost": 20, "range": 4, "targets_self": True},
    "Summon Spirit Wolf": {"type": "pet", "cast_time": 5.0, "cooldown": 10, "mana_cost": 20, "range": 4, "targets_self": True},
    "Verdant Barrage": {"type": "damage", "cast_time": 0.5, "cooldown": 4, "mana_cost": 5, "range": 12},
}
