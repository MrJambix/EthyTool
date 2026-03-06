"""
╔══════════════════════════════════════════════════════════════╗
║  BERSERKER COMBAT PROFILE v3.0                               ║
║                                                              ║
║  ═══ HOW BERSERKER WORKS ═══                                 ║
║                                                              ║
║  RESOURCE: Fury Stacks (0-20)                                ║
║    • Attacks generate stacks on hit                          ║
║    • Stacks decay out of combat                              ║
║    • At 20 stacks: Executioner's Blow does MASSIVE damage    ║
║                                                              ║
║  ═══ SPELL BREAKDOWN ═══                                     ║
║                                                              ║
║  BATTLECRY (30s CD, Instant)                                 ║
║    +10% max HP for 10 seconds.                               ║
║    Cast before pull. WARNING: losing the buff at low HP      ║
║    can kill you — you lose that 10% max HP when it fades.    ║
║                                                              ║
║  BLOODLUST (24s CD, Instant, Self)                           ║
║    Attack speed buff. More hits = more stacks.               ║
║    Cast on CD.                                               ║
║                                                              ║
║  FURIOUS CHARGE (10s CD, Instant, Range:10)                  ║
║    Gap closer. Charge to target. Generates stacks.           ║
║                                                              ║
║  STAGGERING SHOUT (20s CD, Instant, Range:5, AoE)           ║
║    AoE stun around you.                                      ║
║    Interrupt casters. Setup for Cleave. Pair with Undying.   ║
║                                                              ║
║  HEAVY BLOW (6s CD, Instant, Range:2)                        ║
║    Big single-target hit. Spender — consumes stacks.         ║
║    Don't cast below 3 stacks.                                ║
║                                                              ║
║  HAMSTRING (5s CD, Instant, Range:2)                         ║
║    Slows target. CC + minor damage. Generates stacks.        ║
║                                                              ║
║  FURIOUS CLEAVE (2s CD, 0.29s Cast, Melee, AoE)             ║
║    Primary filler + stack builder. Spam this.                ║
║    Each target hit = stacks. AoE = faster stacking.          ║
║                                                              ║
║  RAGING BLOW (3s CD, 0.29s Cast, Range:2)                   ║
║    Secondary filler. Backup stack builder.                   ║
║                                                              ║
║  EXECUTIONER'S BLOW (8s CD, Instant, Range:2)                ║
║    NUKE. At 20 stacks this does MASSIVE bonus damage.        ║
║    This is NOT an execute (doesn't care about target HP).    ║
║    ONLY cast at 20 stacks for maximum value.                 ║
║    Consumes ALL stacks.                                      ║
║                                                              ║
║  UNDYING FURY (45s CD, Instant)                              ║
║    IMMORTALITY. Cannot die while active.                     ║
║    COST: +10% damage taken while active.                     ║
║    REWARD: Heals 10% max HP when it expires.                 ║
║    Pop at ~15-20% HP. Pair with Staggering Shout to          ║
║    reduce damage during the window.                          ║
║                                                              ║
║  ═══ OPTIMAL FLOW ═══                                        ║
║                                                              ║
║  PULL:  Battlecry → Bloodlust → Charge                      ║
║  BUILD: Cleave → Raging → Cleave → Raging (stack to 20)     ║
║  DUMP:  Executioner's Blow at 20 stacks (NUKE)              ║
║  FILL:  Heavy Blow (spend 3+ stacks for burst)              ║
║  LOOP:  Build → Dump → Build → Dump                         ║
║  PANIC: Undying Fury → Staggering Shout → keep swinging     ║
║  REST:  Rest / Meditate between pulls                        ║
╚══════════════════════════════════════════════════════════════╝
"""

# ══════════════════════════════════════════════════════════════
#  STACK SYSTEM
# ══════════════════════════════════════════════════════════════

STACK_ENABLED = True
MAX_STACKS = 20
STACK_DECAY_TIME = 8.0      # Seconds before stacks decay OOC

# ══════════════════════════════════════════════════════════════
#  SPELL METADATA
#
#  Every spell the engine needs to know about.
#  "generates_stacks" = how many stacks gained on cast
#  "consumes_stacks"  = how many stacks spent (0=none, -1=ALL)
#  "min_stacks"       = minimum stacks required to cast
#  "type"             = builder/spender/nuke/buff/cc/gap_closer/defensive/utility
#  "priority_boost"   = extra priority when conditions met
# ══════════════════════════════════════════════════════════════

