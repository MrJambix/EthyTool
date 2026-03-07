"""
╔══════════════════════════════════════════════════════════════╗
║               EARTHGUARD — Earth Tank Build                  ║
║                                                              ║
║  Playstyle: Imbue shield → absorb → spike → counter-burst   ║
║  Tankiest class — stacks shields and absorbs                 ║
╚══════════════════════════════════════════════════════════════╝
"""

HEAL_HP        = 50
DEFENSIVE_HP   = 40
EMERGENCY_HP   = 20
REST_HP        = 80
REST_MP        = 60
MANA_CONSERVE  = 20

TICK_RATE = 0.25
GCD       = 0.3

BUFFS = [
    "Imbue Shield: Earth",
]

OPENER = [
    "Imbue Shield: Earth",
    "Taunt",
    "Solid Core",
    "Geomantic Spikes",
]

GAP_CLOSERS = []

ROTATION = [
    "Earthshaker",                # Big slam (30s CD)
    "Seismic Slam",               # AOE knockback (20s CD)
    "Geomantic Spikes",           # Spike reflect (16s CD)
    "Aftershock",                 # AOE follow-up (12s CD)
    "Protective Shards",          # Ranged shield throw (12s CD)
    "Earth Slash",                # Filler (2s CD)
]

AOE_SPELLS = [
    "Earthshaker",
    "Seismic Slam",
    "Aftershock",
    "Earth Slash",
]

DEFENSIVE_SPELLS = [
    "Solid Core",                 # Big defense CD (42s)
    "Earthly Absorption",         # Absorb shield (14s CD)
    "Geomantic Spikes",           # Spike reflect (16s CD)
]

DEFENSIVE_TRIGGER_HP = 20

DEFENSIVE_COMBO = [
    "Solid Core",
    "Earthly Absorption",
    "Geomantic Spikes",
]

TAUNT_SPELLS = [
    "Taunt",
]

REST_SPELL = "Rest"
MEDITATION_SPELL = "Leyline Meditation"

MAX_STACKS = 0
STACK_DECAY_TIME = 0

SPELL_INFO = {
    "Imbue Shield: Earth": {
        "type": "buff",
        "cast_time": 1.0,
        "cooldown": 30,
        "mana_cost": 0,
        "duration": 600,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Earth Slash": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 2,
        "mana_cost": 2,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Aftershock": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 4,
        "range": 1,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Earthly Absorption": {
        "type": "shield",
        "cast_time": 0,
        "cooldown": 14,
        "mana_cost": 4,
        "duration": 8,
        "range": 3,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Earthshaker": {
        "type": "aoe",
        "cast_time": 1.0,
        "cooldown": 30,
        "mana_cost": 6,
        "range": 1,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Geomantic Spikes": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 16,
        "mana_cost": 4,
        "duration": 10,
        "range": 1,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Protective Shards": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 3,
        "range": 7,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Seismic Slam": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 20,
        "mana_cost": 5,
        "range": 3,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Solid Core": {
        "type": "shield",
        "cast_time": 0,
        "cooldown": 42,
        "mana_cost": 5,
        "duration": 10,
        "range": 1,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Taunt": {
        "type": "cc",
        "cast_time": 0,
        "cooldown": 6,
        "mana_cost": 2,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
}

BUFF_SAFETY = {
    "Imbue Shield: Earth": {
        "warn_before_expiry": 10.0,
        "warn_hp_below": 100,
        "danger": "Shield imbue down! Defense crippled!",
    },
}