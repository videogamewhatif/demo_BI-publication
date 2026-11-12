"""
tests/test_ai.py
=================

Qué hace:
    Pruebas de los 5 archivos de `ai/`: `AIManager` (selección de
    proveedor), `PromptBuilder` (ensamblado de prompts),
    `Memory`/`MemoryEvent` (memoria de la partida), `NPCPersonality`/
    `NPCState`/`NPCAI` (comportamiento de NPC), y `StoryGenerator`
    (que combina los tres primeros para producir texto narrativo).

    De los cuatro módulos de esta entrega, `ai/` es el único que ya
    funcionaba de forma completamente aislada en el análisis inicial
    del proyecto — por eso es el único, junto con `story`/`save`,
    para el que tiene sentido escribir pruebas reales ahora mismo
    (ver la nota sobre `test_engine.py` en el análisis).

Cómo funciona:
    No se prueban `_openai_response`/`_claude_response` más allá de
    confirmar que lanzan `NotImplementedError`: son proveedores
    reales pendientes de credenciales, no código que se pueda
    ejercitar sin red (mismo criterio que se usó con
    `OpenAIImageProvider` en `services/image_service.py`).

Dependencias:
    - pytest.
    - ai.ai_manager, ai.prompt_builder, ai.memory, ai.npc_ai, ai.story_generator.

Autor: Korlo
"""

from __future__ import annotations

import pytest

from ai.ai_manager import AIManager
from ai.memory import Memory, MemoryEvent
from ai.npc_ai import NPCAI, NPCPersonality
from ai.prompt_builder import PromptBuilder
from ai.story_generator import StoryGenerator


# ==================================================
# FIXTURES
# ==================================================


@pytest.fixture
def ai_manager():
    return AIManager()


@pytest.fixture
def prompt_builder():
    return PromptBuilder()


@pytest.fixture
def memory():
    return Memory()


@pytest.fixture
def story_generator(ai_manager, prompt_builder, memory):
    return StoryGenerator(ai_manager=ai_manager, prompt_builder=prompt_builder, memory=memory)


# ==================================================
# AIManager
# ==================================================


def test_ai_manager_default_state(ai_manager):
    assert ai_manager.is_enabled() is True
    assert ai_manager.provider == "local"


def test_ai_manager_local_provider_echoes_prompt(ai_manager):
    response = ai_manager.generate_response("Hola mundo")
    assert response == "[LOCAL AI] Hola mundo"


def test_ai_manager_disabled_returns_empty_string(ai_manager):
    ai_manager.disable()
    assert ai_manager.is_enabled() is False
    assert ai_manager.generate_response("cualquier cosa") == ""


def test_ai_manager_enable_re_enables(ai_manager):
    ai_manager.disable()
    ai_manager.enable()
    assert ai_manager.is_enabled() is True
    assert ai_manager.generate_response("x") == "[LOCAL AI] x"


def test_ai_manager_openai_provider_not_implemented(ai_manager):
    ai_manager.set_provider("openai")
    with pytest.raises(NotImplementedError):
        ai_manager.generate_response("x")


def test_ai_manager_claude_provider_not_implemented(ai_manager):
    ai_manager.set_provider("claude")
    with pytest.raises(NotImplementedError):
        ai_manager.generate_response("x")


def test_ai_manager_unknown_provider_returns_message(ai_manager):
    ai_manager.set_provider("proveedor-inventado")
    assert ai_manager.generate_response("x") == "Proveedor de IA no reconocido."


# ==================================================
# PromptBuilder
# ==================================================


def test_prompt_builder_minimal_prompt_contains_core_fields(prompt_builder):
    prompt = prompt_builder.build(
        player_name="Lucía",
        story_title="El primer empleo",
        current_scene="entrevista",
    )
    assert "Lucía" in prompt
    assert "El primer empleo" in prompt
    assert "entrevista" in prompt


def test_prompt_builder_includes_objective_only_when_given(prompt_builder):
    with_objective = prompt_builder.build(
        player_name="Lucía", story_title="Arco", current_scene="x", objective="Conseguir el ascenso",
    )
    without_objective = prompt_builder.build(
        player_name="Lucía", story_title="Arco", current_scene="x",
    )
    assert "Conseguir el ascenso" in with_objective
    assert "Objetivo:" not in without_objective


