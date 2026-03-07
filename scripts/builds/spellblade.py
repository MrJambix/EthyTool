"""
╔══════════════════════════════════════════════════════════════╗
║                  SPELLBLADE — Arcane Melee Build             ║
║                                                              ║
║  Playstyle: Imbue weapon → burst combo → shield → repeat     ║
║                                                              ║
║  COMBO LOGIC:                                                ║
║    1. Imbue Weapon: Arcane (maintain always)                 ║
║    2. Arcane Blitz (gap close / opener from range)           ║
║    3. Arcane Slashes (spam — 2s CD, main damage)             ║
║    4. Arcane Wave (5s CD, melee cleave)                      ║
║    5. Arcane Shockwave (6s CD, point-blank AOE)              ║
║    6. Supernova (12s CD, big AOE burst)                      ║
║    7. Siphon Instability (10s CD, mana/resource drain)       ║
║                                                              ║
║  DEFENSE:                                                    ║
║    - Arcanic Bulwark — magic shield (20s CD)                 ║
║    - Counterspell — interrupt casters (12s CD)               ║
║                                                              ║
║  BUFF:                                                       ║
║    - Imbue Weapon: Arcane (maintain at all times)            ║
║    - Leyline Brilliance (passive aura)                       ║
╚══════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════
#  THRESHOLDS
# ═══════════════��═══════════════════════════════════════════

HEAL_HP        = 50          # Heal/pot below this
DEFENSIVE_HP   = 40          # Pop Bulwark below this
EMERGENCY_HP   = 20          # All defensives + run
REST_HP        = 80          # Rest out of combat below this
REST_MP        = 60          # Meditate out of combat below this
MANA_CONSERVE  = 20          # Stop using big spells below this MP%

# ═══════════════════════════════════════════════════════════
#  TICK RATE
# ═══════════════════════════════════════════════════════════

TICK_RATE = 0.25
GCD       = 0.3

# ═══════════════════════════════════════════════════════════
#  BUFFS (maintain at all times)
# ═══════════════════════════════════════════════════════════

BUFFS = [
    "Imbue Weapon: Arcane",      # Main buff — always active
    "Leyline Brilliance",        # Passive aura
]

# ═══════════════════════════════════════════════════════════
#  OPENER (from range → into melee)
# ═══════════════════════════════════════════════════════════

OPENER = [
    "Imbue Weapon: Arcane",      # Ensure imbue is up
    "Arcane Blitz",              # Gap close (18s CD, range 7)
    "Arcane Shockwave",          # PB AOE on arrival
    "Arcane Slashes",            # Start slashing
]

# ═══════════════════════════════════════════════════════════
#  GAP CLOSERS
# ═══════════════════════════════════════════════════════════

GAP_CLOSERS = [
    "Arcane Blitz",              # 18s CD, range 7
]

# ═══════════════════════════════════════════════════════════
#  ROTATION (priority order — first available wins)
# ═══════════════════════════════════════════════════════════

ROTATION = [
    "Supernova",                 # Big AOE burst (12s CD) — use on CD
    "Arcane Shockwave",          # PB AOE (6s CD)
    "Arcane Wave",               # Melee cleave (5s CD)
    "Siphon Instability",        # Drain (10s CD)
    "Arcane Slashes",            # Main filler (2s CD)
]

# ═══════════════════════════════════════════════════════════
#  AOE ROTATION (3+ mobs)
# ═══════════════════════════════════════════════════════════

AOE_SPELLS = [
    "Supernova",                 # Big AOE
    "Arcane Shockwave",          # PB AOE
    "Arcane Wave",               # Cleave
    "Arcane Slashes",            # Filler
]

# ═══════════════════════════════════════════════════════════
#  DEFENSIVE
# ═══════════════════════════════════════════════════════════

DEFENSIVE_SPELLS = [
    "Arcanic Bulwark",           # Magic shield (20s CD)
    "Counterspell",              # Interrupt (12s CD)
]

DEFENSIVE_HP = 40
DEFENSIVE_TRIGGER_HP = 20

DEFENSIVE_COMBO = [
    "Arcanic Bulwark",           # Shield first
    "Arcane Slashes",            # Keep DPS while shielded
]

# ═══════════════════════════════════════════════════════════
#  INTERRUPT
# ═══════════════════════════════════════════════════════════

INTERRUPT_SPELLS = [
    "Counterspell",              # 12s CD, range 5
]

# ═══════════════════════════════════════════════════════════
#  REST
# ═══════════════════════════════════════════════════════════

REST_SPELL = "Rest"
MEDITATION_SPELL = "Leyline Meditation"

# ═══════════════════════════════════════════════════════════
#  STACKS (Spellblade doesn't use stacks)
# ═══════════════════════════════════════════════════════════

MAX_STACKS = 0
STACK_DECAY_TIME = 0

# ═══════════════════════════════════════════════════════════
#  SPELL INFO
# ═══════════════════════════════════════════════════════════

SPELL_INFO = {

    # ── Buffs ──

    "Imbue Weapon: Arcane": {
        "type": "buff",
        "cast_time": 1.0,
        "cooldown": 0,
        "mana_cost": 0,
        "duration": 600,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    "Leyline Brilliance": {
        "type": "buff",
        "cast_time": 0,
        "cooldown": 0,
        "mana_cost": 0,
        "duration": 600,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    # ── Gap Closer ──

    "Arcane Blitz": {
        "type": "gap_closer",
        "cast_time": 0,
        "cooldown": 18,
        "mana_cost": 5,
        "range": 7,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    # ── Main Rotation ──

    "Arcane Slashes": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 2,
        "mana_cost": 2,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    "Arcane Wave": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 5,
        "mana_cost": 3,
        "range": 2,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    "Arcane Shockwave": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 6,
        "mana_cost": 4,
        "range": 0,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    "Supernova": {
        "type": "aoe",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 6,
        "range": 3,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    "Siphon Instability": {
        "type": "damage",
        "cast_time": 0,
        "cooldown": 10,
        "mana_cost": 3,
        "range": 5,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    # ── Defensive ──

    "Arcanic Bulwark": {
        "type": "shield",
        "cast_time": 0,
        "cooldown": 20,
        "mana_cost": 5,
        "duration": 8,
        "range": 100,
        "targets_self": True,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },

    "Counterspell": {
        "type": "interrupt",
        "cast_time": 0,
        "cooldown": 12,
        "mana_cost": 2,
        "range": 5,
        "generates_stacks": 0,
        "consumes_stacks": 0,
    },
}

# ═══════════════════════════════════════════════════════════
#  BUFF SAFETY
# ═══════════════════════════════════════════════════════════

BUFF_SAFETY = {
    "Imbue Weapon: Arcane": {
        "warn_before_expiry": 10.0,
        "warn_hp_below": 100,
        "danger": "Weapon imbue down! DPS crippled!",
    },
}