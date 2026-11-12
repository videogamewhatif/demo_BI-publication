"""
config/game_config.py
========================

Qué hace:
    Parámetros de balance del juego que sí tienen un consumidor real
    o un propósito de referencia declarado — no una lista de todo lo
    que "podría" configurarse.

Por qué este archivo se redujo tanto (léase antes de añadir algo aquí):
    Antes de la sesión de consolidación de `config/`, este archivo
    tenía ~40 constantes: un sistema de dificultad completo
    (`EASY`/`NORMAL`/`HARD`/`NIGHTMARE`, con multiplicadores),
    probabilidades de eventos, tasas de economía, límites de
    guardado/historial, flags de IA y de desarrollo. Se verificó con
    grep, no se asumió: de todo eso, únicamente
    `RANDOM_DEATH_CHANCE_PER_YEAR` tenía un consumidor real
    (`managers/time_manager.py`). También había duplicados muertos
    de constantes que sí se usan pero desde otro archivo —
    `MIN_STAT`/`MAX_STAT`/`MIN_MONEY`/`MAX_MONEY` ya viven en
    `config/constant.py`, que es de donde `models.player.Player` los
    importa de verdad.

    El sistema de dificultad se borró por decisión explícita (no
    tenía ningún selector construido en `ui/` que lo usara). Los 4
    valores de impacto se conservaron a propósito, aunque tampoco
    tengan consumidor en código: sirven como referencia para quien
    escriba `effects` en `data/scenarios/*.json` (ver
    `docs/content_authoring_guide.md`), no para que el motor los lea.

Autor: Korlo (consolidado en la sesión de deuda técnica)
"""

# ==========================================================
# FIN DE VIDA (managers/time_manager.py)
# ==========================================================

# Probabilidad de fin de vida por accidente/enfermedad repentina en
# CADA decisión, independiente de salud o edad. "Muy baja pero no
# nula" — mismo orden de magnitud que las probabilidades de eventos
# especiales que tenía este archivo antes de consolidarse (borradas
# por falta de consumidor), no un valor inventado sin relación.
RANDOM_DEATH_CHANCE_PER_YEAR = 0.01

# ==========================================================
# VALORES DE IMPACTO DE REFERENCIA
# ==========================================================
# Sin consumidor en código — son una referencia para quien escriba
# el campo "effects" de una opción en data/scenarios/*.json (ver
# docs/content_authoring_guide.md), para no inventar magnitudes de
# la nada cada vez. No los aplica ni los valida
# tools/scenario_validator.py: cualquier número entra igual.

SMALL_IMPACT = 5
MEDIUM_IMPACT = 10
LARGE_IMPACT = 20
EXTREME_IMPACT = 40
