"""
EthyTool Profile Schema — Validate build profiles (optional Pydantic).
"""

from typing import Optional

try:
    from pydantic import BaseModel, Field
    try:
        from pydantic import ConfigDict
        _pydantic_v2 = True
    except ImportError:
        _pydantic_v2 = False
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object
    Field = lambda **kw: None
    _pydantic_v2 = False


if PYDANTIC_AVAILABLE and _pydantic_v2:
    from pydantic import ConfigDict

if PYDANTIC_AVAILABLE:

    class SpellInfo(BaseModel):
        """Schema for a spell in SPELL_INFO."""
        cd: int = 0
        cooldown: Optional[int] = None
        type: str = "damage"
        duration: int = 0
        cast_time: float = 0
        range: Optional[int] = None
        min_stacks: int = 0
        generates_stacks: int = 0
        consumes_stacks: int = 0
        channel: bool = False
        aoe: bool = False
        desc: str = ""

        if not _pydantic_v2:
            class Config:
                extra = "allow"
        else:
            model_config = ConfigDict(extra="allow")

    class BuildProfile(BaseModel):
        """Schema for a build profile module."""
        SPELL_INFO: dict[str, dict] = {}
        ROTATION: list[str] = []
        OPENER: list[str] = []
        BUFFS: list[str] = []
        DEFENSIVE_SPELLS: list[str] = []
        HEAL_SPELLS: list[str] = []
        AOE_SPELLS: list[str] = []
        GAP_CLOSERS: list[str] = []
        GCD: float = 0.5
        TICK_RATE: float = 0.3
        STACK_ENABLED: bool = False
        MAX_STACKS: int = 20

        if not _pydantic_v2:
            class Config:
                extra = "allow"
        else:
            model_config = ConfigDict(extra="allow")

    def validate_spell_info(name: str, info: dict) -> list[str]:
        """Validate a single spell info dict. Returns list of errors."""
        errors = []
        try:
            SpellInfo(**info)
        except Exception as e:
            errors.append(f"{name}: {e}")
        return errors

    def validate_profile(profile_module) -> list[str]:
        """Validate a loaded profile module. Returns list of errors."""
        errors = []
        spell_info = getattr(profile_module, "SPELL_INFO", {})
        for name, info in spell_info.items():
            errors.extend(validate_spell_info(name, info))
        return errors

else:

    def validate_spell_info(name: str, info: dict) -> list[str]:
        """No-op when Pydantic not installed."""
        return []

    def validate_profile(profile_module) -> list[str]:
        """No-op when Pydantic not installed."""
        return []
