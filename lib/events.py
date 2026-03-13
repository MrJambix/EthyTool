"""
EthyTool Event System — React to game events instead of polling.

Usage:
    conn.on("combat_start", lambda: log("Fight!"))
    conn.on("target_dead", lambda t: loot_all())
    conn.on("hp_below", 30, lambda: conn.do_defend())
"""

import logging
from collections import defaultdict
from typing import Callable, Any, Optional, Union

logger = logging.getLogger("ethytool.events")


class EventMixin:
    """
    Mixin that adds event/hook support to EthyToolConnection.
    Events are emitted by the connection; handlers are called when events fire.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handlers: dict[str, list[tuple[Optional[Union[int, float]], Callable]]] = defaultdict(list)
        self._last_combat = False
        self._last_target_hp: Optional[float] = None
        self._last_had_target = False

    def on(
        self,
        event: str,
        *args,
        handler: Optional[Callable] = None,
        **kwargs,
    ) -> Callable:
        """
        Register a handler for an event.

        For conditional events like hp_below, pass threshold as first arg:
            conn.on("hp_below", 30, handler=lambda: conn.do_defend())

        Returns the handler (for use as decorator).
        """
        if handler is None:
            # Used as decorator: @conn.on("combat_start")
            def decorator(fn):
                self._handlers[event].append((args[0] if args else None, fn))
                return fn
            return decorator
        self._handlers[event].append((args[0] if args else None, handler))
        return handler

    def off(self, event: str, handler: Optional[Callable] = None) -> None:
        """Remove handler(s) for an event. If handler is None, remove all."""
        if handler is None:
            self._handlers[event].clear()
            return
        self._handlers[event] = [(t, h) for t, h in self._handlers[event] if h != handler]

    def emit(self, event: str, *args, **kwargs) -> None:
        """Emit an event to all registered handlers."""
        for threshold, handler in list(self._handlers[event]):
            try:
                if threshold is not None:
                    handler(threshold, *args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                logger.exception("Event handler error for %s: %s", event, e)

    def _tick_events(self) -> None:
        """
        Call this from the main loop to emit state-based events.
        Checks combat_start, combat_end, target_dead, hp_below.
        """
        in_combat = self.in_combat() if hasattr(self, "in_combat") else False
        has_target = self.has_target() if hasattr(self, "has_target") else False
        hp = self.get_hp() if hasattr(self, "get_hp") else 100

        # Combat start/end
        if in_combat and not self._last_combat:
            self.emit("combat_start")
        elif not in_combat and self._last_combat:
            self.emit("combat_end")
        self._last_combat = in_combat

        # Target died
        if self._last_had_target and has_target:
            target_dead = self.is_target_dead() if hasattr(self, "is_target_dead") else False
            if target_dead:
                target_info = self.get_target() if hasattr(self, "get_target") else None
                self.emit("target_dead", target_info)
        self._last_had_target = has_target

        # HP below thresholds
        for threshold, handler in self._handlers.get("hp_below", []):
            if isinstance(threshold, (int, float)) and hp < threshold:
                try:
                    handler()
                except Exception as e:
                    logger.exception("hp_below handler error: %s", e)


class ConnectionEvents:
    """Attaches event support to an existing connection."""

    def __init__(self, conn: Any):
        self.conn = conn
        self._handlers: dict[str, list[tuple[Optional[Union[int, float]], Callable]]] = defaultdict(list)
        self._last_combat = False
        self._last_had_target = False

    def on(self, event: str, *args, handler: Optional[Callable] = None, **kwargs) -> Callable:
        # Support: on("hp_below", 30, lambda: ...) — last positional can be handler
        if handler is None and args and callable(args[-1]):
            handler = args[-1]
            args = args[:-1]
        if handler is None:
            def decorator(fn):
                self._handlers[event].append((args[0] if args else None, fn))
                return fn
            return decorator
        self._handlers[event].append((args[0] if args else None, handler))
        return handler

    def off(self, event: str, handler: Optional[Callable] = None) -> None:
        if handler is None:
            self._handlers[event].clear()
            return
        self._handlers[event] = [(t, h) for t, h in self._handlers[event] if h != handler]

    def emit(self, event: str, *args, **kwargs) -> None:
        for threshold, h in list(self._handlers[event]):
            try:
                if threshold is not None:
                    h(threshold, *args, **kwargs)
                else:
                    h(*args, **kwargs)
            except Exception as e:
                logger.exception("Event handler error for %s: %s", event, e)

    def tick(self) -> None:
        c = self.conn
        in_combat = c.in_combat() if hasattr(c, "in_combat") else False
        has_target = c.has_target() if hasattr(c, "has_target") else False
        hp = c.get_hp() if hasattr(c, "get_hp") else 100
        if in_combat and not self._last_combat:
            self.emit("combat_start")
        elif not in_combat and self._last_combat:
            self.emit("combat_end")
        self._last_combat = in_combat
        if self._last_had_target and has_target and (c.is_target_dead() if hasattr(c, "is_target_dead") else False):
            self.emit("target_dead", c.get_target() if hasattr(c, "get_target") else None)
        self._last_had_target = has_target
        for threshold, h in self._handlers.get("hp_below", []):
            if isinstance(threshold, (int, float)) and hp < threshold:
                try:
                    h()
                except Exception as e:
                    logger.exception("hp_below handler error: %s", e)


def with_events(conn: Any) -> Any:
    """Add on(), off(), emit(), _tick_events() to an existing connection."""
    if hasattr(conn, "_event_helper"):
        return conn
    helper = ConnectionEvents(conn)
    conn._event_helper = helper
    conn.on = helper.on
    conn.off = helper.off
    conn.emit = helper.emit
    conn._tick_events = helper.tick
    return conn
