# ai/npc_ai.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class NPCPersonality:
    """
    Define la personalidad base de un NPC.
    """
    bravery: int = 50
    kindness: int = 50
    intelligence: int = 50
    honesty: int = 50
    aggression: int = 50
    curiosity: int = 50
    loyalty: int = 50


@dataclass
class NPCState:
    """
    Estado actual del NPC.
    """
    mood: str = "neutral"
    relationship: int = 0
    location: str = ""
    goals: List[str] = field(default_factory=list)


class NPCAI:
    """
    Controla el comportamiento lógico de un NPC.
    """

    def __init__(
        self,
        npc_id: str,
        name: str,
        personality: NPCPersonality,
    ):
        self.npc_id = npc_id
        self.name = name
        self.personality = personality
        self.state = NPCState()

    # ==================================================
    # RELACIÓN
    # ==================================================

    def change_relationship(self, amount: int):
        self.state.relationship += amount

    def get_relationship(self) -> int:
        return self.state.relationship

    # ==================================================
    # ESTADO
    # ==================================================

    def set_mood(self, mood: str):
        self.state.mood = mood

    def set_location(self, location: str):
        self.state.location = location

    def add_goal(self, goal: str):
        if goal not in self.state.goals:
            self.state.goals.append(goal)

    def remove_goal(self, goal: str):
        if goal in self.state.goals:
            self.state.goals.remove(goal)

    # ==================================================
    # DECISIONES
    # ==================================================

    def decide_action(self, player_action: str) -> str:
        """
        Decide una acción simple según la personalidad.
        """

        if self.personality.aggression > 80:
            return "attack"

        if self.personality.kindness > 80:
            return "help"

        if self.personality.curiosity > 70:
            return "investigate"

        if self.state.relationship > 50:
            return "support"

        if self.state.relationship < -50:
            return "ignore"

        return "observe"

    # ==================================================
    # CONTEXTO PARA IA
    # ==================================================

    def build_context(self) -> Dict:

        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "mood": self.state.mood,
            "relationship": self.state.relationship,
            "location": self.state.location,
            "goals": self.state.goals,
            "personality": vars(self.personality),
        }