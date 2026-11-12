"""
managers/ending_manager.py
=============================

Qué hace:
    Quinto manager de dominio. No confundir con el `ending_id` que
    ya maneja `models.story.Story` (el cierre de UNA historia
    concreta): esto es un catálogo de finales "de vida" — categorías
    más amplias evaluadas contra las estadísticas finales del
    jugador (p. ej. "Final del Empresario": patrimonio > X), en la
    línea de lo que `engine/ending_engine.py` ya insinuaba antes de
    esta sesión.

    - Catálogo: lee definiciones de `data/endings/<ending_id>.json`
      (mismo mecanismo que `EventManager`/`StoryService`).
    - Desbloqueo por jugador: qué finales de vida ya alcanzó cada
      jugador — persistido con el mismo patrón que
      `services.achievement_service.AchievementService`
      (un documento por `player_id` en `KeyValueRepository`).

Qué NO hace (alcance dejado fuera a propósito):
    No inventa ningún final — `data/endings/` existe pero está vacía;
    diseñarlos es contenido, no código.

Formato esperado de un final (mismo patrón que eventos/effects):

    {
      "title": "...",
      "achievement": "logro_opcional_asociado",
      "requirements": {"stats": {"net_worth": 100000}}
    }

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config.paths import ENDINGS_DIR, SAVES_DIR
from models.player import Player
from services.repositories import (
    ContentRepository,
    JSONContentRepository,
    JSONKeyValueRepository,
    KeyValueRepository,
)

logger = logging.getLogger(__name__)

_KEY_PREFIX = "unlocked_endings_"


class EndingNotFoundError(Exception):
    """No existe ningún final con ese id en el catálogo."""


class EndingManager:
    """Catálogo de finales de vida + qué finales tiene desbloqueados cada jugador."""

    def __init__(
        self,
        content_repository: Optional[ContentRepository] = None,
        progress_repository: Optional[KeyValueRepository] = None,
    ) -> None:
        self._content: ContentRepository = content_repository or JSONContentRepository(ENDINGS_DIR)
        self._progress: KeyValueRepository = progress_repository or JSONKeyValueRepository(SAVES_DIR)

    # ==================================================
    # CATÁLOGO
    # ==================================================

    def get_ending(self, ending_id: str) -> Optional[Dict[str, Any]]:
        """Devuelve la definición del final, o None si no existe."""
        return self._content.load(ending_id)

    def list_endings(self) -> List[str]:
        """Todos los ids de final disponibles en el catálogo."""
        return self._content.list_keys()

    def determine_ending(self, player: Player, ending_ids: Optional[List[str]] = None) -> Optional[str]:
        """
        Recorre `ending_ids` (o todo el catálogo si no se especifica)
        en orden y devuelve el id del PRIMER final cuyos requisitos
        de estadísticas cumple `player`, o None si ninguno.
        """
        candidates = ending_ids if ending_ids is not None else self.list_endings()
        for ending_id in candidates:
            ending = self.get_ending(ending_id)
            if ending is not None and self._requirements_met(player, ending):
                return ending_id
        return None

    def _requirements_met(self, player: Player, ending: Dict[str, Any]) -> bool:
        requirements = ending.get("requirements", {}).get("stats", {})
        for stat, minimum in requirements.items():
            value = getattr(player, stat, None)
            if value is None or value < minimum:
                return False
        return True

    # ==================================================
    # DESBLOQUEO POR JUGADOR
    # ==================================================

    def unlock_ending(self, player_id: str, ending_id: str) -> None:
        """
        Marca `ending_id` como desbloqueado para `player_id`.

        Raises:
            EndingNotFoundError: si `ending_id` no está en el catálogo.
        """
        if self.get_ending(ending_id) is None:
            raise EndingNotFoundError(f"No existe el final '{ending_id}'.")
        unlocked = set(self._unlocked_ids(player_id))
        unlocked.add(ending_id)
        self._progress.set(self._key(player_id), {"unlocked": sorted(unlocked)})
        logger.info("EndingManager: '%s' desbloqueado para %s", ending_id, player_id)

    def has_ending(self, player_id: str, ending_id: str) -> bool:
        """Indica si `player_id` ya desbloqueó `ending_id`."""
        return ending_id in self._unlocked_ids(player_id)

    def list_unlocked(self, player_id: str) -> List[str]:
        """Todos los ids de final que `player_id` ya desbloqueó."""
        return self._unlocked_ids(player_id)

    def _unlocked_ids(self, player_id: str) -> List[str]:
        raw = self._progress.get(self._key(player_id))
        if raw is None:
            return []
        return list(raw.get("unlocked", []))

    @staticmethod
    def _key(player_id: str) -> str:
        return f"{_KEY_PREFIX}{player_id}"
