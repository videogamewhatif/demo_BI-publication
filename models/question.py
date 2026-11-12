"""
models/question.py
------------------
Modelo de una decisión presentada al jugador.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional


@dataclass
class Question:
    # Identificación
    question_id: str

    # Texto mostrado al jugador
    title: str
    description: str = ""

    # Opciones disponibles
    options: List[str] = field(default_factory=list)

    # Información adicional
    question_type: str = "choice"
    time_limit: Optional[int] = None

    # Estado
    answered: bool = False
    selected_option: Optional[int] = None

    # Contexto para la IA
    metadata: Dict[str, str] = field(default_factory=dict)

    # Efectos conocidos (si existen)
    flags: Dict[str, bool] = field(default_factory=dict)

    # -------------------------
    # Métodos
    # -------------------------

    def answer(self, option_index: int):
        """Registra la respuesta del jugador."""
        if option_index < 0 or option_index >= len(self.options):
            raise ValueError("Opción inválida.")

        self.selected_option = option_index
        self.answered = True

    def reset(self):
        """Reinicia la pregunta."""
        self.answered = False
        self.selected_option = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)