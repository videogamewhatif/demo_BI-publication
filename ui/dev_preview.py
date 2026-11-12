"""
ui/dev_preview.py
===================

QUÉ ES ESTO (léase antes de usarlo o de borrarlo):
    Hoy no existe en el proyecto ningún Sistema de Creación de
    Personaje funcional (`managers.player_manager` no existe;
    `engine/game_engine.py` que lo invocaría está roto) ni contenido
    narrativo real en `data/scenarios/`. Sin alguno de los dos, la
    pantalla Historia solo puede mostrarse en su estado vacío
    honesto ("No tienes ninguna historia en curso").

    Este módulo NO es un Sistema de Creación de Personaje ni
    contenido narrativo — es un atajo de desarrollo, claramente
    marcado, que arma un `Player` técnico y arranca la única historia
    de prueba (`data/scenarios/example_ui_fixture.json`, que también
    se documenta a sí misma como placeholder) para poder verificar
    visualmente que capítulo/escena/texto/N-decisiones/panel de
    personaje/historial se conectan de verdad a `services/`.

    Se llega aquí únicamente desde el botón "Vista previa de
    interfaz (datos de ejemplo)" del menú principal — nunca desde
    "Nueva partida" ni "Continuar", que usan los flujos reales
    (o informan honestamente que todavía no existen).

    Bórrese este archivo y `data/scenarios/example_ui_fixture.json`
    en cuanto exista un Sistema de Creación de Personaje real y
    contenido narrativo real.

Autor: Korlo (ui/ añadida en esta sesión; usa StoryManager en vez de
StoryService directo desde la sesión de managers de dominio)
"""

from __future__ import annotations

from typing import Tuple

from managers.story_manager import StoryManager
from models.player import Player
from models.story import Story

PREVIEW_STORY_CONTENT_ID = "example_ui_fixture"
PREVIEW_PLAYER_ID = "dev-preview-player"


def build_preview_player() -> Player:
    """Player técnico de ejemplo — nombres claramente ficticios, no un personaje diseñado."""
    return Player(
        player_id=PREVIEW_PLAYER_ID,
        first_name="Vista",
        last_name="Previa",
        birth_year=2000,
        country="—",
        age=24,
        aspiration="Personaje de ejemplo (dev)",
    )


def get_or_start_preview_story(story_manager: StoryManager, player: Player) -> Story:
    """
    Reutiliza la Story de ejemplo si ya se había iniciado antes
    (persistida vía `StoryManager` como cualquier otra), o la crea
    si es la primera vez.
    """
    for story in story_manager.list_stories_for_player(player.player_id):
        if story.story_content_id == PREVIEW_STORY_CONTENT_ID:
            return story
    return story_manager.start_story(
        player_id=player.player_id,
        story_content_id=PREVIEW_STORY_CONTENT_ID,
        started_at_age=player.age,
    )


def build_preview_session(story_manager: StoryManager) -> Tuple[Player, Story]:
    """Punto de entrada único: devuelve (player, story) listos para `GameplayScreen`."""
    player = build_preview_player()
    story = get_or_start_preview_story(story_manager, player)
    return player, story
