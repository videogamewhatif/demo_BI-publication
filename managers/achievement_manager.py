"""
managers/achievement_manager.py
==================================

Qué hace:
    Sexto manager de dominio. NO reemplaza
    `services.achievement_service.AchievementService` (que ya
    gestiona qué logros tiene OTORGADOS un jugador) — lo envuelve, y
    le añade la mitad que le faltaba a propósito: un catálogo de
    DEFINICIONES de logro con requisitos, para poder comprobar
    automáticamente cuáles debería desbloquear un jugador según sus
    estadísticas (`check()`, `check_all()`), tal como
    `engine/achievement_engine.py` ya esperaba antes de esta sesión.

    - Catálogo: lee definiciones de
      `data/achievements/<achievement_id>.json`.
    - Otorgados: delega en `AchievementService` — no duplica esa
      lógica.
    - Estadísticas de cuenta: si se configura un `StatisticsService`,
      cada desbloqueo real llama a
      `record_achievement_unlocked()` — reutiliza ese contador
      existente en vez de llevar uno propio aparte.

Qué NO hace (alcance dejado fuera a propósito):
    No inventa ningún logro — `data/achievements/` existe pero está
    vacía; diseñarlos es contenido, no código.

Formato esperado de una definición de logro en el catálogo:

    {
      "title": "...",
      "description": "...",
      "requirements": {"stats": {"discipline": 80}}
    }

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config.paths import ACHIEVEMENTS_DIR
from models.achievement import Achievement
from models.player import Player
from services.achievement_service import AchievementService
from services.repositories import ContentRepository, JSONContentRepository
from services.statistics_service import StatisticsService

logger = logging.getLogger(__name__)


class AchievementManager:
    """Catálogo de definiciones de logro + delegación en AchievementService para lo otorgado."""

    def __init__(
        self,
        achievement_service: AchievementService,
        catalog_repository: Optional[ContentRepository] = None,
        statistics_service: Optional[StatisticsService] = None,
    ) -> None:
        self._achievement_service = achievement_service
        self._catalog: ContentRepository = catalog_repository or JSONContentRepository(ACHIEVEMENTS_DIR)
        self._statistics_service = statistics_service

    # ==================================================
    # CATÁLOGO
    # ==================================================

    def get_achievement_definition(self, achievement_id: str) -> Optional[Dict[str, Any]]:
        """La definición cruda (con requisitos) del catálogo, o None si no existe."""
        return self._catalog.load(achievement_id)

    def list_catalog(self) -> List[str]:
        """Todos los ids de logro definidos en el catálogo."""
        return self._catalog.list_keys()

    # ==================================================
    # OTORGADOS (delega en AchievementService, no lo duplica)
    # ==================================================

    def unlock(self, player_id: str, achievement_id: str) -> bool:
        """
        Otorga y desbloquea `achievement_id` para `player_id` si
        todavía no lo tenía. Devuelve False si ya lo tenía (no es un
        error, es un no-op informativo). Si hay `StatisticsService`
        configurado, un desbloqueo real también llama a
        `record_achievement_unlocked()` — mismo contador de cuenta
        que ya usa `ui/screens/statistics_screen.py`, no uno nuevo.
        """
        if self._achievement_service.has_achievement(player_id, achievement_id):
            return False
        definition = self.get_achievement_definition(achievement_id) or {}
        achievement = Achievement(
            achievement_id=achievement_id,
            title=definition.get("title", achievement_id),
            description=definition.get("description", ""),
        )
        self._achievement_service.grant_achievement(player_id, achievement)
        self._achievement_service.unlock_achievement(player_id, achievement_id)
        if self._statistics_service is not None:
            self._statistics_service.record_achievement_unlocked(player_id)
        return True

    def is_unlocked(self, player_id: str, achievement_id: str) -> bool:
        return self._achievement_service.has_achievement(player_id, achievement_id)

    def get_unlocked(self, player_id: str) -> List[Achievement]:
        return self._achievement_service.list_unlocked(player_id)

    # ==================================================
    # COMPROBACIÓN CONTRA REQUISITOS
    # ==================================================

    def check(self, player: Player, achievement_id: str) -> bool:
        """¿`player` cumple los requisitos de `achievement_id` según el catálogo?"""
        definition = self.get_achievement_definition(achievement_id)
        if definition is None:
            return False
        requirements = definition.get("requirements", {}).get("stats", {})
        for stat, minimum in requirements.items():
            value = getattr(player, stat, None)
            if value is None or value < minimum:
                return False
        return True

    def check_all(self, player: Player) -> List[str]:
        """
        Recorre todo el catálogo, desbloqueando (y devolviendo) los
        ids de los logros que `player` cumple y todavía no tenía.
        """
        newly_unlocked: List[str] = []
        for achievement_id in self.list_catalog():
            if self.is_unlocked(player.player_id, achievement_id):
                continue
            if self.check(player, achievement_id):
                if self.unlock(player.player_id, achievement_id):
                    newly_unlocked.append(achievement_id)
        return newly_unlocked

    def get_progress(self, player_id: str) -> Dict[str, Any]:
        """Progreso de logros: {'unlocked', 'total', 'percentage'}."""
        total = len(self.list_catalog())
        unlocked = len(self._achievement_service.list_unlocked(player_id))
        return {
            "unlocked": unlocked,
            "total": total,
            "percentage": (unlocked / total * 100) if total else 0.0,
        }
