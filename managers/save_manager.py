"""
managers/save_manager.py
=========================

Qué hace:
    Decide CUÁNDO guardar la partida — política de autoguardado por
    turnos, guardado rápido con una ranura fija — y delega el CÓMO
    (serializar, escribir, leer) en `services.save_service.SaveService`.

    No mantiene el estado de la partida en curso (no guarda una
    referencia al `Player`/`Story` "actuales"): los recibe como
    parámetro en cada llamada. La razón es que todavía no existe un
    `GameEngine` consolidado que posea esa referencia de forma
    central — cuando exista, seguirá siendo quien llama a este
    manager con el estado vigente, y este manager seguirá sin
    necesitar guardarlo por su cuenta.

Cómo funciona:
    Es exactamente el tipo de "director de orquesta" que describiste:
    no sabe serializar un `Player` ni escribir un archivo — eso es
    `SaveService`. Solo decide SI corresponde autoguardar en este
    turno, y bajo qué nombre de ranura.

Dependencias:
    - services.save_service: SaveService, LoadedGame y sus excepciones.
    - models.player, models.story, models.npc (solo para type hints).

Cómo interactúa con otros módulos:
    `main.py` ya espera `from managers.save_manager import SaveManager`.
    El futuro `GameEngine` debe llamar a `autosave_if_due()` en cada
    turno y a `quick_save()`/`quick_load()` ante el atajo
    correspondiente, en vez de hablar con `SaveService` directamente.

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import List, Optional

from models.npc import NPC
from models.player import Player
from models.story import Story
from services.save_service import (
    LoadedGame,
    SaveNotFoundError,
    SaveService,
    SaveSlot,
    UnsupportedSaveFormatError,
)

logger = logging.getLogger(__name__)

QUICKSAVE_SLOT = "quicksave"
AUTOSAVE_SLOT = "autosave"
DEFAULT_AUTOSAVE_INTERVAL_TURNS = 5

__all__ = [
    "SaveManager",
    "SaveNotFoundError",
    "UnsupportedSaveFormatError",
    "LoadedGame",
    "SaveSlot",
]


class SaveManager:
    """
    Orquesta CUÁNDO se guarda la partida (autoguardado, guardado
    rápido), delegando la persistencia real en `SaveService`.
    """

    def __init__(
        self,
        save_service: SaveService,
        autosave_interval_turns: int = DEFAULT_AUTOSAVE_INTERVAL_TURNS,
    ) -> None:
        if autosave_interval_turns <= 0:
            raise ValueError("autosave_interval_turns debe ser mayor a 0.")
        self._save_service = save_service
        self._autosave_interval = autosave_interval_turns
        self._last_autosave_turn = 0

    # ==================================================
    # GUARDADO MANUAL
    # ==================================================

    def save_now(
        self,
        save_id: str,
        player: Player,
        stories: Optional[List[Story]] = None,
        npcs: Optional[List[NPC]] = None,
    ) -> None:
        """Guarda inmediatamente bajo `save_id`, sin pasar por la política de autoguardado."""
        self._save_service.save_game(save_id, player, stories, npcs)
        logger.info("SaveManager: guardado manual en '%s'.", save_id)

    # ==================================================
    # AUTOGUARDADO
    # ==================================================

    def autosave_if_due(
        self,
        current_turn: int,
        player: Player,
        stories: Optional[List[Story]] = None,
        npcs: Optional[List[NPC]] = None,
    ) -> bool:
        """
        Autoguarda en la ranura `AUTOSAVE_SLOT` si transcurrieron al
        menos `autosave_interval_turns` desde el último autoguardado.

        Returns:
            True si autoguardó en esta llamada, False si todavía no
            correspondía.
        """
        if current_turn - self._last_autosave_turn < self._autosave_interval:
            return False

        self.save_now(AUTOSAVE_SLOT, player, stories, npcs)
        self._last_autosave_turn = current_turn
        logger.info("SaveManager: autoguardado en el turno %s.", current_turn)
        return True

    def turns_until_next_autosave(self, current_turn: int) -> int:
        """Cuántos turnos faltan para el próximo autoguardado (0 si ya corresponde)."""
        remaining = self._autosave_interval - (current_turn - self._last_autosave_turn)
        return max(0, remaining)

    # ==================================================
    # GUARDADO RÁPIDO
    # ==================================================

    def quick_save(
        self,
        player: Player,
        stories: Optional[List[Story]] = None,
        npcs: Optional[List[NPC]] = None,
    ) -> None:
        """Guarda en la ranura fija de guardado rápido, sobrescribiendo la anterior."""
        self.save_now(QUICKSAVE_SLOT, player, stories, npcs)

    def quick_load(self) -> LoadedGame:
        """
        Carga la ranura de guardado rápido.

        Raises:
            SaveNotFoundError: si todavía no se hizo ningún quick_save.
        """
        return self._save_service.load_game(QUICKSAVE_SLOT)

    # ==================================================
    # CARGA Y GESTIÓN DE RANURAS
    # ==================================================

    def load(self, save_id: str) -> LoadedGame:
        """
        Carga la partida `save_id`.

        Raises:
            SaveNotFoundError: si no existe.
            UnsupportedSaveFormatError: si su formato es más nuevo
                que el que este servicio sabe leer.
        """
        return self._save_service.load_game(save_id)

    def delete_save(self, save_id: str) -> None:
        """Elimina la partida `save_id`."""
        self._save_service.delete_save(save_id)

    def save_exists(self, save_id: str) -> bool:
        """Indica si existe una partida guardada con ese id."""
        return self._save_service.save_exists(save_id)

    def list_saves(self) -> List[SaveSlot]:
        """Lista los metadatos de todas las partidas guardadas."""
        return self._save_service.list_saves()