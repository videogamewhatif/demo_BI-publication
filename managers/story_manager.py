"""
managers/story_manager.py
============================

Qué hace:
    Fachada delgada sobre `services.story_service.StoryService` —
    mismo patrón que `SaveManager`/`AudioManager`/`LanguageManager`
    sobre sus respectivos services. `story_service.py` ya lo decía
    en su propio docstring: "Cuando se construya managers/, el
    futuro StoryManager debería delegar aquí en vez de reimplementar
    esta lógica." Este archivo es exactamente eso — ningún método de
    aquí reimplementa nada, todos delegan 1:1.

    Es el primero de los managers de dominio que anticipaba el SDD
    original (`StoryManager`, `PlayerManager`, `EventManager`,
    `EndingManager`, `AchievementManager`, `InventoryManager`,
    `TimeManager` — ver `docs/roadmap.md`). Los otros seis no existen
    todavía porque no tienen un service real al que delegar; este sí.

    A diferencia de `SaveManager` (que sí añade política propia:
    cuándo autoguardar), este manager no añade ninguna decisión de
    "cuándo" — avanzar una historia no tiene una política de tiempo
    como el autoguardado. Existe para que `ui/` (y cualquier futuro
    consumidor) hable con `managers/`, no con `services/`
    directamente, igual que ya pasa con guardado/audio/idioma.

Dependencias:
    - services.story_service: StoryService y sus excepciones.

Cómo interactúa con otros módulos:
    `ui/screens/story_panel.py`, `ui/screens/main_menu_screen.py` y
    `ui/dev_preview.py` lo usan en vez de `StoryService` directamente
    desde esta sesión — ver `docs/changelog.md`.

Autor: Korlo
"""

from __future__ import annotations

from typing import Any, Dict, List

from models.story import Story
from services.story_service import (
    InvalidOptionError,
    InvalidStoryContentError,
    SceneNotFoundError,
    StoryContentNotFoundError,
    StoryNotFoundError,
    StoryService,
)

__all__ = [
    "StoryManager",
    "StoryContentNotFoundError",
    "InvalidStoryContentError",
    "SceneNotFoundError",
    "InvalidOptionError",
    "StoryNotFoundError",
]


class StoryManager:
    """Fachada sobre `StoryService` — delega el progreso narrativo sin añadir lógica propia."""

    def __init__(self, story_service: StoryService) -> None:
        self._story_service = story_service

    def start_story(self, player_id: str, story_content_id: str, started_at_age: int) -> Story:
        return self._story_service.start_story(player_id, story_content_id, started_at_age)

    def get_current_scene(self, story: Story) -> Dict[str, Any]:
        return self._story_service.get_current_scene(story)

    def is_current_scene_ending(self, story: Story) -> bool:
        return self._story_service.is_current_scene_ending(story)

    def choose_option(self, story: Story, option_index: int) -> Story:
        return self._story_service.choose_option(story, option_index)

    def finish_story(self, story: Story, ending_id: str) -> Story:
        return self._story_service.finish_story(story, ending_id)

    def fail_story(self, story: Story, reason: str = "") -> Story:
        return self._story_service.fail_story(story, reason)

    def get_story(self, story_id: str) -> Story:
        return self._story_service.get_story(story_id)

    def list_stories_for_player(self, player_id: str) -> List[Story]:
        return self._story_service.list_stories_for_player(player_id)

    def list_active_stories_for_player(self, player_id: str) -> List[Story]:
        return self._story_service.list_active_stories_for_player(player_id)
