# ai/ai_manager.py

from typing import Any, Dict, Optional


class AIManager:
    """
    Administrador principal de la IA.

    Su función es centralizar cualquier sistema de inteligencia
    artificial utilizado por el juego, ya sea IA local o APIs externas.
    """

    def __init__(self):
        self.enabled = True
        self.provider = "local"

    def set_provider(self, provider: str) -> None:
        """
        Cambia el proveedor de IA.
        Ejemplos:
            - local
            - openai
            - claude
        """
        self.provider = provider

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def is_enabled(self) -> bool:
        return self.enabled

    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera una respuesta utilizando el proveedor seleccionado.
        """

        if not self.enabled:
            return ""

        context = context or {}

        if self.provider == "local":
            return self._local_response(prompt, context)

        if self.provider == "openai":
            return self._openai_response(prompt, context)

        if self.provider == "claude":
            return self._claude_response(prompt, context)

        return "Proveedor de IA no reconocido."

    def _local_response(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        IA local simple.
        Puede reemplazarse por reglas, árboles de decisión
        o modelos propios.
        """
        return f"[LOCAL AI] {prompt}"

    def _openai_response(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Aquí se integrará la API de OpenAI.
        """
        raise NotImplementedError("OpenAI aún no implementado.")

    def _claude_response(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Aquí se integrará la API de Claude.
        """
        raise NotImplementedError("Claude aún no implementado.")