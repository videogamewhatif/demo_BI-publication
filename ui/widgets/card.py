"""
ui/widgets/card.py
===================

Qué hace:
    `Card`: un `QFrame` con fondo, esquinas redondeadas y sombra
    ligera — el contenedor base reutilizado por casi todos los
    paneles de la interfaz (panel de personaje, historial, opciones
    de decisión, etc.), siguiendo el estilo de tarjeta pedido en la
    referencia visual.

Cómo funciona:
    El radio de esquina se aplica por QSS; la sombra NO se puede
    hacer por QSS en Qt (no existe `box-shadow`), así que se usa
    `QGraphicsDropShadowEffect`, la vía estándar de Qt para esto.
    Acepta un color de borde opcional (`accent_color`) para las
    tarjetas de decisión, que en la referencia tienen un borde de
    color distinto según la opción.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QVBoxLayout

from ui import theme


class Card(QFrame):
    """Contenedor con fondo blanco, esquinas redondeadas y sombra ligera."""

    clicked = Signal()

    def __init__(
        self,
        parent=None,
        *,
        padding: int = theme.SPACE_MD,
        radius: int = theme.RADIUS_MD,
        accent_color: Optional[str] = None,
        clickable: bool = False,
    ) -> None:
        super().__init__(parent)
        self._radius = radius
        self._accent_color = accent_color
        self._selected = False

        if clickable:
            self.setCursor(Qt.PointingHandCursor)
            self._clickable = True
        else:
            self._clickable = False

        self.setObjectName("Card")
        self._apply_style()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(15, 23, 42, 30))  # sombra sutil, no negro puro
        self.setGraphicsEffect(shadow)

        self.body_layout = QVBoxLayout(self)
        self.body_layout.setContentsMargins(padding, padding, padding, padding)
        self.body_layout.setSpacing(theme.SPACE_SM)

    def set_selected(self, selected: bool) -> None:
        """Resalta la tarjeta (usado por las tarjetas de decisión al recibir foco/hover)."""
        self._selected = selected
        self._apply_style()

    def _apply_style(self) -> None:
        border_color = self._accent_color or theme.BORDER
        border_width = "2px" if (self._accent_color or self._selected) else "1px"
        self.setStyleSheet(
            f"""
            #Card {{
                background-color: {theme.CARD};
                border: {border_width} solid {border_color};
                border-radius: {self._radius}px;
            }}
            """
        )

    def mousePressEvent(self, event) -> None:
        super().mousePressEvent(event)
        if getattr(self, "_clickable", False):
            self.clicked.emit()
