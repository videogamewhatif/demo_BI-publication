"""
models/npc.py
==============

Qué hace:
    Define `NPC`: la ficha simplificada de un personaje no jugable
    (familia, pareja, amistades, relaciones profesionales) con la
    que el `Player` interactúa a lo largo de la partida
    (VITA_Game_Design_Document.md §11 "Relaciones").

    Un NPC tiene "su propia vida en segundo plano que evoluciona
    con el tiempo" (§11) — por eso incluye `current_situation` y
    `age`, no solo datos estáticos de creación.

Cómo funciona:
    Dataclass con validación en `__post_init__` (afinidad y salud
    acotadas 0-100 vía `models.scales.clamp`, igual que `Player`) y
    mutadores explícitos para afinidad, salud e historial de
    interacción.

    Deliberadamente NO incluye inventario propio: `models/inventory.py`
    ya modela el inventario del jugador, y darle a NPC su propia
    lista de objetos reproduciría en este modelo la misma violación
    de responsabilidad única que tenía el `Player` anterior (ver
    análisis previo). Si un NPC necesita "portar" un objeto
    relevante para una historia, esa relación se modela en el
    contenido narrativo (JSON), no como un campo estructural aquí.

    Tampoco incluye campos específicos de matrimonio
    (Satisfacción_marital, Historial_matrimonial de
    VITA_Game_Design_Document.md §12) ni de crianza (§13): son
    mecánicas de sistemas completos que no se han diseñado todavía
    y añadirlas ahora sería anticipar (YAGNI) una forma de dato que
    bien podría cambiar. Cuando se aborde el Sistema de Matrimonio,
    lo natural es una tabla/objeto de valor asociado por
    `relationship_type == SPOUSE`, no campos sueltos en todo NPC.

Dependencias:
    - config.constant: PersonalityTrait, RelationshipType, MIN_STAT,
      MAX_STAT.
    - models.scales: función `clamp` compartida con Player.

Cómo interactúa con otros módulos:
    Ningún otro archivo importa `models.npc` todavía. `ai/npc_ai.py`
    define por su cuenta una `NPCPersonality`/`NPCState` distintas
    de este modelo — es una duplicación de responsabilidad ya
    existente en el proyecto (el comportamiento de IA debería leer
    sus rasgos desde este `NPC`, no mantener su propio catálogo).
    No se corrige en este archivo porque `ai/npc_ai.py` ya funciona
    de forma aislada y tocarlo no fue parte de lo pedido para esta
    entrega; queda documentado como pendiente para cuando se revise
    la carpeta `ai/`.

Autor: Korlo
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from config.constant import MAX_STAT, MIN_STAT, PersonalityTrait, RelationshipType
from models.scales import clamp, is_in_range

logger = logging.getLogger(__name__)


@dataclass
class NPC:
    """
    Ficha simplificada de un personaje no jugable.

    Atributos:
        npc_id, name: identidad.
        relationship_type: tipo de vínculo con el jugador.
        affinity: afinidad de la relación (0-100, VITA GDD §11).
        health, is_alive, age: estado vital simplificado.
        personality_traits: mismo catálogo cerrado que usa Player.
        description: bio estática definida en la creación del NPC.
        current_situation: estado narrativo dinámico, actualizado a
            medida que "su vida en segundo plano" evoluciona.
        interaction_history: IDs o resúmenes breves de interacciones
            pasadas relevantes con el jugador.
        memory: hechos sueltos que el NPC recuerda sobre el jugador
            (clave -> valor), consumido por `ai/npc_ai.py` y
            `ai/story_generator.py` como contexto de generación.
    """

    npc_id: str
    name: str
    relationship_type: RelationshipType

    affinity: int = 50
    health: int = 100
    is_alive: bool = True
    age: int | None = None

    personality_traits: List[PersonalityTrait] = field(default_factory=list)

    description: str = ""
    current_situation: str = ""
    interaction_history: List[str] = field(default_factory=list)
    memory: Dict[str, str] = field(default_factory=dict)

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    def __post_init__(self) -> None:
        """Valida identidad y acota afinidad/salud a su rango permitido."""
        if not self.npc_id:
            raise ValueError("npc_id no puede estar vacío.")
        if not self.name:
            raise ValueError("name no puede estar vacío.")
        if self.age is not None and self.age < 0:
            raise ValueError("age no puede ser negativo.")

        self.affinity = self._clamp_stat("affinity", self.affinity)
        self.health = self._clamp_stat("health", self.health)

    @staticmethod
    def _clamp_stat(name: str, value: int) -> int:
        """Acota un atributo 0-100, avisando si estaba fuera de rango."""
        if not is_in_range(value, MIN_STAT, MAX_STAT):
            logger.warning(
                "NPC: '%s'=%s fuera de rango [%s, %s]; se acota.",
                name, value, MIN_STAT, MAX_STAT,
            )
        return clamp(value, MIN_STAT, MAX_STAT)

    # ==================================================
    # AFINIDAD Y ESTADO VITAL
    # ==================================================

    def modify_affinity(self, amount: int, reason: str) -> None:
        """Modifica la afinidad con el jugador en `amount`."""
        previous = self.affinity
        self.affinity = self._clamp_stat("affinity", self.affinity + amount)
        logger.info(
            "NPC %s: affinity %s -> %s (%s)",
            self.npc_id, previous, self.affinity, reason,
        )

    def decay_affinity(self, amount: int) -> None:
        """
        Reduce la afinidad por falta de interacción a lo largo del
        tiempo (VITA_Game_Design_Document.md §11: "decaimiento
        natural de afinidad si no hay interacción").
        """
        if amount < 0:
            raise ValueError("amount debe ser positivo.")
        self.modify_affinity(-amount, reason="decaimiento natural por inactividad")

    def damage(self, amount: int) -> None:
        """Aplica daño de salud al NPC; lo marca como fallecido en 0."""
        if amount < 0:
            raise ValueError("amount debe ser positivo.")
        self.health = self._clamp_stat("health", self.health - amount)
        if self.health <= 0:
            self.kill()

    def heal(self, amount: int) -> None:
        """Recupera salud del NPC, solo si sigue con vida."""
        if amount < 0:
            raise ValueError("amount debe ser positivo.")
        if self.is_alive:
            self.health = self._clamp_stat("health", self.health + amount)

    def kill(self) -> None:
        """Marca al NPC como fallecido."""
        self.health = 0
        self.is_alive = False
        logger.info("NPC %s: falleció", self.npc_id)

    # ==================================================
    # RASGOS Y MEMORIA
    # ==================================================

    def add_personality_trait(self, trait: PersonalityTrait) -> None:
        """Añade un rasgo de personalidad si el NPC aún no lo tiene."""
        if trait not in self.personality_traits:
            self.personality_traits.append(trait)

    def remember(self, key: str, value: str) -> None:
        """Guarda un hecho que el NPC recuerda sobre el jugador."""
        self.memory[key] = value

    def forget(self, key: str) -> None:
        """Elimina un hecho recordado."""
        self.memory.pop(key, None)

    def record_interaction(self, summary: str) -> None:
        """Añade un resumen breve al historial de interacciones."""
        self.interaction_history.append(summary)

    def update_situation(self, situation: str) -> None:
        """Actualiza la situación narrativa actual del NPC."""
        self.current_situation = situation

    # ==================================================
    # SERIALIZACIÓN
    # ==================================================

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el NPC a un diccionario serializable a JSON.

        Se implementa explícitamente (no `asdict()` a secas) porque
        `relationship_type` y `personality_traits` son enums y deben
        serializarse a su `.value`.
        """
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "relationship_type": self.relationship_type.value,
            "affinity": self.affinity,
            "health": self.health,
            "is_alive": self.is_alive,
            "age": self.age,
            "personality_traits": [t.value for t in self.personality_traits],
            "description": self.description,
            "current_situation": self.current_situation,
            "interaction_history": list(self.interaction_history),
            "memory": dict(self.memory),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NPC":
        """Reconstruye un NPC desde un diccionario (inverso de to_dict)."""
        return cls(
            npc_id=data["npc_id"],
            name=data["name"],
            relationship_type=RelationshipType(data["relationship_type"]),
            affinity=data.get("affinity", 50),
            health=data.get("health", 100),
            is_alive=data.get("is_alive", True),
            age=data.get("age"),
            personality_traits=[
                PersonalityTrait(t) for t in data.get("personality_traits", [])
            ],
            description=data.get("description", ""),
            current_situation=data.get("current_situation", ""),
            interaction_history=list(data.get("interaction_history", [])),
            memory=dict(data.get("memory", {})),
        )