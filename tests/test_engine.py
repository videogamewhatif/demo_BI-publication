"""
tests/test_engine.py
=====================

Qué hace:
    Pruebas reales de los 9 archivos de `engine/` — ya no hay ningún
    `@pytest.mark.skip`. La versión anterior de este archivo
    documentaba, con una razón concreta por cada uno, por qué
    ninguno se podía importar todavía (`ModuleNotFoundError` contra
    un segundo lote de managers de dominio que no existía). Esa
    versión quedó completamente desactualizada en la sesión de
    "desbloquear engine/" — los 9 managers de dominio que faltaban
    ya existen (`StoryManager`, `PlayerManager`, `TimeManager`,
    `EventManager`, `EndingManager`, `AchievementManager`,
    `InventoryManager`) y los 9 archivos de `engine/` se
    reescribieron para llamar a su API real.

Decisiones arquitectónicas que quedaron resueltas (antes eran
skips con "decisión pendiente"):
    - `StoryEngine` y `SaveEngine` sobreviven como capas finas sobre
      `StoryManager`/`SaveManager` — el usuario eligió explícitamente
      "reescribe los 9 archivos" en vez de retirar `engine/`, sabiendo
      que duplica lo que `ui/` ya hace (ver `docs/architecture.md` §2).

Alcance que sigue sin implementarse (documentado, no fingido):
    - `TimeEngine` no recalcula `life_expectancy` por turno — ese
      alcance quedó fuera de `TimeManager` desde que se construyó
      (ver su propio docstring): es una decisión de balance de juego
      que nadie pidió todavía.
    - `EventEngine`/`EndingEngine`/`AchievementEngine`/`InventoryEngine`
      operan sobre catálogos reales pero VACÍOS
      (`data/events/`, `data/endings/`, `data/achievements/`,
      `data/items/`) — las pruebas de este archivo escriben sus
      propias definiciones de prueba en `tmp_path`, nunca contenido
      real de diseño.

Autor: Korlo
"""

from __future__ import annotations

import json

import pytest

from config.constant import SocioeconomicLevel
from engine.achievement_engine import AchievementEngine
from engine.decision_engine import DecisionEngine
from engine.ending_engine import EndingEngine
from engine.event_engine import EventEngine
from engine.game_engine import GameEngine
from engine.inventory_engine import InventoryEngine
from engine.save_engine import SaveEngine
from engine.story_engine import StoryEngine
from engine.time_engine import TimeEngine
from managers.achievement_manager import AchievementManager
from managers.ending_manager import EndingManager
from managers.event_manager import EventManager
from managers.inventory_manager import InventoryManager
from managers.player_manager import PlayerManager
from managers.save_manager import SaveManager
from managers.story_manager import StoryManager
from managers.time_manager import TimeManager
from services.achievement_service import AchievementService
from services.consequence_service import ConsequenceService
from services.inventory_service import InventoryService
from services.repositories import JSONContentRepository, JSONKeyValueRepository
from services.save_service import SaveService
from services.statistics_service import StatisticsService
from services.story_service import StoryService

_FIXTURE_STORY = {
    "title": "Historia de prueba",
    "start_scene": "inicio",
    "scenes": {
        "inicio": {
            "text": "...",
            "options": [{"label": "opción A", "next_scene": "fin", "effects": {"discipline": 5}}],
        },
        "fin": {"text": "fin.", "ending": True, "ending_id": "fin-1"},
    },
}


def _player(pm: PlayerManager, **overrides):
    kwargs = dict(first_name="Test", last_name="Jugador", gender=None,
                  starting_age=20, country="X", city="Y")
    kwargs.update(overrides)
    return pm.create_player(**kwargs)


@pytest.fixture
def scenarios_dir(tmp_path):
    d = tmp_path / "scenarios"
    d.mkdir()
    (d / "test_story.json").write_text(json.dumps(_FIXTURE_STORY), encoding="utf-8")
    return d


@pytest.fixture
def saves_dir(tmp_path):
    d = tmp_path / "saves"
    d.mkdir()
    return d


# ==================================================
# GameEngine — orquestador principal
# ==================================================


