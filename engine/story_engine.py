"""
engine/story_engine.py
=========================

Motor encargado de controlar el flujo narrativo — reescrito en la
sesión de "desbloquear engine/" para llamar a la API real de
`managers.story_manager.StoryManager` (antes de esta sesión, este
archivo instanciaba `StoryManager()` sin argumentos y esperaba que
`get_story(id)` devolviera un dict crudo con `["scenes"]` — ninguna
de las dos cosas es cierta del `StoryManager` real, que requiere
`story_service` en el constructor y opera sobre objetos `Story`).

Mantiene el mismo estilo "con estado" que tenía originalmente
(`start()`, `get_current_scene()`, `choose_option()`,
`is_finished()` sin tener que pasar el objeto `Story` en cada
llamada) — útil para consumidores que prefieren esa forma en vez de
la explícita de `StoryManager`. `ui/` sigue usando `StoryManager`
directamente; esto es una capa de conveniencia alternativa, no un
reemplazo — ver `docs/architecture.md` §2 sobre por qué existe esta
duplicación a propósito.

Autor: Korlo
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from managers.story_manager import InvalidOptionError, SceneNotFoundError, StoryManager
from models.story import Story


class StoryEngine:
    """Gestiona el avance de UNA historia a la vez, con estado interno (Story real, no un dict)."""

    def __init__(self, story_manager: StoryManager) -> None:
        self.story_manager = story_manager
        self.current_story: Optional[Story] = None

    def start(self, player_id: str, story_content_id: str, started_at_age: int) -> Story:
        """Inicia una historia nueva y la deja como la actual."""
        self.current_story = self.story_manager.start_story(player_id, story_content_id, started_at_age)
        return self.current_story

    def get_current_scene(self) -> Optional[Dict[str, Any]]:
        """La escena actual de `current_story`, o None si no hay historia activa."""
        if self.current_story is None:
            return None
        return self.story_manager.get_current_scene(self.current_story)

    def choose_option(self, option_index: int) -> bool:
        """
        Procesa la decisión del jugador y avanza `current_story` a
        la siguiente escena. Devuelve False (sin lanzar excepción)
        si no hay historia activa o el índice no es válido — mismo
        comportamiento tolerante que tenía la versión original.
        """
        if self.current_story is None:
            return False
        try:
            self.current_story = self.story_manager.choose_option(self.current_story, option_index)
            return True
        except (InvalidOptionError, SceneNotFoundError):
            return False

    def is_finished(self) -> bool:
        """Indica si `current_story` llegó a una escena de cierre."""
        if self.current_story is None:
            return True
        return self.story_manager.is_current_scene_ending(self.current_story)

    def get_current_story_id(self) -> Optional[str]:
        """El `story_id` de la historia actual, o None si no hay ninguna."""
        return None if self.current_story is None else self.current_story.story_id

    def reset(self) -> None:
        """Olvida la historia actual (no la borra de disco, solo del estado de este motor)."""
        self.current_story = None
