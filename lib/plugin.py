"""
EthyTool Plugin System — Discover and load bots via ethytool.yaml manifest.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class PluginInfo:
    """Metadata for a third-party bot/plugin."""

    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    entry: str = "main.py"
    requires: list[str] = field(default_factory=list)
    path: Optional[Path] = None

    @property
    def entry_path(self) -> Optional[Path]:
        if self.path and self.entry:
            return self.path / self.entry
        return None


def load_plugin_manifest(plugin_dir: Path) -> Optional[PluginInfo]:
    """Load ethytool.yaml from a plugin directory."""
    for name in ("ethytool.yaml", "ethytool.yml", "plugin.yaml"):
        p = plugin_dir / name
        if p.exists():
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                req = data.get("requires", [])
                if isinstance(req, str):
                    req = [req]
                return PluginInfo(
                    name=data.get("name", plugin_dir.name),
                    version=str(data.get("version", "1.0.0")),
                    author=data.get("author", ""),
                    description=data.get("description", ""),
                    entry=data.get("entry", "main.py"),
                    requires=req,
                    path=plugin_dir,
                )
            except Exception:
                pass
    return None


def load_plugins(plugins_dir: Path) -> list[PluginInfo]:
    """
    Discover all plugins in a directory. Each subdir with ethytool.yaml is a plugin.
    """
    results = []
    if not plugins_dir.exists():
        return results
    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            info = load_plugin_manifest(item)
            if info:
                results.append(info)
    return results
