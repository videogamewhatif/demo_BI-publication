"""
models/scales.py
=================

Qué hace:
    Provee utilidades numéricas compartidas para las variables del
    Estado de Personaje (EP) y de los NPC, que casi siempre se
    mueven en una escala acotada (típicamente 0-100, o -100 a 100
    para Reputación — ver VITA_Game_Design_Document.md §3).

Cómo funciona:
    Expone una única función `clamp()` que acota un valor numérico
    a un rango cerrado [minimum, maximum], y `is_in_range()` para
    comprobaciones sin mutar el valor. No mantiene estado propio.

Dependencias:
    Ninguna (módulo puro, sin efectos secundarios).

Cómo interactúa con otros módulos:
    Lo usan models/player.py y models/npc.py para no duplicar la
    misma lógica de acotamiento en cada mutador de atributo.

Autor: Korlo
"""

from typing import TypeVar

Number = TypeVar("Number", int, float)


def clamp(value: Number, minimum: Number, maximum: Number) -> Number:
    """
    Acota `value` al rango cerrado [minimum, maximum].

    Args:
        value: Valor a acotar.
        minimum: Límite inferior inclusivo.
        maximum: Límite superior inclusivo.

    Returns:
        El valor acotado al rango permitido. Conserva el tipo
        (int o float) del valor de entrada.

    Raises:
        ValueError: Si `minimum` es mayor que `maximum`.

    Examples:
        >>> clamp(150, 0, 100)
        100
        >>> clamp(-20, 0, 100)
        0
        >>> clamp(50, 0, 100)
        50
    """
    if minimum > maximum:
        raise ValueError(
            f"El límite inferior ({minimum}) no puede ser mayor "
            f"que el límite superior ({maximum})."
        )
    return max(minimum, min(maximum, value))


def is_in_range(value: Number, minimum: Number, maximum: Number) -> bool:
    """
    Indica si `value` ya se encuentra dentro de [minimum, maximum].

    Útil para decidir si vale la pena registrar una advertencia de
    "valor fuera de rango" antes de acotarlo silenciosamente.
    """
    return minimum <= value <= maximum