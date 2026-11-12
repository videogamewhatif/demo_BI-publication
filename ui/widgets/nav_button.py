"""
ui/widgets/nav_button.py
=========================

Qué hace:
    `SidebarButton`: botón de navegación checkable (icono + texto)
    para la barra lateral. Cuando está activo se resalta con el
    fondo/texto morado suave de la referencia visual
    (`theme.ACCENT_PURPLE_SOFT` / `theme.ACCENT_PURPLE`, ambos
    reexportados de `config/colors.py`).

Cómo funciona:
    Es un `QPushButton` `checkable=True`; quien lo use debe meterlo
    en un `QButtonGroup` (ver `ui/screens/gameplay_screen.py`) para
    que solo uno esté activo a la vez. No contiene lógica de
    navegación: solo emite la señal estándar `toggled`/`clicked` de
    Qt, igual que cualquier botón — quien conecta la señal decide
    qué pantalla mostrar.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton

from ui import theme


class SidebarButton(QPushButton):
    """Botón de navegación de la barra lateral, con estado activo/inactivo."""

    def __init__(self, text: str, icon_glyph: str = "", parent=None) -> None:
        label = f"{icon_glyph}   {text}" if icon_glyph else text
        super().__init__(label, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)
        self.setStyleSheet(self._qss())

    def _qss(self) -> str:
        return f"""
        QPushButton {{
            text-align: left;
            padding-left: {theme.SPACE_MD}px;
            border-radius: {theme.RADIUS_SM}px;
            border: none;
            background-color: transparent;
            color: {theme.TEXT_SECONDARY};
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {theme.BACKGROUND};
        }}
        QPushButton:checked {{
            background-color: {theme.ACCENT_PURPLE_SOFT};
            color: {theme.ACCENT_PURPLE};
            font-weight: 700;
        }}
        """
