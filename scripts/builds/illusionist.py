"""
╔══════════════════════════════════════════════════════════════╗
║               ILLUSIONIST — Mind Mage Build                  ║
║                                                              ║
║  Playstyle: Ranged caster — DoTs, CC, burst from distance    ║
║  Power Spike spam filler, weave CDs, Panic for CC            ║
║  Shift to reposition, Mirage + Mantra for defense            ║
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
    "Mirage",                    # Illusion defense (30s CD)
]

OPENER = [
    "Mirage",
    "Energy Surge",              # Opener burst
    "Phantom Daggers",           # Big channel
    "Mindshatter",               # Hard hit
]

GAP_CLOSERS = [
    "Shift",                     # Teleport (18s CD, range 8)
]

ROTATION = [
    "Phantom Daggers",           # Big channel damage (20s CD, 2.0s cast)
    "Overload",                  # Burst (15s CD)
    "Energy Surge",              # Ranged nuke (12s CD)
    "Mindshatter",               # Hard hit (6s CD, 1.5s cast)
    "Spiteful Shadows",          # DoT/debuff (20s CD)  -- from utility
    "Panic",                     # CC (8s CD)
    "Power Spike",               # Filler (2s CD, instant)
]

AOE_SPELLS = [
    "Overload",                  # AOE burst
    "Deja Vu",                   # AOE echo (20s CD)
    "Power Spike",               # Filler
]

DOTS = [
    "Mark Of Subversion",        # DoT mark (12s CD)
]

DEFENSIVE_SPELLS = [
    "Mirage",                    # Illusion (30s CD)
    "Mantra Of Resolve",         # Self shield (30s CD)
    "Shift",                     # Escape teleport
]

DEFENSIVE_TRIGGER_HP = 20

DEFENSIVE_COMBO = [
    "Mantra Of Resolve",
    "Shift",
    "Panic",
]

INTERRUPT_SPELLS = [
    "Panic",                     # Fear / interrupt
]

REST_SPELL = "Rest"
MEDITATION_SPELL = "Leyline Meditation"

MAX_STACKS = 0
STACK_DECAY_TIME = 0

SPELL_INFO = {
    "Power Spike": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 2,
        "mana_cost": 2,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Mindshatter": {
        "type": "damage",
        "cast_time": 1.5,
        "cooldown": 6,
        "mana_cost": 4,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Energy Surge": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 4,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Phantom Daggers": {
        "type": "damage",
        "cast_time": 2.0,
        "cooldown": 20,
        "mana_cost": 6,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Overload": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 15,
        "mana_cost": 5,
        "range": 0,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Panic": {
        "type": "cc",
        "cast_time": 0,
        "cooldown": 8,
        "mana_cost": 3,
        "range": 10,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Deja Vu": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 20,
        "mana_cost": 5,
        "range": 0,
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
    "Mirage": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 30,
        "mana_cost": 4,
        "duration": 15,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Mantra Of Resolve": {
        "type": "shield",
        "cast_time": 0,
        "cooldown": 30,
        "mana_cost": 5,
        "duration": 8,
        "range": 0,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Shift": {
        "type": "gap_closer",
        "cast_time": 0,
        "cooldown": 18,
        "mana_cost": 3,
        "range": 8,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
}

BUFF_SAFETY = {
    "Mirage": {
        "warn_before_expiry": 5.0,
        "warn_hp_below": 100,
        "danger": "Mirage down! Vulnerable!",
    },
}