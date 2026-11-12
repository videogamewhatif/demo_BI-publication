"""
services/story_service.py
==========================

Qué hace:
    Crea y hace avanzar historias (arcos narrativos) para un
    jugador, combinando el contenido estático de la historia (JSON,
    solo lectura) con el progreso dinámico del jugador dentro de
    ella (`models.story.Story`, lectura/escritura).

    Es el reemplazo funcional de lo que `engine/story_engine.py` y
    `engine/decision_engine.py` intentaban hacer — recordemos que
    `decision_engine.py` ni siquiera contenía la clase correcta (ver
    análisis previo del proyecto). Cuando se construya `managers/`,
    el futuro `StoryManager` debería delegar aquí en vez de
    reimplementar esta lógica.

Cómo funciona:
    Depende de dos abstracciones (ver `services/repositories.py`):

    - `ContentRepository`: lee la definición de la historia (título,
      escenas, opciones) desde `data/scenarios/<story_content_id>.json`.
      Es contenido de diseño; nunca se modifica en tiempo de
      ejecución.
    - `KeyValueRepository`: persiste el progreso (capítulo, escena
      actual, flags, decisiones tomadas) de cada `Story` del
      jugador.

    Formato esperado de una definición de historia en JSON:
        {
          "title": "El primer empleo",
          "genre": "drama laboral",
          "setting": "Oficina en la ciudad",
          "objective": "Conseguir el ascenso",
          "start_scene": "entrevista",
          "scenes": {
            "entrevista": {
              "text": "...",
              "options": [
                {"label": "Aceptar el puesto", "next_scene": "primer_dia"},
                {"label": "Pedir tiempo para pensarlo", "next_scene": "reflexion"}
              ],
              "ending": false
            },
            "primer_dia": {
              "text": "...",
              "options": [],
              "ending": true,
              "ending_id": "ending-carrera-estable"
            }
          }
        }

Dependencias:
    - services.repositories: ContentRepository, KeyValueRepository.
    - models.story: Story.
    - config.paths: SCENARIOS_DIR, SAVES_DIR.

Cómo interactúa con otros módulos:
    El contenido de las historias (data/scenarios/) todavía no
    existe en el proyecto — es contenido narrativo que el equipo de
    diseño debe crear como archivos JSON; este servicio solo define
    el contrato que esos archivos deben cumplir.

Autor: Korlo
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from config.paths import SAVES_DIR, SCENARIOS_DIR
from models.story import Story
from services.repositories import (
    ContentRepository,
    JSONContentRepository,
    JSONKeyValueRepository,
    KeyValueRepository,
)

logger = logging.getLogger(__name__)

_PROGRESS_KEY_PREFIX = "story_"
_REQUIRED_CONTENT_KEYS = {"title", "start_scene", "scenes"}


class StoryContentNotFoundError(Exception):
    """Se lanza cuando no existe contenido para el story_content_id pedido."""


class InvalidStoryContentError(Exception):
    """Se lanza cuando el contenido de una historia no cumple el formato esperado."""


class SceneNotFoundError(Exception):
    """Se lanza cuando la escena actual de una Story no existe en su contenido."""


class InvalidOptionError(Exception):
    """Se lanza cuando se elige una opción fuera de rango en la escena actual."""


class StoryNotFoundError(Exception):
    """Se lanza cuando se busca el progreso de una Story que no existe."""


class StoryService:
    """
    Crea y hace avanzar historias (arcos narrativos) para un
    jugador, separando el contenido estático (JSON) del progreso
    dinámico (`Story`).
    """

    def __init__(
        self,
        content_repository: Optional[ContentRepository] = None,
        progress_repository: Optional[KeyValueRepository] = None,
    ) -> None:
        self._content_repository: ContentRepository = (
            content_repository or JSONContentRepository(SCENARIOS_DIR)
        )
        self._progress_repository: KeyValueRepository = (
            progress_repository or JSONKeyValueRepository(SAVES_DIR)
        )

    # ==================================================
    # CREACIÓN
    # ==================================================

    def start_story(
        self,
        player_id: str,
        story_content_id: str,
        started_at_age: Optional[int] = None,
    ) -> Story:
        """
        Crea una nueva `Story` para el jugador a partir de una
        definición de contenido, la persiste y la devuelve.

        Raises:
            StoryContentNotFoundError: si `story_content_id` no
                existe en el repositorio de contenido.
            InvalidStoryContentError: si el contenido existe pero no
                cumple el formato esperado.
        """
        content = self._load_content(story_content_id)
        story = Story(
            story_id=str(uuid.uuid4()),
            player_id=player_id,
            title=content["title"],
            story_content_id=story_content_id,
            genre=content.get("genre", ""),
            setting=content.get("setting", ""),
            objective=content.get("objective", ""),
            current_scene_id=content["start_scene"],
            started_at_age=started_at_age,
        )
        self._persist(story)
        logger.info(
            "StoryService: nueva historia '%s' (%s) para jugador %s",
            story.title, story.story_id, player_id,
        )
        return story

    # ==================================================
    # CONSULTA DE ESCENA ACTUAL
    # ==================================================

    def get_current_scene(self, story: Story) -> Dict[str, Any]:
        """
        Devuelve la definición de la escena actual de `story` (texto
        y opciones), leída desde su contenido JSON.

        Raises:
            InvalidStoryContentError: si la Story no tiene
                `story_content_id` (no se puede resolver su contenido).
            SceneNotFoundError: si la escena actual no existe en el
                contenido de la historia.
        """
        content = self._content_for(story)
        scene = content.get("scenes", {}).get(story.current_scene_id)
        if scene is None:
            raise SceneNotFoundError(
                f"La escena '{story.current_scene_id}' no existe en "
                f"el contenido de '{story.title}'."
            )
        return scene

    def is_current_scene_ending(self, story: Story) -> bool:
        """Indica si la escena actual es un cierre de la historia."""
        return bool(self.get_current_scene(story).get("ending", False))

    # ==================================================
    # AVANCE
    # ==================================================

    def choose_option(self, story: Story, option_index: int) -> Story:
        """
        Aplica la opción elegida por el jugador: registra la
        decisión, avanza a la escena siguiente (o cierra la historia
        si la nueva escena es un final) y persiste el progreso.

        Raises:
            InvalidOptionError: si `option_index` está fuera de
                rango para la escena actual.
        """
        scene = self.get_current_scene(story)
        options = scene.get("options", [])

        if not (0 <= option_index < len(options)):
            raise InvalidOptionError(
                f"Opción {option_index} fuera de rango "
                f"(la escena actual tiene {len(options)} opciones)."
            )

        chosen = options[option_index]
        story.add_choice(chosen.get("label", f"Opción {option_index}"))
        story.advance_scene(chosen["next_scene"])

        if self.is_current_scene_ending(story):
            new_scene = self.get_current_scene(story)
            ending_id = new_scene.get("ending_id", "ending-generic")
            story.finish(ending_id)

        self._persist(story)
        return story

    def finish_story(self, story: Story, ending_id: str) -> Story:
        """Cierra manualmente la historia con el final indicado."""
        story.finish(ending_id)
        self._persist(story)
        return story

    def fail_story(self, story: Story, reason: str = "") -> Story:
        """Marca la historia como fallida (por ejemplo, por decisión del jugador)."""
        story.fail(reason)
        self._persist(story)
        return story

    # ==================================================
    # CONSULTA DE PROGRESO
    # ==================================================

    def get_story(self, story_id: str) -> Story:
        """
        Recupera el progreso guardado de una Story por su id.

        Raises:
            StoryNotFoundError: si no existe progreso guardado con ese id.
        """
        raw = self._progress_repository.get(self._progress_key(story_id))
        if raw is None:
            raise StoryNotFoundError(f"No existe progreso para la historia '{story_id}'.")
        return Story.from_dict(raw)

    def list_stories_for_player(self, player_id: str) -> List[Story]:
        """Lista todas las Story (activas o cerradas) de un jugador."""
        stories: List[Story] = []
        for key in self._progress_repository.list_keys(prefix=_PROGRESS_KEY_PREFIX):
            raw = self._progress_repository.get(key)
            if raw is not None and raw.get("player_id") == player_id:
                stories.append(Story.from_dict(raw))
        return stories

    def list_active_stories_for_player(self, player_id: str) -> List[Story]:
        """Lista solo las Story en curso (`is_active`) de un jugador."""
        return [
            story for story in self.list_stories_for_player(player_id)
            if story.is_active
        ]

    # ==================================================
    # INTERNO — PERSISTENCIA
    # ==================================================

    def _persist(self, story: Story) -> None:
        self._progress_repository.set(
            self._progress_key(story.story_id), story.to_dict()
        )

    @staticmethod
    def _progress_key(story_id: str) -> str:
        return f"{_PROGRESS_KEY_PREFIX}{story_id}"

    # ==================================================
    # INTERNO — CONTENIDO
    # ==================================================

    def _load_content(self, story_content_id: str) -> Dict[str, Any]:
        content = self._content_repository.load(story_content_id)
        if content is None:
            raise StoryContentNotFoundError(
                f"No existe contenido de historia '{story_content_id}'."
            )
        self._validate_content(content, story_content_id)
        return content

    def _content_for(self, story: Story) -> Dict[str, Any]:
        if not story.story_content_id:
            raise InvalidStoryContentError(
                f"La historia '{story.story_id}' no tiene story_content_id; "
                "no se puede resolver su contenido."
            )
        return self._load_content(story.story_content_id)

    @staticmethod
    def _validate_content(content: Dict[str, Any], story_content_id: str) -> None:
        missing = _REQUIRED_CONTENT_KEYS - content.keys()
        if missing:
            raise InvalidStoryContentError(
                f"Contenido de historia '{story_content_id}' incompleto; "
                f"faltan claves: {sorted(missing)}."
            )
        if content["start_scene"] not in content["scenes"]:
            raise InvalidStoryContentError(
                f"'start_scene' ({content['start_scene']!r}) no existe "
                f"en 'scenes' para '{story_content_id}'."
            )