# ai/prompt_builder.py

from typing import Any, Dict, List, Optional


class PromptBuilder:
    """
    Construye prompts para cualquier proveedor de IA.

    Se encarga de reunir el contexto del juego y convertirlo
    en un único prompt listo para enviarse al modelo.
    """

    def __init__(self):
        self.system_prompt = (
            "Eres el narrador de un videojuego de decisiones. "
            "Mantén coherencia con la historia, personajes, "
            "objetos y consecuencias de las decisiones."
        )

    def build(
        self,
        player_name: str,
        story_title: str,
        current_scene: str,
        inventory: Optional[List[str]] = None,
        variables: Optional[Dict[str, Any]] = None,
        history: Optional[List[str]] = None,
        objective: Optional[str] = None,
        user_input: Optional[str] = None,
    ) -> str:
        """
        Genera un prompt completo para la IA.
        """

        inventory = inventory or []
        variables = variables or {}
        history = history or []

        prompt = [
            f"Sistema:\n{self.system_prompt}",
            "",
            f"Jugador: {player_name}",
            f"Historia: {story_title}",
            f"Escena actual: {current_scene}",
        ]

        if objective:
            prompt.append(f"Objetivo: {objective}")

        if inventory:
            prompt.append(
                "\nInventario:\n- " +
                "\n- ".join(inventory)
            )

        if variables:
            prompt.append("\nVariables del juego:")
            for key, value in variables.items():
                prompt.append(f"- {key}: {value}")

        if history:
            prompt.append("\nEventos recientes:")
            for event in history[-10:]:
                prompt.append(f"- {event}")

        if user_input:
            prompt.append(f"\nAcción del jugador:\n{user_input}")

        prompt.append(
            "\nResponde únicamente con la narración y las "
            "consecuencias de la acción."
        )

        return "\n".join(prompt)

    def build_system_prompt(self) -> str:
        """
        Devuelve únicamente el prompt del sistema.
        """
        return self.system_prompt

    def set_system_prompt(self, prompt: str) -> None:
        """
        Permite cambiar el prompt base.
        """
        self.system_prompt = prompt

    def add_rule(self, rule: str) -> None:
        """
        Agrega una regla permanente al prompt.
        """
        self.system_prompt += f"\n- {rule}"