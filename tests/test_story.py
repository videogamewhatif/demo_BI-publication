"""
tests/test_story.py
====================

Qué hace:
    Pruebas de `models/story.py` (el dataclass `Story`, un arco
    narrativo discreto con capítulos) y `services/story_service.py`
    (`StoryService`, que combina ese modelo con contenido JSON de
    solo lectura para crear y avanzar historias).

Cómo funciona:
    Usa `tmp_path` (fixture estándar de pytest: un directorio
    temporal único por prueba, limpiado automáticamente) para que
    cada prueba de `StoryService` tenga su propio repositorio de
    contenido y de progreso, sin pisarse entre pruebas ni depender
    de `data/`/`saves/` reales.

Dependencias:
    - pytest.
    - models.story: Story.
    - config.constant: StoryStatus.
    - services.story_service: StoryService y sus excepciones.
    - services.repositories: JSONContentRepository, JSONKeyValueRepository.

Autor: Korlo
"""

from __future__ import annotations

import json

import pytest

from config.constant import StoryStatus
from models.story import Story
from services.repositories import JSONContentRepository, JSONKeyValueRepository
from services.story_service import (
    InvalidOptionError,
    InvalidStoryContentError,
    SceneNotFoundError,
    StoryContentNotFoundError,
    StoryNotFoundError,
    StoryService,
)

SAMPLE_CONTENT = {
    "title": "El primer empleo",
    "genre": "drama laboral",
    "setting": "Oficina en la ciudad",
    "objective": "Conseguir el ascenso",
    "start_scene": "entrevista",
    "scenes": {
        "entrevista": {
            "text": "Te entrevistan para el puesto.",
            "options": [
                {"label": "Aceptar el puesto", "next_scene": "primer_dia"},
                {"label": "Pedir tiempo para pensarlo", "next_scene": "reflexion"},
            ],
            "ending": False,
        },
        "reflexion": {
            "text": "Lo piensas unos días.",
            "options": [
                {"label": "Aceptar finalmente", "next_scene": "primer_dia"},
            ],
            "ending": False,
        },
        "primer_dia": {
            "text": "Tu primer día de trabajo.",
            "options": [],
            "ending": True,
            "ending_id": "ending-carrera-estable",
        },
    },
}


# ==================================================
# FIXTURES
# ==================================================


@pytest.fixture
def story_service(tmp_path):
    """StoryService con repositorios JSON aislados en un directorio temporal."""
    content_dir = tmp_path / "scenarios"
    content_dir.mkdir()
    (content_dir / "primer_empleo.json").write_text(
        json.dumps(SAMPLE_CONTENT), encoding="utf-8"
    )
    return StoryService(
        content_repository=JSONContentRepository(content_dir),
        progress_repository=JSONKeyValueRepository(tmp_path / "saves"),
    )


# ==================================================
# MODELO: Story
# ==================================================


def test_story_creation_defaults():
    """Una Story recién creada empieza en curso, en el capítulo 1 y en 'start'."""
    story = Story(story_id="s1", player_id="p1", title="Arco de prueba")
    assert story.status == StoryStatus.IN_PROGRESS
    assert story.chapter == 1
    assert story.current_scene_id == "start"
    assert story.is_active is True
    assert story.is_finished is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"story_id": "", "player_id": "p1", "title": "X"},
        {"story_id": "s1", "player_id": "", "title": "X"},
        {"story_id": "s1", "player_id": "p1", "title": ""},
        {"story_id": "s1", "player_id": "p1", "title": "X", "chapter": 0},
        {"story_id": "s1", "player_id": "p1", "title": "X", "current_scene_id": ""},
        {"story_id": "s1", "player_id": "p1", "title": "X", "started_at_age": -1},
    ],
)
def test_story_rejects_invalid_construction(kwargs):
    """Cada campo con una regla de validación la aplica en __post_init__."""
    with pytest.raises(ValueError):
        Story(**kwargs)


def test_story_advance_scene_records_event():
    story = Story(story_id="s1", player_id="p1", title="Arco")
    story.advance_scene("entrevista")
    assert story.current_scene_id == "entrevista"
    assert "Escena: entrevista" in story.events


def test_story_advance_chapter_resets_scene():
    story = Story(story_id="s1", player_id="p1", title="Arco", current_scene_id="final_cap1")
    story.advance_chapter()
    assert story.chapter == 2
    assert story.current_scene_id == "start"

    story.advance_chapter(first_scene_id="intro_cap3")
    assert story.chapter == 3
    assert story.current_scene_id == "intro_cap3"


def test_story_flags():
    story = Story(story_id="s1", player_id="p1", title="Arco")
    assert story.has_flag("conoce_secreto") is False
    story.add_flag("conoce_secreto")
    assert story.has_flag("conoce_secreto") is True
    story.add_flag("conoce_secreto", value=False)
    assert story.has_flag("conoce_secreto") is False


