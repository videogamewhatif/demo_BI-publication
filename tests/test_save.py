"""
tests/test_save.py
===================

Qué hace:
    Pruebas de `services/save_service.py` (`SaveService`, la
    persistencia real de una partida) y `managers/save_manager.py`
    (`SaveManager`, que decide CUÁNDO guardar — autoguardado,
    guardado rápido — y delega en `SaveService`).

Cómo funciona:
    Cada prueba usa `tmp_path` para que su repositorio de guardado
    sea independiente y no interfiera con las demás. Las pruebas de
    `SaveManager` construyen su propio `SaveService` de igual forma,
    porque `SaveManager` no reemplaza a `SaveService`: lo orquesta.

Dependencias:
    - pytest.
    - models.player, models.story, models.npc.
    - config.constant: RelationshipType.
    - services.save_service, services.repositories.
    - managers.save_manager.

Autor: Korlo
"""

from __future__ import annotations

import pytest

from config.constant import RelationshipType
from managers.save_manager import AUTOSAVE_SLOT, QUICKSAVE_SLOT, SaveManager
from models.npc import NPC
from models.player import Player
from models.story import Story
from services.repositories import JSONKeyValueRepository
from services.save_service import (
    SaveNotFoundError,
    SaveService,
    UnsupportedSaveFormatError,
)


# ==================================================
# FIXTURES
# ==================================================


@pytest.fixture
def player():
    """Un Player mínimo y válido, reutilizado por la mayoría de las pruebas."""
    return Player(
        player_id="p-1",
        first_name="Lucía",
        last_name="Fernández",
        birth_year=2005,
        country="MX",
    )


@pytest.fixture
def save_repository(tmp_path):
    return JSONKeyValueRepository(tmp_path / "saves")


@pytest.fixture
def save_service(save_repository):
    return SaveService(repository=save_repository)


@pytest.fixture
def save_manager(save_service):
    return SaveManager(save_service, autosave_interval_turns=5)


# ==================================================
# SaveService
# ==================================================


def test_save_and_load_full_game(save_service, player):
    story = Story(story_id="s-1", player_id=player.player_id, title="Un arco")
    npc = NPC(npc_id="npc-1", name="Marta", relationship_type=RelationshipType.PARENT)

    save_service.save_game("slot1", player=player, stories=[story], npcs=[npc])
    loaded = save_service.load_game("slot1")

    assert loaded.player.full_name == player.full_name
    assert loaded.stories[0].title == "Un arco"
    assert loaded.npcs[0].name == "Marta"


def test_save_game_without_stories_or_npcs(save_service, player):
    """stories y npcs son opcionales; una partida sin ninguno debe guardarse igual."""
    save_service.save_game("slot1", player=player)
    loaded = save_service.load_game("slot1")
    assert loaded.stories == []
    assert loaded.npcs == []


def test_save_game_rejects_empty_save_id(save_service, player):
    with pytest.raises(ValueError):
        save_service.save_game("", player=player)


def test_load_missing_save_raises(save_service):
    with pytest.raises(SaveNotFoundError):
        save_service.load_game("no-existe")


def test_load_newer_format_raises(save_service, save_repository, player):
    save_service.save_game("slot1", player=player)
    # Simula una partida guardada con un formato más nuevo del que
    # este servicio sabe leer, escribiendo directamente al repositorio
    # (a través de su API pública, no de un atributo privado).
    raw = save_repository.get("save_slot1")
    raw["format_version"] = 999
    save_repository.set("save_slot1", raw)

    with pytest.raises(UnsupportedSaveFormatError):
        save_service.load_game("slot1")


def test_save_exists(save_service, player):
    assert save_service.save_exists("slot1") is False
    save_service.save_game("slot1", player=player)
    assert save_service.save_exists("slot1") is True


def test_delete_save(save_service, player):
    save_service.save_game("slot1", player=player)
    save_service.delete_save("slot1")
    assert save_service.save_exists("slot1") is False


def test_delete_missing_save_raises(save_service):
    with pytest.raises(SaveNotFoundError):
        save_service.delete_save("no-existe")


def test_list_saves_returns_metadata_without_full_load(save_service, player):
    save_service.save_game("slot1", player=player)
    save_service.save_game("slot2", player=player)

    slots = save_service.list_saves()
    assert {slot.save_id for slot in slots} == {"slot1", "slot2"}
    assert all(slot.player_name == "Lucía Fernández" for slot in slots)


# ==================================================
# SaveManager — autoguardado
# ==================================================


def test_autosave_does_not_trigger_before_interval(save_manager, player):
    assert save_manager.autosave_if_due(current_turn=3, player=player) is False
    assert save_manager.save_exists(AUTOSAVE_SLOT) is False


def test_autosave_triggers_at_interval(save_manager, player):
    assert save_manager.autosave_if_due(current_turn=5, player=player) is True
    assert save_manager.save_exists(AUTOSAVE_SLOT) is True


def test_autosave_respects_interval_from_last_save(save_manager, player):
    save_manager.autosave_if_due(current_turn=5, player=player)
    assert save_manager.autosave_if_due(current_turn=7, player=player) is False
    assert save_manager.autosave_if_due(current_turn=10, player=player) is True


def test_turns_until_next_autosave(save_manager, player):
    assert save_manager.turns_until_next_autosave(current_turn=0) == 5
    save_manager.autosave_if_due(current_turn=5, player=player)
    assert save_manager.turns_until_next_autosave(current_turn=7) == 3
    assert save_manager.turns_until_next_autosave(current_turn=20) == 0


def test_save_manager_rejects_non_positive_interval(save_service):
    with pytest.raises(ValueError):
        SaveManager(save_service, autosave_interval_turns=0)


# ==================================================
# SaveManager — guardado rápido y manual
# ==================================================


def test_quick_save_and_load(save_manager, player):
    with pytest.raises(SaveNotFoundError):
        save_manager.quick_load()

    save_manager.quick_save(player)
    loaded = save_manager.quick_load()
    assert loaded.player.full_name == player.full_name
    assert save_manager.save_exists(QUICKSAVE_SLOT) is True


def test_save_now_and_list_saves(save_manager, player):
    save_manager.save_now("manual-1", player)
    slots = {slot.save_id for slot in save_manager.list_saves()}
    assert "manual-1" in slots


def test_save_manager_delete_save(save_manager, player):
    save_manager.save_now("manual-1", player)
    save_manager.delete_save("manual-1")
    assert save_manager.save_exists("manual-1") is False