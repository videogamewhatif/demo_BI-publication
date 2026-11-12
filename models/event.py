"""
models/event.py
---------------
Modelo de un evento dentro de la historia.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class Event:
    # Identificación
    event_id: str
    title: str

    # Información
    description: str = ""
    event_type: str = "story"   # story, combat, dialogue, puzzle, discovery...

    # Estado
    completed: bool = False

    # Participantes
    npcs: List[str] = field(default_factory=list)

    # Objetos involucrados
    items: List[str] = field(default_factory=list)

    # Variables modificadas
    flags: Dict[str, bool] = field(default_factory=dict)

    # Consecuencias
    rewards: Dict[str, int] = field(default_factory=dict)
    penalties: Dict[str, int] = field(default_factory=dict)

    # Datos opcionales
    metadata: Dict[str, str] = field(default_factory=dict)

    # Tiempo
    timestamp: Optional[str] = None

    # --------------------------
    # Métodos
    # --------------------------

    def add_flag(self, flag: str, value: bool = True):
        self.flags[flag] = value

    def add_reward(self, key: str, value: int):
        self.rewards[key] = value

    def add_penalty(self, key: str, value: int):
        self.penalties[key] = value

    def finish(self):
        self.completed = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)