def test_prompt_builder_includes_inventory(prompt_builder):
    prompt = prompt_builder.build(
        player_name="Lucía", story_title="Arco", current_scene="x",
        inventory=["diploma", "llaves del auto"],
    )
    assert "diploma" in prompt
    assert "llaves del auto" in prompt


def test_prompt_builder_includes_variables(prompt_builder):
    prompt = prompt_builder.build(
        player_name="Lucía", story_title="Arco", current_scene="x",
        variables={"salud": 80, "estres": 20},
    )
    assert "salud: 80" in prompt
    assert "estres: 20" in prompt


def test_prompt_builder_history_truncates_to_last_ten(prompt_builder):
    history = [f"evento {i}" for i in range(15)]
    prompt = prompt_builder.build(
        player_name="Lucía", story_title="Arco", current_scene="x", history=history,
    )
    assert "evento 14" in prompt  # el más reciente sí aparece
    assert "evento 4" not in prompt  # los primeros 5 quedaron fuera de los últimos 10
    assert "evento 5" in prompt  # el décimo desde el final sí aparece


def test_prompt_builder_includes_user_input(prompt_builder):
    prompt = prompt_builder.build(
        player_name="Lucía", story_title="Arco", current_scene="x", user_input="Acepto el trabajo",
    )
    assert "Acepto el trabajo" in prompt


def test_prompt_builder_system_prompt_get_set(prompt_builder):
    original = prompt_builder.build_system_prompt()
    assert "narrador" in original.lower()

    prompt_builder.set_system_prompt("Nuevo prompt de sistema")
    assert prompt_builder.build_system_prompt() == "Nuevo prompt de sistema"


def test_prompt_builder_add_rule_appends():
    builder = PromptBuilder()
    before = builder.build_system_prompt()
    builder.add_rule("Nunca reveles el final de antemano")
    after = builder.build_system_prompt()
    assert after.startswith(before)
    assert "Nunca reveles el final de antemano" in after


# ==================================================
# Memory / MemoryEvent
# ==================================================


def test_memory_add_and_get_recent_events(memory):
    for i in range(5):
        memory.add_event(MemoryEvent(id=f"e{i}", description=f"Evento {i}"))
    recent = memory.get_recent_events(limit=3)
    assert [e.id for e in recent] == ["e2", "e3", "e4"]


def test_memory_get_important_events_filters_by_importance(memory):
    memory.add_event(MemoryEvent(id="e1", description="menor", importance=3))
    memory.add_event(MemoryEvent(id="e2", description="mayor", importance=9))
    important = memory.get_important_events(minimum_importance=7)
    assert [e.id for e in important] == ["e2"]


def test_memory_variables(memory):
    assert memory.get_variable("inexistente") is None
    assert memory.get_variable("inexistente", default="x") == "x"
    memory.set_variable("salud", 80)
    assert memory.get_variable("salud") == 80


def test_memory_relationships(memory):
    assert memory.get_relationship("npc-1") == 0
    memory.set_relationship("npc-1", 10)
    assert memory.get_relationship("npc-1") == 10
    memory.modify_relationship("npc-1", 5)
    assert memory.get_relationship("npc-1") == 15
    memory.modify_relationship("npc-2", -5)  # no existía; parte de 0
    assert memory.get_relationship("npc-2") == -5


def test_memory_facts(memory):
    assert memory.recall("nombre_madre") is None
    memory.remember("nombre_madre", "Marta")
    assert memory.recall("nombre_madre") == "Marta"


def test_memory_to_dict_from_dict_roundtrip(memory):
    memory.add_event(MemoryEvent(id="e1", description="Graduación", importance=8, chapter="cap1", tags=["logro"]))
    memory.set_variable("salud", 90)
    memory.set_relationship("npc-1", 20)
    memory.remember("secreto", "Sabe tocar el piano")

    data = memory.to_dict()
    restored = Memory.from_dict(data)

    assert restored.to_dict() == data
    assert restored.events[0].id == "e1"
    assert restored.get_relationship("npc-1") == 20
    assert restored.recall("secreto") == "Sabe tocar el piano"


# ==================================================
# NPCAI / NPCPersonality / NPCState
# ==================================================


def test_npc_personality_defaults():
    personality = NPCPersonality()
    assert personality.bravery == 50
    assert personality.kindness == 50


