"""
EthyTool Debug — Debug mode, script dependencies, error handling.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("ethytool.debug")

_debug_mode = False


def set_debug(enabled: bool = True) -> None:
    """Enable/disable debug mode. When on, pipe traffic and extra logs are shown."""
    global _debug_mode
    _debug_mode = enabled


def is_debug() -> bool:
    return _debug_mode


def ensure_dependencies(requires: list[str], script_path: Optional[Path] = None) -> bool:
    """
    Ensure script dependencies are installed. Tries pip install if missing.
    Returns True if all deps available.
    """
    missing = []
    for spec in requires:
        pkg = spec.split(">=")[0].split("==")[0].split("[")[0].strip()
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            missing.append(spec)

    if not missing:
        return True

    logger.warning("Missing dependencies: %s. Attempting pip install...", missing)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install dependencies: %s", e)
        return False


def get_script_requires(script_path: Path) -> list[str]:
    """
    Parse script for requires. Looks for:
    - # requires: numpy, opencv-python
    - Docstring with requires: ["numpy"]
    """
    requires = []
    try:
        text = script_path.read_text(encoding="utf-8", errors="ignore")
        for line in text.split("\n")[:30]:
            if "# requires:" in line.lower():
                part = line.split(":", 1)[1].strip()
                requires.extend(x.strip() for x in part.split(",") if x.strip())
        # Docstring
        if '"""' in text or "'''" in text:
            import re
            for m in re.finditer(r'requires:\s*\[(.*?)\]', text, re.DOTALL):
                import ast
                try:
                    requires.extend(ast.literal_eval("[" + m.group(1) + "]"))
                except Exception:
                    pass
    except Exception:
        pass
    return list(dict.fromkeys(requires))  # dedupe
