"""
ui/screens/character_creation/identity_step.py
================================================

Paso 1 del flujo de creación de personaje: nombre, apellido y género.

`gender` se guarda como str libre (igual que el campo `Optional[str]`
de `models.player.Player`) — el proyecto no tiene un enum de género
definido hoy, y usar str libre es lo que el propio campo ya hace.
Las opciones predefinidas que se muestran son sugerencias, no una
lista cerrada; el jugador también puede escribir libremente.

Emite `step_complete` con `{"first_name", "last_name", "gender"}`
cuando los campos obligatorios (nombre y apellido) están rellenos
y el jugador pulsa "Siguiente".

Autor: Korlo
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ui import theme
from ui.widgets.card import Card

_GENDER_OPTIONS = ["Masculino", "Femenino", "No binario", "Prefiero no decirlo"]


class IdentityStep(QWidget):
    """Paso 1 — nombre, apellido, género."""

    step_complete = Signal(dict)  # {"first_name", "last_name", "gender"}

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(theme.SPACE_LG)

        card = Card()
        title = QLabel("¿Quién eres?")
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H1}px; font-weight: 800; color: {theme.TEXT_PRIMARY};"
        )
        subtitle = QLabel("Empieza por lo más básico — cómo te llamas.")
        subtitle.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_BODY}px;")
        card.body_layout.addWidget(title)
        card.body_layout.addWidget(subtitle)
        card.body_layout.addSpacing(theme.SPACE_SM)

        self._first_name = self._labeled_input("Nombre *", card)
        self._last_name = self._labeled_input("Apellido *", card)

        gender_label = QLabel("Género")
        gender_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;"
        )
        card.body_layout.addWidget(gender_label)

        self._gender_group = QButtonGroup()
        gender_row = QHBoxLayout()
        gender_row.setSpacing(theme.SPACE_SM)
        self._gender_buttons: dict[str, QRadioButton] = {}
        for option in _GENDER_OPTIONS:
            rb = QRadioButton(option)
            rb.setStyleSheet(f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
            self._gender_buttons[option] = rb
            self._gender_group.addButton(rb)
            gender_row.addWidget(rb)
        self._gender_buttons[_GENDER_OPTIONS[0]].setChecked(True)
        gender_row.addStretch(1)
        card.body_layout.addLayout(gender_row)

        layout.addWidget(card)

        self._error_label = QLabel("")
        self._error_label.setStyleSheet(f"color: {theme.ERROR}; font-size: {theme.FONT_SIZE_SMALL}px;")
        self._error_label.hide()
        layout.addWidget(self._error_label)

        btn_next = QPushButton("Siguiente →")
        btn_next.setFixedHeight(44)
        btn_next.setStyleSheet(
            f"QPushButton {{ background-color: {theme.ACCENT_PURPLE}; color: {theme.TEXT_WHITE}; "
            f"border-radius: {theme.RADIUS_SM}px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}"
        )
        btn_next.clicked.connect(self._handle_next)
        layout.addWidget(btn_next)
        layout.addStretch(1)

    def _labeled_input(self, label_text: str, parent_card: Card) -> QLineEdit:
        label = QLabel(label_text)
        label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;"
        )
        field = QLineEdit()
        field.setStyleSheet(
            f"QLineEdit {{ border: 1px solid {theme.BORDER_STRONG}; border-radius: {theme.RADIUS_SM}px; "
            f"padding: 8px 12px; font-size: {theme.FONT_SIZE_BODY}px; "
            f"background: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; }}"
        )
        parent_card.body_layout.addWidget(label)
        parent_card.body_layout.addWidget(field)
        return field

    def _handle_next(self) -> None:
        first = self._first_name.text().strip()
        last = self._last_name.text().strip()
        if not first or not last:
            self._error_label.setText("El nombre y el apellido son obligatorios.")
            self._error_label.show()
            return
        self._error_label.hide()
        checked = self._gender_group.checkedButton()
        gender = checked.text() if checked else None
        self.step_complete.emit({
            "first_name": first,
            "last_name": last,
            "gender": gender,
        })

    def reset(self) -> None:
        self._first_name.setText("")
        self._last_name.setText("")
        self._gender_buttons[_GENDER_OPTIONS[0]].setChecked(True)
        self._error_label.hide()
