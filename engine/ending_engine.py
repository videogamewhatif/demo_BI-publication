"""
engine/ending_engine.py
==========================

Motor encargado de gestionar los finales de vida — reescrito en la
sesión de "desbloquear engine/" contra la API real de
`managers.ending_manager.EndingManager` (antes esperaba
`EndingManager()`/`PlayerManager()`/`AchievementManager()` sin
argumentos con métodos como `unlock_ending`/`get_stat` que nunca
existieron en `PlayerManager`).

Envoltorio delgado a propósito: `EndingManager` ya hace el trabajo
real (catálogo + desbloqueo por jugador); este archivo expone esa
misma API con los nombres que tenía la versión original, y añade el
único paso que de verdad combinaba dos managers — desbloquear un
logro asociado al final, si el final lo trae.

Autor: Korlo
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from managers.achievement_manager import AchievementManager
from managers.ending_manager import EndingManager, EndingNotFoundError
from models.player import Player


class EndingEngine:
    """Envoltorio delgado sobre EndingManager, con el logro asociado opcional."""

    def __init__(
        self,
        ending_manager: EndingManager,
        achievement_manager: Optional[AchievementManager] = None,
    ) -> None:
        self.ending_manager = ending_manager
        self.achievement_manager = achievement_manager

    def get_ending(self, ending_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un final por su id."""
        return self.ending_manager.get_ending(ending_id)

    def unlock_ending(self, player_id: str, ending_id: str) -> Optional[Dict[str, Any]]:
        """
        Marca `ending_id` como desbloqueado para `player_id`. Si el
        final trae un logro asociado (`ending["achievement"]`) y hay
        `AchievementManager` configurado, también lo desbloquea.
        Devuelve la definición del final, o None si no existe.
        """
        try:
            self.ending_manager.unlock_ending(player_id, ending_id)
        except EndingNotFoundError:
            return None

        ending = self.get_ending(ending_id)
        if ending and "achievement" in ending and self.achievement_manager is not None:
            self.achievement_manager.unlock(player_id, ending["achievement"])

        return ending

    def determine_ending(self, player: Player, ending_ids: Optional[List[str]] = None) -> Optional[str]:
        """Determina cuál final corresponde a `player` según sus estadísticas."""
        return self.ending_manager.determine_ending(player, ending_ids)

    def has_ending(self, player_id: str, ending_id: str) -> bool:
        """Comprueba si `player_id` ya desbloqueó `ending_id`."""
        return self.ending_manager.has_ending(player_id, ending_id)
