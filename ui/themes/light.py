"""
ui/themes/light.py
=====================

Qué hace:
    Define `LIGHT`, el tema claro — el que la interfaz ya usaba
    antes de que existiera `ui/themes/` (blanco/gris muy claro de
    fondo, texto oscuro, acentos azul y morado). Es el tema por
    defecto (`ui.themes.DEFAULT_THEME_NAME`).

Cómo funciona:
    Cada valor viene de `config/colors.py` sin modificar — este
    archivo solo los agrupa bajo la forma `Theme`. Ningún hex nuevo
    se define aquí.

Autor: Korlo (ui/themes/ añadida en esta sesión)
"""

from __future__ import annotations

from config import colors as _c
from ui.themes import Theme

LIGHT = Theme(
    NAME="light",
    IS_DARK=False,

    BACKGROUND=_c.BACKGROUND,
    SURFACE=_c.SURFACE,
    CARD=_c.CARD,
    SIDEBAR_BG=_c.SIDEBAR,

    TEXT_PRIMARY=_c.TEXT_PRIMARY,
    TEXT_SECONDARY=_c.TEXT_SECONDARY,
    TEXT_DISABLED=_c.TEXT_DISABLED,
    TEXT_WHITE=_c.TEXT_WHITE,

    BORDER=_c.BORDER_LIGHT,
    BORDER_STRONG=_c.BORDER,

    ACCENT_PRIMARY=_c.PRIMARY,
    ACCENT_PRIMARY_HOVER=_c.PRIMARY_DARK,
    ACCENT_PRIMARY_LIGHT=_c.PRIMARY_LIGHT,
    ACCENT_PURPLE=_c.REPUTATION,
    ACCENT_PURPLE_SOFT=_c.EVENT_SPECIAL,

    INPUT_BACKGROUND=_c.INPUT_BACKGROUND,
    INPUT_BORDER=_c.INPUT_BORDER,
)
