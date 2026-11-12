"""
models/inventory.py
-------------------
Modelo del inventario del jugador.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from models.item import Item


@dataclass
class Inventory:
    # Objetos del inventario
    items: List[Item] = field(default_factory=list)

    # Capacidad máxima (None = ilimitado)
    capacity: Optional[int] = None

    # --------------------------
    # Métodos
    # --------------------------

    def add_item(self, item: Item) -> bool:
        """Añade un objeto al inventario."""
        if self.capacity is not None and len(self.items) >= self.capacity:
            return False

        self.items.append(item)
        return True

    def remove_item(self, item_id: str) -> bool:
        """Elimina un objeto por su ID."""
        for item in self.items:
            if item.item_id == item_id:
                self.items.remove(item)
                return True
        return False

    def has_item(self, item_id: str) -> bool:
        """Comprueba si el objeto existe."""
        return any(item.item_id == item_id for item in self.items)

    def get_item(self, item_id: str) -> Optional[Item]:
        """Obtiene un objeto por su ID."""
        for item in self.items:
            if item.item_id == item_id:
                return item
        return None

    def clear(self):
        """Vacía el inventario."""
        self.items.clear()

    def count(self) -> int:
        """Número de objetos."""
        return len(self.items)

    def to_dict(self):
        data = asdict(self)
        return data

    @classmethod
    def from_dict(cls, data: dict):
        inventory = cls(capacity=data.get("capacity"))

        for item_data in data.get("items", []):
            inventory.items.append(Item.from_dict(item_data))

        return inventory