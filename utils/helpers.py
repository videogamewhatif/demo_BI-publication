"""
utils/helpers.py
=================

Qué hace:
    Utilidades de texto genéricas, sin relación con ningún dominio
    específico del juego. Deliberadamente corto: `utils/helpers.py`
    tiende a convertirse en un cajón de sastre si se le agrega
    cualquier función sin un motivo concreto — cada función de este
    archivo tiene una razón puntual para existir (documentada abajo)
    en vez de estar "por si acaso".

Por qué existe `wrap_text`:
    `services/image_service.py` (`PlaceholderImageProvider`) tenía
    su propio `_wrap_text()` privado para envolver el prompt sobre
    la imagen de marcador de posición. Con `utils/` ya existiendo,
    se extrajo aquí y `image_service.py` pasa a reutilizarlo (ver la
    sección de refactors en la Explicación).

Dependencias:
    - Solo biblioteca estándar.

Autor: Korlo
"""

from __future__ import annotations

from typing import List, Optional


def wrap_text(text: str, max_chars_per_line: int) -> str:
    """
    Envuelve `text` en líneas de a lo sumo `max_chars_per_line`
    caracteres, cortando por palabras completas (nunca parte una
    palabra a la mitad).

    Args:
        text: texto a envolver.
        max_chars_per_line: ancho máximo de cada línea, en caracteres.

    Returns:
        `text` con saltos de línea (`\\n`) insertados donde
        corresponde.

    Raises:
        ValueError: si `max_chars_per_line` no es positivo.
    """
    if max_chars_per_line <= 0:
        raise ValueError("max_chars_per_line debe ser mayor que 0.")

    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars_per_line:
            if current:
                lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


def truncate_text(text: str, max_length: int, suffix: str = "…") -> str:
    """
    Recorta `text` a `max_length` caracteres (incluyendo `suffix`),
    sin partir palabras a la mitad cuando es posible.

    Args:
        text: texto a recortar.
        max_length: longitud máxima total del resultado.
        suffix: texto a añadir cuando se recorta (por defecto, "…").

    Returns:
        `text` sin cambios si ya cabe en `max_length`; si no, una
        versión recortada que termina en `suffix`.

    Raises:
        ValueError: si `max_length` es menor que `len(suffix)`.
    """
    if max_length < len(suffix):
        raise ValueError("max_length no puede ser menor que len(suffix).")
    if len(text) <= max_length:
        return text

    limit = max_length - len(suffix)
    truncated = text[:limit]
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return f"{truncated}{suffix}"


def format_currency(amount: float, symbol: str = "$", decimals: int = 2) -> str:
    """
    Formatea `amount` como texto de moneda, con separador de miles
    y el símbolo indicado (por ejemplo, para mostrar
    `Player.net_worth` en una futura interfaz).

    Examples:
        >>> format_currency(1234567.5)
        '$1,234,567.50'
        >>> format_currency(-500, symbol="€", decimals=0)
        '-€500'
    """
    sign = "-" if amount < 0 else ""
    return f"{sign}{symbol}{abs(amount):,.{decimals}f}"


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """
    Devuelve `f"{count} {singular_o_plural}"`, en español: usa
    `singular` si `count == 1`, y `plural` (o `singular + 's'` si no
    se especifica `plural`) en cualquier otro caso.

    Examples:
        >>> pluralize(1, "hijo")
        '1 hijo'
        >>> pluralize(3, "hijo")
        '3 hijos'
        >>> pluralize(2, "relación", "relaciones")
        '2 relaciones'
    """
    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural if plural is not None else singular + 's'}"