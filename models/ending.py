"""
models/ending.py
----------------
Modelo de un final del juego.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class Ending:
    # Identificación
    ending_id: str
    title: str

    # Narrativa
    description: str = ""

    # Clasificación
    ending_type: str = "neutral"   # good, bad, neutral, secret, true
    rarity: str = "common"         # common, rare, legendary

    # Estado
    unlocked: bool = False

    # Estadísticas finales
    score: int = 0
    survival: bool = True

    # Requisitos (informativos)
    required_flags: Dict[str, bool] = field(default_factory=dict)
    required_choices: List[str] = field(default_factory=list)

    # Recompensas
    rewards: List[str] = field(default_factory=list)

    # Información adicional
    metadata: Dict[str, str] = field(default_factory=dict)

    # Tiempo de desbloqueo
    unlocked_at: Optional[str] = None

    # --------------------------
    # Métodos
    # --------------------------

    def unlock(self):
        """Desbloquea este final."""
        self.unlocked = True

    def add_reward(self, reward: str):
        """Añade una recompensa."""
        if reward not in self.rewards:
            self.rewards.append(reward)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)