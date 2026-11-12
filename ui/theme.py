"""
ui/theme.py
===========

Qué hace:
    Punto único que el resto de `ui/` importa (`from ui import
    theme`) para leer tokens visuales. Antes de `ui/themes/`, esto
    era un módulo de constantes estáticas; ahora reenvía cada color
    estructural (fondo, superficie, texto, borde, acento) al tema
    ACTIVO en `ui/themes/` (`light` por defecto, o `dark`), vía
    `__getattr__` de módulo (PEP 562) — así ningún archivo de
    `ui/widgets/` ni `ui/screens/` tuvo que cambiar una sola línea
    para que exista modo oscuro: `theme.BACKGROUND` sigue
    funcionando igual, solo que ahora depende de qué tema esté
    activo.

    Los colores semánticos/categóricos (SUCCESS/WARNING/ERROR/INFO,
    colores de estadísticas) y los tokens que no son de color
    (espaciado, radios, tipografía) NO pasan por el tema activo:
    siguen siendo globals reales de este módulo, iguales en
    cualquier tema — ver `ui/themes/__init__.py` para la razón.

Cómo cambiar de tema:
    `ui.theme.set_theme("dark")` (o `"light"`), o `toggle_theme()`.
    Desde esta sesión, cambiar de tema SÍ repinta en caliente lo que
    ya está en pantalla: `set_theme()`/`toggle_theme()` notifican a
    quien se haya suscrito con `on_theme_changed()`.
    `ui/windows/main_window.py` es el único suscriptor hoy — cuando
    el tema cambia, reconstruye `MainMenuScreen` y `GameplayScreen`
    desde cero (conservando la sesión activa si había una) en vez de
    que cada uno de los ~15 widgets de `ui/widgets/`/`ui/screens/`
    tenga que saber reaplicar su propio estilo. Ver
    `docs/architecture.md` para el detalle de esa decisión.

Autor: Korlo (ui/theme.py reescrito junto con ui/themes/ en esta
sesión; repintado en caliente vía on_theme_changed() añadido después)
"""

from __future__ import annotations

from typing import Any, Callable, List

from config import colors as _c
from ui.themes import DEFAULT_THEME_NAME, THEMES, Theme

# ==========================================================
# TEMA ACTIVO
# ==========================================================

_active_theme_name: str = DEFAULT_THEME_NAME
_theme_change_listeners: List[Callable[[str], None]] = []


def set_theme(name: str) -> None:
    """
    Activa el tema `name` ("light" o "dark") y notifica a quien se
    haya suscrito con `on_theme_changed()`. No hace nada (ni
    notifica) si `name` ya era el tema activo.

    Raises:
        ValueError: si `name` no está registrado en `ui.themes.THEMES`.
    """
    if name not in THEMES:
        raise ValueError(
            f"Tema desconocido: '{name}'. Disponibles: {sorted(THEMES)}."
        )
    global _active_theme_name
    if name == _active_theme_name:
        return
    _active_theme_name = name
    for callback in list(_theme_change_listeners):
        callback(name)


def toggle_theme() -> str:
    """Alterna entre 'light' y 'dark'. Devuelve el nombre del tema que quedó activo."""
    set_theme("dark" if _active_theme_name == "light" else "light")
    return _active_theme_name


def on_theme_changed(callback: Callable[[str], None]) -> None:
    """
    Registra `callback(nombre_del_tema_nuevo)` para que se llame
    cada vez que `set_theme()`/`toggle_theme()` cambian el tema de
    verdad (no se llama si se pide el mismo tema que ya estaba
    activo). Es la pieza que permite el repintado en caliente sin
    que cada widget individual tenga que suscribirse por su cuenta —
    ver la nota de arriba.
    """
    _theme_change_listeners.append(callback)


def off_theme_changed(callback: Callable[[str], None]) -> None:
    """Cancela una suscripción hecha con `on_theme_changed()`. No falla si no estaba suscrito."""
    if callback in _theme_change_listeners:
        _theme_change_listeners.remove(callback)


def get_active_theme() -> Theme:
    """El objeto `Theme` completo actualmente activo (para quien necesite más de un campo a la vez)."""
    return THEMES[_active_theme_name]


