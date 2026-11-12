"""
ui/themes/__init__.py
========================

Qué hace:
    Define `Theme`, la forma común que deben tener `light.py` y
    `dark.py` (mismos campos, valores distintos), y expone
    `THEMES` — el registro `{"light": LIGHT, "dark": DARK}` que
    `ui/theme.py` usa para saber qué tema hay activo en cada
    momento.

Por qué los nombres de campo van en MAYÚSCULAS (no es el estilo
habitual de un dataclass):
    Porque `ui/theme.py` ya expone estos mismos nombres
    (`theme.BACKGROUND`, `theme.ACCENT_PURPLE`, etc.) como atributos
    de módulo desde antes de que existiera este paquete, y ya los
    usan ~20 archivos de `ui/widgets/` y `ui/screens/`. Manteniendo
    el campo `Theme.BACKGROUND` (en vez de `Theme.background`),
    `ui/theme.py` puede reenviar cada atributo con un simple
    `getattr(tema_activo, nombre)`, sin traducir nombres y sin tener
    que tocar ninguno de esos ~20 archivos para añadir modo oscuro.

Qué NO incluye `Theme` (a propósito):
    - Colores semánticos/categóricos (SUCCESS/WARNING/ERROR/INFO,
      colores de estadísticas): significan lo mismo sin importar el
      tema, así que `ui/theme.py` los sigue sirviendo directamente
      desde `config/colors.py`, no desde aquí.
    - Espaciado y tipografía (SPACE_*, RADIUS_*, FONT_*): no son
      colores, no cambian entre temas, y ya viven en `ui/theme.py`.

Cómo interactúa con otros módulos:
    Cada valor de `Theme` proviene de `config/colors.py` — light.py
    y dark.py no inventan hex sueltos, solo componen tokens que ya
    existen ahí (`config/colors.py` sigue siendo la única fuente de
    colores del proyecto, tal como se declara en su propio docstring).

Autor: Korlo (ui/themes/ añadida en esta sesión)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class Theme:
    """
    Los tokens de color que SÍ cambian entre modo claro y oscuro.
    `light.py` y `dark.py` instancian uno cada uno; nunca se
    modifica en caliente (frozen) — cambiar de tema significa
    activar una instancia distinta, no mutar la actual.
    """

    NAME: str
    IS_DARK: bool

    # Fondos / superficies
    BACKGROUND: str
    SURFACE: str
    CARD: str
    SIDEBAR_BG: str

    # Texto
    TEXT_PRIMARY: str
    TEXT_SECONDARY: str
    TEXT_DISABLED: str
    TEXT_WHITE: str

    # Bordes
    BORDER: str
    BORDER_STRONG: str

    # Acentos (azul primario, morado secundario)
    ACCENT_PRIMARY: str
    ACCENT_PRIMARY_HOVER: str
    ACCENT_PRIMARY_LIGHT: str
    ACCENT_PURPLE: str
    ACCENT_PURPLE_SOFT: str

    # Campos de formulario (QLineEdit, QComboBox...)
    INPUT_BACKGROUND: str
    INPUT_BORDER: str


from ui.themes.light import LIGHT  # noqa: E402  (import tardío: depende de Theme, definido arriba)
from ui.themes.dark import DARK  # noqa: E402

THEMES: Dict[str, Theme] = {
    LIGHT.NAME: LIGHT,
    DARK.NAME: DARK,
}

DEFAULT_THEME_NAME = LIGHT.NAME

__all__ = ["Theme", "LIGHT", "DARK", "THEMES", "DEFAULT_THEME_NAME"]
