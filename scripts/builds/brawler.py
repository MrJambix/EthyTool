"""
╔══════════════════════════════════════════════════════════════╗
║                 BRAWLER — Combo Fighter Build                ║
║                                                              ║
║  Playstyle: Jab spam → weave cooldowns → Knockout finisher   ║
║  Fast melee with 0 CD filler, combo style                    ║
║                                                              ║
║  COMBO LOGIC:                                                ║
║    Jab (0 CD) is the filler between everything               ║
║    Weave Hook/Uppercut/Cross/Kick on cooldown                ║
║    Knockout when target is low — big finisher                ║
║    Feint for dodge, Combative Focus for burst window          ║
╚══════════════════════════════════════════════════════════════╝
"""

HEAL_HP        = 50
DEFENSIVE_HP   = 35
EMERGENCY_HP   = 20
REST_HP        = 80
REST_MP        = 60
MANA_CONSERVE  = 15

TICK_RATE = 0.2          # Fast tick — Brawler is spammy
GCD       = 0.2

BUFFS = [
    "Combative Focus",           # Burst window (60s CD)
]

OPENER = [
    "Brawler's Rush",            # Gap close
    "Combative Focus",           # Burst buff
    "Fierce Uppercut",           # Opener hit
    "Fast Hook",                 # Follow-up
]

GAP_CLOSERS = [
    "Brawler's Rush",            # 20s CD, range 5
]

ROTATION = [
    "Knockout",                  # Finisher (18s CD) — big damage
    "Fierce Uppercut",           # 6s CD
    "Powerful Cross",            # 6s CD
    "Fast Hook",                 # 6s CD
    "Horizontal Kick",           # 6s CD
    "Quick Jab",                 # 0 CD — always available filler
]

AOE_SPELLS = [
    "Horizontal Kick",           # Kick hits in arc
    "Quick Jab",                 # Filler
]

DEFENSIVE_SPELLS = [
    "Feint",                     # Dodge (15s CD)
]

DEFENSIVE_TRIGGER_HP = 20

DEFENSIVE_COMBO = [
    "Feint",
    "Quick Jab",
]

REST_SPELL = "Rest"
MEDITATION_SPELL = "Leyline Meditation"

MAX_STACKS = 0
STACK_DECAY_TIME = 0

SPELL_INFO = {
    "Quick Jab": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 0,
        "mana_cost": 1,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Fast Hook": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 6,
        "mana_cost": 2,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Fierce Uppercut": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 6,
        "mana_cost": 3,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Powerful Cross": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 6,
        "mana_cost": 3,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Horizontal Kick": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 6,
        "mana_cost": 3,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Knockout": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 18,
        "mana_cost": 5,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Brawler's Rush": {
        "type": "gap_closer",
        "cast_time": 0,
        "cooldown": 20,
        "mana_cost": 4,
        "range": 5,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Feint": {
        "type": "defensive",
        "cast_time": 0,
        "cooldown": 15,
        "mana_cost": 3,
        "duration": 3,
        "range": 2,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
    "Combative Focus": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 60,
        "mana_cost": 0,
        "duration": 15,
        "range": 100,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
}

BUFF_SAFETY = {}