#!/usr/bin/env python3
"""
tools/validate_scenario.py
=============================

CLI para el equipo de diseño: valida uno o más archivos de contenido
narrativo antes de que lleguen a `data/scenarios/` en producción.

Uso:
    python tools/validate_scenario.py data/scenarios/mi_historia.json
    python tools/validate_scenario.py data/scenarios/*.json
    python tools/validate_scenario.py --all      # valida todo data/scenarios/

Código de salida: 0 si no hay ERRORES (puede haber warnings), 1 si
hay al menos un ERROR — pensado para poder usarse en un hook de
pre-commit o en CI el día que el proyecto tenga alguno.

Autor: Korlo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.paths import SCENARIOS_DIR  # noqa: E402
from tools.scenario_validator import has_errors, validate_scenario_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida contenido narrativo de What If?")
    parser.add_argument("files", nargs="*", help="Archivos .json a validar")
    parser.add_argument(
        "--all", action="store_true", help=f"Valida todos los .json de {SCENARIOS_DIR}"
    )
    args = parser.parse_args()

    if args.all:
        paths = sorted(SCENARIOS_DIR.glob("*.json"))
        if not paths:
            print(f"No hay archivos .json en {SCENARIOS_DIR}.")
            return 0
    elif args.files:
        paths = [Path(f) for f in args.files]
    else:
        parser.print_help()
        return 1

    any_errors = False
    for path in paths:
        issues = validate_scenario_file(path)
        print(f"\n=== {path} ===")
        if not issues:
            print("  Sin problemas.")
            continue
        for issue in issues:
            print(f"  {issue}")
        if has_errors(issues):
            any_errors = True

    print()
    if any_errors:
        print("Resultado: hay ERRORES — este contenido rompería el juego tal cual está.")
        return 1
    print("Resultado: sin errores (puede haber warnings arriba, revísalos igual).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
