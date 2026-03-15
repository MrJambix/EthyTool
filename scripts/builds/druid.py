"""
╔══════════════════════════════════════════════════════════════╗
║               DRUID — Nature Mage Build                      ║
║                                                              ║
║  Playstyle: Ranged caster — Nature damage, heals, roots      ║
║  Narun's Blast / Bolt of Narun DPS, Nourishing Touch heals  ║
╚══════════════════════════════════════════════════════════════╝
"""

# Discipline level — set your level; skills in SKILL_LEVEL_REQUIREMENTS are blocked until you have the level.
# TODO: Add your discipline's skill: level pairs below.
DISCIPLINE_LEVEL = 25
SKILL_LEVEL_REQUIREMENTS = {
    # "Skill Name": 5,
    # "Other Skill": 10,
}
IGNORED_SPELLS = {s for s, req in SKILL_LEVEL_REQUIREMENTS.items() if DISCIPLINE_LEVEL < req}

HEAL_HP        = 70
DEFENSIVE_HP   = 40
EMERGENCY_HP   = 25
REST_HP        = 70
REST_MP        = 80

TICK_RATE = 0.3
GCD       = 0.3

BUFFS = [
    "Bloom",                    # Buff on self or targeted ally (30s CD), no Seed of Silcress required
]

# Don't cast if already active (detected via PLAYER_BUFFS)
BUFF_CONFIG = {
    "Bloom": {
        "detect_buff": True,
        "buff_ids": ["Bloom", "BloomStatus"],
    },
}

OPENER = [
    "Bloom",
    "Ironbark",
    "Narun's Blast",
    "Flourish",
    "Bolt of Narun",
]

ROTATION = [
    "Narun's Blast",            # Big hit (8s CD, 1.9s cast)
    "Bloom",                    # Buff/nuke (30s CD)
    "Flourish",                 # (8s CD, 0.5s cast)
    "Ensnaring Spore",          # Root/CC (18s CD)
    "Seed of Silcress",         # Filler (2s CD)
    "Bolt of Narun",            # Filler (0 CD, 1.45s cast)
]

HEAL_SPELLS = [
    "Nourishing Touch",         # Single target heal (1.45s cast)
    "Grove of Rejuvenation",    # AOE heal (36s CD)
]

DEFENSIVE_SPELLS = [
    "Ironbark",                 # Self armor (45s CD)
]

DEFENSIVE_TRIGGER_HP = 20

REST_SPELL = "Rest"
MEDITATION_SPELL = "Rest"       # Druids use Rest for mana (no Leyline Meditation)
MEDITATION_MANA_PCT = 0         # Disable in-combat meditation (Rest is 20s channel, OOC only)

SPELL_INFO = {
    "Bloom": {"type": "buff", "cast_time": 0, "cooldown": 30, "mana_cost": 6, "range": 10},
    "Bolt of Narun": {"type": "damage", "cast_time": 1.46, "cooldown": 0, "mana_cost": 6, "range": 10},
    "Ensnaring Spore": {"type": "cc", "cast_time": 1.46, "cooldown": 18, "mana_cost": 5, "range": 10},
    "Flourish": {"type": "damage", "cast_time": 0.49, "cooldown": 8, "mana_cost": 14, "range": 10},
    "Grove of Rejuvenation": {"type": "heal", "cast_time": 0, "cooldown": 36, "mana_cost": 14, "range": 10},
    "Ironbark": {"type": "defensive", "cast_time": 0, "cooldown": 45, "mana_cost": 25, "range": 0, "targets_self": True},
    "Narun's Blast": {"type": "damage", "cast_time": 1.94, "cooldown": 8, "mana_cost": 12, "range": 10},
    "Nourishing Touch": {"type": "heal", "cast_time": 1.46, "cooldown": 0, "mana_cost": 6, "range": 10},
    "Purify Corruption": {"type": "utility", "cast_time": 0, "cooldown": 6, "mana_cost": 6, "range": 10},
    "Seed of Silcress": {"type": "damage", "cast_time": 0, "cooldown": 2, "mana_cost": 6, "range": 10},
    "Spiritual Outburst": {"type": "aoe", "cast_time": 0, "cooldown": 42, "mana_cost": 250, "channel_time": 6},
}
