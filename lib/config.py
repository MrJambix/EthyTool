"""
EthyTool Config — Load settings from YAML/TOML files.
"""

import os
from pathlib import Path
from typing import Any, Optional

_config: Optional[dict] = None
_config_path: Optional[Path] = None


def _find_config_dir() -> Path:
    """Find config directory: cwd, then script dir, then EthyTool root."""
    cwd = Path.cwd()
    for candidate in [cwd, cwd / "..", cwd / ".." / ".."]:
        for name in ("ethytool.yaml", "ethytool.yml", "config.yaml", "config.yml"):
            p = candidate.resolve() / name
            if p.exists():
                return p.parent
    return cwd


def load_config(
    path: Optional[Path] = None,
    env_prefix: str = "ETHYTOOL_",
) -> dict:
    """
    Load config from YAML or TOML. Env vars override (ETHYTOOL_COMBAT_TICK_RATE etc).
    """
    global _config, _config_path
    config_dir = path.parent if path and path.exists() else _find_config_dir()
    config_path = path if path and path.exists() else None
    if not config_path:
        for name in ("ethytool.yaml", "ethytool.yml", "config.yaml"):
            candidate = config_dir / name
            if candidate.exists():
                config_path = candidate
                break
        config_path = config_path or (config_dir / "ethytool.yaml")

    data: dict = {}
    if config_path.exists():
        _config_path = config_path
        try:
            import yaml
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except ImportError:
            pass
        except Exception:
            pass

    # Env overrides: ETHYTOOL_COMBAT_TICK_RATE -> combat.tick_rate
    for key, val in os.environ.items():
        if key.startswith(env_prefix):
            subkey = key[len(env_prefix):].lower()
            parts = subkey.split("_")
            d = data
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            try:
                if isinstance(val, str) and val.lower() in ("true", "false"):
                    val = val.lower() == "true"
                elif isinstance(val, str) and val.isdigit():
                    val = int(val)
                elif isinstance(val, str) and val.replace(".", "").isdigit():
                    val = float(val)
            except (ValueError, TypeError):
                pass
            d[parts[-1]] = val

    _config = data
    return data


def get_config(*keys: str, default: Any = None) -> Any:
    """Get nested config value: get_config('combat', 'tick_rate', default=0.3)."""
    global _config
    if _config is None:
        load_config()
    d = _config or {}
    for k in keys:
        d = d.get(k, {}) if isinstance(d, dict) else default
        if d is None:
            return default
    return d if d != {} else default