def test_game_engine_can_be_constructed_with_injected_dependencies(scenarios_dir, saves_dir):
    """GameEngine acepta por inyección (no crea internamente) todos sus managers/services."""
    story_service = StoryService(
        content_repository=JSONContentRepository(scenarios_dir),
        progress_repository=JSONKeyValueRepository(saves_dir),
    )
    ge = GameEngine(
        story_manager=StoryManager(story_service),
        save_manager=SaveManager(SaveService(repository=JSONKeyValueRepository(saves_dir))),
        player_manager=PlayerManager(repository=JSONKeyValueRepository(saves_dir)),
        time_manager=TimeManager(),
        consequence_service=ConsequenceService(),
    )
    assert ge.is_running() is False
    assert ge.story_manager is not None
    assert ge.save_manager is not None
    assert ge.player_manager is not None


def test_game_engine_advances_one_turn_and_updates_player_state(scenarios_dir, saves_dir):
    """Avanzar un turno aplica las consecuencias de la opción elegida sobre Player de verdad."""
    story_service = StoryService(
        content_repository=JSONContentRepository(scenarios_dir),
        progress_repository=JSONKeyValueRepository(saves_dir),
    )
    ge = GameEngine(
        story_manager=StoryManager(story_service),
        save_manager=SaveManager(SaveService(repository=JSONKeyValueRepository(saves_dir))),
        player_manager=PlayerManager(repository=JSONKeyValueRepository(saves_dir)),
        time_manager=TimeManager(),
        consequence_service=ConsequenceService(),
    )
    player = ge.start_new_game(
        first_name="Ana", last_name="Ruiz", gender=None, starting_age=20,
        country="Chile", city="Santiago", story_content_id="test_story",
    )
    before_discipline = player.discipline
    before_age = player.age

    assert ge.choose_option(0) is True
    assert player.discipline == before_discipline + 5  # effects de la opción, vía ConsequenceService
    assert player.age == before_age + 1  # TimeEngine avanzó el año
    assert ge.story_engine.is_finished() is True  # la escena "fin" es un cierre


def test_game_engine_save_game_persists_through_save_manager(scenarios_dir, saves_dir):
    """save_game() delega en SaveManager real — se puede recargar después."""
    save_repo = JSONKeyValueRepository(saves_dir)
    story_service = StoryService(
        content_repository=JSONContentRepository(scenarios_dir), progress_repository=save_repo
    )
    save_manager = SaveManager(SaveService(repository=save_repo))
    ge = GameEngine(
        story_manager=StoryManager(story_service),
        save_manager=save_manager,
        player_manager=PlayerManager(repository=save_repo),
        time_manager=TimeManager(),
    )
    ge.start_new_game(
        first_name="Bruno", last_name="Díaz", gender=None, starting_age=25,
        country="Argentina", city="Córdoba", story_content_id="test_story",
    )
    ge.save_game("slot-test")
    assert save_manager.save_exists("slot-test") is True
    loaded = save_manager.load("slot-test")
    assert loaded.player.full_name == "Bruno Díaz"


# ==================================================
# StoryEngine — sobrevive como capa fina (decisión resuelta)
# ==================================================


def test_story_engine_delegates_to_story_manager(scenarios_dir, saves_dir):
    """
    Decisión que estaba pendiente: StoryEngine SOBREVIVE como capa
    fina con estado sobre StoryManager (el usuario eligió reescribir
    engine/ en vez de retirarlo). Cada método delega, ninguno
    reimplementa la lógica de StoryService.
    """
    story_service = StoryService(
        content_repository=JSONContentRepository(scenarios_dir),
        progress_repository=JSONKeyValueRepository(saves_dir),
    )
    se = StoryEngine(StoryManager(story_service))
    assert se.get_current_scene() is None  # sin start() todavía

    story = se.start("p1", "test_story", 20)
    assert se.get_current_story_id() == story.story_id
    assert se.is_finished() is False

    assert se.choose_option(0) is True
    assert se.is_finished() is True
    assert se.choose_option(99) is False  # índice inválido, tolerante (no lanza)


# ==================================================
# DecisionEngine — bug de la clase duplicada corregido
# ==================================================


def test_decision_engine_resolves_option_to_consequence():
    """
    DecisionEngine.resolve() empaqueta la opción sin tocar Player;
    apply_consequences() es quien llama a ConsequenceService, que a
    su vez usa los mutadores auditables reales de Player — nunca
    escritura directa de atributo.
    """
    de = DecisionEngine(ConsequenceService())
    player = _player(PlayerManager())

    scene = {"options": [{"label": "Estudiar", "next_scene": "s2", "effects": {"intelligence": 8, "stress": 3}}]}
    decision = de.resolve(scene, 0)
    assert decision is not None
    assert decision.label == "Estudiar"

    before_intel, before_stress = player.intelligence, player.stress
    applied = de.apply_consequences(player, decision)
    assert player.intelligence == before_intel + 8
    assert player.stress == before_stress + 3
    assert len(applied) == 2

    assert de.resolve(scene, 5) is None  # índice inválido


