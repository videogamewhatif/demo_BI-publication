"""
models/achievement.py
---------------------
Modelo de un logro del juego.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class Achievement:
    # Identificación
    achievement_id: str
    title: str

    # Información
    description: str = ""
    category: str = "general"

    # Clasificación
    rarity: str = "common"      # common, rare, epic, legendary
    points: int = 0

    # Estado
    unlocked: bool = False
    unlocked_at: Optional[str] = None

    # Requisitos (informativos)
    required_flags: Dict[str, bool] = field(default_factory=dict)
    required_choices: List[str] = field(default_factory=list)

    # Recompensas
    rewards: List[str] = field(default_factory=list)

    # Información adicional
    metadata: Dict[str, str] = field(default_factory=dict)

    # --------------------------
    # Métodos
    # --------------------------

    def unlock(self):
        """Desbloquea el logro."""
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