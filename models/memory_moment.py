"""
models/memory_moment.py
------------------------
Modelo de un Momento Clave del Álbum de Vida
(What_If_Vision_Document.md §5.3, §5.5).

`Player.memory_moments` (models/player.py) solo guarda IDs — la
ficha completa (texto, categoría, edad narrativa, decisión que lo
originó, ilustración) vive acá, tal como anticipaba el docstring de
`Player.unlock_memory_moment()`.
"""

from dataclasses import asdict, dataclass
from typing import Optional

# Subconjunto curado de eventos que Momento Clave (Vision Document
# §5.3) — no todos los eventos generan una ilustración. Un scene de
# data/scenarios/ que se marque con "memory_moment" debe declarar
# una de estas categorías (el validador de escenarios avisa si no).
VALID_MEMORY_CATEGORIES = frozenset({
    "nacimiento",
    "hito_educativo",
    "hito_profesional",
    "hito_relacional",
    "hito_salud",
    "consecuencia_extrema",
    "desenlace_final",
})


@dataclass
class MemoryMoment:
    # Identificación
    moment_id: str
    player_id: str

    # Clasificación (una de VALID_MEMORY_CATEGORIES)
    category: str

    # Contenido — reutiliza texto ya autorado (title/text de la
    # escena que lo originó), nunca inventa contenido nuevo acá.
    title: str
    text: str

    # "Fecha narrativa" (Vision Document §5.3): el juego mide tiempo
    # en edad del personaje, no en calendario.
    age_at_moment: int

    # La decisión que lo originó (label de la opción elegida), si
    # aplica — None para momentos que no vienen de una decisión
    # puntual (ej. "nacimiento").
    origin_decision: Optional[str] = None

    # Ruta a la ilustración generada por ImageService, o None si
    # todavía no se generó (o falló la generación — un momento se
    # desbloquea igual aunque la imagen falle).
    image_path: Optional[str] = None

    # Timestamp ISO real (no narrativo) de cuándo se desbloqueó.
    unlocked_at: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