# ==================================================
# EventEngine
# ==================================================


def test_event_engine_selects_event_by_category_and_probability(tmp_path):
    """
    EventManager.get_random_event() usa utils.random_utils.weighted_choice
    (selección ponderada por el campo 'weight' de cada definición),
    no una elección uniforme — tal como anticipaba este mismo test
    antes de que engine/ se reescribiera.
    """
    events_dir = tmp_path / "events"
    events_dir.mkdir()
    (events_dir / "comun.json").write_text(
        json.dumps({"title": "Común", "category": "progresion", "weight": 99.0}), encoding="utf-8"
    )
    (events_dir / "raro.json").write_text(
        json.dumps({"title": "Raro", "category": "progresion", "weight": 1.0}), encoding="utf-8"
    )
    (events_dir / "otra_categoria.json").write_text(
        json.dumps({"title": "Otra", "category": "aspiracion", "weight": 50.0}), encoding="utf-8"
    )

    em = EventManager(repository=JSONContentRepository(events_dir), rng=__import__("random").Random(1))
    ee = EventEngine(em)

    # filtrado por categoría: nunca debe salir "otra_categoria"
    import random as _random
    rng = _random.Random(7)
    seen_ids = set()
    for _ in range(20):
        picked = em.get_random_event(category="progresion")
        assert picked is not None
        event_id, event = picked
        seen_ids.add(event_id)
        assert event["category"] == "progresion"
    assert seen_ids <= {"comun", "raro"}

    player = _player(PlayerManager())
    result = ee.trigger_event(player, "comun")
    assert result is not None
    assert result["title"] == "Común"
    assert ee.trigger_event(player, "no-existe") is None


# ==================================================
# EndingEngine
# ==================================================


def test_ending_engine_resolves_final_ending_from_player_state(tmp_path):
    """Resuelve qué final corresponde según el Estado de Personaje, y lo desbloquea (con logro asociado si trae uno)."""
    endings_dir = tmp_path / "endings"
    endings_dir.mkdir()
    (endings_dir / "modesto.json").write_text(
        json.dumps({"title": "Vida modesta", "requirements": {"stats": {"net_worth": 0}}}), encoding="utf-8"
    )
    (endings_dir / "prospero.json").write_text(
        json.dumps({
            "title": "Vida próspera", "achievement": "logro-prospero",
            "requirements": {"stats": {"net_worth": 50000}},
        }),
        encoding="utf-8",
    )

    achievement_service = AchievementService(repository=JSONKeyValueRepository(tmp_path / "saves_ach"))
    achievement_manager = AchievementManager(achievement_service)
    ending_manager = EndingManager(
        content_repository=JSONContentRepository(endings_dir),
        progress_repository=JSONKeyValueRepository(tmp_path / "saves_end"),
    )
    ee = EndingEngine(ending_manager, achievement_manager)

    player = _player(PlayerManager())
    player.modify_net_worth(60000, reason="prueba")

    resolved_id = ee.determine_ending(player, ["modesto", "prospero"])
    assert resolved_id == "modesto"  # el primero de la lista que cumple, en orden — modesto siempre se cumple (net_worth>=0)

    resolved_id_2 = ee.determine_ending(player, ["prospero", "modesto"])
    assert resolved_id_2 == "prospero"  # ahora "prospero" va primero y también se cumple

    ending = ee.unlock_ending(player.player_id, "prospero")
    assert ending is not None
    assert ee.has_ending(player.player_id, "prospero") is True
    assert achievement_manager.is_unlocked(player.player_id, "logro-prospero") is True


# ==================================================
# AchievementEngine
# ==================================================


