"""
tools/scenario_validator.py
==============================

Qué hace:
    Valida un archivo de contenido narrativo
    (`data/scenarios/<id>.json`) contra el esquema real que
    `services/story_service.py` espera — verificado línea por línea
    contra ese archivo, no adivinado. Pensado para que quien escriba
    historias (equipo de diseño) detecte errores ANTES de que el
    juego los encuentre en tiempo de ejecución.

Por qué existe, más allá de lo que ya valida `StoryService`:
    `StoryService._validate_content()` solo comprueba 3 cosas:
    que existan `title`/`start_scene`/`scenes`, y que `start_scene`
    esté en `scenes`. Todo lo demás (`next_scene` apuntando a una
    escena que no existe, escenas sin salida que no son un final,
    escenas nunca alcanzables, ningún final alcanzable desde el
    inicio) NO se valida ahí — se descubre recién cuando un jugador
    llega a ese punto concreto y el juego lanza un `KeyError` o se
    queda atascado. Este módulo adelanta esos errores al momento de
    escribir el contenido, no al de jugarlo.

Dos niveles de aviso:
    - ERROR: el contenido rompería el juego tal cual está (falta una
      clave obligatoria, `next_scene` apunta a una escena
      inexistente, `next_scene` falta por completo en una opción,
      `effects` usa una clave que `ConsequenceService` no reconoce o
      un valor no numérico).
    - WARNING: el contenido funcionaría, pero probablemente no es lo
      que se quería (una escena nunca se puede alcanzar, una escena
      sin opciones que no está marcada como final, un final sin
      `ending_id` propio, ningún final alcanzable desde el inicio).

Cómo se usa:
    - Como script: `python tools/validate_scenario.py data/scenarios/mi_historia.json`
    - Como test automático: `tests/test_scenario_content.py` valida
      TODOS los archivos de `data/scenarios/` en cada corrida de pytest.
    - Programáticamente: `validate_scenario_file(path)` devuelve una
      lista de `Issue`.

Autor: Korlo
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Set

from models.memory_moment import VALID_MEMORY_CATEGORIES
from services.consequence_service import VALID_EFFECT_KEYS

# Mismas claves que services/story_service.py::_REQUIRED_CONTENT_KEYS —
# si esa constante cambia allá, hay que actualizarla aquí también.
REQUIRED_CONTENT_KEYS = {"title", "start_scene", "scenes"}


@dataclass
class Issue:
    """Un problema detectado en el contenido: nivel, dónde y qué."""

    level: str  # "error" | "warning"
    scene_id: str  # "" si el problema es del documento completo, no de una escena concreta
    message: str

    def __str__(self) -> str:
        location = f"[{self.scene_id}] " if self.scene_id else ""
        return f"{self.level.upper():7s} {location}{self.message}"


def validate_scenario_dict(content: Dict[str, Any], source_name: str = "") -> List[Issue]:
    """
    Valida un diccionario ya parseado (el resultado de `json.load()`).
    No toca disco — `validate_scenario_file()` es la versión que sí
    lee un archivo.
    """
    issues: List[Issue] = []

    # --- Claves obligatorias (igual que StoryService._validate_content) ---
    missing = REQUIRED_CONTENT_KEYS - content.keys()
    if missing:
        issues.append(Issue("error", "", f"Faltan claves obligatorias: {sorted(missing)}."))
        return issues  # sin esto no se puede seguir validando nada más

    scenes = content.get("scenes", {})
    if not isinstance(scenes, dict) or not scenes:
        issues.append(Issue("error", "", "'scenes' debe ser un objeto con al menos una escena."))
        return issues

    start_scene = content["start_scene"]
    if start_scene not in scenes:
        issues.append(
            Issue("error", "", f"'start_scene' ({start_scene!r}) no existe en 'scenes'.")
        )

    # --- Por escena: next_scene válido, forma correcta ---
    referenced: Set[str] = {start_scene} if start_scene in scenes else set()
    for scene_id, scene in scenes.items():
        if not isinstance(scene, dict):
            issues.append(Issue("error", scene_id, "La escena debe ser un objeto."))
            continue

        is_ending = bool(scene.get("ending", False))
        options = scene.get("options", [])

        if not isinstance(options, list):
            issues.append(Issue("error", scene_id, "'options' debe ser una lista."))
            options = []

        if not options and not is_ending:
            issues.append(
                Issue(
                    "warning", scene_id,
                    "No tiene opciones y no está marcada como final ('ending': true) "
                    "— el jugador se quedaría sin nada que hacer aquí.",
                )
            )

        if options and is_ending:
            issues.append(
                Issue(
                    "warning", scene_id,
                    "Está marcada como final pero además tiene opciones — "
                    "las opciones nunca se van a mostrar (StoryPanel oculta las "
                    "opciones cuando is_current_scene_ending() es True).",
                )
            )

        if is_ending and not scene.get("ending_id"):
            issues.append(
                Issue(
                    "warning", scene_id,
                    "Es un final sin 'ending_id' propio — StoryService le pondría "
                    "'ending-generic', lo que hace indistinguibles todos los finales "
                    "que caigan en ese caso.",
                )
            )

        for i, option in enumerate(options):
            if not isinstance(option, dict):
                issues.append(Issue("error", scene_id, f"La opción {i} debe ser un objeto."))
                continue
            if "next_scene" not in option:
                issues.append(
                    Issue(
                        "error", scene_id,
                        f"La opción {i} ({option.get('label', 'sin label')!r}) no tiene "
                        f"'next_scene' — StoryService.choose_option() lanzaría un "
                        f"KeyError en tiempo real si un jugador la elige.",
                    )
                )
                continue
            target = option["next_scene"]
            referenced.add(target)
            if target not in scenes:
                issues.append(
                    Issue(
                        "error", scene_id,
                        f"La opción {i} ({option.get('label', 'sin label')!r}) apunta a "
                        f"'{target}', que no existe en 'scenes'.",
                    )
                )
            if not option.get("label"):
                issues.append(
                    Issue("warning", scene_id, f"La opción {i} no tiene 'label' (texto del botón).")
                )

            effects = option.get("effects")
            if effects is not None:
                if not isinstance(effects, dict):
                    issues.append(
                        Issue("error", scene_id, f"La opción {i}: 'effects' debe ser un objeto {{atributo: delta}}.")
                    )
                else:
                    unknown_keys = set(effects) - VALID_EFFECT_KEYS
                    if unknown_keys:
                        issues.append(
                            Issue(
                                "error", scene_id,
                                f"La opción {i}: 'effects' usa claves no reconocidas "
                                f"{sorted(unknown_keys)} — válidas: {sorted(VALID_EFFECT_KEYS)}.",
                            )
                        )
                    non_numeric = {k: v for k, v in effects.items() if not isinstance(v, (int, float))}
                    if non_numeric:
                        issues.append(
                            Issue(
                                "error", scene_id,
                                f"La opción {i}: 'effects' tiene valores no numéricos: {non_numeric}.",
                            )
                        )

        if not scene.get("text"):
            issues.append(
                Issue("warning", scene_id, "No tiene 'text' — StoryPanel mostraría la escena vacía.")
            )

        memory_moment = scene.get("memory_moment")
        if memory_moment is not None:
            if not isinstance(memory_moment, dict) or not memory_moment.get("category"):
                issues.append(
                    Issue(
                        "warning", scene_id,
                        "'memory_moment' está presente pero no tiene 'category' — "
                        "MemoryManager no podría clasificar este Momento Clave.",
                    )
                )
            elif memory_moment["category"] not in VALID_MEMORY_CATEGORIES:
                issues.append(
                    Issue(
                        "warning", scene_id,
                        f"'memory_moment.category' ({memory_moment['category']!r}) no está en "
                        f"la lista curada del Vision Document — válidas: {sorted(VALID_MEMORY_CATEGORIES)}.",
                    )
                )

    # --- Escenas nunca alcanzables ---
    unreachable = set(scenes.keys()) - referenced
    for scene_id in sorted(unreachable):
        issues.append(
            Issue(
                "warning", scene_id,
                "Nunca se referencia desde 'start_scene' ni desde ningún 'next_scene' "
                "— contenido muerto, ningún jugador la va a ver.",
            )
        )

    # --- ¿Hay al menos un final alcanzable desde start_scene? ---
    if start_scene in scenes:
        reachable = _reachable_scenes(scenes, start_scene)
        has_reachable_ending = any(
            bool(scenes[sid].get("ending", False)) for sid in reachable if sid in scenes
        )
        if not has_reachable_ending:
            issues.append(
                Issue(
                    "warning", "",
                    "Desde 'start_scene' no se puede llegar a ninguna escena marcada "
                    "como final ('ending': true) — la historia nunca terminaría.",
                )
            )

    return issues


def _reachable_scenes(scenes: Dict[str, Any], start: str) -> Set[str]:
    """BFS simple sobre next_scene para saber qué escenas se pueden alcanzar desde `start`."""
    seen: Set[str] = set()
    frontier = [start]
    while frontier:
        current = frontier.pop()
        if current in seen or current not in scenes:
            continue
        seen.add(current)
        for option in scenes[current].get("options", []):
            if isinstance(option, dict) and "next_scene" in option:
                frontier.append(option["next_scene"])
    return seen


def validate_scenario_file(path: Path) -> List[Issue]:
    """Lee y valida un archivo JSON de contenido narrativo. Errores de parseo cuentan como Issue, no como excepción."""
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        return [Issue("error", "", f"No se pudo leer el archivo: {error}")]

    try:
        content = json.loads(raw)
    except json.JSONDecodeError as error:
        return [Issue("error", "", f"JSON inválido: {error}")]

    if not isinstance(content, dict):
        return [Issue("error", "", "El archivo debe contener un objeto JSON en la raíz.")]

    return validate_scenario_dict(content, source_name=path.name)


def has_errors(issues: List[Issue]) -> bool:
    """True si `issues` contiene al menos un problema de nivel 'error' (no solo warnings)."""
    return any(issue.level == "error" for issue in issues)
