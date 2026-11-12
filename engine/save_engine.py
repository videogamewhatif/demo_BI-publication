"""
engine/save_engine.py
========================

Motor encargado de guardar/cargar partidas — reescrito en la sesión
de "desbloquear engine/" contra la API real de
`managers.save_manager.SaveManager` (antes esperaba `SaveManager()`
sin argumentos — el real requiere `save_service` — y armaba un
único blob `{"player", "inventory", "story"}` a mano).

Por qué ya no incluye inventario en el guardado explícitamente:
    `services.inventory_service.InventoryService` y
    `services.achievement_service.AchievementService` ya persisten
    por su cuenta, en cuanto se llama a `add_item()`/`grant_achievement()`
    — no esperan a un guardado explícito. `SaveManager` real solo
    guarda `Player` + `Story` (lo único que sí necesita un momento
    explícito de "guardar ahora"). Envolver eso aquí sería
    reimplementar una decisión de guardado que `SaveManager` ya
    toma correctamente.

Autor: Korlo
"""

from __future__ import annotations

from typing import List, Optional

from managers.save_manager import SaveManager, SaveNotFoundError
from managers.save_manager import QUICKSAVE_SLOT
from models.player import Player
from models.story import Story


class SaveEngine:
    """Envoltorio delgado sobre SaveManager (guardado/carga de Player + Story)."""

    def __init__(self, save_manager: SaveManager) -> None:
        self.save_manager = save_manager

    def save(self, player: Player, stories: List[Story], slot: str = QUICKSAVE_SLOT) -> None:
        """Guarda el estado actual del juego en `slot`."""
        self.save_manager.save_now(slot, player, stories)

    def load(self, slot: str = QUICKSAVE_SLOT) -> Optional[dict]:
        """
        Carga la partida de `slot`. Devuelve `{"player", "stories"}`,
        o None si no existe (tolerante, sin lanzar excepción — mismo
        comportamiento que tenía la versión original).
        """
        try:
            loaded = self.save_manager.load(slot)
        except SaveNotFoundError:
            return None
        return {"player": loaded.player, "stories": loaded.stories}

    def delete(self, slot: str) -> None:
        """Elimina la partida guardada en `slot`."""
        self.save_manager.delete_save(slot)

    def exists(self, slot: str) -> bool:
        """Comprueba si existe una partida guardada en `slot`."""
        return self.save_manager.save_exists(slot)

    def list_saves(self):
        """Devuelve todas las partidas guardadas disponibles."""
        return self.save_manager.list_saves()

    def autosave(self, player: Player, stories: List[Story]):
        """Guardado rápido — usa la misma ranura que 'Continuar' en el menú principal."""
        return self.save_manager.quick_save(player, stories)
