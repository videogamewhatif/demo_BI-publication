"""
services/memory_service.py
============================

Qué hace:
    Persiste y recupera los Momentos Clave (`MemoryMoment`) del
    Álbum de Vida de un jugador. Mismo patrón exacto que
    `achievement_service.py`/`inventory_service.py`: un documento
    por `player_id` en `KeyValueRepository`, con
    `MemoryMoment.to_dict()`/`from_dict()` para la serialización.

    No decide CUÁNDO se desbloquea un momento ni genera su
    ilustración — eso es `managers/memory_manager.py` (managers
    deciden cuándo/qué, services deciden cómo, mismo criterio que ya
    rige el resto del proyecto).

Dependencias:
    - services.repositories: KeyValueRepository, JSONKeyValueRepository (por defecto).
    - models.memory_moment: MemoryMoment.
    - config.paths: SAVES_DIR (progreso de jugador, no contenido narrativo).

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import List, Optional

from config.paths import SAVES_DIR
from models.memory_moment import MemoryMoment
from services.repositories import JSONKeyValueRepository, KeyValueRepository

logger = logging.getLogger(__name__)

_KEY_PREFIX = "memory_"


class MemoryService:
    """Persiste el Álbum de Vida de un jugador, uno por `player_id`."""

    def __init__(self, repository: Optional[KeyValueRepository] = None) -> None:
        self._repository: KeyValueRepository = repository or JSONKeyValueRepository(SAVES_DIR)

    def list_moments(self, player_id: str) -> List[MemoryMoment]:
        """Devuelve los Momentos Clave de `player_id`, ordenados como se desbloquearon. Vacío si no tiene ninguno."""
        raw = self._repository.get(self._key(player_id))
        if raw is None:
            return []
        return [MemoryMoment.from_dict(d) for d in raw.get("moments", [])]

    def add_moment(self, player_id: str, moment: MemoryMoment) -> MemoryMoment:
        """
        Añade `moment` al Álbum de `player_id` y persiste el
        resultado. Silenciosamente no hace nada si ya existe un
        momento con ese `moment_id` (idempotente — a diferencia de
        `AchievementService.grant_achievement()`, este disparo es
        automático, no una acción explícita del jugador, así que no
        tiene sentido lanzar una excepción por repetirlo).
        """
        moments = self.list_moments(player_id)
        if any(m.moment_id == moment.moment_id for m in moments):
            return moment
        moments.append(moment)
        self._persist(player_id, moments)
        logger.info(
            "MemoryService: momento '%s' (%s) añadido al Álbum de %s",
            moment.moment_id, moment.category, player_id,
        )
        return moment

    def _persist(self, player_id: str, moments: List[MemoryMoment]) -> None:
        self._repository.set(self._key(player_id), {"moments": [m.to_dict() for m in moments]})

    @staticmethod
    def _key(player_id: str) -> str:
        return f"{_KEY_PREFIX}{player_id}"
