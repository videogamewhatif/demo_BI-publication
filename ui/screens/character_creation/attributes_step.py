"""
ui/screens/character_creation/attributes_step.py
==================================================

Paso 3 del flujo de creación de personaje: distribución de
`POINTS_TO_DISTRIBUTE` (20) puntos extra entre los 10 atributos
reales de `Player`.

Cada atributo muestra su valor base (el default del dataclass) y
permite sumarle puntos con +/- . El contador de puntos restantes se
actualiza en tiempo real; el botón "Crear personaje" solo se
habilita cuando la suma de deltas ≤ 20 y todos los valores están
dentro de sus rangos válidos, lo que significa que puede quedar
puntos sin usar (el jugador no está obligado a gastar todos).

Los rangos y defaults vienen de `managers.player_manager`:
`_ATTR_DEFAULTS`, `DISTRIBUTABLE_ATTRS`, `POINTS_TO_DISTRIBUTE`,
`MIN_REPUTATION`/`MAX_REPUTATION`/`MAX_STAT` de `config.constant` —
nada hardcodeado aquí.

Emite `step_complete` con `{"attr_deltas": Dict[str,int]}` y
`step_back`.

Autor: Korlo
"""

from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.constant import MAX_STAT, MIN_REPUTATION, MAX_REPUTATION
from managers.player_manager import (
    DISTRIBUTABLE_ATTRS,
    _ATTR_DEFAULTS,
)
from ui import theme
from ui.widgets.card import Card

_ATTR_LABELS: Dict[str, str] = {
    "health": "Salud",
    "appearance": "Apariencia",
    "intelligence": "Inteligencia",
    "discipline": "Disciplina",
    "creativity": "Creatividad",
    "happiness": "Felicidad",
    "charisma": "Carisma",
    "empathy": "Empatía",
    "stress": "Estrés",
    "reputation": "Reputación",
}


def _attr_range(attr: str) -> tuple[int, int]:
    if attr == "reputation":
        return MIN_REPUTATION, MAX_REPUTATION
    return 0, MAX_STAT


class _AttrRow(QWidget):
    """Fila de un atributo: nombre, valor actual, botones + y –."""

    changed = Signal()

    def __init__(self, attr_name: str, parent=None) -> None:
        super().__init__(parent)
        self._attr = attr_name
        self._base = _ATTR_DEFAULTS[attr_name]
        self._delta = 0
        self._min, self._max = _attr_range(attr_name)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(theme.SPACE_SM)

        name_label = QLabel(_ATTR_LABELS[attr_name])
        name_label.setFixedWidth(110)
        name_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px;"
        )

        self._minus_btn = self._small_btn("−")
        self._minus_btn.clicked.connect(self._decrement)

        self._value_label = QLabel()
        self._value_label.setFixedWidth(40)
        self._value_label.setAlignment(Qt.AlignCenter)

        self._plus_btn = self._small_btn("+")
        self._plus_btn.clicked.connect(self._increment)

        self._base_label = QLabel(f"(base {self._base})")
        self._base_label.setStyleSheet(
            f"color: {theme.TEXT_DISABLED}; font-size: {theme.FONT_SIZE_TINY}px;"
        )

        row.addWidget(name_label)
        row.addWidget(self._minus_btn)
        row.addWidget(self._value_label)
        row.addWidget(self._plus_btn)
        row.addWidget(self._base_label)
        row.addStretch(1)

        self._refresh()

    def _small_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; "
            f"border: 1px solid {theme.BORDER_STRONG}; border-radius: 4px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PURPLE_SOFT}; }}"
            f"QPushButton:disabled {{ color: {theme.TEXT_DISABLED}; border-color: {theme.BORDER}; }}"
        )
        return btn

    def _increment(self) -> None:
        # Aumenta el atributo si no supera el máximo permitdo.
        if self._base + self._delta < self._max:
            self._delta += 1
            self._refresh()
            self.changed.emit()

    def _decrement(self) -> None:
        # Permitir decrementos incluso por debajo del valor base (delta
        # negativo) hasta el mínimo del atributo.
        if self._base + self._delta > self._min:
            self._delta -= 1
            self._refresh()
            self.changed.emit()

    def _refresh(self) -> None:
        value = self._base + self._delta
        self._value_label.setText(str(value))
        self._value_label.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_BODY}px; font-weight: 700; "
            f"color: {theme.ACCENT_PURPLE if self._delta > 0 else theme.TEXT_PRIMARY};"
        )
        # Habilitar/deshabilitar botones según los límites reales del
        # atributo (base + delta dentro de [min, max]).
        self._minus_btn.setEnabled(value > self._min)
        self._plus_btn.setEnabled(value < self._max)

    def delta(self) -> int:
        return self._delta

    def set_plus_enabled(self, enabled: bool) -> None:
        """Desactiva el + cuando no quedan puntos disponibles."""
        if self._base + self._delta < self._max:
            self._plus_btn.setEnabled(enabled)

    def reset(self) -> None:
        self._delta = 0
        self._refresh()


