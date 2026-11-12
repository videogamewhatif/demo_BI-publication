"""
services/save_service.py
=========================

Qué hace:
    Orquesta el guardado y la carga de una partida completa: agrupa
    el `Player`, sus `Story` activas/relevantes y los `NPC`
    involucrados bajo un único identificador de partida (`save_id`),
    para que quien lo use (el futuro `GameEngine`, o un
    `managers/save_manager.py`) no tenga que conocer el formato de
    persistencia ni ensamblar esas piezas a mano.

Cómo funciona:
    Depende de `services.repositories.KeyValueRepository` (una
    interfaz, no una implementación concreta — Dependency
    Inversion). No sabe si por debajo hay archivos JSON o SQLite; eso
    es justamente lo que esa abstracción mantiene oculto. Cada
    partida se serializa como un único documento con
    `format_version`, para poder migrar el formato de guardado en el
    futuro sin romper partidas ya guardadas.

Dependencias:
    - services.repositories: KeyValueRepository, JSONKeyValueRepository (por defecto).
    - models.player: Player.
    - models.story: Story.
    - models.npc: NPC.
    - config.paths: SAVES_DIR (ubicación por defecto del repositorio).

Cómo interactúa con otros módulos:
    Reemplaza la lógica que hoy está dispersa y rota entre
    `engine/save_engine.py` (depende de un `managers/` inexistente)
    y `database/` (tres esquemas de guardado sin consolidar — ver
    análisis previo). Cuando se construya `managers/`, el futuro
    `SaveManager` debería delegar aquí en vez de reimplementar esta
    lógica.

Autor: Korlo
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.paths import SAVES_DIR
from models.npc import NPC
from models.player import Player
from models.story import Story
from services.repositories import JSONKeyValueRepository, KeyValueRepository

logger = logging.getLogger(__name__)

SAVE_FORMAT_VERSION = 1
_KEY_PREFIX = "save_"


class SaveNotFoundError(Exception):
    """Se lanza al intentar cargar o eliminar una partida que no existe."""


class UnsupportedSaveFormatError(Exception):
    """
    Se lanza cuando una partida guardada fue escrita con una versión
    de formato más nueva que la que este servicio sabe leer.
    """


@dataclass
class SaveSlot:
    """
    Metadatos ligeros de una partida guardada, sin cargar el
    contenido completo — pensado para listar partidas en un menú de
    "Continuar" sin deserializar cada Player/Story/NPC.
    """

    save_id: str
    player_name: str
    player_age: int
    saved_at: str  # ISO 8601, UTC


@dataclass
class LoadedGame:
    """Resultado de cargar una partida: sus tres piezas ya reconstruidas."""

    player: Player
    stories: List[Story]
    npcs: List[NPC]


class SaveService:
    """
    Orquesta el guardado y la carga de partidas completas.

    Una partida guardada agrupa el Player, sus Story y sus NPC bajo
    un único `save_id`, de modo que guardar/cargar sea una sola
    operación atómica desde el punto de vista de quien la usa.
    """

    def __init__(self, repository: Optional[KeyValueRepository] = None) -> None:
        self._repository: KeyValueRepository = repository or JSONKeyValueRepository(
            SAVES_DIR
        )

    # ==================================================
    # GUARDADO
    # ==================================================

    def save_game(
        self,
        save_id: str,
        player: Player,
        stories: Optional[List[Story]] = None,
        npcs: Optional[List[NPC]] = None,
    ) -> None:
        """
        Guarda una partida completa bajo `save_id`, sobrescribiendo
        cualquier partida previa con el mismo id.

        Args:
            save_id: identificador de la ranura de guardado (por
                ejemplo, "autosave" o un UUID por partida).
            player: Estado de Personaje a persistir.
            stories: historias activas/relevantes del jugador.
                Vacío por defecto.
            npcs: NPC relevantes para reconstruir la partida (familia,
                relaciones activas). Vacío por defecto.

        Raises:
            ValueError: si `save_id` está vacío.
        """
        if not save_id:
            raise ValueError("save_id no puede estar vacío.")

        payload: Dict[str, Any] = {
            "format_version": SAVE_FORMAT_VERSION,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "player": player.to_dict(),
            "stories": [story.to_dict() for story in (stories or [])],
            "npcs": [npc.to_dict() for npc in (npcs or [])],
        }
        self._repository.set(self._key(save_id), payload)
        logger.info("SaveService: partida '%s' guardada.", save_id)

    # ==================================================
    # CARGA
    # ==================================================

    def load_game(self, save_id: str) -> LoadedGame:
        """
        Carga una partida completa.

        Raises:
            SaveNotFoundError: si no existe una partida con ese id.
            UnsupportedSaveFormatError: si el formato guardado es de
                una versión más nueva que la que este servicio sabe
                leer.
        """
        raw = self._repository.get(self._key(save_id))
        if raw is None:
            raise SaveNotFoundError(f"No existe la partida '{save_id}'.")

        format_version = raw.get("format_version", 1)
        if format_version > SAVE_FORMAT_VERSION:
            raise UnsupportedSaveFormatError(
                f"La partida '{save_id}' fue guardada con un formato "
                f"más nuevo ({format_version}) del que este servicio "
                f"sabe leer ({SAVE_FORMAT_VERSION})."
            )

        logger.info("SaveService: partida '%s' cargada.", save_id)
        return LoadedGame(
            player=Player.from_dict(raw["player"]),
            stories=[Story.from_dict(s) for s in raw.get("stories", [])],
            npcs=[NPC.from_dict(n) for n in raw.get("npcs", [])],
        )

    # ==================================================
    # GESTIÓN DE RANURAS
    # ==================================================

    def save_exists(self, save_id: str) -> bool:
        """Indica si existe una partida guardada con ese id."""
        return self._repository.get(self._key(save_id)) is not None

    def delete_save(self, save_id: str) -> None:
        """
        Elimina una partida guardada.

        Raises:
            SaveNotFoundError: si no existe una partida con ese id.
        """
        if not self.save_exists(save_id):
            raise SaveNotFoundError(f"No existe la partida '{save_id}'.")
        self._repository.delete(self._key(save_id))
        logger.info("SaveService: partida '%s' eliminada.", save_id)

    def list_saves(self) -> List[SaveSlot]:
        """
        Lista los metadatos de todas las partidas guardadas, sin
        cargar el contenido completo de cada una (útil para un menú
        de "Continuar").
        """
        slots: List[SaveSlot] = []
        for key in self._repository.list_keys(prefix=_KEY_PREFIX):
            raw = self._repository.get(key)
            if raw is None:
                continue
            player_data = raw.get("player", {})
            slots.append(
                SaveSlot(
                    save_id=key[len(_KEY_PREFIX):],
                    player_name=(
                        f"{player_data.get('first_name', '?')} "
                        f"{player_data.get('last_name', '?')}"
                    ),
                    player_age=player_data.get("age", 0),
                    saved_at=raw.get("saved_at", ""),
                )
            )
        return sorted(slots, key=lambda slot: slot.saved_at, reverse=True)

    @staticmethod
    def _key(save_id: str) -> str:
        """Aplica el prefijo de namespace para no mezclar claves con otros servicios."""
        return f"{_KEY_PREFIX}{save_id}"