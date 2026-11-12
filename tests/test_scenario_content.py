"""
tests/test_scenario_content.py
=================================

Qué hace:
    Valida automáticamente, en cada corrida de `pytest`, TODOS los
    archivos `.json` de `data/scenarios/` con
    `tools/scenario_validator.py` — para que un error de contenido
    narrativo (una escena inexistente, un final sin salida) se
    detecte en CI/al correr los tests, no cuando un jugador llegue a
    ese punto exacto de la historia.

    No valida la CALIDAD de la escritura (eso no es evaluable por
    código) — solo la ESTRUCTURA: que el JSON sea válido, que las
    referencias entre escenas existan, que toda historia pueda
    terminar.

Cómo funciona:
    `pytest.mark.parametrize` sobre cada archivo real de
    `data/scenarios/` — si mañana hay 20 historias, cada una aparece
    como su propio caso de prueba con nombre propio, no como un solo
    test genérico que dice "algo falló en algún archivo".

Autor: Korlo
"""

import pytest

from config.paths import SCENARIOS_DIR
from tools.scenario_validator import has_errors, validate_scenario_file

_SCENARIO_FILES = sorted(SCENARIOS_DIR.glob("*.json")) if SCENARIOS_DIR.is_dir() else []


@pytest.mark.parametrize(
    "scenario_path", _SCENARIO_FILES, ids=[p.name for p in _SCENARIO_FILES]
)
def test_scenario_has_no_structural_errors(scenario_path):
    """Ningún archivo de data/scenarios/ debe tener ERRORES (los warnings no fallan el test)."""
    issues = validate_scenario_file(scenario_path)
    errors = [i for i in issues if i.level == "error"]
    assert not errors, (
        f"{scenario_path.name} tiene {len(errors)} error(es):\n"
        + "\n".join(f"  - {e}" for e in errors)
    )


def test_at_least_one_scenario_exists():
    """
    Si esto falla, `data/scenarios/` está vacía — que es honesto hoy
    (solo tiene el fixture de desarrollo), pero el test existe para
    que el día que se borre `example_ui_fixture.json` sin haber
    puesto contenido real todavía, quede claro por qué no hay nada
    que parametrizar arriba, en vez de que la ausencia pase
    silenciosa.
    """
    assert _SCENARIO_FILES, (
        f"No hay ningún archivo .json en {SCENARIOS_DIR} — StoryService "
        f"no tiene ninguna historia que pueda arrancar."
    )
