"""
utils/validators.py
====================

Qué hace:
    Validadores genéricos de strings y formato: cadenas no vacías,
    longitud dentro de un rango, formato de email, identificadores
    seguros (para usar como clave/id) y fechas ISO 8601.

Por qué NO valida rangos numéricos:
    `models/scales.py` ya tiene `clamp()`/`is_in_range()` para las
    variables numéricas del Estado de Personaje (0-100,
    -100 a 100, etc.). Reimplementar una validación de rango
    numérico aquí sería duplicar esa lógica — este archivo se
    enfoca deliberadamente en formato de texto, que es un problema
    distinto y no lo cubre `models/scales.py`.

Todavía sin consumidor en el proyecto:
    No existe todavía ninguna pantalla de creación de personaje ni
    sistema de cuentas de usuario — por eso nada importa este
    archivo todavía. Queda completo y probado para cuando se
    construyan (mismo caso que `OpenAIImageProvider`, listo sin una
    API key configurada).

Cómo funciona:
    Cada función es un predicado puro (`is_...() -> bool`) en vez de
    lanzar excepciones: quien llama decide qué excepción lanzar y
    con qué mensaje, en vez de heredar un tipo de excepción nuevo
    que competiría con el `ValueError` que ya usa el resto del
    proyecto (`Player`, `NPC`, `Story`, todos los servicios).

Dependencias:
    - Solo biblioteca estándar (re, datetime).

Autor: Korlo
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def is_non_empty_string(value: object) -> bool:
    """
    Indica si `value` es un string no vacío tras quitar espacios en
    los extremos (una cadena de solo espacios NO cuenta como
    válida).
    """
    return isinstance(value, str) and len(value.strip()) > 0


def is_within_length(value: str, minimum: int = 0, maximum: Optional[int] = None) -> bool:
    """
    Indica si `len(value)` está entre `minimum` y `maximum`
    (inclusive). `maximum=None` significa sin límite superior.

    Raises:
        ValueError: si `minimum` es negativo, o si `maximum` es
            menor que `minimum`.
    """
    if minimum < 0:
        raise ValueError("minimum no puede ser negativo.")
    if maximum is not None and maximum < minimum:
        raise ValueError("maximum no puede ser menor que minimum.")
    if len(value) < minimum:
        return False
    if maximum is not None and len(value) > maximum:
        return False
    return True


def is_valid_email(value: str) -> bool:
    """
    Indica si `value` tiene forma de email (`algo@dominio.tld`).

    Es una validación pragmática de formato, no una verificación
    exhaustiva contra el RFC 5322 completo (ese estándar admite
    casos tan inusuales que validarlo estrictamente suele rechazar
    más direcciones reales de las que acepta incorrectamente una
    validación simple como esta).
    """
    return bool(_EMAIL_PATTERN.match(value))


def is_valid_identifier(value: str) -> bool:
    """
    Indica si `value` es un identificador seguro: solo letras,
    dígitos, guion y guion bajo, sin espacios. Útil para validar
    ids que se usarán como clave de repositorio o nombre de archivo
    ANTES de pasarlos a `utils.file_utils.safe_filename` (que
    normaliza, pero no avisa si el id ya venía con caracteres
    inesperados).
    """
    return bool(_IDENTIFIER_PATTERN.match(value)) if value else False


def is_valid_iso_date(value: str) -> bool:
    """Indica si `value` es una fecha válida en formato ISO 8601 (`AAAA-MM-DD`)."""
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def is_valid_iso_datetime(value: str) -> bool:
    """Indica si `value` es una fecha y hora válidas en formato ISO 8601."""
    try:
        datetime.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False