def test_npc_ai_initial_state():
    npc = NPCAI(npc_id="npc-1", name="Marta", personality=NPCPersonality())
    assert npc.get_relationship() == 0
    assert npc.state.mood == "neutral"
    assert npc.state.goals == []


def test_npc_ai_relationship_changes():
    npc = NPCAI(npc_id="npc-1", name="Marta", personality=NPCPersonality())
    npc.change_relationship(10)
    npc.change_relationship(-3)
    assert npc.get_relationship() == 7


def test_npc_ai_mood_and_location():
    npc = NPCAI(npc_id="npc-1", name="Marta", personality=NPCPersonality())
    npc.set_mood("feliz")
    npc.set_location("cocina")
    assert npc.state.mood == "feliz"
    assert npc.state.location == "cocina"


def test_npc_ai_goals_no_duplicates():
    npc = NPCAI(npc_id="npc-1", name="Marta", personality=NPCPersonality())
    npc.add_goal("cuidar el jardín")
    npc.add_goal("cuidar el jardín")
    assert npc.state.goals == ["cuidar el jardín"]
    npc.remove_goal("cuidar el jardín")
    assert npc.state.goals == []
    npc.remove_goal("no-estaba")  # no debe fallar


@pytest.mark.parametrize(
    "personality_kwargs, relationship, expected_action",
    [
        ({"aggression": 90}, 0, "attack"),
        ({"kindness": 90}, 0, "help"),
        ({"curiosity": 80}, 0, "investigate"),
        ({}, 60, "support"),
        ({}, -60, "ignore"),
        ({}, 0, "observe"),
        # La agresividad tiene prioridad sobre la amabilidad si ambas son altas:
        ({"aggression": 90, "kindness": 90}, 0, "attack"),
    ],
)
def test_npc_ai_decide_action_priority(personality_kwargs, relationship, expected_action):
    npc = NPCAI(npc_id="npc-1", name="Marta", personality=NPCPersonality(**personality_kwargs))
    npc.state.relationship = relationship
    assert npc.decide_action("cualquier acción del jugador") == expected_action


def test_npc_ai_build_context_shape():
    npc = NPCAI(npc_id="npc-1", name="Marta", personality=NPCPersonality())
    npc.set_mood("feliz")
    npc.add_goal("aprender a tejer")
    context = npc.build_context()

    assert context["npc_id"] == "npc-1"
    assert context["name"] == "Marta"
    assert context["mood"] == "feliz"
    assert context["goals"] == ["aprender a tejer"]
    assert context["personality"]["bravery"] == 50


# ==================================================
# StoryGenerator
# ==================================================


def test_story_generator_generate_scene_includes_context(story_generator, memory):
    memory.add_event(MemoryEvent(id="e1", description="Conoció a su jefe"))
    response = story_generator.generate_scene(
        player_name="Lucía",
        story_title="El primer empleo",
        current_scene="entrevista",
        objective="Conseguir el ascenso",
        inventory=["diploma"],
        variables={"estres": 30},
    )
    # El AIManager local hace eco del prompt completo -> puede
    # inspeccionarse el contenido para confirmar que se ensambló bien.
    assert response.startswith("[LOCAL AI]")
    assert "Lucía" in response
    assert "El primer empleo" in response
    assert "diploma" in response
    assert "Conoció a su jefe" in response  # viene de la memoria


def test_story_generator_generate_dialogue(story_generator):
    response = story_generator.generate_dialogue(
        npc_name="Marta", player_input="¿Cómo estás?", context="Es la madre del jugador.",
    )
    assert response.startswith("[LOCAL AI]")
    assert "Marta" in response
    assert "¿Cómo estás?" in response


def test_story_generator_generate_event(story_generator):
    response = story_generator.generate_event("El jugador acaba de graduarse.")
    assert response.startswith("[LOCAL AI]")
    assert "graduarse" in response


def test_story_generator_generate_item_description(story_generator):
    response = story_generator.generate_item_description("reloj de bolsillo")
    assert response.startswith("[LOCAL AI]")
    assert "reloj de bolsillo" in response


def test_story_generator_propagates_disabled_ai_manager(story_generator, ai_manager):
    ai_manager.disable()
    assert story_generator.generate_event("cualquier cosa") == ""