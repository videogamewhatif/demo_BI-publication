"""
managers/time_manager.py
===========================

Qué hace:
    Tercer manager de dominio — el "futuro Sistema de Edad" que
    `models.player.Player.advance_age()` ya menciona textualmente en
    su propio docstring desde antes de que este archivo existiera.
    Dos responsabilidades:

    1. `advance_time(player)`: avanza la edad. En esta primera
       versión, 1 año por decisión, sin que el contenido lo defina
       (decisión explícita: más simple que un campo `years_passed`
       por opción, que queda como posible extensión si hace falta
       más control narrativo del ritmo).
    2. `check_life_status(player)`: decide si la vida del personaje
       terminó, y por qué.

Motivos de fin de vida (se comprueban en este orden; el primero que
se cumple gana — no hay doble causa):
    1. "salud" — `player.is_alive` es False (`health` llegó a 0; el
       criterio ya existía en `Player`, no se reimplementa aquí).
    2. "vejez" — la edad alcanzó o superó `player.life_expectancy`.
    3. "accidente" / "enfermedad repentina" — una probabilidad baja
       pero no nula en CADA decisión
       (`config.game_config.RANDOM_DEATH_CHANCE_PER_YEAR`),
       independiente de salud o edad. Pedido explícitamente: "puede
       haber accidentes, enfermedades, etc... una muy baja
       probabilidad pero no nula".

Qué NO hace (alcance dejado fuera a propósito, no en silencio):
    El propio docstring de `Player.advance_age()` dice: "El
    recálculo real de salud/estrés por envejecimiento pertenece al
    futuro Sistema de Edad, no a este modelo (SRP)". Esta primera
    versión NO implementa esa curva de envejecimiento — la edad
    avanza pero no descuenta salud ni sube estrés automáticamente.
    Definir cuánto y a partir de qué edad es una decisión de balance
    de juego que no se pidió en esta sesión; se deja señalada aquí
    (`docs/roadmap.md`) en vez de inventarla sin que nadie la pidiera.

Autor: Korlo
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Optional

from config.game_config import RANDOM_DEATH_CHANCE_PER_YEAR
from models.player import Player

logger = logging.getLogger(__name__)

# Etiquetas de causa cuando el fin de vida es por la probabilidad
# aleatoria (no por salud ni por vejez, que tienen su propia etiqueta
# fija). Categórico, no texto narrativo — la pantalla de fin de vida
# decide cómo frasearlo.
RANDOM_DEATH_CAUSES = ("accidente", "enfermedad repentina")


@dataclass(frozen=True)
class LifeEndResult:
    """Por qué y a qué edad terminó una vida."""

    cause: str  # "salud" | "vejez" | uno de RANDOM_DEATH_CAUSES
    age_at_end: int


class TimeManager:
    """Avanza el tiempo del personaje y decide cuándo (y por qué) termina una vida."""

    def __init__(self, random_seed: Optional[int] = None) -> None:
        # random_seed solo para pruebas deterministas — en una
        # partida real se deja None (aleatorio de verdad).
        self._rng = random.Random(random_seed)

    def advance_time(self, player: Player, years: int = 1) -> None:
        """Avanza `years` años (1 por defecto). Usa el mutador real de Player, no reimplementa el incremento."""
        player.advance_age(years)

    def check_life_status(self, player: Player) -> Optional[LifeEndResult]:
        """
        Comprueba, en orden, las condiciones de fin de vida.
        Devuelve `None` si el personaje sigue con vida.
        """
        if not player.is_alive:
            logger.info("TimeManager: %s falleció por salud a los %d años.", player.player_id, player.age)
            return LifeEndResult(cause="salud", age_at_end=player.age)

        if player.age >= player.life_expectancy:
            logger.info("TimeManager: %s falleció de vejez a los %d años.", player.player_id, player.age)
            return LifeEndResult(cause="vejez", age_at_end=player.age)

        if self._rng.random() < RANDOM_DEATH_CHANCE_PER_YEAR:
            cause = self._rng.choice(RANDOM_DEATH_CAUSES)
            logger.info(
                "TimeManager: %s falleció por causa imprevista ('%s') a los %d años.",
                player.player_id, cause, player.age,
            )
            return LifeEndResult(cause=cause, age_at_end=player.age)

        return None
