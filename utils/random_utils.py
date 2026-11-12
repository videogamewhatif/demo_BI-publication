"""
utils/random_utils.py
======================

Qué hace:
    Utilidades de aleatoriedad orientadas a las necesidades del
    juego: tiradas de estadísticas, elección con probabilidad,
    elección ponderada, y selección de varios elementos sin
    repetición (por ejemplo, "hasta 3 rasgos de personalidad de una
    tabla de 20" — VITA_Game_Design_Document.md §2, ya mencionado en
    el docstring de `Player.add_personality_trait`).

    Todavía sin consumidor en el proyecto: la Creación de Personaje
    (quien tiraría estos dados) todavía no se ha construido como
    servicio. Queda listo para cuando se construya.

Cómo funciona:
    Cada función acepta un `random.Random` opcional (`rng`). Si no
    se pasa, usa el módulo `random` global. Pasar una instancia
    propia (`random.Random(semilla)`) permite pruebas deterministas
    y, más adelante, funciones como "repetir la misma vida con la
    misma semilla" si el diseño del juego lo llegara a querer — sin
    que este módulo tenga que cambiar.

Dependencias:
    - Solo biblioteca estándar (random).

Autor: Korlo
"""

from __future__ import annotations

import random as _random
from typing import Dict, List, Optional, Sequence, TypeVar

T = TypeVar("T")


def roll_stat(minimum: int = 0, maximum: int = 100, rng: Optional[_random.Random] = None) -> int:
    """
    Tira un valor entero entre `minimum` y `maximum`, inclusive —
    pensado para generar atributos iniciales del personaje.

    Raises:
        ValueError: si `minimum` es mayor que `maximum`.
    """
    if minimum > maximum:
        raise ValueError("minimum no puede ser mayor que maximum.")
    generator = rng or _random
    return generator.randint(minimum, maximum)


def chance(probability: float, rng: Optional[_random.Random] = None) -> bool:
    """
    Devuelve True con probabilidad `probability` (0.0 a 1.0).

    Raises:
        ValueError: si `probability` no está en [0.0, 1.0].
    """
    if not (0.0 <= probability <= 1.0):
        raise ValueError("probability debe estar entre 0.0 y 1.0.")
    generator = rng or _random
    return generator.random() < probability


def weighted_choice(options: Dict[T, float], rng: Optional[_random.Random] = None) -> T:
    """
    Elige una clave de `options` con probabilidad proporcional a su
    peso (el valor asociado).

    Args:
        options: mapa de elemento -> peso relativo (no necesita
            sumar 1.0; se normaliza internamente).

    Raises:
        ValueError: si `options` está vacío, o si algún peso es
            negativo, o si todos los pesos son 0.
    """
    if not options:
        raise ValueError("options no puede estar vacío.")
    if any(weight < 0 for weight in options.values()):
        raise ValueError("Ningún peso puede ser negativo.")
    if sum(options.values()) == 0:
        raise ValueError("Al menos un peso debe ser mayor que 0.")

    generator = rng or _random
    items = list(options.keys())
    weights = list(options.values())
    return generator.choices(items, weights=weights, k=1)[0]


def pick_one(items: Sequence[T], rng: Optional[_random.Random] = None) -> T:
    """
    Elige un elemento al azar de `items`, con probabilidad uniforme.

    Raises:
        ValueError: si `items` está vacío.
    """
    if not items:
        raise ValueError("items no puede estar vacío.")
    generator = rng or _random
    return generator.choice(list(items))


def pick_many(
    items: Sequence[T],
    count: int,
    rng: Optional[_random.Random] = None,
) -> List[T]:
    """
    Elige `count` elementos distintos de `items`, sin repetición.

    Args:
        items: población de la que elegir.
        count: cuántos elementos elegir (puede ser menor que
            `len(items)`; nunca se repite un elemento).

    Raises:
        ValueError: si `count` es negativo, o mayor que `len(items)`.
    """
    if count < 0:
        raise ValueError("count no puede ser negativo.")
    if count > len(items):
        raise ValueError(
            f"count ({count}) no puede ser mayor que la cantidad de "
            f"elementos disponibles ({len(items)})."
        )
    generator = rng or _random
    return generator.sample(list(items), k=count)