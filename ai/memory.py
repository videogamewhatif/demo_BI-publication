# ai/memory.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MemoryEvent:
    """
    Evento ocurrido durante la partida.
    """
    id: str
    description: str
    importance: int = 1      # 1-10
    chapter: Optional[str] = None
    tags: List[str] = field(default_factory=list)


class Memory:
    """
    Gestiona toda la memoria utilizada por la IA.

    Guarda:
    - Eventos importantes.
    - Variables narrativas.
    - Relaciones.
    - Hechos permanentes.
    - Historial reciente.
    """

    def __init__(self):

        self.events: List[MemoryEvent] = []

        self.variables: Dict[str, Any] = {}

        self.relationships: Dict[str, int] = {}

        self.facts: Dict[str, Any] = {}

    # ==================================================
    # EVENTOS
    # ==================================================

    def add_event(self, event: MemoryEvent):

        self.events.append(event)

    def get_recent_events(self, limit: int = 10):

        return self.events[-limit:]

    def get_important_events(self, minimum_importance: int = 7):

        return [
            event
            for event in self.events
            if event.importance >= minimum_importance
        ]

    # ==================================================
    # VARIABLES
    # ==================================================

    def set_variable(self, key: str, value: Any):

        self.variables[key] = value

    def get_variable(self, key: str, default=None):

        return self.variables.get(key, default)

    # ==================================================
    # RELACIONES
    # ==================================================

    def set_relationship(self, npc_id: str, value: int):

        self.relationships[npc_id] = value

    def modify_relationship(self, npc_id: str, amount: int):

        current = self.relationships.get(npc_id, 0)
        self.relationships[npc_id] = current + amount

    def get_relationship(self, npc_id: str):

        return self.relationships.get(npc_id, 0)

    # ==================================================
    # HECHOS
    # ==================================================

    def remember(self, key: str, value: Any):

        self.facts[key] = value

    def recall(self, key: str):

        return self.facts.get(key)

    # ==================================================
    # EXPORTAR
    # ==================================================

    def to_dict(self):

        return {
            "events": [
                {
                    "id": e.id,
                    "description": e.description,
                    "importance": e.importance,
                    "chapter": e.chapter,
                    "tags": e.tags,
                }
                for e in self.events
            ],
            "variables": self.variables,
            "relationships": self.relationships,
            "facts": self.facts,
        }

    # ==================================================
    # IMPORTAR
    # ==================================================

    @classmethod
    def from_dict(cls, data: Dict):

        memory = cls()

        memory.variables = data.get("variables", {})
        memory.relationships = data.get("relationships", {})
        memory.facts = data.get("facts", {})

        for event in data.get("events", []):

            memory.events.append(
                MemoryEvent(
                    id=event["id"],
                    description=event["description"],
                    importance=event.get("importance", 1),
                    chapter=event.get("chapter"),
                    tags=event.get("tags", []),
                )
            )

        return memory