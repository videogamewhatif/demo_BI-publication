"""
engine/inventory_engine.py
=============================

Motor encargado de gestionar el inventario — reescrito en la sesión
de "desbloquear engine/" contra la API real de
`managers.inventory_manager.InventoryManager` (antes esperaba
`InventoryManager()`/`PlayerManager()` sin argumentos con un
`modify_stat()` en `PlayerManager` que nunca existió).

Envoltorio delgado a propósito: `InventoryManager` ya hace todo el
trabajo real (catálogo + inventario real + uso de objetos vía
ConsequenceService); este archivo solo expone esa misma API con los
nombres que tenía la versión original.

Autor: Korlo
"""

from __future__ import annotations

from managers.inventory_manager import InventoryManager
from models.inventory import Inventory
from models.player import Player


class InventoryEngine:
    """Envoltorio delgado sobre InventoryManager."""

    def __init__(self, inventory_manager: InventoryManager) -> None:
        self.inventory_manager = inventory_manager

    def add_item(self, player_id: str, item_id: str, quantity: int = 1) -> Inventory:
        """Agrega `quantity` unidades de `item_id` al inventario de `player_id`."""
        return self.inventory_manager.add_item(player_id, item_id, quantity)

    def remove_item(self, player_id: str, item_id: str) -> Inventory:
        """Elimina `item_id` del inventario de `player_id`."""
        return self.inventory_manager.remove_item(player_id, item_id)

    def has_item(self, player_id: str, item_id: str) -> bool:
        """Comprueba si `player_id` posee `item_id`."""
        return self.inventory_manager.has_item(player_id, item_id)

    def use_item(self, player: Player, item_id: str) -> bool:
        """Usa un objeto del inventario de `player` y aplica sus efectos."""
        return self.inventory_manager.use_item(player, item_id)

    def get_inventory(self, player_id: str) -> Inventory:
        """Devuelve el inventario completo de `player_id`."""
        return self.inventory_manager.get_inventory(player_id)

    def clear_inventory(self, player_id: str) -> Inventory:
        """Vacía el inventario de `player_id`."""
        return self.inventory_manager.clear_inventory(player_id)
