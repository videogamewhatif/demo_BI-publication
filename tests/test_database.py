"""
tests/test_database.py
=========================

Qué hace:
    Prueba los 7 repositorios de `database/repositories.py` contra
    un archivo SQLite temporal real (`tmp_path`) — ida y vuelta
    completa: guardar un dataclass real (`Player`, `Story`, `Item`,
    `Achievement`) y recuperarlo, verificando que cada campo
    sobrevivió el viaje, incluidas las listas que se guardan en
    tablas relacionadas aparte.

Autor: Korlo (reconstruido en la sesión de deuda técnica)
"""

from __future__ import annotations

import pytest

from config.constant import CivilStatus, EducationLevel, PersonalityTrait, SocioeconomicLevel, StoryStatus, Talent
from database.engine import create_all, create_database_engine
from database.repositories import (
    AchievementRepository,
    EndingRepository,
    InventoryRepository,
    PlayerNotFoundError,
    PlayerRepository,
    SaveSlotRepository,
    StatisticsRepository,
    StoryNotFoundError,
    StoryRepository,
)
from models.achievement import Achievement
from models.item import Item
from models.player import FamilyTree, Player, PlayerStatistics
from models.story import Story
from services.statistics_service import AccountStatistics


@pytest.fixture
def engine(tmp_path):
    eng = create_database_engine(tmp_path / "test.db")
    create_all(eng)
    return eng


def _full_player(player_id="p1") -> Player:
    return Player(
        player_id=player_id,
        first_name="Ana",
        last_name="Ruiz",
        gender="Femenino",
        birth_year=2000,
        country="Chile",
        city="Santiago",
        socioeconomic_origin=SocioeconomicLevel.LOW,
        health_genetics=65,
        age=24,
        life_expectancy=82.0,
        health=90,
        appearance=55,
        intelligence=70,
        discipline=60,
        creativity=80,
        stress=20,
        happiness=75,
        charisma=65,
        empathy=70,
        reputation=15,
        personality_traits=[PersonalityTrait.AMBITIOUS, PersonalityTrait.CAUTIOUS],
        talents=[Talent.ARTISTIC],
        aspiration="Ser arquitecta",
        net_worth=5000.0,
        annual_income=12000.0,
        debt=500.0,
        education_level=EducationLevel.UNIVERSITY,
        current_profession="Estudiante",
        civil_status=CivilStatus.SINGLE,
        family=FamilyTree(
            parent_ids=["npc-mom", "npc-dad"],
            sibling_ids=["npc-brother"],
            spouse_id=None,
            children_ids=[],
        ),
        active_relationships=["npc-friend-1", "npc-friend-2"],
        statistics=PlayerStatistics(turns_played=12, decisions_made=8, key_moments_unlocked=2),
        memory_moments=["moment-1", "moment-2", "moment-3"],
    )


# ==================================================
# PlayerRepository
# ==================================================


def test_player_repository_round_trip(engine):
    repo = PlayerRepository(engine)
    original = _full_player()

    repo.save_player(original)
    recovered = repo.get_player("p1")

    assert recovered.player_id == original.player_id
    assert recovered.full_name == original.full_name
    assert recovered.age == original.age
    assert recovered.health == original.health
    assert recovered.net_worth == original.net_worth
    assert recovered.socioeconomic_origin == original.socioeconomic_origin
    assert recovered.education_level == original.education_level
    assert recovered.civil_status == original.civil_status
    assert set(recovered.personality_traits) == set(original.personality_traits)
    assert set(recovered.talents) == set(original.talents)
    assert sorted(recovered.active_relationships) == sorted(original.active_relationships)
    assert recovered.memory_moments == original.memory_moments  # orden importa acá
    assert sorted(recovered.family.parent_ids) == sorted(original.family.parent_ids)
    assert recovered.family.sibling_ids == original.family.sibling_ids
    assert recovered.statistics.turns_played == original.statistics.turns_played


def test_player_repository_not_found(engine):
    repo = PlayerRepository(engine)
    assert repo.player_exists("no-existe") is False
    with pytest.raises(PlayerNotFoundError):
        repo.get_player("no-existe")


def test_player_repository_resave_replaces_not_duplicates(engine):
    """Guardar el mismo player_id dos veces reemplaza, no duplica filas relacionadas."""
    repo = PlayerRepository(engine)
    player = _full_player()
    repo.save_player(player)

    player.memory_moments = ["solo-un-momento"]
    repo.save_player(player)

    recovered = repo.get_player("p1")
    assert recovered.memory_moments == ["solo-un-momento"]


# ==================================================
# StoryRepository
# ==================================================