SPELL_INFO = {
    "Battlecry": {
        "cd": 30, "type": "buff", "duration": 10,
        "generates_stacks": 0, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "+10% max HP for 10s. Cast pre-pull.",
    },
    "Bloodlust": {
        "cd": 24, "type": "buff", "duration": 0,
        "generates_stacks": 0, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "Attack speed buff. More speed = more stacks.",
    },
    "Furious Charge": {
        "cd": 10, "type": "gap_closer", "range": 10,
        "generates_stacks": 1, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "Charge to target. Generates 1 stack.",
    },
    "Staggering Shout": {
        "cd": 20, "type": "cc", "range": 5, "aoe": True,
        "generates_stacks": 0, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "AoE stun. Pair with Undying Fury.",
    },
    "Heavy Blow": {
        "cd": 6, "type": "spender", "range": 2,
        "generates_stacks": 0, "consumes_stacks": 3, "min_stacks": 3,
        "desc": "Big hit. Consumes 3 stacks.",
    },
    "Hamstring": {
        "cd": 5, "type": "cc", "range": 2,
        "generates_stacks": 1, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "Slow target. Generates 1 stack.",
    },
    "Furious Cleave": {
        "cd": 2, "cast_time": 0.29, "type": "builder", "aoe": True,
        "generates_stacks": 1, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "AoE filler. Primary stack builder. Spam this.",
    },
    "Raging Blow": {
        "cd": 3, "cast_time": 0.29, "type": "builder", "range": 2,
        "generates_stacks": 1, "consumes_stacks": 0, "min_stacks": 0,
        "desc": "Single-target filler. Secondary stack builder.",
    },
    "Executioner's Blow": {
        "cd": 8, "type": "nuke", "range": 2,
        "generates_stacks": 0, "consumes_stacks": -1, "min_stacks": 20,
        "desc": "NUKE — massive damage at 20 stacks. Consumes ALL.",
    },
    "Undying Fury": {
        "cd": 45, "type": "defensive",
        "generates_stacks": 0, "consumes_stacks": 0, "min_stacks": 0,
        "duration": 10,
        "extra_damage_taken": 0.10,
        "heal_on_expiry": 0.10,
        "desc": "Cannot die. +10% dmg taken. Heals 10% on expiry.",
    },
}

# ══════════════════════════════════════════════════════════════
#  BUFFS
# ══════════════════════════════════════════════════════════════

BUFFS = ["Battlecry", "Bloodlust"]
REBUFF_INTERVAL = 22.0

BUFF_DURATIONS = {
    "Battlecry": 10.0,
    "Bloodlust": 6,         # Unknown / permanent until overwritten
}

# Safety: warn if Battlecry about to expire at low HP
BUFF_SAFETY = {
    "Battlecry": {
        "warn_hp_below": 30,
        "warn_before_expiry": 2.0,
        "danger": "Losing 10% max HP can kill you!",
    },
}

# ══════════════════════════════════════════════════════════════
#  OPENER — Pull sequence
# ══════════════════════════════════════════════════════════════

OPENER = ["Battlecry", "Bloodlust"]

# ══════════════════════════════════════════════════════════════
#  GAP CLOSERS
# ══════════════════════════════════════════════════════════════

GAP_CLOSERS = ["Furious Charge"]

# ══════════════════════════════════════════════════════════════
#  MAIN ROTATION — Priority order
#
#  The engine casts the FIRST spell in this list that is:
#    1. Off cooldown
#    2. Meets min_stacks requirement
#
#  Executioner's at top because when you hit 20 stacks, DUMP.
#  But min_stacks=20 means it only fires at full stacks.
# ══════════════════════════════════════════════════════════════

ROTATION = [
    "Executioner's Blow",  # 8s CD  — NUKE at 20 stacks (gated by min_stacks)
    "Staggering Shout",    # 20s CD — AoE stun
    "Heavy Blow",          # 6s CD  — spender (needs 3 stacks)
    "Hamstring",           # 5s CD  — slow + 1 stack
    "Furious Cleave",      # 2s CD  — main builder
    "Raging Blow",         # 3s CD  — backup builder
]

# ══════════════════════════════════════════════════════════════
#  AOE ROTATION — Cleave priority for faster stacking
# ══════════════════════════════════════════════════════════════

AOE_SPELLS = [
    "Staggering Shout",
    "Executioner's Blow",  # Dump if at 20
    "Furious Cleave",      # AoE + stacks from each target
    "Raging Blow",
    "Heavy Blow",
]
AOE_THRESHOLD = 3

# ══════════════════════════════════════════════════════════════
#  DEFENSIVE
# ══════════════════════════════════════════════════════════════

DEFENSIVE_SPELLS = ["Undying Fury"]
DEFENSIVE_HP = 40.0
DEFENSIVE_TRIGGER_HP = 20   # Pop Undying at this %

# Combo: after popping Undying, immediately cast these
DEFENSIVE_COMBO = ["Staggering Shout"]

# ══════════════════════════════════════════════════════════════
#  KITING — Panic mode
# ══════════════════════════════════════════════════════════════

KITE_HP = 15
KITE_SPELLS = [
    "Undying Fury",
    "Staggering Shout",
    "Hamstring",
    "Furious Charge",
]

# ══════════════════════════════════════════════════════════════
#  HEALING — Berserker has none
# ════════════════���═════════════════════════════════════════════

HEAL_SPELLS = []
HEAL_HP = 0

# ══════════════════════════════════════════════════════════════
#  REST
# ══════════════════════════════════════════════════════════════

REST_SPELL = "Rest"
REST_HP = 70
REST_MP = 50
MEDITATION_SPELL = "Leyline Meditation"

# ══════════════════════════════════════════════════════════════
#  TIMING
# ══════════════════════════════════════════════════════════════

TICK_RATE = 0.3
GCD = 0.5