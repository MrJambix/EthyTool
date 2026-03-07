"""
╔══════════════════════════════════════════════════════════════╗
║               DEMONKNIGHT — Lifesteal Tank Build             ║
║                                                              ║
║  Playstyle: Imbue → Leech → Zone → Whirlwind → self-heal    ║
║  Sustain through damage with lifesteal, not mitigation       ║
╚══════════════════════════════════════════════════════════════╝
"""

HEAL_HP        = 50
DEFENSIVE_HP   = 35
EMERGENCY_HP   = 20
REST_HP        = 80
REST_MP        = 60
MANA_CONSERVE  = 20

TICK_RATE = 0.25
GCD       = 0.3

BUFFS = [
    "Might of Barlon",
]

OPENER = [
    "Might of Barlon",
    "Taunt",
    "Barlon's Zone of Gluttony",
    "Barlon's Strike",
]

GAP_CLOSERS = []

ROTATION = [
    "Barlon's Devastation",       # Big hit (30s CD)
    "Demonic Retribution",        # Damage reflect (30s CD)
    "Barlon's Zone of Gluttony",  # AOE zone (12s CD)
    "Barlon's Leech",             # Lifesteal (8s CD)
    "Vitality Strike",            # Self-heal strike (18s CD)
    "Barlon's Whirlwind",         # AOE spin (5s CD)
    "Barlon's Strike",            # Filler (3s CD)
]

AOE_SPELLS = [
    "Barlon's Zone of Gluttony",
    "Barlon's Whirlwind",
    "Barlon's Devastation",
    "Barlon's Strike",
]

DEFENSIVE_SPELLS = [
    "Demonic Bulwark",            # Shield (18s CD)
    "Vitality Strike",            # Self-heal (18s CD)
]

DEFENSIVE_TRIGGER_HP = 20

DEFENSIVE_COMBO = [
    "Demonic Bulwark",
    "Vitality Strike",
    "Barlon's Leech",
]

TAUNT_SPELLS = [
    "Taunt",
]

REST_SPELL = "Rest"
MEDITATION_SPELL = "Leyline Meditation"

MAX_STACKS = 0
STACK_DECAY_TIME = 0

SPELL_INFO = {
    "Might of Barlon": {
        "type": "buff",
        "cast_time": 1.0,
        "cooldown": 0,
        "mana_cost": 0,
        "duration": 600,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Barlon's Strike": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 3,
        "mana_cost": 2,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Barlon's Leech": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 8,
        "mana_cost": 3,
        "range": 3,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Barlon's Whirlwind": {
        "type": "aoe",
        "cast_time": 0.4,
        "cooldown": 5,
        "mana_cost": 4,
        "range": 1,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Barlon's Zone of Gluttony": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 5,
        "range": 3,
        "duration": 8,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Barlon's Devastation": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 30,
        "mana_cost": 6,
        "range": 1,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Demonic Bulwark": {
        "type": "shield",
        "cast_time": 0,
        "cooldown": 18,
        "mana_cost": 4,
        "duration": 8,
        "range": 0,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Demonic Retribution": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 30,
        "mana_cost": 5,
        "duration": 10,
        "range": 1,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Vitality Strike": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 18,
        "mana_cost": 4,
        "range": 2,
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
    "Might of Barlon": {
        "warn_before_expiry": 10.0,
        "warn_hp_below": 100,
        "danger": "Barlon imbue down! Lifesteal crippled!",
    },
}