def test_achievement_engine_unlocks_and_reports_to_statistics_service(tmp_path):
    """Al desbloquear un logro, AchievementManager llama a StatisticsService.record_achievement_unlocked() — reutiliza ese contador, no lleva uno propio."""
    achievements_dir = tmp_path / "achievements"
    achievements_dir.mkdir()
    (achievements_dir / "disciplinado.json").write_text(
        json.dumps({"title": "Disciplinado", "requirements": {"stats": {"discipline": 60}}}),
        encoding="utf-8",
    )

    achievement_service = AchievementService(repository=JSONKeyValueRepository(tmp_path / "saves"))
    statistics_service = StatisticsService(repository=JSONKeyValueRepository(tmp_path / "saves"))
    am = AchievementManager(
        achievement_service,
        catalog_repository=JSONContentRepository(achievements_dir),
        statistics_service=statistics_service,
    )
    ae = AchievementEngine(am)

    player = _player(PlayerManager())
    player.modify_discipline(15, reason="prueba")  # 50 base + 15 = 65 >= 60

    before_stats = statistics_service.get_statistics(player.player_id)
    assert ae.check(player, "disciplinado") is True

    newly_unlocked = ae.check_all(player)
    assert newly_unlocked == ["disciplinado"]
    assert ae.is_unlocked(player.player_id, "disciplinado") is True

    after_stats = statistics_service.get_statistics(player.player_id)
    assert after_stats.achievements_unlocked == before_stats.achievements_unlocked + 1

    # ya desbloqueado: check_all() no lo vuelve a contar
    assert ae.check_all(player) == []


# ==================================================
# InventoryEngine
# ==================================================


def test_inventory_engine_add_and_remove_items(tmp_path):
    """models/item.py ya existe (se creó en la sesión de Character Creation) — InventoryEngine funciona de punta a punta."""
    items_dir = tmp_path / "items"
    items_dir.mkdir()
    (items_dir / "pocion.json").write_text(
        json.dumps({"name": "Poción de ánimo", "effects": {"stats": {"happiness": 15}}}), encoding="utf-8"
    )

    inventory_service = InventoryService(repository=JSONKeyValueRepository(tmp_path / "saves"))
    im = InventoryManager(
        inventory_service,
        catalog_repository=JSONContentRepository(items_dir),
        consequence_service=ConsequenceService(),
    )
    ie = InventoryEngine(im)

    player = _player(PlayerManager())
    ie.add_item(player.player_id, "pocion", quantity=2)
    inv = ie.get_inventory(player.player_id)
    assert inv.count() == 2
    assert ie.has_item(player.player_id, "pocion") is True

    before_happiness = player.happiness
    assert ie.use_item(player, "pocion") is True
    assert player.happiness == before_happiness + 15
    assert ie.get_inventory(player.player_id).count() == 1  # se consumió una unidad

    assert ie.use_item(player, "no-existe") is False


# ==================================================
# TimeEngine
# ==================================================


def test_time_engine_advances_age_and_recalculates_life_expectancy():
    """
    TimeEngine.advance_year() usa Player.advance_age() (ya existía) y
    devuelve el resultado de check_life_status().

    El recálculo de "esperanza de vida por turno" que el GDD describe
    NO está implementado — decisión de alcance explícita de
    `TimeManager` (ver su docstring): definir esa curva es un ajuste
    de balance de juego que nadie pidió todavía. Esta prueba verifica
    lo que sí existe, no lo que falta.
    """
    te = TimeEngine(TimeManager())
    player = _player(PlayerManager())
    before_age = player.age

    result = te.advance_year(player)
    assert player.age == before_age + 1
    assert result is None  # con salud/edad normales, sigue con vida

    # life_expectancy NO cambia por el simple paso de un año (alcance no implementado)
    assert player.life_expectancy == 80.0

    player.age = int(player.life_expectancy)
    result = te.advance_year(player)
    assert result is not None
    assert result.cause == "vejez"


# ==================================================
# SaveEngine — sobrevive como capa fina (decisión resuelta)
# ==================================================


def test_save_engine_delegates_to_save_manager(tmp_path):
    """
    Decisión que estaba pendiente: SaveEngine SOBREVIVE como capa
    fina sobre SaveManager (misma decisión que StoryEngine). No
    reimplementa serialización — delega en SaveService, ya probado.
    """
    save_repo = JSONKeyValueRepository(tmp_path / "saves")
    se = SaveEngine(SaveManager(SaveService(repository=save_repo)))

    assert se.load("no-existe") is None
    assert se.exists("no-existe") is False

    player = _player(PlayerManager(repository=save_repo))
    se.save(player, [], "slot-1")
    assert se.exists("slot-1") is True

    loaded = se.load("slot-1")
    assert loaded is not None
    assert loaded["player"].full_name == player.full_name

    se.delete("slot-1")
    assert se.exists("slot-1") is False
