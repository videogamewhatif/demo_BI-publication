"""
managers/inventory_manager.py
================================

Qué hace:
    Séptimo (y último que faltaba) manager de dominio. Envuelve
    `services.inventory_service.InventoryService` (que ya gestiona
    el inventario real por jugador) y le añade lo que le faltaba
    para poder "usar" un objeto con efecto: un catálogo de
    DEFINICIONES de objeto (`data/items/<item_id>.json`) con sus
    efectos — `engine/inventory_engine.py` ya esperaba esto antes de
    esta sesión (`use_item()` aplicando `effects.stats`).

    - Catálogo: lee definiciones de `data/items/<item_id>.json`.
    - Inventario real: delega en `InventoryService` — no duplica esa
      lógica.
    - Usar un objeto: consume el objeto del inventario del jugador Y
      aplica los efectos de su definición vía `ConsequenceService`.

Qué NO hace (alcance dejado fuera a propósito):
    No inventa ningún objeto — `data/items/` existe pero está vacía;
    diseñarlos es contenido, no código.

Formato esperado de una definición de objeto en el catálogo:

    {
      "name": "...",
      "description": "...",
      "effects": {"stats": {"happiness": 10}}
    }

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from config.paths import ITEMS_DIR
from models.inventory import Inventory
from models.item import Item
from models.player import Player
from services.consequence_service import ConsequenceService
from services.inventory_service import InventoryService, ItemNotFoundError
from services.repositories import ContentRepository, JSONContentRepository

logger = logging.getLogger(__name__)


class InventoryManager:
    """Catálogo de definiciones de objeto + delegación en InventoryService para el inventario real."""

    def __init__(
        self,
        inventory_service: InventoryService,
        catalog_repository: Optional[ContentRepository] = None,
        consequence_service: Optional[ConsequenceService] = None,
    ) -> None:
        self._inventory_service = inventory_service
        self._catalog: ContentRepository = catalog_repository or JSONContentRepository(ITEMS_DIR)
        self._consequence_service = consequence_service

    # ==================================================
    # CATÁLOGO
    # ==================================================

    def get_item_definition(self, item_id: str) -> Optional[Dict[str, Any]]:
        """La definición cruda (con efectos) del catálogo, o None si no existe."""
        return self._catalog.load(item_id)

    # ==================================================
    # INVENTARIO REAL (delega en InventoryService, no lo duplica)
    # ==================================================

    def add_item(self, player_id: str, item_id: str, quantity: int = 1) -> Inventory:
        """
        Añade `quantity` unidades de `item_id` al inventario de
        `player_id`, usando el nombre del catálogo si existe.
        """
        definition = self.get_item_definition(item_id) or {}
        name = definition.get("name", item_id)
        inventory = self._inventory_service.get_inventory(player_id)
        for _ in range(max(1, quantity)):
            inventory = self._inventory_service.add_item(
                player_id, Item(item_id=item_id, name=name)
            )
        return inventory

    def remove_item(self, player_id: str, item_id: str) -> Inventory:
        return self._inventory_service.remove_item(player_id, item_id)

    def has_item(self, player_id: str, item_id: str) -> bool:
        return self._inventory_service.has_item(player_id, item_id)

    def get_inventory(self, player_id: str) -> Inventory:
        return self._inventory_service.get_inventory(player_id)

    def clear_inventory(self, player_id: str) -> Inventory:
        return self._inventory_service.clear_inventory(player_id)

    # ==================================================
    # USO DE OBJETOS (catálogo + ConsequenceService)
    # ==================================================

    def use_item(self, player: Player, item_id: str) -> bool:
        """
        Usa un objeto: comprueba que el jugador lo tenga, aplica los
        efectos de su definición en el catálogo (si hay
        `ConsequenceService` configurado), y lo quita del inventario.

        Devuelve False (sin lanzar excepción) si el jugador no tiene
        el objeto o si no existe una definición para él en el
        catálogo — usar un objeto inexistente/no poseído no es un
        error de programación, es un caso normal de juego.
        """
        definition = self.get_item_definition(item_id)
        if definition is None:
            return False
        if not self.has_item(player.player_id, item_id):
            return False

        effects = definition.get("effects", {}).get("stats", {})
        if self._consequence_service is not None and effects:
            self._consequence_service.apply_effects(
                player, effects, reason=f"objeto usado: {definition.get('name', item_id)}"
            )

        try:
            self.remove_item(player.player_id, item_id)
        except ItemNotFoundError:
            return False

        logger.info("InventoryManager: %s usó '%s'", player.player_id, item_id)
        return True
