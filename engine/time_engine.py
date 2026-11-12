"""
engine/time_engine.py
========================

Motor encargado del paso del tiempo — reescrito en la sesión de
"desbloquear engine/" contra la API real de
`managers.time_manager.TimeManager`.

Diferencia importante con la versión original (léase antes de
extender este archivo):
    El `time_engine.py` de antes de esta sesión esperaba un
    calendario completo — `advance_minutes()`, `advance_hours()`,
    `get_datetime()`, `get_day()`, `get_month()`, `get_year()` — y
    eventos programados por fecha/hora. Nada de eso existe en el
    proyecto: `TimeManager` real solo cuenta años completos por
    decisión (`advance_time(player, years=1)`), sin granularidad
    menor. Esa parte del diseño original nunca se construyó (ni en
    `TimeManager` ni en ningún otro lado) — este archivo NO la
    inventa aquí tampoco, solo expone lo que sí existe de verdad.

Autor: Korlo
"""

from __future__ import annotations

from typing import Optional

from managers.time_manager import LifeEndResult, TimeManager
from models.player import Player


class TimeEngine:
    """Envoltorio delgado sobre TimeManager — avanza el tiempo y consulta el resultado de fin de vida."""

    def __init__(self, time_manager: TimeManager) -> None:
        self.time_manager = time_manager

    def advance_year(self, player: Player, years: int = 1) -> Optional[LifeEndResult]:
        """
        Avanza `years` años sobre `player` y comprueba de inmediato
        si la vida terminó. Devuelve el `LifeEndResult` si terminó,
        o None si `player` sigue con vida.
        """
        self.time_manager.advance_time(player, years)
        return self.time_manager.check_life_status(player)

    def get_age(self, player: Player) -> int:
        """La edad actual de `player` (dato real de `Player.age`, no propio de este motor)."""
        return player.age

    def check_life_status(self, player: Player) -> Optional[LifeEndResult]:
        """Comprueba fin de vida sin avanzar el tiempo — ver `TimeManager.check_life_status()`."""
        return self.time_manager.check_life_status(player)
