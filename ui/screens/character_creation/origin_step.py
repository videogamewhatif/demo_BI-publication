"""
ui/screens/character_creation/origin_step.py
==============================================

Paso 2 del flujo de creación de personaje: edad de inicio, país,
ciudad y origen socioeconómico.

`SocioeconomicLevel` ya existe en `config/constant.py` y es el campo
real de `Player.socioeconomic_origin` — se muestra tal cual, sin
inventar otra escala.

Emite `step_complete` con `{"starting_age", "country", "city",
"socioeconomic_origin"}` y `step_back` cuando el jugador pulsa
"← Atrás".

Autor: Korlo
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from config.constant import SocioeconomicLevel
from ui import theme
from ui.widgets.card import Card

_SOCIO_LABELS = {
    SocioeconomicLevel.VERY_LOW: "Muy bajo",
    SocioeconomicLevel.LOW: "Bajo",
    SocioeconomicLevel.MEDIUM: "Medio",
    SocioeconomicLevel.HIGH: "Alto",
    SocioeconomicLevel.VERY_HIGH: "Muy alto",
}


class OriginStep(QWidget):
    """Paso 2 — edad de inicio, país, ciudad y origen socioeconómico."""

    step_complete = Signal(dict)
    step_back = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(theme.SPACE_LG)

        card = Card()
        title = QLabel("¿De dónde vienes?")
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_H1}px; font-weight: 800; color: {theme.TEXT_PRIMARY};"
        )
        subtitle = QLabel("El contexto en el que empiezas define muchas de tus posibilidades.")
        subtitle.setStyleSheet(f"color: {theme.TEXT_SECONDARY}; font-size: {theme.FONT_SIZE_BODY}px;")
        card.body_layout.addWidget(title)
        card.body_layout.addWidget(subtitle)
        card.body_layout.addSpacing(theme.SPACE_SM)

        # Edad de inicio
        age_label = QLabel("Edad al comenzar *")
        age_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;"
        )
        self._age_spin = QSpinBox()
        self._age_spin.setRange(1, 80)
        self._age_spin.setValue(18)
        self._age_spin.setStyleSheet(
            f"QSpinBox {{ border: 1px solid {theme.BORDER_STRONG}; border-radius: {theme.RADIUS_SM}px; "
            f"padding: 6px 10px; font-size: {theme.FONT_SIZE_BODY}px; "
            f"background: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; }}"
        )
        card.body_layout.addWidget(age_label)
        card.body_layout.addWidget(self._age_spin)

        self._country = self._labeled_input("País *", card)
        self._city = self._labeled_input("Ciudad *", card)

        # Origen socioeconómico
        socio_label = QLabel("Origen socioeconómico *")
        socio_label.setStyleSheet(
            f"color: {theme.TEXT_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-weight: 600;"
        )
        self._socio_combo = QComboBox()
        for level in SocioeconomicLevel:
            self._socio_combo.addItem(_SOCIO_LABELS[level], userData=level)
        self._socio_combo.setCurrentIndex(2)  # MEDIUM por defecto
        self._socio_combo.setStyleSheet(
            f"QComboBox {{ border: 1px solid {theme.BORDER_STRONG}; border-radius: {theme.RADIUS_SM}px; "
            f"padding: 6px 10px; font-size: {theme.FONT_SIZE_BODY}px; "
            f"background: {theme.SURFACE}; color: {theme.TEXT_PRIMARY}; }}"
        )
        card.body_layout.addWidget(socio_label)
        card.body_layout.addWidget(self._socio_combo)

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

        btn_next = QPushButton("Siguiente →")
        btn_next.setFixedHeight(44)
        btn_next.setStyleSheet(
            f"QPushButton {{ background-color: {theme.ACCENT_PURPLE}; color: {theme.TEXT_WHITE}; "
            f"border-radius: {theme.RADIUS_SM}px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY_HOVER}; }}"
        )
        btn_next.clicked.connect(self._handle_next)

        btn_row.addWidget(btn_back)
        btn_row.addStretch(1)
        btn_row.addWidget(btn_next)
        layout.addLayout(btn_row)
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
        country = self._country.text().strip()
        city = self._city.text().strip()
        if not country or not city:
            self._error_label.setText("El país y la ciudad son obligatorios.")
            self._error_label.show()
            return
        self._error_label.hide()
        selected_level = self._socio_combo.currentData()
        self.step_complete.emit({
            "starting_age": self._age_spin.value(),
            "country": country,
            "city": city,
            "socioeconomic_origin": selected_level,
        })

    def reset(self) -> None:
        self._age_spin.setValue(18)
        self._country.setText("")
        self._city.setText("")
        self._socio_combo.setCurrentIndex(2)
        self._error_label.hide()
