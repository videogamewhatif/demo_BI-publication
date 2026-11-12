"""
ui/themes/dark.py
====================

Qué hace:
    Define `DARK`, el tema oscuro — fondos slate muy oscuros,
    texto casi blanco, y los mismos acentos azul/morado pero en su
    variante más clara (leen mejor sobre fondo oscuro que el tono
    usado en `light.py`).

Qué se mantiene igual que en modo claro (a propósito, ver
`config/colors.py` sección "MODO OSCURO"):
    Los colores semánticos (éxito/aviso/error/info) y los de
    estadísticas (salud, reputación, inteligencia...) NO se
    redefinen aquí — `ui/theme.py` los sirve igual sin importar el
    tema activo, porque su significado no debe cambiar con el modo.

Cómo funciona:
    Cada valor viene de la sección "MODO OSCURO" de
    `config/colors.py` (añadida junto con este archivo) — ningún hex
    se inventa suelto aquí tampoco.

Autor: Korlo (ui/themes/ añadida en esta sesión)
"""

from __future__ import annotations

from config import colors as _c
from ui.themes import Theme

DARK = Theme(
    NAME="dark",
    IS_DARK=True,

    BACKGROUND=_c.DARK_BACKGROUND,
    SURFACE=_c.DARK_SURFACE,
    CARD=_c.DARK_CARD,
    SIDEBAR_BG=_c.DARK_SIDEBAR,

    TEXT_PRIMARY=_c.DARK_TEXT_PRIMARY,
    TEXT_SECONDARY=_c.DARK_TEXT_SECONDARY,
    TEXT_DISABLED=_c.DARK_TEXT_DISABLED,
    TEXT_WHITE=_c.DARK_TEXT_WHITE,

    BORDER=_c.DARK_BORDER_LIGHT,
    BORDER_STRONG=_c.DARK_BORDER,

    ACCENT_PRIMARY=_c.DARK_ACCENT_PRIMARY,
    ACCENT_PRIMARY_HOVER=_c.DARK_ACCENT_PRIMARY_HOVER,
    ACCENT_PRIMARY_LIGHT=_c.DARK_ACCENT_PRIMARY_LIGHT,
    ACCENT_PURPLE=_c.DARK_ACCENT_PURPLE,
    ACCENT_PURPLE_SOFT=_c.DARK_ACCENT_PURPLE_SOFT,

    INPUT_BACKGROUND=_c.DARK_INPUT_BACKGROUND,
    INPUT_BORDER=_c.DARK_INPUT_BORDER,
)
