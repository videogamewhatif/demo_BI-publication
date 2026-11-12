"""
services/demo_service.py
==========================

DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA

Qué es esto:
    Punto de entrada único de la Partida Demo usada para presentar el
    prototipo a un inversionista (~4-5 minutos, contenido narrativo
    fijo, siempre toma la ruta A). Arma una sesión (`Player`, `Story`,
    `StoryManager`, `SaveManager`) completamente aislada del sistema
    principal, para que jugar la demo:

    - NO llame ninguna API de IA (el contenido es
      `data/demo_story.json`, JSON estático, leído por el mismo
      `StoryService` que ya usa el juego real).
    - NO cree cuenta ni pase por creación de personaje: el `Player`
      de demostración se construye aquí mismo con valores fijos.
    - NO escriba en Supabase ni en `saves/` (disco): tanto el
      progreso de la historia como los "guardados rápidos" que
      `GameplayScreen` dispara tras cada decisión (ver
      `ui/screens/gameplay_screen.py::_handle_story_advanced`) se
      persisten en `InMemoryKeyValueRepository`, que vive y muere con
      el proceso — nunca toca disco.

Cómo se mantiene aislado del juego principal (para poder borrarlo):
    Reutiliza tal cual `StoryService`, `StoryManager`, `SaveService`,
    `SaveManager`, `ConsequenceService`, `GameplayScreen` y
    `StoryPanel` — ningún archivo del motor/UI compartido importa
    nada de este módulo. Solo `ui/screens/main_menu_screen.py` (el
    botón "Jugar demo") y `ui/windows/main_window.py` (para alojar la
    segunda instancia de `GameplayScreen` que usa esta sesión) llaman
    a `build_demo_session()`. Borrar este archivo, `data/demo_story.json`
    y esas dos referencias deja el juego principal exactamente como
    estaba.

    `CompletionWatchingStoryManager` es la única pieza "inteligente":
    es una subclase de `StoryManager` (sin tocar el archivo real) que
    avisa via callback cuando la historia de demo llega a su final,
    para que `MainWindow` pueda mostrar el cierre ("FIN DE LA DEMO" +
    botón "Volver al inicio") sin que `StoryPanel`/`GameplayScreen`
    necesiten saber que existe una demo.

Valores del jugador de demostración (decisión de contenido, no de
arquitectura — ver conversación de implementación):
    Nombre "Alex Rivera", 24 años, $2,500 de patrimonio inicial,
    salud 100, origen socioeconómico medio. "Estatus social" (pedido
    como stat 0-100 que sube 50 -> 55 en el Evento 4) se mapea a
    `Player.reputation`: es el único atributo numérico de
    `ConsequenceService.VALID_EFFECT_KEYS` que encaja — el proyecto
    ya lo muestra en pantalla como "Reputación".

Autor: Korlo (sesión de la Partida Demo)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from config.constant import SocioeconomicLevel
from config.paths import DATA_DIR
from managers.save_manager import SaveManager
from managers.story_manager import StoryManager
from models.player import Player
from models.story import Story
from services.repositories import JSONContentRepository, KeyValueRepository
from services.save_service import SaveService
from services.story_service import StoryService

DEMO_STORY_CONTENT_ID = "demo_story"
DEMO_PLAYER_ID = "demo-alex"

_DEMO_AGE = 24
_DEMO_MONEY = 2500.0
_DEMO_HEALTH = 100
_DEMO_SOCIAL_STATUS = 50  # -> Player.reputation, ver docstring del módulo.


# ==================================================
# REPOSITORIO EN MEMORIA — nunca toca disco ni Supabase
# ==================================================


class InMemoryKeyValueRepository(KeyValueRepository):
    """
    DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA

    Implementación de `KeyValueRepository` que guarda todo en un
    diccionario en memoria del proceso. Cumple el mismo contrato que
    `JSONKeyValueRepository` (ver `services/repositories.py`), así
    que `StoryService`/`SaveService` no notan la diferencia — pero
    nada de lo que escriban aquí sobrevive al cierre de la demo ni
    llega a `saves/` ni a Supabase.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        value = self._store.get(key)
        return dict(value) if value is not None else None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        self._store[key] = dict(value)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def list_keys(self, prefix: str = "") -> List[str]:
        return sorted(k for k in self._store if k.startswith(prefix))


# ==================================================
# STORYMANAGER QUE AVISA CUANDO LA DEMO TERMINA
# ==================================================


class CompletionWatchingStoryManager(StoryManager):
    """
    DEMO TEMPORAL - ELIMINAR CUANDO SE INTEGRE LA API DE IA

    Subclase de `StoryManager` (el real, sin modificarlo) que además
    invoca `on_finished(story)` cuando una decisión hace que la
    historia llegue a su final — es la única forma de que
    `MainWindow` sepa mostrar el cierre de la demo sin que
    `GameplayScreen`/`StoryPanel` (compartidos con el juego real)
    necesiten conocer el concepto de "demo".
    """

    def __init__(self, story_service: StoryService, on_finished: Callable[[Story], None]) -> None:
        super().__init__(story_service)
        self._on_finished = on_finished

    def choose_option(self, story: Story, option_index: int) -> Story:
        updated = super().choose_option(story, option_index)
        if updated.is_finished:
            self._on_finished(updated)
        return updated


# ==================================================
# CONSTRUCCIÓN DE LA SESIÓN DE DEMO
# ==================================================


@dataclass
class DemoSession:
    """Todo lo que `MainWindow` necesita para alojar la demo en una `GameplayScreen` aislada."""

    player: Player
    story: Story
    story_manager: StoryManager
    save_manager: SaveManager


def build_demo_player() -> Player:
    """Jugador de demostración con valores fijos — no requiere creación de personaje."""
    birth_year = datetime.now(timezone.utc).year - _DEMO_AGE
    return Player(
        player_id=DEMO_PLAYER_ID,
        first_name="Alex",
        last_name="Rivera",
        birth_year=birth_year,
        country="—",
        age=_DEMO_AGE,
        health=_DEMO_HEALTH,
        net_worth=_DEMO_MONEY,
        reputation=_DEMO_SOCIAL_STATUS,
        socioeconomic_origin=SocioeconomicLevel.MEDIUM,
        aspiration="Demo de presentación",
    )


def build_demo_session(on_finished: Callable[[Story], None]) -> DemoSession:
    """
    Punto de entrada único: arma un `Player`/`Story`/`StoryManager`/
    `SaveManager` de demo completamente nuevos y aislados. Se llama
    una vez por cada clic en "Jugar demo" (ver `ui/windows/main_window.py`),
    así que cada partida de demo empieza siempre desde el Evento 1.

    `on_finished` se invoca con la `Story` ya actualizada en el
    momento exacto en que la demo llega a su final (ver
    `CompletionWatchingStoryManager`).
    """
    content_repository = JSONContentRepository(DATA_DIR)
    story_service = StoryService(
        content_repository=content_repository,
        progress_repository=InMemoryKeyValueRepository(),
    )
    story_manager = CompletionWatchingStoryManager(story_service, on_finished)

    save_manager = SaveManager(save_service=SaveService(repository=InMemoryKeyValueRepository()))

    player = build_demo_player()
    story = story_manager.start_story(
        player_id=player.player_id,
        story_content_id=DEMO_STORY_CONTENT_ID,
        started_at_age=player.age,
    )

    return DemoSession(player=player, story=story, story_manager=story_manager, save_manager=save_manager)
