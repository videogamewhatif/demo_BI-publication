"""
services/statistics_service.py
===============================

Qué hace:
    Agrega estadísticas a nivel de CUENTA (entre partidas): total de
    vidas jugadas, total de muertes, tiempo total jugado y logros
    desbloqueados. Corresponde conceptualmente a la tabla
    `user_statistics` de `database/users_schema.sql`.

    Es deliberadamente distinto de `models.player.PlayerStatistics`
    (turns_played, decisions_made, key_moments_unlocked), que vive
    DENTRO de una sola vida y se descarta —narrativamente hablando—
    cuando esa vida termina. Este servicio es quien "cosecha" esos
    números al final de cada vida y los sube al nivel de cuenta; no
    duplica su cálculo, los agrega.

Cómo funciona:
    Depende de `KeyValueRepository` (ver services/repositories.py)
    para persistir un documento de estadísticas por `user_id`.
    Expone `record_life_ended()` como el único punto de entrada para
    cerrar una vida y sumar sus números a la cuenta, y
    `record_achievement_unlocked()` como punto de entrada separado
    para cuando el futuro Sistema de Logros desbloquee uno — son dos
    eventos distintos (fin de vida vs. logro) y mezclarlos en un solo
    método habría acoplado dos responsabilidades distintas.

Dependencias:
    - services.repositories: KeyValueRepository, JSONKeyValueRepository (por defecto).
    - models.player: Player (se lee su `statistics`, no se modifica).
    - config.paths: SAVES_DIR.

Cómo interactúa con otros módulos:
    El futuro `managers/player_manager.py` (o el Sistema de
    Condiciones de Derrota del GDD) debe llamar a
    `record_life_ended()` cuando un `Player` deja de estar vivo o
    la partida termina por cualquier otro cierre narrativo.

Autor: Korlo
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional

from config.paths import SAVES_DIR
from models.player import Player
from services.repositories import JSONKeyValueRepository, KeyValueRepository

logger = logging.getLogger(__name__)

_KEY_PREFIX = "stats_"


@dataclass
class AccountStatistics:
    """
    Estadísticas agregadas de una cuenta de usuario, acumuladas a
    través de todas las vidas jugadas.

    `total_play_time` se mide en turnos jugados (suma de
    `PlayerStatistics.turns_played` de cada vida), no en tiempo de
    reloj: el proyecto todavía no tiene un cronómetro de sesión, y
    turnos jugados es una métrica ya disponible y consistente con el
    modelo de "Bucle de Vida por turnos" del GDD. Si más adelante se
    añade un cronómetro real, este campo puede pasar a medir
    segundos sin cambiar la interfaz pública de este servicio.
    """

    user_id: str
    total_games: int = 0
    total_deaths: int = 0
    total_play_time: int = 0
    achievements_unlocked: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convierte las estadísticas a diccionario serializable."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccountStatistics":
        """Reconstruye estadísticas de cuenta desde un diccionario."""
        return cls(
            user_id=data["user_id"],
            total_games=data.get("total_games", 0),
            total_deaths=data.get("total_deaths", 0),
            total_play_time=data.get("total_play_time", 0),
            achievements_unlocked=data.get("achievements_unlocked", 0),
        )


class StatisticsService:
    """Agrega y persiste estadísticas de cuenta a través de las vidas jugadas."""

    def __init__(self, repository: Optional[KeyValueRepository] = None) -> None:
        self._repository: KeyValueRepository = repository or JSONKeyValueRepository(
            SAVES_DIR
        )

    # ==================================================
    # CONSULTA
    # ==================================================

    def get_statistics(self, user_id: str) -> AccountStatistics:
        """
        Devuelve las estadísticas de la cuenta `user_id`, o un
        registro en cero si todavía no tiene ninguna vida cerrada.
        """
        raw = self._repository.get(self._key(user_id))
        if raw is None:
            return AccountStatistics(user_id=user_id)
        return AccountStatistics.from_dict(raw)

    # ==================================================
    # REGISTRO DE EVENTOS
    # ==================================================

    def record_life_ended(self, user_id: str, player: Player, died: bool) -> AccountStatistics:
        """
        Cosecha las estadísticas de una vida que acaba de terminar
        (`player`) y las suma a la cuenta `user_id`.

        Args:
            user_id: cuenta a la que pertenece esta vida.
            player: Estado de Personaje de la vida que terminó.
            died: True si la vida terminó por muerte del personaje
                (Salud a 0); False si terminó por cualquier otro
                cierre narrativo (jubilación, final especial, etc.).
        """
        stats = self.get_statistics(user_id)
        stats.total_games += 1
        stats.total_play_time += player.statistics.turns_played
        if died:
            stats.total_deaths += 1

        self._persist(stats)
        logger.info(
            "StatisticsService: vida de %s cerrada para cuenta %s "
            "(died=%s, turns=%s)",
            player.full_name, user_id, died, player.statistics.turns_played,
        )
        return stats

    def record_achievement_unlocked(self, user_id: str) -> AccountStatistics:
        """Incrementa el contador de logros desbloqueados de la cuenta."""
        stats = self.get_statistics(user_id)
        stats.achievements_unlocked += 1
        self._persist(stats)
        logger.info("StatisticsService: logro desbloqueado para cuenta %s", user_id)
        return stats

    def reset_statistics(self, user_id: str) -> AccountStatistics:
        """Reinicia las estadísticas de una cuenta a cero."""
        stats = AccountStatistics(user_id=user_id)
        self._persist(stats)
        logger.info("StatisticsService: estadísticas de %s reiniciadas", user_id)
        return stats

    # ==================================================
    # INTERNO
    # ==================================================

    def _persist(self, stats: AccountStatistics) -> None:
        self._repository.set(self._key(stats.user_id), stats.to_dict())

    @staticmethod
    def _key(user_id: str) -> str:
        return f"{_KEY_PREFIX}{user_id}"