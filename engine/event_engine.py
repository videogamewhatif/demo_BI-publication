"""
engine/event_engine.py
=========================

Motor encargado de gestionar eventos — reescrito en la sesión de
"desbloquear engine/" contra la API real de
`managers.event_manager.EventManager` (antes esperaba
`EventManager()`/`PlayerManager()` sin argumentos con métodos
`get_stat`/`modify_stat` que nunca existieron en la implementación
real).

Envoltorio delgado a propósito: `EventManager` ya hace todo el
trabajo real (catálogo + disparo + efectos vía ConsequenceService);
este archivo solo expone esa misma API con los nombres que tenía la
versión original, para quien prefiera este estilo.

Autor: Korlo
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from managers.event_manager import EventManager
from models.player import Player


class EventEngine:
    """Envoltorio delgado sobre EventManager."""

    def __init__(self, event_manager: EventManager) -> None:
        self.event_manager = event_manager

    def trigger_event(self, player: Player, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Dispara `event_id` sobre `player`. Devuelve la definición del
        evento si se disparó, o None si no existe o no se cumplen
        los requisitos (tolerante, sin lanzar excepción — mismo
        comportamiento que tenía la versión original).
        """
        from managers.event_manager import EventNotFoundError, EventRequirementsNotMetError
        try:
            event, _applied = self.event_manager.trigger_event(player, event_id)
            return event
        except (EventNotFoundError, EventRequirementsNotMetError):
            return None

    def random_event(self, player: Player, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Obtiene y dispara un evento al azar del catálogo (opcionalmente filtrado por categoría)."""
        picked = self.event_manager.get_random_event(category)
        if picked is None:
            return None
        event_id, _event = picked
        return self.trigger_event(player, event_id)

    def can_trigger(self, player: Player, event: Dict[str, Any]) -> bool:
        """Verifica si `player` cumple los requisitos de `event` sin dispararlo."""
        return self.event_manager.can_trigger(player, event)