def current_theme_name() -> str:
    """El nombre del tema activo ("light" / "dark")."""
    return _active_theme_name


def __getattr__(name: str) -> Any:
    """
    PEP 562. Reenvía cualquier nombre que sea un campo de `Theme`
    (BACKGROUND, ACCENT_PURPLE, etc.) al tema activo. Los nombres
    que SÍ son globals reales de este módulo (SPACE_MD, STAT_COLORS,
    SUCCESS...) nunca llegan aquí — Python los resuelve antes, sin
    pasar por `__getattr__`.
    """
    active = get_active_theme()
    if hasattr(active, name):
        return getattr(active, name)
    raise AttributeError(f"module 'ui.theme' has no attribute '{name}'")


# ==========================================================
# COLOR SEMÁNTICO / CATEGÓRICO — igual en cualquier tema
# ==========================================================

SUCCESS = _c.SUCCESS
WARNING = _c.WARNING
ERROR = _c.ERROR
INFO = _c.INFO

# Un color por atributo real de `models.player.Player` (ver
# config/colors.py, sección añadida junto con ui/).
STAT_COLORS = {
    "health": _c.HEALTH,
    "happiness": _c.HAPPINESS,
    "stress": _c.STRESS,
    "reputation": _c.REPUTATION,
    "intelligence": _c.INTELLIGENCE,
    "discipline": _c.DISCIPLINE,
    "creativity": _c.CREATIVITY,
    "charisma": _c.CHARISMA,
    "empathy": _c.EMPATHY,
    "appearance": _c.APPEARANCE,
}

# ==========================================================
# ESPACIADO / RADIOS — no son colores, iguales en cualquier tema
# ==========================================================

SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 16
SPACE_LG = 24
SPACE_XL = 32

RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16

# ==========================================================
# TIPOGRAFÍA — igual en cualquier tema
# ==========================================================
# Sin fuentes propias en assets/fonts todavía (ver
# managers/resource_manager.py): se usa una pila de fuentes de
# sistema, no una custom, para no depender de un archivo que no
# existe.

FONT_FAMILY = '"Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif'

FONT_SIZE_H1 = 24
FONT_SIZE_H2 = 18
FONT_SIZE_BODY = 13
FONT_SIZE_SMALL = 11
FONT_SIZE_TINY = 10


def base_stylesheet() -> str:
    """
    QSS global de la aplicación para el tema ACTIVO en el momento de
    la llamada. Si se llama a `set_theme()` después, hay que volver
    a llamar a esta función (y reaplicar el resultado con
    `QApplication.setStyleSheet`) para que el cambio se refleje —
    ver la nota de alcance en el docstring del módulo.
    """
    t = get_active_theme()
    # El tooltip siempre usa alto contraste respecto al tema activo:
    # fondo oscuro+texto claro en tema claro, fondo claro+texto oscuro
    # en tema oscuro (en vez de heredar los mismos colores que ya
    # tiene el fondo general, que lo dejarían ilegible).
    tooltip_bg = t.TEXT_PRIMARY
    tooltip_text = t.BACKGROUND
    return f"""
    QWidget {{
        background-color: {t.BACKGROUND};
        color: {t.TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE_BODY}px;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {t.BORDER_STRONG};
        border-radius: 4px;
        min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QPushButton {{
        border: none;
        border-radius: {RADIUS_SM}px;
        padding: 8px 16px;
        font-weight: 600;
    }}

    QLineEdit, QComboBox {{
        border: 1px solid {t.INPUT_BORDER};
        border-radius: {RADIUS_SM}px;
        padding: 6px 10px;
        background: {t.INPUT_BACKGROUND};
        color: {t.TEXT_PRIMARY};
    }}

    QToolTip {{
        background-color: {tooltip_bg};
        color: {tooltip_text};
        border: none;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    """


def stat_color(stat_name: str) -> str:
    """Color asignado a un atributo de `Player` por su nombre de campo; gris si no está mapeado."""
    return STAT_COLORS.get(stat_name, _c.GRAY_400)