def _full_story(story_id="s1", player_id="p1") -> Story:
    return Story(
        story_id=story_id,
        player_id=player_id,
        title="El primer empleo",
        story_content_id="example_ui_fixture",
        genre="drama",
        setting="ciudad",
        objective="conseguir trabajo",
        chapter=2,
        current_scene_id="oficina",
        status=StoryStatus.IN_PROGRESS,
        summary="Un resumen.",
        current_situation="En la entrevista.",
        events=["Escena: inicio", "Escena: oficina"],
        important_choices=["Aceptó el trabajo", "Rechazó la oferta inicial"],
        active_npcs=["npc-jefe"],
        flags={"conoce_jefe": True, "tiene_referencia": False},
        started_at_age=22,
        ending_id=None,
    )


def test_story_repository_round_trip(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = StoryRepository(engine)
    original = _full_story()

    repo.save_story(original)
    recovered = repo.get_story("s1")

    assert recovered.title == original.title
    assert recovered.chapter == original.chapter
    assert recovered.status == original.status
    assert recovered.events == original.events  # orden importa
    assert recovered.important_choices == original.important_choices
    assert recovered.active_npcs == original.active_npcs
    assert recovered.flags == original.flags
    assert recovered.started_at_age == original.started_at_age


def test_story_repository_not_found(engine):
    with pytest.raises(StoryNotFoundError):
        StoryRepository(engine).get_story("no-existe")


def test_story_repository_list_for_player(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = StoryRepository(engine)
    repo.save_story(_full_story("s1"))
    repo.save_story(_full_story("s2"))

    stories = repo.list_stories_for_player("p1")
    assert {s.story_id for s in stories} == {"s1", "s2"}


# ==================================================
# InventoryRepository
# ==================================================


def test_inventory_repository_add_and_remove(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = InventoryRepository(engine)

    repo.add_item("p1", Item(item_id="sword", name="Espada", quantity=1, metadata={"forjado_por": "Ana"}))
    repo.add_item("p1", Item(item_id="shield", name="Escudo"))

    items = repo.get_items("p1")
    assert len(items) == 2
    sword = next(i for i in items if i.item_id == "sword")
    assert sword.metadata == {"forjado_por": "Ana"}

    removed = repo.remove_item("p1", "sword")
    assert removed is True
    assert len(repo.get_items("p1")) == 1

    assert repo.remove_item("p1", "no-existe") is False


def test_inventory_repository_clear(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = InventoryRepository(engine)
    repo.add_item("p1", Item(item_id="a", name="A"))
    repo.add_item("p1", Item(item_id="b", name="B"))
    repo.clear_inventory("p1")
    assert repo.get_items("p1") == []


# ==================================================
# AchievementRepository
# ==================================================


def test_achievement_repository_grant_and_unlock(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = AchievementRepository(engine)

    achievement = Achievement(
        achievement_id="primer-paso", title="Primer paso", description="Diste el primer paso.",
        rewards=["insignia-bronce"], required_flags={"tutorial_completo": True},
    )
    repo.grant_achievement("p1", achievement)

    all_ach = repo.list_achievements("p1")
    assert len(all_ach) == 1
    assert all_ach[0].unlocked is False
    assert all_ach[0].rewards == ["insignia-bronce"]
    assert all_ach[0].required_flags == {"tutorial_completo": True}

    unlocked = repo.unlock_achievement("p1", "primer-paso", "2026-01-01T00:00:00")
    assert unlocked is True
    all_ach = repo.list_achievements("p1")
    assert all_ach[0].unlocked is True
    assert all_ach[0].unlocked_at == "2026-01-01T00:00:00"

    assert repo.unlock_achievement("p1", "no-existe", "2026-01-01") is False


# ==================================================
# EndingRepository
# ==================================================


def test_ending_repository_unlock_and_check(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = EndingRepository(engine)

    assert repo.has_ending("p1", "final-prospero") is False
    repo.unlock_ending("p1", "final-prospero", "2026-01-01T00:00:00")
    assert repo.has_ending("p1", "final-prospero") is True
    assert repo.list_unlocked("p1") == ["final-prospero"]


# ==================================================
# StatisticsRepository
# ==================================================


def test_statistics_repository_defaults_and_save(engine):
    repo = StatisticsRepository(engine)
    empty = repo.get_statistics("p1")
    assert empty.total_games == 0

    stats = AccountStatistics(user_id="p1", total_games=3, total_deaths=1, total_play_time=120, achievements_unlocked=2)
    repo.save_statistics("p1", stats)

    recovered = repo.get_statistics("p1")
    assert recovered.total_games == 3
    assert recovered.total_deaths == 1
    assert recovered.achievements_unlocked == 2


# ==================================================
# SaveSlotRepository
# ==================================================


def test_save_slot_repository_round_trip(engine):
    PlayerRepository(engine).save_player(_full_player())
    repo = SaveSlotRepository(engine)

    repo.save_slot("quicksave", _full_player(), "2026-01-01T00:00:00")
    slots = repo.list_slots()
    assert len(slots) == 1
    assert slots[0]["save_id"] == "quicksave"
    assert slots[0]["player_name"] == "Ana Ruiz"

    repo.delete_slot("quicksave")
    assert repo.list_slots() == []