def test_story_npc_linking():
    story = Story(story_id="s1", player_id="p1", title="Arco")
    story.link_npc("npc-1")
    story.link_npc("npc-1")  # duplicado, no debe repetirse
    assert story.active_npcs == ["npc-1"]
    story.unlink_npc("npc-1")
    assert story.active_npcs == []
    story.unlink_npc("no-estaba")  # no debe fallar


def test_story_finish_sets_status_and_ending():
    story = Story(story_id="s1", player_id="p1", title="Arco")
    story.finish("ending-feliz")
    assert story.status == StoryStatus.COMPLETED
    assert story.ending_id == "ending-feliz"
    assert story.is_active is False
    assert story.is_finished is True


def test_story_finish_requires_ending_id():
    story = Story(story_id="s1", player_id="p1", title="Arco")
    with pytest.raises(ValueError):
        story.finish("")


def test_story_fail_and_abandon():
    failed = Story(story_id="s1", player_id="p1", title="Arco")
    failed.fail("motivo")
    assert failed.status == StoryStatus.FAILED

    abandoned = Story(story_id="s2", player_id="p1", title="Otro arco")
    abandoned.abandon("fin de la partida")
    assert abandoned.status == StoryStatus.ABANDONED


def test_story_to_dict_from_dict_roundtrip():
    story = Story(
        story_id="s1",
        player_id="p1",
        title="Arco completo",
        story_content_id="primer_empleo",
        started_at_age=18,
    )
    story.advance_scene("entrevista")
    story.add_choice("Aceptó el puesto")
    story.add_flag("tiene_trabajo")
    story.link_npc("npc-jefe")
    story.finish("ending-carrera-estable")

    data = story.to_dict()
    restored = Story.from_dict(data)

    assert restored.to_dict() == data
    assert restored.status == StoryStatus.COMPLETED
    assert restored.story_content_id == "primer_empleo"


# ==================================================
# SERVICIO: StoryService
# ==================================================


def test_start_story_creates_from_content(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo", started_at_age=18)
    assert story.title == "El primer empleo"
    assert story.current_scene_id == "entrevista"
    assert story.story_content_id == "primer_empleo"
    assert story.started_at_age == 18


def test_start_story_missing_content_raises(story_service):
    with pytest.raises(StoryContentNotFoundError):
        story_service.start_story(player_id="p1", story_content_id="no-existe")


def test_start_story_invalid_content_raises(tmp_path):
    content_dir = tmp_path / "scenarios"
    content_dir.mkdir()
    (content_dir / "malo.json").write_text(
        json.dumps({"title": "Malo", "start_scene": "x", "scenes": {}}), encoding="utf-8"
    )
    service = StoryService(
        content_repository=JSONContentRepository(content_dir),
        progress_repository=JSONKeyValueRepository(tmp_path / "saves"),
    )
    with pytest.raises(InvalidStoryContentError):
        service.start_story(player_id="p1", story_content_id="malo")


def test_get_current_scene_returns_text_and_options(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    scene = story_service.get_current_scene(story)
    assert scene["text"] == "Te entrevistan para el puesto."
    assert len(scene["options"]) == 2
    assert story_service.is_current_scene_ending(story) is False


def test_get_current_scene_missing_scene_raises(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    story.current_scene_id = "escena_inexistente"
    with pytest.raises(SceneNotFoundError):
        story_service.get_current_scene(story)


def test_choose_option_advances_without_closing(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    story = story_service.choose_option(story, 1)  # "Pedir tiempo para pensarlo"
    assert story.current_scene_id == "reflexion"
    assert story.important_choices == ["Pedir tiempo para pensarlo"]
    assert story.status == StoryStatus.IN_PROGRESS


def test_choose_option_auto_closes_on_ending_scene(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    story = story_service.choose_option(story, 0)  # "Aceptar el puesto" -> primer_dia (ending)
    assert story.current_scene_id == "primer_dia"
    assert story.status == StoryStatus.COMPLETED
    assert story.ending_id == "ending-carrera-estable"


def test_choose_option_invalid_index_raises(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    with pytest.raises(InvalidOptionError):
        story_service.choose_option(story, 99)


def test_choose_option_persists_progress(story_service):
    story = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    story_service.choose_option(story, 1)

    reloaded = story_service.get_story(story.story_id)
    assert reloaded.current_scene_id == "reflexion"
    assert reloaded.important_choices == story.important_choices


def test_get_story_not_found_raises(story_service):
    with pytest.raises(StoryNotFoundError):
        story_service.get_story("no-existe")


def test_list_stories_for_player(story_service):
    story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    story2 = story_service.start_story(player_id="p1", story_content_id="primer_empleo")
    story_service.start_story(player_id="otro-jugador", story_content_id="primer_empleo")

    stories = story_service.list_stories_for_player("p1")
    assert len(stories) == 2

    story_service.fail_story(story2, reason="prueba")
    active = story_service.list_active_stories_for_player("p1")
    assert len(active) == 1
    assert active[0].story_id != story2.story_id