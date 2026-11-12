# ai/story_generator.py

from typing import Dict, List, Optional

from ai.ai_manager import AIManager
from ai.prompt_builder import PromptBuilder
from ai.memory import Memory


class StoryGenerator:
    """
    Genera contenido narrativo utilizando la IA.

    No controla la lógica del juego; únicamente produce
    texto coherente con el contexto recibido.
    """

    def __init__(
        self,
        ai_manager: AIManager,
        prompt_builder: PromptBuilder,
        memory: Memory,
    ):
        self.ai_manager = ai_manager
        self.prompt_builder = prompt_builder
        self.memory = memory

    def generate_scene(
        self,
        player_name: str,
        story_title: str,
        current_scene: str,
        objective: str,
        inventory: Optional[List[str]] = None,
        variables: Optional[Dict] = None,
    ) -> str:
        """
        Genera la narración de una escena.
        """

        prompt = self.prompt_builder.build(
            player_name=player_name,
            story_title=story_title,
            current_scene=current_scene,
            objective=objective,
            inventory=inventory or [],
            variables=variables or {},
            history=[
                event.description
                for event in self.memory.get_recent_events()
            ],
        )

        return self.ai_manager.generate_response(prompt)

    def generate_dialogue(
        self,
        npc_name: str,
        player_input: str,
        context: str,
    ) -> str:
        """
        Genera el diálogo de un NPC.
        """

        prompt = (
            f"Eres {npc_name}.\n\n"
            f"Contexto:\n{context}\n\n"
            f"Jugador:\n{player_input}\n\n"
            "Responde únicamente como el personaje."
        )

        return self.ai_manager.generate_response(prompt)

    def generate_event(
        self,
        description: str,
    ) -> str:
        """
        Genera un evento inesperado.
        """

        prompt = (
            "Genera un evento interesante para una historia.\n\n"
            f"Contexto:\n{description}"
        )

        return self.ai_manager.generate_response(prompt)

    def generate_item_description(
        self,
        item_name: str,
    ) -> str:
        """
        Genera la descripción narrativa de un objeto.
        """

        prompt = (
            f"Describe el objeto '{item_name}' "
            "como si perteneciera al mundo del juego."
        )

        return self.ai_manager.generate_response(prompt)