"""
╔══════════════════════════════════════════════════════════════╗
║              SHADOWCASTER — Shadow DoT Caster Build          ║
║                                                              ║
║  Playstyle: Apply DoTs → nuke with Shadowblast → sustain     ║
║  Ranged caster, shadow themed, self-buff with armor + embrace║
║  Shadowbolt filler, Banish for hard CC                       ║
╚══════════════════════════════════════════════════════════════╝
"""

HEAL_HP        = 50
DEFENSIVE_HP   = 40
EMERGENCY_HP   = 20
REST_HP        = 80
REST_MP        = 60
MANA_CONSERVE  = 25

TICK_RATE = 0.3
GCD       = 0.3

BUFFS = [
    "Shadow Armor",              # Self armor buff (30s CD)
    "Embrace Shadow",            # Shadow power buff (30s CD)
]

OPENER = [
    "Shadow Armor",
    "Embrace Shadow",
    "Mark Of Subversion",
    "Corrupt Mind",
    "Shadowblast",
]

GAP_CLOSERS = []

# DoTs applied first, then nukes
DOTS = [
    "Mark Of Subversion",        # DoT mark (12s CD)
    "Corrupt Mind",              # DoT (0 CD, instant)
]

ROTATION = [
    "Banish to Shadow",          # Hard CC nuke (36s CD, 1.0s cast)
    "Shadow Ball",               # Big nuke (18s CD)
    "Spiteful Shadows",          # DoT burst (20s CD)
    "Shadowstream",              # AOE channel (36s CD)
    "Mark Of Subversion",        # Refresh DoT (12s CD)
    "Corrupt Mind",              # Refresh DoT (0 CD)
    "Shadowblast",               # Hard-cast nuke (0 CD, 2.0s cast)
    "Shadowbolt",                # Filler cast (0 CD, 1.5s cast)
]

AOE_SPELLS = [
    "Shadowstream",              # AOE channel
    "Spiteful Shadows",          # AOE DoT
    "Shadowblast",               # Splash?
    "Shadowbolt",                # Filler
]

DEFENSIVE_SPELLS = [
    "Shadow Armor",              # Armor buff (30s CD)
    "Embrace Shadow",            # Power buff (30s CD)
]

DEFENSIVE_TRIGGER_HP = 20

DEFENSIVE_COMBO = [
    "Shadow Armor",
    "Banish to Shadow",          # CC enemy while you recover
]

CC_SPELLS = [
    "Banish to Shadow",          # Hard CC (36s CD)
]

REST_SPELL = "Rest"
MEDITATION_SPELL = "Leyline Meditation"

MAX_STACKS = 0
STACK_DECAY_TIME = 0

SPELL_INFO = {
    "Shadowbolt": {
        "type": "damage",
        "cast_time": 1.5,
        "cooldown": 0,
        "mana_cost": 3,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Shadowblast": {
        "type": "damage",
        "cast_time": 2.0,
        "cooldown": 0,
        "mana_cost": 5,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Shadow Ball": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 18,
        "mana_cost": 5,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Corrupt Mind": {
        "type": "dot",
        "cast_time": 0,
        "cooldown": 0,
        "mana_cost": 2,
        "duration": 15,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Mark Of Subversion": {
        "type": "dot",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 3,
        "duration": 12,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Spiteful Shadows": {
        "type": "dot",
        "cast_time": 0,
        "cooldown": 20,
        "mana_cost": 4,
        "duration": 10,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Banish to Shadow": {
        "type": "cc",
        "cast_time": 1.0,
        "cooldown": 36,
        "mana_cost": 6,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Shadowstream": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 36,
        "mana_cost": 6,
        "range": 0,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Shadow Armor": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 30,
        "mana_cost": 3,
        "duration": 300,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Embrace Shadow": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 30,
        "mana_cost": 3,
        "duration": 300,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
}

BUFF_SAFETY = {
    "Shadow Armor": {
        "warn_before_expiry": 10.0,
        "warn_hp_below": 100,
        "danger": "Shadow Armor down!",
    },
    "Embrace Shadow": {
        "warn_before_expiry": 10.0,
        "warn_hp_below": 100,
        "danger": "Embrace Shadow down! DPS reduced!",
    },
}