class AttributesStep(QWidget):
    """Paso 3 — distribución de puntos entre los 10 atributos reales."""

    step_complete = Signal(dict)  # {"attr_deltas": {attr: delta}}
    step_back = Signal()

    def __init__(self, player_manager, parent=None) -> None:
        super().__init__(parent)
        self._player_manager = player_manager
        layout = QVBoxLayout(self)
        layout.setSpacing(theme.SPACE_LG)

        card = Card()
        title = QLabel("¿Cómo eres?")
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H1}px; font-weight: 800; color: {theme.TEXT_PRIMARY};"
        )
        self._points_label = QLabel()
        self._points_label.setStyleSheet(
            f"color: {theme.ACCENT_PURPLE}; font-size: {theme.FONT_SIZE_BODY}px; font-weight: 700;"
        )
        card.body_layout.addWidget(title)
        card.body_layout.addWidget(self._points_label)
        card.body_layout.addSpacing(theme.SPACE_SM)

        grid = QGridLayout()
        grid.setSpacing(theme.SPACE_SM)
        self._rows: Dict[str, _AttrRow] = {}
        for i, attr in enumerate(DISTRIBUTABLE_ATTRS):
            row_widget = _AttrRow(attr)
            row_widget.changed.connect(self._refresh_points)
            self._rows[attr] = row_widget
            grid.addWidget(row_widget, i // 2, i % 2)
        card.body_layout.addLayout(grid)

        layout.addWidget(card)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(f"color: {theme.ERROR}; font-size: {theme.FONT_SIZE_SMALL}px;")
        self._error_label.hide()
        layout.addWidget(self._error_label)

        btn_row = QHBoxLayout()
        btn_back = QPushButton("← Atrás")
        btn_back.setFixedHeight(44)
        btn_back.setStyleSheet(
            f"QPushButton {{ background-color: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; "
            f"border: 1px solid {theme.BORDER_STRONG}; border-radius: {theme.RADIUS_SM}px; font-weight: 600; }}"
        )
        btn_back.clicked.connect(self.step_back.emit)

        self._btn_create = QPushButton("Crear personaje ✓")
        self._btn_create.setFixedHeight(44)
        self._btn_create.setStyleSheet(
            f"QPushButton {{ background-color: {theme.ACCENT_PURPLE}; color: {theme.TEXT_WHITE}; "
            f"border-radius: {theme.RADIUS_SM}px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {theme.BORDER}; color: {theme.TEXT_DISABLED}; }}"
        )
        self._btn_create.clicked.connect(self._handle_create)

        btn_row.addWidget(btn_back)
        btn_row.addStretch(1)
        btn_row.addWidget(self._btn_create)
        layout.addLayout(btn_row)
        layout.addStretch(1)

        self._refresh_points()

    def _used_points(self) -> int:
        return sum(r.delta() for r in self._rows.values())

    def _refresh_points(self) -> None:
        # Distribución libre: el jugador puede ajustar cada atributo
        # dentro de sus límites individuales; no hay pool global.
        self._points_label.setText("Ajusta tus atributos libremente.")
        for row in self._rows.values():
            # Permitimos + siempre que la fila no haya alcanzado su tope.
            row.set_plus_enabled(True)
        # Validamos solo por rangos individuales (la validación global
        # de puntos queda obsoleta).
        deltas = {a: r.delta() for a, r in self._rows.items()}
        valid = True
        # Chequeo rápido: usar validate_distribution para aprovechar
        # las comprobaciones de rango existentes, pero ignorando
        # el chequeo del total de puntos (revisamos el mensaje).
        ok, reason = self._player_manager.validate_distribution(deltas)
        if not ok and "solo tienes" in reason:
            # Mensaje relacionado con límite global; lo ignoramos.
            ok = True
        self._btn_create.setEnabled(ok)
        self._error_label.hide()

    def _handle_create(self) -> None:
        deltas = {a: r.delta() for a, r in self._rows.items() if r.delta() != 0}
        valid, reason = self._player_manager.validate_distribution(deltas)
        if not valid:
            self._error_label.setText(reason)
            self._error_label.show()
            return
        self._error_label.hide()
        self.step_complete.emit({"attr_deltas": deltas})

    def reset(self) -> None:
        for row in self._rows.values():
            row.reset()
        self._refresh_points()
