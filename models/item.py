"""
models/item.py
---------------
Modelo de un objeto del inventario del jugador.

No existía en el proyecto — `models/inventory.py` ya hacía
`from models.item import Item` desde antes, así que ese archivo no
se podía importar hasta ahora. Se sigue el mismo estilo que
`models/achievement.py`/`models/event.py` (dataclass simple,
`to_dict`/`from_dict` vía `asdict`/`cls(**data)`) para que combine
con el resto de `models/`.

Solo define el esquema — ningún objeto real del juego se inventa
aquí; el contenido real de items es trabajo de diseño, no de este
archivo.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict


@dataclass
class Item:
    # Identificación
    item_id: str
    name: str

    # Información
    description: str = ""
    item_type: str = "general"   # general, consumable, key_item, cosmetic...

    # Clasificación — mismas categorías de rareza que
    # config/colors.py ya define (COMMON, UNCOMMON, RARE, EPIC, LEGENDARY)
    rarity: str = "common"

    # Cantidad
    quantity: int = 1
    stackable: bool = True

    # Uso
    consumable: bool = False

    # Información adicional
    metadata: Dict[str, str] = field(default_factory=dict)

    # --------------------------
    # Métodos
    # --------------------------

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
