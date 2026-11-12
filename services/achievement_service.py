"""
services/achievement_service.py
==================================

Qué hace:
    Resuelve "los logros del jugador X" — la pieza que faltaba y
    que `ui/screens/achievements_screen.py` ya estaba esperando
    (`set_achievements()`).

    Deliberadamente NO define ningún catálogo de qué logros existen
    en el juego (eso sería inventar contenido de diseño). Este
    servicio solo administra la colección de `Achievement` que un
    jugador concreto ya tiene otorgada — quién decide otorgar cada
    uno (una decisión de historia, un hito, un logro secreto...) es
    responsabilidad de un sistema que todavía no existe.

    `Achievement.unlocked`/`unlocked_at` (ver `models/achievement.py`)
    viven en el propio objeto: `grant_achievement()` lo añade a la
    colección del jugador (normalmente ya con `unlocked=True`, pero
    no se fuerza — deja abierta la posibilidad de "logro visible
    pero todavía bloqueado", que algunos juegos usan), y
    `unlock_achievement()` sirve para el caso de un logro ya
    otorgado que se desbloquea después.

Cómo funciona:
    Mismo patrón que `services/statistics_service.py` y
    `services/inventory_service.py`: un documento por `player_id` en
    `KeyValueRepository`, serializando la lista de `Achievement` con
    su propio `to_dict()`/`from_dict()`.

Dependencias:
    - services.repositories: KeyValueRepository, JSONKeyValueRepository (por defecto).
    - models.achievement: Achievement.
    - config.paths: SAVES_DIR (progreso de jugador, no contenido narrativo).

Cómo interactúa con otros módulos:
    `ui/screens/gameplay_screen.py` llama a `list_achievements()` al
    cargar una sesión para poblar `AchievementsScreen`. Cuando exista
    un Sistema de Logros real, sería quien llame a
    `grant_achievement()`/`unlock_achievement()`.

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import List, Optional

from config.paths import SAVES_DIR
from models.achievement import Achievement
from services.repositories import JSONKeyValueRepository, KeyValueRepository

logger = logging.getLogger(__name__)

_KEY_PREFIX = "achievements_"


class AchievementNotFoundError(Exception):
    """El jugador no tiene ningún logro con ese `achievement_id`."""


class DuplicateAchievementError(Exception):
    """El jugador ya tiene un logro con ese `achievement_id`."""


class AchievementService:
    """Persiste y gestiona los logros otorgados a un jugador, uno por `player_id`."""

    def __init__(self, repository: Optional[KeyValueRepository] = None) -> None:
        self._repository: KeyValueRepository = repository or JSONKeyValueRepository(
            SAVES_DIR
        )

    # ==================================================
    # CONSULTA
    # ==================================================

    def list_achievements(self, player_id: str) -> List[Achievement]:
        """Todos los logros otorgados a `player_id` (desbloqueados o no)."""
        raw = self._repository.get(self._key(player_id))
        if raw is None:
            return []
        return [Achievement.from_dict(item) for item in raw.get("achievements", [])]

    def list_unlocked(self, player_id: str) -> List[Achievement]:
        """Solo los logros de `player_id` con `unlocked=True`."""
        return [a for a in self.list_achievements(player_id) if a.unlocked]

    def has_achievement(self, player_id: str, achievement_id: str) -> bool:
        return any(a.achievement_id == achievement_id for a in self.list_achievements(player_id))

    # ==================================================
    # MODIFICACIÓN
    # ==================================================

    def grant_achievement(self, player_id: str, achievement: Achievement) -> Achievement:
        """
        Añade `achievement` a la colección de `player_id`.

        Raises:
            DuplicateAchievementError: si el jugador ya tiene un
                logro con ese `achievement_id`.
        """
        achievements = self.list_achievements(player_id)
        if any(a.achievement_id == achievement.achievement_id for a in achievements):
            raise DuplicateAchievementError(
                f"{player_id} ya tiene el logro '{achievement.achievement_id}'."
            )
        achievements.append(achievement)
        self._persist(player_id, achievements)
        logger.info(
            "AchievementService: '%s' otorgado a %s (unlocked=%s)",
            achievement.title, player_id, achievement.unlocked,
        )
        return achievement

    def unlock_achievement(self, player_id: str, achievement_id: str) -> Achievement:
        """
        Marca como desbloqueado un logro que `player_id` ya tenía
        otorgado.

        Raises:
            AchievementNotFoundError: si el jugador no tiene ese
                logro en su colección (hay que otorgarlo primero con
                `grant_achievement()`).
        """
        achievements = self.list_achievements(player_id)
        for achievement in achievements:
            if achievement.achievement_id == achievement_id:
                achievement.unlock()
                self._persist(player_id, achievements)
                logger.info("AchievementService: '%s' desbloqueado para %s", achievement_id, player_id)
                return achievement
        raise AchievementNotFoundError(f"{player_id} no tiene el logro '{achievement_id}'.")

    # ==================================================
    # INTERNO
    # ==================================================

    def _persist(self, player_id: str, achievements: List[Achievement]) -> None:
        self._repository.set(
            self._key(player_id),
            {"achievements": [a.to_dict() for a in achievements]},
        )

    @staticmethod
    def _key(player_id: str) -> str:
        return f"{_KEY_PREFIX}{player_id}"
