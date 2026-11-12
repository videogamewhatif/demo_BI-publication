"""
engine/achievement_engine.py
===============================

Motor encargado de gestionar los logros — reescrito en la sesión de
"desbloquear engine/" contra la API real de
`managers.achievement_manager.AchievementManager` (antes esperaba
`AchievementManager()`/`PlayerManager()` sin argumentos con métodos
como `has_achievement`/`get_achievements` que vivían en
`PlayerManager`, cuando en realidad esa responsabilidad es de
`services.achievement_service.AchievementService`).

Envoltorio delgado a propósito: `AchievementManager` ya hace todo el
trabajo real; este archivo solo expone esa misma API con los nombres
que tenía la versión original.

Autor: Korlo
"""

from __future__ import annotations

from typing import Any, Dict, List

from managers.achievement_manager import AchievementManager
from models.player import Player


class AchievementEngine:
    """Envoltorio delgado sobre AchievementManager."""

    def __init__(self, achievement_manager: AchievementManager) -> None:
        self.achievement_manager = achievement_manager

    def unlock(self, player_id: str, achievement_id: str) -> bool:
        """Desbloquea un logro. Devuelve False si ya estaba desbloqueado."""
        return self.achievement_manager.unlock(player_id, achievement_id)

    def is_unlocked(self, player_id: str, achievement_id: str) -> bool:
        """Comprueba si un logro ya fue desbloqueado."""
        return self.achievement_manager.is_unlocked(player_id, achievement_id)

    def check(self, player: Player, achievement_id: str) -> bool:
        """Verifica si `player` cumple los requisitos de `achievement_id` según el catálogo."""
        return self.achievement_manager.check(player, achievement_id)

    def check_all(self, player: Player) -> List[str]:
        """Comprueba todos los logros del catálogo y desbloquea los que correspondan."""
        return self.achievement_manager.check_all(player)

    def get_progress(self, player_id: str) -> Dict[str, Any]:
        """Devuelve el progreso de logros: {'unlocked', 'total', 'percentage'}."""
        return self.achievement_manager.get_progress(player_id)

    def get_unlocked(self, player_id: str):
        """Devuelve los logros desbloqueados de `player_id`."""
        return self.achievement_manager.get_unlocked(player_id)
