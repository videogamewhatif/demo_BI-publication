"""
ui/widgets/stat_bar.py
=======================

Qué hace:
    `StatBar`: fila con nombre de atributo, barra de progreso
    coloreada y valor numérico — la unidad visual que compone el
    panel de personaje (un `StatBar` por cada atributo real de
    `models.player.Player`).

Cómo funciona:
    Recibe el rango real del atributo (la mayoría 0-100 vía
    `config.constant.MIN_STAT`/`MAX_STAT`, pero `reputation` usa
    -100..100 vía `MIN_REPUTATION`/`MAX_REPUTATION`) para no asumir
    0-100 a ciegas y mostrar la barra mal escalada en ese caso.

Autor: Korlo (ui/ añadida en esta sesión)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from ui import theme


class StatBar(QWidget):
    """Fila de: etiqueta — barra de progreso coloreada — valor numérico."""

    def __init__(
        self,
        label: str,
        value: float,
        *,
        minimum: int = 0,
        maximum: int = 100,
        color: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._minimum = minimum
        self._maximum = maximum
        self._color = color or theme.ACCENT_PURPLE

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;"
        )

        self._value_label = QLabel()
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value_label.setStyleSheet(
            f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )

        header.addWidget(self._label)
        header.addStretch(1)
        header.addWidget(self._value_label)

        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        self._bar.setRange(minimum, maximum)

        outer.addLayout(header)
        outer.addWidget(self._bar)

        self.set_value(value)

    def set_value(self, value: float) -> None:
        """Actualiza barra y etiqueta numérica al valor real actual del atributo."""
        clamped = max(self._minimum, min(self._maximum, int(round(value))))
        self._bar.setValue(clamped)
        self._value_label.setText(str(int(round(value))))
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {theme.BORDER};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {self._color};
                border-radius: 4px;
            }}
            """
        )
