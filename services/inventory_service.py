"""
services/inventory_service.py
================================

Qué hace:
    Resuelve "el inventario del jugador X" — la pieza que faltaba y
    que `ui/screens/inventory_screen.py` ya estaba esperando
    (`set_items()`). Antes de este archivo, `models/inventory.py`
    (`Inventory`, con `add_item`/`remove_item`/`has_item`) existía
    pero nada lo conectaba a un `player_id` concreto ni lo persistía.

    No inventa qué objetos existen en el juego — ver
    `models/item.py`, que solo define el esquema. Este servicio
    únicamente guarda/recupera la colección de `Item` que OTRO
    sistema (todavía no construido: eventos, tienda, recompensas de
    decisión...) le entregue vía `add_item()`.

Cómo funciona:
    Mismo patrón que `services/statistics_service.py`: un documento
    por `player_id` en `KeyValueRepository`, con `Inventory.to_dict()`/
    `from_dict()` para la serialización — `Inventory` ya sabía hacer
    esto, no hubo que añadírselo.

Dependencias:
    - services.repositories: KeyValueRepository, JSONKeyValueRepository (por defecto).
    - models.inventory: Inventory.
    - models.item: Item.
    - config.paths: SAVES_DIR (mismo directorio base que
      statistics_service.py y save_service.py: es progreso de
      jugador, no contenido narrativo).

Cómo interactúa con otros módulos:
    `ui/screens/gameplay_screen.py` llama a `get_inventory()` al
    cargar una sesión para poblar `InventoryScreen`. El futuro
    Sistema de Consecuencias (o de eventos) sería quien llame a
    `add_item()`/`remove_item()` cuando una decisión otorgue o quite
    un objeto — ninguno de los dos existe todavía.

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Optional

from config.paths import SAVES_DIR
from models.inventory import Inventory
from models.item import Item
from services.repositories import JSONKeyValueRepository, KeyValueRepository

logger = logging.getLogger(__name__)

_KEY_PREFIX = "inventory_"


class ItemNotFoundError(Exception):
    """El `item_id` pedido no está en el inventario de ese jugador."""


class InventoryFullError(Exception):
    """El inventario alcanzó su `capacity` y no admite más objetos."""


class InventoryService:
    """Persiste y gestiona el inventario de un jugador, uno por `player_id`."""

    def __init__(self, repository: Optional[KeyValueRepository] = None) -> None:
        self._repository: KeyValueRepository = repository or JSONKeyValueRepository(
            SAVES_DIR
        )

    # ==================================================
    # CONSULTA
    # ==================================================

    def get_inventory(self, player_id: str) -> Inventory:
        """Devuelve el inventario de `player_id`, o uno vacío si todavía no tiene ninguno."""
        raw = self._repository.get(self._key(player_id))
        if raw is None:
            return Inventory()
        return Inventory.from_dict(raw)

    def has_item(self, player_id: str, item_id: str) -> bool:
        """Indica si el jugador tiene un objeto con ese `item_id`."""
        return self.get_inventory(player_id).has_item(item_id)

    # ==================================================
    # MODIFICACIÓN
    # ==================================================

    def add_item(self, player_id: str, item: Item) -> Inventory:
        """
        Añade `item` al inventario de `player_id` y persiste el
        resultado.

        Raises:
            InventoryFullError: si el inventario tiene `capacity`
                fija y ya está lleno.
        """
        inventory = self.get_inventory(player_id)
        if not inventory.add_item(item):
            raise InventoryFullError(
                f"El inventario de {player_id} está lleno (capacidad {inventory.capacity})."
            )
        self._persist(player_id, inventory)
        logger.info("InventoryService: '%s' añadido al inventario de %s", item.name, player_id)
        return inventory

    def remove_item(self, player_id: str, item_id: str) -> Inventory:
        """
        Quita el objeto `item_id` del inventario de `player_id` y
        persiste el resultado.

        Raises:
            ItemNotFoundError: si el jugador no tiene ese objeto.
        """
        inventory = self.get_inventory(player_id)
        if not inventory.remove_item(item_id):
            raise ItemNotFoundError(f"'{item_id}' no está en el inventario de {player_id}.")
        self._persist(player_id, inventory)
        logger.info("InventoryService: '%s' quitado del inventario de %s", item_id, player_id)
        return inventory

    def clear_inventory(self, player_id: str) -> Inventory:
        """Vacía por completo el inventario de `player_id`."""
        inventory = self.get_inventory(player_id)
        inventory.clear()
        self._persist(player_id, inventory)
        logger.info("InventoryService: inventario de %s vaciado", player_id)
        return inventory

    # ==================================================
    # INTERNO
    # ==================================================

    def _persist(self, player_id: str, inventory: Inventory) -> None:
        self._repository.set(self._key(player_id), inventory.to_dict())

    @staticmethod
    def _key(player_id: str) -> str:
        return f"{_KEY_PREFIX}{player_id}"
