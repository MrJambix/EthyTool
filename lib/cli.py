"""
EthyTool CLI — Run scripts, list plugins, simulate DPS.
"""

import sys
import threading
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

# Ensure parent is in path
_parent = Path(__file__).resolve().parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

app = typer.Typer(
    name="ethytool",
    help="EthyTool — Mod Creator & Bot Creator Library for Ethyrial",
)
console = Console()


def _setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@app.command()
def run(
    script: Path = typer.Argument(..., help="Path to bot script (.py)"),
    pid: Optional[int] = typer.Option(None, "--pid", "-p", help="Game process ID"),
    timeout: int = typer.Option(60, "--timeout", "-t", help="Connection timeout (seconds)"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Run a bot script. Connects to game, injects conn and stop_event."""
    _setup_logging(verbose)
    if not script.exists():
        console.print(f"[red]Script not found: {script}[/red]")
        raise typer.Exit(1)

    import importlib.util
    from ethytool_lib import create_connection
    from ethytool.bot import run_bot, BotBase

    conn = create_connection(pid=pid)
    console.print(f"Connecting to game (timeout={timeout}s)...")
    if not conn.connect(timeout=timeout):
        console.print("[red]Failed to connect. Is the game running with EthyTool injected?[/red]")
        raise typer.Exit(1)
    console.print("[green]Connected![/green]")

    stop_event = threading.Event()

    def log(msg: str):
        console.print(f"[cyan][{script.stem}][/cyan] {msg}")

    try:
        from ethytool.events import with_events
        with_events(conn)
    except ImportError:
        pass

    script_dir = str(script.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    spec = importlib.util.spec_from_file_location(script.stem, str(script))
    mod = importlib.util.module_from_spec(spec)
    mod.conn = conn
    mod.stop_event = stop_event
    mod.ethytool = conn
    mod.log = log
    mod.print = lambda *a, **kw: log(" ".join(str(x) for x in a))

    def _run():
        spec.loader.exec_module(mod)
        # If exec returned, script had no blocking loop - check for main/run/BotBase
        if hasattr(mod, "main") and callable(mod.main):
            mod.main(conn, stop_event)
        elif hasattr(mod, "run") and callable(mod.run):
            mod.run(conn, stop_event)
        else:
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, type) and issubclass(obj, BotBase) and obj is not BotBase:
                    run_bot(obj(), conn, stop_event, log_fn=log)
                    break

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    try:
        th.join()
    except KeyboardInterrupt:
        stop_event.set()
        console.print("[yellow]Stopping...[/yellow]")
        th.join(timeout=5)


@app.command("list")
def list_cmd(
    plugins_dir: Optional[Path] = typer.Option(
        None,
        "--plugins",
        "-p",
        help="Plugins directory (default: scripts/plugins)",
    ),
):
    """List available scripts and plugins."""
    from ethytool.plugin import load_plugins

    base = Path(__file__).resolve().parent.parent
    scripts_dir = base / "dist" / "scripts" if (base / "dist" / "scripts").exists() else base / "scripts"
    plugins_dir = plugins_dir or scripts_dir / "plugins"

    table = Table(title="EthyTool Scripts & Plugins")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Description", style="dim")

    # Built-in scripts
    if scripts_dir.exists():
        for p in sorted(scripts_dir.glob("*.py")):
            if not p.name.startswith("_"):
                table.add_row(p.stem, "script", "")

    # Plugins
    for p in load_plugins(plugins_dir):
        table.add_row(p.name, "plugin", p.description or p.entry)

    console.print(table)


@app.command()
def sim(
    profiles: list[str] = typer.Argument(..., help="Build names (e.g. berserker spellblade)"),
    duration: float = typer.Option(60.0, "--duration", "-d"),
    no_chart: bool = typer.Option(False, "--no-chart"),
):
    """Run DPS simulation for build profiles."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dist" / "scripts"))
    try:
        import dps_dashboard
        dps_dashboard.cmd_simulate(
            profiles + (["--no-chart"] if no_chart else [])
        )
    except ImportError:
        console.print("[red]DPS dashboard not found. Run from EthyTool directory.[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show EthyTool version."""
    from ethytool import __version__
    console.print(f"EthyTool v{__version__}")


if __name__ == "__main__":
    app()
