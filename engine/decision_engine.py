"""
engine/decision_engine.py
============================

Motor encargado de resolver una decisión — reescrito en la sesión de
"desbloquear engine/". Antes de esta sesión, este archivo tenía un
bug real: su docstring decía "story_engine.py" y definía una clase
`StoryEngine` duplicada, no una clase de decisiones (ver
`docs/architecture.md` §2, ya documentado antes de corregirlo aquí).

Qué hace de verdad:
    `VITA_Game_Design_Document.md` (§4) describe el Sistema de
    Decisiones como algo que "no modifica variables directamente;
    genera el objeto 'decision_tomada' que consume el Sistema de
    Consecuencias". Eso es literalmente lo que hace esta clase:
    `resolve()` empaqueta la opción elegida en un `DecisionMade`
    (sin tocar `Player`), y `apply_consequences()` es quien la pasa a
    `ConsequenceService` — el único con permiso de escribir en
    `Player` (GDD §5).

    Esta misma lógica ya vive, de forma más directa, en
    `ui/screens/story_panel.py::_apply_effects_if_any()` — este
    archivo la formaliza como un componente reutilizable de
    `engine/`, a costa de duplicar ese camino (decisión aceptada
    explícitamente para "desbloquear engine/", ver el changelog).

Autor: Korlo
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.player import Player
from services.consequence_service import ConsequenceService


@dataclass(frozen=True)
class DecisionMade:
    """El objeto 'decision_tomada' que describe el GDD — sin ningún efecto aplicado todavía."""

    label: str
    next_scene: str
    effects: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    """Resuelve una opción elegida en un `DecisionMade`, y opcionalmente aplica sus efectos."""

    def __init__(self, consequence_service: Optional[ConsequenceService] = None) -> None:
        self.consequence_service = consequence_service

    def resolve(self, scene: Dict[str, Any], option_index: int) -> Optional[DecisionMade]:
        """
        Empaqueta la opción `option_index` de `scene` en un
        `DecisionMade`. No modifica nada — solo lee. Devuelve None
        si el índice no es válido para esta escena.
        """
        options = scene.get("options", [])
        if not (0 <= option_index < len(options)):
            return None
        option = options[option_index]
        return DecisionMade(
            label=option.get("label", ""),
            next_scene=option.get("next_scene", ""),
            effects=option.get("effects", {}) or {},
        )

    def apply_consequences(
        self, player: Player, decision: DecisionMade, reason: Optional[str] = None
    ) -> List[str]:
        """
        Aplica `decision.effects` sobre `player` vía
        `ConsequenceService`. Sin `ConsequenceService` configurado, o
        sin efectos, no hace nada y devuelve una lista vacía.
        """
        if self.consequence_service is None or not decision.effects:
            return []
        return self.consequence_service.apply_effects(
            player, decision.effects, reason=reason or f"decisión: {decision.label}"
        )
