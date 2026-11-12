"""
services/consequence_service.py
==================================

Qué hace:
    El Sistema de Consecuencias que `VITA_Game_Design_Document.md`
    (§5) describe como "el único sistema con permiso de escritura
    sobre el EP [Estado de Personaje]". No existía ni como esqueleto
    — ni siquiera en el `engine/` roto había un `consequence_engine.py`.

    `apply_effects(player, effects, reason)` es el único punto de
    entrada: recibe un diccionario `{atributo: delta}` y aplica cada
    uno usando el mutador auditable correspondiente de `Player`
    (`modify_health()`, etc.) — nunca escribe un atributo
    directamente (`player.health = ...`), que es justo lo que el GDD
    prohíbe hacer fuera de este sistema.

    Este servicio es agnóstico de historia: no sabe qué es una
    `Story` ni una escena. El primer (y hoy único) consumidor es
    `ui/screens/story_panel.py`, que lee el campo `effects` de la
    opción elegida y se lo pasa — pero cualquier futuro sistema
    (eventos, uso de objetos, logros con recompensa en stats) puede
    llamarlo igual.

Alcance deliberadamente limitado — solo atributos con mutador de
tipo delta (léase antes de ampliar esta lista):
    `VALID_EFFECT_KEYS` cubre los 10 atributos 0-100/-100..100 más
    `net_worth`, porque todos comparten la misma forma
    `modify_x(amount, reason)` — sumar/restar un delta. `annual_income`
    (`set_annual_income`, fija un valor absoluto) y `debt`
    (`add_debt`/`reduce_debt`, dos verbos distintos para el mismo
    campo) NO están incluidos: mezclarlos en un diccionario plano de
    deltas habría sido ambiguo (¿el número es un delta o un valor
    absoluto?). Si hace falta cubrirlos, es una extensión aparte con
    su propia decisión de formato, no una ampliación silenciosa de
    esta lista.

Cómo se define un efecto en el contenido narrativo:
    En `data/scenarios/*.json`, cada opción puede traer un campo
    `effects` opcional:

        {"label": "...", "next_scene": "...", "effects": {"happiness": -5, "discipline": 3}}

    Documentado en `docs/content_authoring_guide.md`. Validado
    estructuralmente por `tools/scenario_validator.py` (claves
    válidas, valores numéricos) antes de que llegue a producción.

Autor: Korlo
"""

from __future__ import annotations

import logging
from typing import Dict, List, Union

from models.player import Player

logger = logging.getLogger(__name__)

Number = Union[int, float]

# Cada clave debe tener un mutador `modify_<clave>(amount, reason)`
# real en Player — ver la nota de alcance arriba sobre por qué
# net_worth entra y annual_income/debt no.
VALID_EFFECT_KEYS = frozenset({
    "health", "appearance",
    "intelligence", "discipline", "creativity",
    "stress", "happiness",
    "charisma", "empathy",
    "reputation",
    "net_worth",
})


class InvalidEffectsError(Exception):
    """El diccionario de efectos tiene una clave desconocida o un valor no numérico."""


class ConsequenceService:
    """
    El único sistema autorizado a modificar el Estado de Personaje.
    Sin estado propio — opera directamente sobre el `Player` que se
    le pase, que quien lo llame es responsable de persistir después
    (ver `ui/screens/story_panel.py` + `GameplayScreen`, que ya
    guardan tras cada decisión).
    """

    # Mapeo clave de efecto -> nombre del mutador real en Player.
    # Todas siguen el patrón modify_<attr>(amount, reason) excepto
    # ninguna aquí — si algún día una no lo sigue, no pertenece a
    # VALID_EFFECT_KEYS (ver docstring del módulo).
    _MUTATOR_NAMES: Dict[str, str] = {key: f"modify_{key}" for key in VALID_EFFECT_KEYS}

    def apply_effects(
        self, player: Player, effects: Dict[str, Number], reason: str
    ) -> List[str]:
        """
        Aplica cada `{atributo: delta}` de `effects` sobre `player`
        usando su mutador auditable correspondiente. Devuelve una
        lista de descripciones legibles de lo aplicado (para logging
        o para mostrarle un resumen al jugador más adelante, si hace
        falta).

        No hace nada si `effects` está vacío o es `None` — la
        mayoría de las opciones de historia hoy no tienen `effects`
        todavía, y eso es válido: simplemente no cambia nada.

        Raises:
            InvalidEffectsError: si alguna clave no está en
                `VALID_EFFECT_KEYS`, o algún valor no es numérico.
                Se valida TODO antes de aplicar nada, para no dejar
                a `player` a medio modificar si el diccionario tiene
                un error a mitad de camino.
        """
        if not effects:
            return []

        self._validate(effects)

        applied: List[str] = []
        for attr, delta in effects.items():
            mutator = getattr(player, self._MUTATOR_NAMES[attr])
            before = getattr(player, attr)
            mutator(delta, reason)
            after = getattr(player, attr)
            applied.append(f"{attr}: {before} -> {after} (delta pedido: {delta:+g})")

        logger.info(
            "ConsequenceService: aplicados %d efecto(s) a %s (%s). Razón: %s",
            len(applied), player.player_id, "; ".join(applied), reason,
        )
        return applied

    @staticmethod
    def _validate(effects: Dict[str, Number]) -> None:
        unknown = set(effects) - VALID_EFFECT_KEYS
        if unknown:
            raise InvalidEffectsError(
                f"Claves de efecto desconocidas: {sorted(unknown)}. "
                f"Válidas: {sorted(VALID_EFFECT_KEYS)}."
            )
        non_numeric = {k: v for k, v in effects.items() if not isinstance(v, (int, float))}
        if non_numeric:
            raise InvalidEffectsError(
                f"Valores de efecto no numéricos: {non_numeric}."
            )
